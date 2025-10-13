#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor de Inferencia FastAPI Optimizado - VisiFruit
======================================================

Servidor HTTP/2 de alto rendimiento para inferencia remota de YOLOv8.
Diseñado para ejecutarse en una laptop/PC con GPU y servir a Raspberry Pi 5.

Características:
- FastAPI con soporte HTTP/2
- Autenticación por tokens Bearer
- Compresión de respuestas
- Cache de modelos
- Métricas de rendimiento
- Health checks
- Rate limiting inteligente
- Logging detallado

Requisitos:
- Python 3.8+
- FastAPI, Uvicorn
- YOLOv8 (ultralytics)
- CUDA (opcional, para GPU)

Autor(es): Gabriel Calderón, Elias Bautista
Fecha: Octubre 2025
Versión: 2.0 - Enterprise Edition
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import time
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import numpy as np
import cv2
import psutil
import GPUtil
from contextlib import asynccontextmanager

# FastAPI y dependencias
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# YOLOv8
try:
    from ultralytics import YOLO
    import torch
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ YOLOv8 no disponible. Instala con: pip install ultralytics")

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==================== CONFIGURACIÓN ====================

class ServerConfig:
    """Configuración del servidor de inferencia."""
    # Modelo YOLOv8
    MODEL_PATH = os.getenv("MODEL_PATH", "weights/best.pt")
    MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    MODEL_FP16 = os.getenv("MODEL_FP16", "true").lower() == "true" and MODEL_DEVICE == "cuda"
    
    # Autenticación
    AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    AUTH_TOKENS = os.getenv("AUTH_TOKENS", "visifruittoken2025,debugtoken").split(",")
    
    # Servidor
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "9000"))
    SERVER_WORKERS = int(os.getenv("SERVER_WORKERS", "1"))
    
    # Rate Limiting
    RATE_LIMIT = os.getenv("RATE_LIMIT", "60/minute")
    
    # Optimización
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "1920"))
    JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "85"))
    
    # Cache
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))  # segundos


# ==================== MODELOS DE DATOS ====================

class InferenceRequest(BaseModel):
    """Modelo para solicitud de inferencia."""
    imgsz: int = Field(default=640, ge=320, le=1280)
    conf: float = Field(default=0.5, ge=0.0, le=1.0)
    iou: float = Field(default=0.45, ge=0.0, le=1.0)
    max_det: int = Field(default=100, ge=1, le=300)
    class_names_json: Optional[str] = None


class Detection(BaseModel):
    """Modelo para una detección individual."""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    area: Optional[int] = None
    center: Optional[List[int]] = None  # [cx, cy]


class InferenceResponse(BaseModel):
    """Modelo para respuesta de inferencia."""
    success: bool
    detections: List[Detection]
    inference_ms: float
    pre_ms: float
    post_ms: float
    total_ms: float
    model_device: str
    timestamp: str


class HealthResponse(BaseModel):
    """Modelo para respuesta de health check."""
    status: str
    model_loaded: bool
    device: str
    gpu_available: bool
    cpu_percent: float
    memory_percent: float
    gpu_memory_mb: Optional[float] = None
    uptime_seconds: float
    requests_served: int


# ==================== SERVIDOR DE INFERENCIA ====================

