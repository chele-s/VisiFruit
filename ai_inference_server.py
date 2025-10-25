#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servidor de Inferencia FastAPI Optimizado - VisiFruit
======================================================

Servidor HTTP/2 de alto rendimiento para inferencia remota con múltiples modelos.
Diseñado para ejecutarse en una laptop/PC con GPU y servir a Raspberry Pi 5.

Modelos soportados:
- YOLOv8: Ultrarrápido, ideal para tiempo real (recomendado)
- RT-DETR: Mayor precisión, basado en transformers

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
- Ultralytics (YOLOv8/RT-DETR)
- CUDA (opcional, para GPU)

Autor(es): Gabriel Calderón, Elias Bautista
Fecha: Octubre 2025
Versión: 2.1 - Dual Model Edition
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

# Ultralytics (YOLOv8 / RT-DETR)
try:
    from ultralytics import YOLO, RTDETR
    import torch
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    print("⚠️ Ultralytics no disponible. Instala con: pip install ultralytics")

# RF-DETR (Roboflow - Local)
try:
    from rfdetr import RFDETRNano, RFDETRSmall, RFDETRMedium, RFDETRBase
    RFDETR_AVAILABLE = True
except ImportError:
    RFDETR_AVAILABLE = False
    print("⚠️ RF-DETR no disponible. Instala con: pip install rfdetr")

# Roboflow Inference (API REST - no requiere SDK especial)
# Usamos requests que ya está disponible
ROBOFLOW_INFERENCE_AVAILABLE = True  # Siempre disponible con requests

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
    # Modelo de IA - Selección de arquitectura
    # Opciones: "yolov8", "rtdetr", "rfdetr" (local), "roboflow" (Inference API)
    MODEL_TYPE = os.getenv("MODEL_TYPE", "yolov8").lower()
    MODEL_PATH = os.getenv("MODEL_PATH", "weights/best.pt")  # Ruta al modelo entrenado
    RFDETR_VARIANT = os.getenv("RFDETR_VARIANT", "base").lower()  # "nano", "small", "medium", "base"
    
    # Roboflow Inference API (para modelos entrenados en Roboflow)
    ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
    ROBOFLOW_PROJECT_ID = os.getenv("ROBOFLOW_PROJECT_ID", "")  # ej: "visifruit-gpdwu"
    ROBOFLOW_VERSION = os.getenv("ROBOFLOW_VERSION", "3")  # versión del modelo
    ROBOFLOW_API_URL = os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com")
    
    MODEL_DEVICE = os.getenv("MODEL_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
    MODEL_FP16 = os.getenv("MODEL_FP16", "true").lower() == "true" and MODEL_DEVICE == "cuda"
    
    # Autenticación
    AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    AUTH_TOKENS = os.getenv("AUTH_TOKENS", "visifruittoken2025,debugtoken").split(",")
    
    # Servidor
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "9000"))
    SERVER_WORKERS = int(os.getenv("SERVER_WORKERS", "1"))
    
    # Rate Limiting (aumentado para tiempo real: 30 FPS = 1800/minute)
    RATE_LIMIT = os.getenv("RATE_LIMIT", "1800/minute")
    
    # Optimización
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "1920"))
    JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "70"))
    
    # Cache
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", "60"))  # segundos
    
    # Visualización y logging
    LOG_EVERY_N_FRAMES = int(os.getenv("LOG_EVERY_N_FRAMES", "30"))  # Log cada N frames
    SAVE_ANNOTATED_FRAMES = os.getenv("SAVE_ANNOTATED_FRAMES", "false").lower() == "true"
    ANNOTATED_FRAMES_DIR = os.getenv("ANNOTATED_FRAMES_DIR", "logs/annotated_frames")
    ENABLE_MJPEG_STREAM = os.getenv("ENABLE_MJPEG_STREAM", "true").lower() == "true"
    STREAM_MAX_FPS = int(os.getenv("STREAM_MAX_FPS", "10"))
    STREAM_KEEPALIVE_MS = int(os.getenv("STREAM_KEEPALIVE_MS", "250"))


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
    """Servidor de inferencia multi-modelo (YOLOv8/RT-DETR)."""
    
    def __init__(self):
        self.model: Optional[YOLO] = None
        self.roboflow_api_key: Optional[str] = None  # API Key de Roboflow
        self.roboflow_model_id: Optional[str] = None  # Model ID (project/version)
        self.model_type: str = "Unknown"  # Se establece al cargar el modelo
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
        
        # Estadísticas de rendimiento en tiempo real
        self.perf_stats = {
            "frame_count": 0,
            "fps_start_time": time.time(),
            "current_fps": 0.0,
            "avg_latency_ms": 0.0,
            "detections_count": 0,
            "last_log_time": time.time()
        }
        
        # Para streaming MJPEG
        self.latest_annotated_frame: Optional[bytes] = None
        self.frame_condition: Optional[asyncio.Condition] = None
        self.last_frame_id = 0
        
        # Cache de resultados
        self.cache: Dict[str, Any] = {}
        self.cache_enabled = ServerConfig.ENABLE_CACHE
        
        logger.info(f"📊 Servidor configurado: Device={self.device}, FP16={self.fp16}")
    
    async def initialize(self):
        """Inicializa el modelo YOLOv8."""
        try:
            # Inicializar condition para streaming
            self.frame_condition = asyncio.Condition()
            try:
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Esperando frames...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                # Convertir BGR a RGB para navegadores web
                placeholder_rgb = cv2.cvtColor(placeholder, cv2.COLOR_BGR2RGB)
                _, buf = cv2.imencode('.jpg', placeholder_rgb, [cv2.IMWRITE_JPEG_QUALITY, ServerConfig.JPEG_QUALITY])
                self.latest_annotated_frame = buf.tobytes()
                self.last_frame_id = 0
            except Exception:
                pass
            
            # Validar tipo de modelo
            model_type = ServerConfig.MODEL_TYPE
            if model_type not in ["yolov8", "rtdetr", "rfdetr", "rfdetr_local", "roboflow"]:
                logger.warning(f"⚠️ Tipo de modelo '{model_type}' no válido. Usando YOLOv8 por defecto.")
                model_type = "yolov8"
            
            if model_type == "yolov8":
                model_name = "YOLOv8"
            elif model_type == "rtdetr":
                model_name = "RT-DETR"
            elif model_type == "roboflow":
                model_name = f"Roboflow RF-DETR API ({ServerConfig.ROBOFLOW_PROJECT_ID})"
            elif model_type == "rfdetr_local":
                model_name = "RF-DETR Local (Checkpoint de Roboflow)"
            else:
                model_name = f"RF-DETR-{ServerConfig.RFDETR_VARIANT.capitalize()}"
            
            logger.info(f"🔄 Cargando modelo {model_name}")
            
            # Verificar que el archivo existe (no requerido para RF-DETR pre-entrenado ni Roboflow)
            model_path = Path(ServerConfig.MODEL_PATH)
            if model_type in ["yolov8", "rtdetr"] and not model_path.exists():
                raise FileNotFoundError(f"Modelo no encontrado: {ServerConfig.MODEL_PATH}")
            
            if model_path.exists() and model_type not in ["roboflow"]:
                logger.info(f"📂 Usando pesos desde: {ServerConfig.MODEL_PATH}")
            
            # Cargar modelo según el tipo seleccionado
            if model_type == "rfdetr_local":
                # RF-DETR Local - Cargar checkpoint de Roboflow directamente
                if not model_path.exists():
                    raise FileNotFoundError(f"Modelo no encontrado: {ServerConfig.MODEL_PATH}")
                
                logger.info(f"📦 Cargando RF-DETR desde checkpoint de Roboflow")
                logger.info(f"   Archivo: {model_path}")
                
                try:
                    # Intentar cargar con Ultralytics YOLO (Roboflow a veces exporta así)
                    logger.info("🔄 Intentando carga con Ultralytics YOLO...")
                    self.model = YOLO(str(model_path))
                    self.model_type = "RF-DETR-Local-YOLO"
                    logger.info("✅ Modelo cargado con Ultralytics YOLO")
                    
                except Exception as e1:
                    logger.warning(f"⚠️ Carga con YOLO falló: {e1}")
                    
                    try:
                        # Intentar cargar con RTDETR
                        logger.info("🔄 Intentando carga con RT-DETR...")
                        self.model = RTDETR(str(model_path))
                        self.model_type = "RF-DETR-Local-RTDETR"
                        logger.info("✅ Modelo cargado con RT-DETR")
                        
                    except Exception as e2:
                        logger.error(f"❌ Carga con RT-DETR también falló: {e2}")
                        raise ValueError(
                            f"No se pudo cargar el modelo RF-DETR local.\n"
                            f"Error YOLO: {e1}\n"
                            f"Error RT-DETR: {e2}\n\n"
                            f"SOLUCIÓN: Usa MODEL_TYPE=roboflow para usar la API de Roboflow"
                        )
                
                self.model_loaded = True
                
            elif model_type == "roboflow":
                # Roboflow Inference API (REST)
                if not ServerConfig.ROBOFLOW_API_KEY:
                    raise ValueError("ROBOFLOW_API_KEY no configurado en .env")
                if not ServerConfig.ROBOFLOW_PROJECT_ID:
                    raise ValueError("ROBOFLOW_PROJECT_ID no configurado en .env")
                
                logger.info(f"🌐 Configurando Roboflow Inference API...")
                logger.info(f"   Proyecto: {ServerConfig.ROBOFLOW_PROJECT_ID}")
                logger.info(f"   Versión: {ServerConfig.ROBOFLOW_VERSION}")
                
                # Guardar configuración para usar en inferencia
                self.roboflow_api_key = ServerConfig.ROBOFLOW_API_KEY
                self.roboflow_model_id = f"{ServerConfig.ROBOFLOW_PROJECT_ID}/{ServerConfig.ROBOFLOW_VERSION}"
                
                self.model_type = f"Roboflow-{ServerConfig.ROBOFLOW_PROJECT_ID}"
                self.model_loaded = True
                logger.info("✅ Roboflow Inference configurado correctamente")
                
            elif model_type == "rfdetr":
                if not RFDETR_AVAILABLE:
                    raise ImportError("RF-DETR no está instalado. Instala con: pip install rfdetr")
                
                # Seleccionar variante de RF-DETR
                variant = ServerConfig.RFDETR_VARIANT
                
                # Cargar modelo con pesos personalizados si existen
                if model_path.exists():
                    logger.info(f"📦 Cargando modelo RF-DETR-{variant.capitalize()} con pesos personalizados")
                    logger.info(f"   Desde: {model_path}")
                    try:
                        # RF-DETR acepta checkpoint_path en el constructor
                        # Esto es la forma correcta de cargar pesos personalizados
                        checkpoint_path = str(model_path)
                        
                        # Inicializar modelo según variante con checkpoint personalizado
                        if variant == "nano":
                            self.model = RFDETRNano(checkpoint_path=checkpoint_path)
                        elif variant == "small":
                            self.model = RFDETRSmall(checkpoint_path=checkpoint_path)
                        elif variant == "medium":
                            self.model = RFDETRMedium(checkpoint_path=checkpoint_path)
                        else:  # base por defecto
                            self.model = RFDETRBase(checkpoint_path=checkpoint_path)
                        
                        logger.info("✅ Pesos personalizados cargados correctamente")
                        
                    except Exception as e:
                        logger.error(f"❌ Error cargando pesos personalizados: {e}")
                        logger.info("📦 Usando checkpoint pre-entrenado de Roboflow como fallback...")
                        
                        # Fallback a checkpoint pre-entrenado (sin checkpoint_path)
                        if variant == "nano":
                            self.model = RFDETRNano()
                        elif variant == "small":
                            self.model = RFDETRSmall()
                        elif variant == "medium":
                            self.model = RFDETRMedium()
                        else:
                            self.model = RFDETRBase()
                else:
                    # No hay pesos custom, usar checkpoint pre-entrenado de Roboflow
                    logger.info(f"📦 Usando checkpoint pre-entrenado de Roboflow COCO")
                    logger.info(f"   Variante: RF-DETR-{variant.capitalize()}")
                    
                    # Inicializar sin checkpoint_path usa pesos pre-entrenados de Roboflow
                    if variant == "nano":
                        self.model = RFDETRNano()
                    elif variant == "small":
                        self.model = RFDETRSmall()
                    elif variant == "medium":
                        self.model = RFDETRMedium()
                    else:  # base por defecto
                        self.model = RFDETRBase()
                
                self.model_type = f"RF-DETR-{variant.capitalize()}"
                
                # Optimizar para inferencia
                try:
                    self.model.optimize_for_inference()
                    logger.info("⚡ Modelo optimizado para inferencia (hasta 2x más rápido)")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo optimizar para inferencia: {e}")
                    
            elif model_type == "rtdetr":
                if not ULTRALYTICS_AVAILABLE:
                    raise ImportError("Ultralytics no está instalado")
                try:
                    # Intentar carga directa
                    self.model = RTDETR(str(model_path))
                    self.model_type = "RT-DETR"
                except Exception as e:
                    # Si falla, intentar cargar como YOLO (algunos modelos RT-DETR se guardan así)
                    logger.warning(f"⚠️ Carga directa RT-DETR falló: {e}")
                    logger.info("🔄 Intentando carga alternativa...")
                    self.model = YOLO(str(model_path))
                    self.model_type = "RT-DETR (cargado como YOLO)"
            else:  # yolov8
                if not ULTRALYTICS_AVAILABLE:
                    raise ImportError("Ultralytics no está instalado")
                self.model = YOLO(str(model_path))
                self.model_type = "YOLOv8"
            
            # Configurar dispositivo
            if self.device == "cuda" and torch.cuda.is_available():
                logger.info(f"🎮 GPU detectada: {torch.cuda.get_device_name(0)}")
                # El modelo se mueve automáticamente al dispositivo en predict()
            else:
                logger.info("💻 Usando CPU para inferencia")
                self.device = "cpu"
                self.fp16 = False
            
            # Warmup (solo para modelos locales, no para Roboflow API)
            if "Roboflow" not in self.model_type:
                await self._warmup()
            
            self.model_loaded = True
            logger.info(f"✅ Modelo {self.model_type} cargado y listo")
            
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
    
    def _verify_color_space(self, image: np.ndarray) -> np.ndarray:
        """
        Verifica y corrige el espacio de color de la imagen.
        Detecta si los canales RGB/BGR están invertidos.
        
        Args:
            image: Imagen a verificar
            
        Returns:
            Imagen con espacio de color corregido
        """
        try:
            # Calcular dominancia de canales en una pequeña muestra
            sample = image[::10, ::10]  # Submuestreo para velocidad
            
            # Calcular promedios de cada canal
            b_mean = np.mean(sample[:, :, 0])
            g_mean = np.mean(sample[:, :, 1])
            r_mean = np.mean(sample[:, :, 2])
            
            # Detectar inversión RGB/BGR
            # Múltiples heurísticas para detectar inversión:
            
            # 1. Canal rojo dominante cuando debería ser azul (común en cámaras RGB)
            if r_mean > b_mean * 1.2 and r_mean > 100:
                logger.debug("🔄 Inversión RGB→BGR detectada, corrigiendo...")
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                return image
            
            # 2. Detectar tonos rosados/magentas anormales (típico de inversión)
            # Si hay mucho magenta/rosa (R+B alto, G bajo), probablemente está invertido
            magenta_intensity = (r_mean + b_mean) / 2
            if magenta_intensity > g_mean * 1.5 and magenta_intensity > 120:
                logger.debug("🔄 Tonos magenta detectados, invirtiendo canales...")
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                return image
            
            return image
        except Exception as e:
            logger.debug(f"Error verificando espacio de color: {e}")
            return image
    
    async def infer(self, image: np.ndarray, params: InferenceRequest) -> InferenceResponse:
        """Realiza inferencia en una imagen."""
        start_time = time.time()
        self.stats["requests_total"] += 1
        
        try:
            # Verificar y corregir espacio de color si está invertido
            # Esto corrige el problema de colores rosados/magentas de la cámara
            image = self._verify_color_space(image)
            
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
            
            # Inferencia (diferente según el tipo de modelo)
            inference_start = time.time()
            
            # Determinar tipo de modelo
            is_rfdetr = "RF-DETR" in self.model_type
            is_roboflow = "Roboflow" in self.model_type
            
            if is_roboflow:
                # Roboflow Inference API (REST)
                import requests
                from PIL import Image as PILImage
                import base64
                from io import BytesIO
                
                # Convertir BGR a RGB para Roboflow
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = PILImage.fromarray(image_rgb)
                
                # Encodear imagen a base64 para la API
                buffered = BytesIO()
                pil_image.save(buffered, format="JPEG", quality=95)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # Hacer inferencia via API REST de Roboflow
                api_url = f"{ServerConfig.ROBOFLOW_API_URL}/{self.roboflow_model_id}"
                
                # Roboflow espera la imagen directamente en el body
                response = requests.post(
                    api_url,
                    params={
                        "api_key": self.roboflow_api_key,
                        "confidence": int(params.conf * 100),  # Roboflow espera 0-100
                        "overlap": int(params.iou * 100)
                    },
                    data=img_base64,  # Enviar base64 directamente
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                response.raise_for_status()  # Lanzar error si falla
                roboflow_results = response.json()
                
                results = None
                detections_sv = None
                
            elif is_rfdetr:
                # RF-DETR usa API diferente - devuelve supervision.Detections directamente
                # Necesita imagen en formato PIL o RGB numpy array
                from PIL import Image as PILImage
                
                # Convertir BGR (OpenCV) a RGB para RF-DETR
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = PILImage.fromarray(image_rgb)
                
                # RF-DETR predict devuelve supervision.Detections
                detections_sv = self.model.predict(pil_image, threshold=params.conf)
                results = None  # RF-DETR no usa formato Results de Ultralytics
                roboflow_results = None
                
            else:
                # YOLO/RT-DETR usan API de Ultralytics
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
                detections_sv = None
                roboflow_results = None
            
            inference_ms = (time.time() - inference_start) * 1000
            
            # Post-procesamiento
            post_start = time.time()
            
            # Obtener nombres de clases
            class_names = params.class_names_json
            if class_names:
                try:
                    class_names = json.loads(class_names)
                except:
                    class_names = ["apple", "pear", "lemon"]
            else:
                class_names = ["apple", "pear", "lemon"]
            
            detections = []
            
            # Procesar según tipo de modelo
            if is_roboflow and roboflow_results:
                # Roboflow Inference API devuelve formato específico
                predictions = roboflow_results.get("predictions", [])
                
                for i, pred in enumerate(predictions):
                    try:
                        # Extraer datos de la predicción de Roboflow
                        x_center = pred.get("x", 0)
                        y_center = pred.get("y", 0)
                        width = pred.get("width", 0)
                        height = pred.get("height", 0)
                        
                        # Convertir de formato centro+tamaño a xyxy
                        x1 = int(x_center - width / 2)
                        y1 = int(y_center - height / 2)
                        x2 = int(x_center + width / 2)
                        y2 = int(y_center + height / 2)
                        
                        confidence = float(pred.get("confidence", 0))
                        class_name = pred.get("class", "unknown")
                        
                        # Buscar class_id en class_names
                        try:
                            class_id = class_names.index(class_name) if class_name in class_names else 0
                        except:
                            class_id = 0
                        
                        # Centro y área
                        cx = int(x_center)
                        cy = int(y_center)
                        area = width * height
                        
                        detection = Detection(
                            class_id=class_id,
                            class_name=class_name,
                            confidence=confidence,
                            bbox=[x1, y1, x2, y2],
                            area=int(area),
                            center=[cx, cy]
                        )
                        
                        detections.append(detection)
                        
                    except Exception as e:
                        logger.warning(f"Error procesando detección Roboflow {i}: {e}")
                        
            elif is_rfdetr and detections_sv is not None:
                # RF-DETR devuelve supervision.Detections
                if len(detections_sv) > 0:
                    for i in range(len(detections_sv.xyxy)):
                        try:
                            # Extraer datos de supervision.Detections
                            box_xyxy = detections_sv.xyxy[i]
                            confidence = float(detections_sv.confidence[i])
                            class_id = int(detections_sv.class_id[i])
                            
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
                            logger.warning(f"Error procesando detección RF-DETR {i}: {e}")
                            
            elif results and len(results) > 0:
                # YOLO/RT-DETR devuelven formato Ultralytics
                result = results[0]
                if result.boxes is not None:
                    boxes = result.boxes
                    
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
                            logger.warning(f"Error procesando detección YOLO/RT-DETR {i}: {e}")
            
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
            
            # Actualizar estadísticas de rendimiento
            self.perf_stats["frame_count"] += 1
            self.perf_stats["detections_count"] += len(detections)
            
            # Calcular FPS
            elapsed = time.time() - self.perf_stats["fps_start_time"]
            if elapsed > 0:
                self.perf_stats["current_fps"] = self.perf_stats["frame_count"] / elapsed
            
            # Calcular latencia promedio
            if self.stats["requests_success"] > 0:
                self.perf_stats["avg_latency_ms"] = self.stats["total_inference_time_ms"] / self.stats["requests_success"]
            
            # Logging frecuente cada N frames
            if self.perf_stats["frame_count"] % ServerConfig.LOG_EVERY_N_FRAMES == 0:
                logger.info(
                    f"📊 FPS: {self.perf_stats['current_fps']:.1f} | "
                    f"Latencia: {self.perf_stats['avg_latency_ms']:.1f}ms | "
                    f"Frames: {self.perf_stats['frame_count']} | "
                    f"Detecciones: {self.perf_stats['detections_count']}"
                )
            
            # Log individual si hay detecciones
            if len(detections) > 0:
                logger.info(f"✅ {len(detections)} frutas en {total_ms:.1f}ms "
                          f"(inf:{inference_ms:.1f}ms) | FPS: {self.perf_stats['current_fps']:.1f}")
            
            # Crear frame anotado para streaming
            if ServerConfig.ENABLE_MJPEG_STREAM or ServerConfig.SAVE_ANNOTATED_FRAMES:
                annotated_img = self._create_annotated_image(image.copy(), detections)
                
                # Guardar frame si está habilitado
                if ServerConfig.SAVE_ANNOTATED_FRAMES and len(detections) > 0:
                    self._save_annotated_frame(annotated_img, detections)
                
                # Encodear para streaming
                if ServerConfig.ENABLE_MJPEG_STREAM:
                    # Convertir BGR a RGB para navegadores web
                    annotated_img_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
                    _, buffer = cv2.imencode('.jpg', annotated_img_rgb, 
                                            [cv2.IMWRITE_JPEG_QUALITY, ServerConfig.JPEG_QUALITY])
                    self.latest_annotated_frame = buffer.tobytes()
                    self.last_frame_id += 1
                    # Notificar a TODOS los consumidores que hay un frame nuevo
                    if self.frame_condition is not None:
                        async with self.frame_condition:
                            self.frame_condition.notify_all()
            
            return response
            
        except Exception as e:
            self.stats["requests_failed"] += 1
            logger.error(f"❌ Error en inferencia: {e}")
            raise
    
    def _create_annotated_image(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Crea una imagen anotada con bounding boxes."""
        # Colores por clase (formato BGR para OpenCV)
        colors = {
            "apple": (0, 255, 0),    # Verde (BGR)
            "pear": (255, 0, 0),     # Azul (BGR)
            "lemon": (0, 255, 255),  # Amarillo (BGR)
            "unknown": (128, 128, 128)  # Gris (BGR)
        }
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = colors.get(det.class_name, (255, 255, 255))
            
            # Dibujar bbox
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Etiqueta
            label = f"{det.class_name} {det.confidence:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            # Fondo para el texto
            cv2.rectangle(image, (x1, y1 - h - 4), (x1 + w, y1), color, -1)
            cv2.putText(image, label, (x1, y1 - 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Agregar info de FPS y stats
        info_text = f"FPS: {self.perf_stats['current_fps']:.1f} | Detecciones: {len(detections)}"
        cv2.putText(image, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return image
    
    def _save_annotated_frame(self, image: np.ndarray, detections: List[Detection]):
        """Guarda frame anotado en disco."""
        try:
            save_dir = Path(ServerConfig.ANNOTATED_FRAMES_DIR)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"detection_{timestamp}_{len(detections)}fruits.jpg"
            filepath = save_dir / filename
            
            cv2.imwrite(str(filepath), image, 
                       [cv2.IMWRITE_JPEG_QUALITY, ServerConfig.JPEG_QUALITY])
            logger.debug(f"💾 Frame guardado: {filepath}")
        except Exception as e:
            logger.warning(f"Error guardando frame: {e}")
    
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
    conf: float = Form(0.2),
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
    
    # Agregar estadísticas de rendimiento
    stats.update({
        "fps": inference_server.perf_stats["current_fps"],
        "total_detections": inference_server.perf_stats["detections_count"],
        "frames_processed": inference_server.perf_stats["frame_count"]
    })
    
    return stats


@app.get("/stream")
async def mjpeg_stream():
    """
    Streaming MJPEG en vivo con bounding boxes.
    
    Accede a esta URL en tu navegador para ver las detecciones en tiempo real:
    http://TU_IP:9000/stream
    """
    from fastapi.responses import StreamingResponse
    
    if not ServerConfig.ENABLE_MJPEG_STREAM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Streaming MJPEG deshabilitado"
        )
    
    async def generate_frames():
        """Generador de frames MJPEG con keepalive y límite de FPS por cliente."""
        last_sent_frame_id = -1
        last_send_time = 0.0
        min_interval = 1.0 / ServerConfig.STREAM_MAX_FPS if ServerConfig.STREAM_MAX_FPS > 0 else 0.0
        keepalive_s = ServerConfig.STREAM_KEEPALIVE_MS / 1000.0

        while True:
            async with inference_server.frame_condition:
                try:
                    await asyncio.wait_for(inference_server.frame_condition.wait(), timeout=keepalive_s)
                except asyncio.TimeoutError:
                    pass

                now = time.time()
                if (inference_server.latest_annotated_frame is not None and 
                    (inference_server.last_frame_id != last_sent_frame_id or (now - last_send_time) >= keepalive_s)):

                    if min_interval > 0 and (now - last_send_time) < min_interval:
                        await asyncio.sleep(min_interval - (now - last_send_time))
                        now = time.time()

                    last_sent_frame_id = inference_server.last_frame_id
                    frame_data = inference_server.latest_annotated_frame
                    last_send_time = now

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Cache-Control: no-cache, no-store, must-revalidate\r\n'
                           b'Pragma: no-cache\r\n'
                           b'Expires: 0\r\n'
                           b'X-Frame-ID: ' + str(last_sent_frame_id).encode() + b'\r\n'
                           b'\r\n' + 
                           frame_data + b'\r\n')
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",  # Deshabilitar buffering en nginx
            "Connection": "keep-alive"
        }
    )


@app.get("/perf")
async def get_performance_stats():
    """
    Obtiene estadísticas de rendimiento en tiempo real.
    No requiere autenticación para facilitar monitoreo.
    """
    perf = inference_server.perf_stats.copy()
    
    # Agregar más métricas útiles
    uptime = time.time() - inference_server.stats["startup_time"]
    
    return {
        "fps": round(perf["current_fps"], 2),
        "avg_latency_ms": round(perf["avg_latency_ms"], 2),
        "frames_processed": perf["frame_count"],
        "total_detections": perf["detections_count"],
        "uptime_seconds": round(uptime, 1),
        "requests_total": inference_server.stats["requests_total"],
        "requests_success": inference_server.stats["requests_success"],
        "timestamp": datetime.now().isoformat()
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    # Log de configuración
    logger.info("=" * 60)
    logger.info("🎯 CONFIGURACIÓN DEL SERVIDOR")
    if ServerConfig.MODEL_TYPE == "yolov8":
        model_type_display = "YOLOv8"
    elif ServerConfig.MODEL_TYPE == "rtdetr":
        model_type_display = "RT-DETR"
    elif ServerConfig.MODEL_TYPE == "rfdetr":
        model_type_display = f"RF-DETR-{ServerConfig.RFDETR_VARIANT.capitalize()}"
    else:
        model_type_display = ServerConfig.MODEL_TYPE.upper()
    logger.info(f"   Arquitectura: {model_type_display}")
    logger.info(f"   Modelo: {ServerConfig.MODEL_PATH}")
    logger.info(f"   Device: {ServerConfig.MODEL_DEVICE}")
    logger.info(f"   FP16: {ServerConfig.MODEL_FP16}")
    logger.info(f"   Autenticación: {ServerConfig.AUTH_ENABLED}")
    logger.info(f"   Host: {ServerConfig.SERVER_HOST}")
    logger.info(f"   Puerto: {ServerConfig.SERVER_PORT}")
    logger.info(f"   Rate Limit: {ServerConfig.RATE_LIMIT}")
    logger.info("")
    logger.info("📊 VISUALIZACIÓN Y RENDIMIENTO")
    logger.info(f"   Log cada N frames: {ServerConfig.LOG_EVERY_N_FRAMES}")
    logger.info(f"   Streaming MJPEG: {ServerConfig.ENABLE_MJPEG_STREAM}")
    logger.info(f"   Guardar frames: {ServerConfig.SAVE_ANNOTATED_FRAMES}")
    if ServerConfig.SAVE_ANNOTATED_FRAMES:
        logger.info(f"   Directorio: {ServerConfig.ANNOTATED_FRAMES_DIR}")
    logger.info("")
    logger.info("🌐 ENDPOINTS DISPONIBLES")
    logger.info(f"   http://{ServerConfig.SERVER_HOST}:{ServerConfig.SERVER_PORT}/health")
    logger.info(f"   http://{ServerConfig.SERVER_HOST}:{ServerConfig.SERVER_PORT}/infer")
    logger.info(f"   http://{ServerConfig.SERVER_HOST}:{ServerConfig.SERVER_PORT}/stats")
    logger.info(f"   http://{ServerConfig.SERVER_HOST}:{ServerConfig.SERVER_PORT}/perf")
    if ServerConfig.ENABLE_MJPEG_STREAM:
        logger.info(f"   🎥 http://{ServerConfig.SERVER_HOST}:{ServerConfig.SERVER_PORT}/stream")
    logger.info("=" * 60)
    
    # Ejecutar servidor con optimizaciones para streaming
    uvicorn.run(
        "ai_inference_server:app",
        host=ServerConfig.SERVER_HOST,
        port=ServerConfig.SERVER_PORT,
        workers=ServerConfig.SERVER_WORKERS,
        reload=False,
        access_log=False,  # Desactivar access log para mejor rendimiento
        log_level="info",
        timeout_keep_alive=75,
        # Optimizaciones para streaming de baja latencia
        limit_concurrency=100,
        backlog=2048
    )