class InferenceServer:
    """Servidor de inferencia YOLOv8 optimizado."""
    
    def __init__(self):
        self.model: Optional[YOLO] = None
        self.model_loaded = False
        self.device = ServerConfig.MODEL_DEVICE
        self.fp16 = ServerConfig.MODEL_FP16
        
        # Estadísticas
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "total_inference_time_ms": 0.0,
            "startup_time": time.time()
        }
        
        # Cache de resultados
        self.cache: Dict[str, Any] = {}
        self.cache_enabled = ServerConfig.ENABLE_CACHE
        
        logger.info(f"📊 Servidor configurado: Device={self.device}, FP16={self.fp16}")
    
    async def initialize(self):
        """Inicializa el modelo YOLOv8."""
        try:
            if not YOLO_AVAILABLE:
                raise ImportError("YOLOv8 no está instalado")
            
            logger.info(f"🔄 Cargando modelo YOLOv8 desde {ServerConfig.MODEL_PATH}")
            
            # Verificar que el archivo existe
            model_path = Path(ServerConfig.MODEL_PATH)
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo no encontrado: {ServerConfig.MODEL_PATH}")
            
            # Cargar modelo
            self.model = YOLO(str(model_path))
            
            # Configurar dispositivo
            if self.device == "cuda" and torch.cuda.is_available():
                logger.info(f"🎮 GPU detectada: {torch.cuda.get_device_name(0)}")
                # El modelo se mueve automáticamente al dispositivo en predict()
            else:
                logger.info("💻 Usando CPU para inferencia")
                self.device = "cpu"
                self.fp16 = False
            
            # Warmup
            await self._warmup()
            
            self.model_loaded = True
            logger.info("✅ Modelo YOLOv8 cargado y listo")
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            self.model_loaded = False
            raise
    
    async def _warmup(self):
        """Realiza warmup del modelo."""
        logger.info("🔥 Realizando warmup del modelo...")
        
        # Crear imagen dummy
        dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # Ejecutar 3 inferencias de warmup
        for i in range(3):
            start = time.time()
            _ = self.model.predict(
                dummy_img,
                imgsz=640,
                conf=0.5,
                device=self.device,
                half=self.fp16,
                verbose=False
            )
            warmup_time = (time.time() - start) * 1000
            logger.info(f"   Warmup {i+1}/3: {warmup_time:.1f}ms")
    
    def _calculate_image_hash(self, image: np.ndarray) -> str:
        """Calcula hash de la imagen para cache."""
        # Reducir imagen para hash más rápido
        small = cv2.resize(image, (64, 64))
        return hashlib.md5(small.tobytes()).hexdigest()
    
    async def infer(self, image: np.ndarray, params: InferenceRequest) -> InferenceResponse:
        """Realiza inferencia en una imagen."""
        start_time = time.time()
        self.stats["requests_total"] += 1
        
        try:
            # Verificar cache si está habilitado
            if self.cache_enabled:
                img_hash = self._calculate_image_hash(image)
                cache_key = f"{img_hash}_{params.imgsz}_{params.conf}_{params.iou}"
                
                if cache_key in self.cache:
                    cached = self.cache[cache_key]
                    # Verificar TTL
                    if time.time() - cached["timestamp"] < ServerConfig.CACHE_TTL:
                        logger.debug("✨ Resultado desde cache")
                        self.stats["requests_success"] += 1
                        return cached["response"]
            
            # Pre-procesamiento
            pre_start = time.time()
            
            # Redimensionar si es necesario
            h, w = image.shape[:2]
            if max(h, w) > ServerConfig.MAX_IMAGE_SIZE:
                scale = ServerConfig.MAX_IMAGE_SIZE / max(h, w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                image = cv2.resize(image, (new_w, new_h))
                logger.debug(f"Imagen redimensionada de {w}x{h} a {new_w}x{new_h}")
            
            pre_ms = (time.time() - pre_start) * 1000
            
            # Inferencia
            inference_start = time.time()
            
            results = self.model.predict(
                image,
                imgsz=params.imgsz,
                conf=params.conf,
                iou=params.iou,
                max_det=params.max_det,
                device=self.device,
                half=self.fp16,
                verbose=False
            )
            
            inference_ms = (time.time() - inference_start) * 1000
            
            # Post-procesamiento
            post_start = time.time()
            
            detections = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    boxes = result.boxes
                    
                    # Obtener nombres de clases
                    class_names = params.class_names_json
                    if class_names:
                        try:
                            class_names = json.loads(class_names)
                        except:
                            class_names = ["apple", "pear", "lemon"]
                    else:
                        class_names = ["apple", "pear", "lemon"]
                    
                    for i in range(len(boxes)):
                        try:
                            # Extraer datos
                            box_xyxy = boxes.xyxy[i].cpu().numpy()
                            confidence = float(boxes.conf[i].cpu().numpy())
                            class_id = int(boxes.cls[i].cpu().numpy())
                            
                            # Coordenadas
                            x1, y1, x2, y2 = map(int, box_xyxy)
                            
                            # Centro y área
                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)
                            area = (x2 - x1) * (y2 - y1)
                            
                            # Nombre de clase
                            class_name = class_names[class_id] if class_id < len(class_names) else "unknown"
                            
                            detection = Detection(
                                class_id=class_id,
                                class_name=class_name,
                                confidence=confidence,
                                bbox=[x1, y1, x2, y2],
                                area=area,
                                center=[cx, cy]
                            )
                            
                            detections.append(detection)
                            
                        except Exception as e:
                            logger.warning(f"Error procesando detección {i}: {e}")
            
            post_ms = (time.time() - post_start) * 1000
            total_ms = (time.time() - start_time) * 1000
            
            # Actualizar estadísticas
            self.stats["requests_success"] += 1
            self.stats["total_inference_time_ms"] += inference_ms
            
            # Crear respuesta
            response = InferenceResponse(
                success=True,
                detections=detections,
                inference_ms=inference_ms,
                pre_ms=pre_ms,
                post_ms=post_ms,
                total_ms=total_ms,
                model_device=self.device,
                timestamp=datetime.now().isoformat()
            )
            
            # Guardar en cache si está habilitado
            if self.cache_enabled and 'cache_key' in locals():
                self.cache[cache_key] = {
                    "response": response,
                    "timestamp": time.time()
                }
                
                # Limpiar cache antiguo
                if len(self.cache) > 100:
                    # Eliminar entradas más antiguas
                    oldest_keys = sorted(self.cache.keys(), 
                                       key=lambda k: self.cache[k]["timestamp"])[:20]
                    for key in oldest_keys:
                        del self.cache[key]
            
            # Log de rendimiento
            if len(detections) > 0:
                logger.info(f"✅ Inferencia: {len(detections)} frutas en {total_ms:.1f}ms "
                          f"(pre:{pre_ms:.1f}ms, inf:{inference_ms:.1f}ms, post:{post_ms:.1f}ms)")
            
            return response
            
        except Exception as e:
            self.stats["requests_failed"] += 1
            logger.error(f"❌ Error en inferencia: {e}")
            raise
    
    def get_health_status(self) -> HealthResponse:
        """Obtiene el estado de salud del servidor."""
        uptime = time.time() - self.stats["startup_time"]
        
        # CPU y memoria
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # GPU (si está disponible)
        gpu_memory_mb = None
        if self.device == "cuda" and torch.cuda.is_available():
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_memory_mb = gpus[0].memoryUsed
            except:
                pass
        
        return HealthResponse(
            status="ok" if self.model_loaded else "error",
            model_loaded=self.model_loaded,
            device=self.device,
            gpu_available=torch.cuda.is_available(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            gpu_memory_mb=gpu_memory_mb,
            uptime_seconds=uptime,
            requests_served=self.stats["requests_success"]
        )


# ==================== AUTENTICACIÓN ====================

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica el token de autenticación."""
    if not ServerConfig.AUTH_ENABLED:
        return True
    
    token = credentials.credentials
    if token not in ServerConfig.AUTH_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token inválido"
        )
    return token


# ==================== APLICACIÓN FASTAPI ====================

# Instancia del servidor
inference_server = InferenceServer()

# Limiter para rate limiting
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación."""
    # Startup
    logger.info("🚀 Iniciando servidor de inferencia VisiFruit...")
    await inference_server.initialize()
    yield
    # Shutdown
    logger.info("🛑 Apagando servidor...")

# Crear aplicación FastAPI
app = FastAPI(
    title="VisiFruit AI Inference Server",
    description="Servidor de inferencia YOLOv8 optimizado para detección de frutas",
    version="2.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "service": "VisiFruit AI Inference Server",
        "version": "2.0",
        "status": "running" if inference_server.model_loaded else "initializing"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check del servidor."""
    return inference_server.get_health_status()


@app.post("/infer")
@limiter.limit(ServerConfig.RATE_LIMIT)
async def infer(
    request: Request,
    image: UploadFile = File(...),
    imgsz: int = Form(640),
    conf: float = Form(0.5),
    iou: float = Form(0.45),
    max_det: int = Form(100),
    class_names_json: Optional[str] = Form(None),
    token: str = Depends(verify_token)
):
    """
    Realiza inferencia en una imagen.
    
    Args:
        image: Archivo de imagen (JPEG/PNG)
        imgsz: Tamaño de entrada del modelo (320-1280)
        conf: Umbral de confianza (0.0-1.0)
        iou: Umbral de IoU para NMS (0.0-1.0)
        max_det: Máximo número de detecciones (1-300)
        class_names_json: Nombres de clases en formato JSON
    
    Returns:
        Resultado de inferencia con detecciones
    """
    try:
        # Verificar que el modelo está cargado
        if not inference_server.model_loaded:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Modelo no está cargado"
            )
        
        # Leer imagen
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Imagen inválida"
            )
        
        # Crear request
        params = InferenceRequest(
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            max_det=max_det,
            class_names_json=class_names_json
        )
        
        # Realizar inferencia
        result = await inference_server.infer(img, params)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint de inferencia: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/stats")
async def get_stats(token: str = Depends(verify_token)):
    """Obtiene estadísticas del servidor."""
    stats = inference_server.stats.copy()
    
    # Calcular promedios
    if stats["requests_success"] > 0:
        stats["avg_inference_ms"] = stats["total_inference_time_ms"] / stats["requests_success"]
    else:
        stats["avg_inference_ms"] = 0
    
    # Tasa de éxito
    if stats["requests_total"] > 0:
        stats["success_rate"] = stats["requests_success"] / stats["requests_total"]
    else:
        stats["success_rate"] = 0
    
    return stats


# ==================== MAIN ====================

if __name__ == "__main__":
    # Log de configuración
    logger.info("=" * 60)
    logger.info("🎯 CONFIGURACIÓN DEL SERVIDOR")
    logger.info(f"   Modelo: {ServerConfig.MODEL_PATH}")
    logger.info(f"   Device: {ServerConfig.MODEL_DEVICE}")
    logger.info(f"   FP16: {ServerConfig.MODEL_FP16}")
    logger.info(f"   Autenticación: {ServerConfig.AUTH_ENABLED}")
    logger.info(f"   Host: {ServerConfig.SERVER_HOST}")
    logger.info(f"   Puerto: {ServerConfig.SERVER_PORT}")
    logger.info(f"   Rate Limit: {ServerConfig.RATE_LIMIT}")
    logger.info("=" * 60)
    
    # Ejecutar servidor
    uvicorn.run(
        "ai_inference_server:app",
        host=ServerConfig.SERVER_HOST,
        port=ServerConfig.SERVER_PORT,
        workers=ServerConfig.SERVER_WORKERS,
        reload=False,
        access_log=True
    )
