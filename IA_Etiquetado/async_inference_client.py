#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente de Inferencia Asíncrono Optimizado para Raspberry Pi 5
==============================================================

Cliente HTTP asíncrono ultra-optimizado para comunicación con servidor de IA.
Reemplaza el cliente síncrono con requests por uno asíncrono con httpx.

Características:
- HTTP/2 y multiplexing para mejor rendimiento
- Circuit breaker inteligente
- Compresión de imágenes adaptativa
- Token de autenticación
- Timeouts optimizados
- Pool de conexiones reutilizables
- Fallback inteligente

Autor(es): Gabriel Calderón, Elias Bautista
Fecha: Octubre 2025
Versión: 2.0 - Async Edition
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import cv2
from datetime import datetime, timedelta

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️ httpx no disponible. Instala con: pip install httpx")

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del Circuit Breaker."""
    CLOSED = "closed"  # Funcionando normal
    OPEN = "open"      # Falla detectada, rechazando peticiones
    HALF_OPEN = "half_open"  # Probando recuperación


@dataclass
class CircuitBreaker:
    """Circuit Breaker para manejo inteligente de fallos."""
    failure_threshold: int = 5
    timeout_seconds: float = 30.0
    half_open_requests: int = 1
    
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    failure_count: int = field(default=0, init=False)
    last_failure_time: Optional[float] = field(default=None, init=False)
    half_open_count: int = field(default=0, init=False)
    
    def record_success(self):
        """Registra una operación exitosa."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("🟢 Circuit Breaker: CLOSED (recuperado)")
        self.failure_count = 0
    
    def record_failure(self):
        """Registra una falla."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"🔴 Circuit Breaker: OPEN (fallos: {self.failure_count})")
    
    def can_attempt(self) -> bool:
        """Verifica si se puede intentar una operación."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) > self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.half_open_count = 0
                logger.info("🟡 Circuit Breaker: HALF_OPEN (probando recuperación)")
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_count < self.half_open_requests:
                self.half_open_count += 1
                return True
            return False
        
        return False


class AsyncInferenceClient:
    """
    Cliente HTTP asíncrono optimizado para inferencia remota.
    
    Usa httpx con HTTP/2, connection pooling y circuit breaker.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el cliente asíncrono.
        
        Args:
            config: Configuración del cliente con:
                - server_url: URL del servidor
                - auth_token: Token de autenticación (opcional)
                - timeouts: Configuración de timeouts
                - compression: Configuración de compresión
                - circuit_breaker: Configuración del circuit breaker
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx es requerido. Instala con: pip install httpx")
        
        # URLs y endpoints
        self.server_url = config.get("server_url", "http://localhost:9000").rstrip("/")
        self.health_endpoint = config.get("health_endpoint", "/health")
        self.infer_endpoint = config.get("infer_endpoint", "/infer")
        
        # Autenticación
        self.auth_token = config.get("auth_token", None)
        
        # Timeouts optimizados
        timeout_cfg = config.get("timeouts", {})
        self.connect_timeout = float(timeout_cfg.get("connect", 0.5))
        self.read_timeout = float(timeout_cfg.get("read", 1.0))
        self.write_timeout = float(timeout_cfg.get("write", 1.0))
        self.pool_timeout = float(timeout_cfg.get("pool", 0.5))
        
        # Compresión adaptativa
        compress_cfg = config.get("compression", {})
        self.jpeg_quality = int(compress_cfg.get("jpeg_quality", 85))
        self.max_dimension = int(compress_cfg.get("max_dimension", 640))
        self.auto_quality = bool(compress_cfg.get("auto_quality", True))
        
        # Circuit Breaker
        cb_cfg = config.get("circuit_breaker", {})
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=cb_cfg.get("failure_threshold", 3),
            timeout_seconds=cb_cfg.get("timeout_seconds", 20.0),
            half_open_requests=cb_cfg.get("half_open_requests", 1)
        )
        
        # Cliente HTTP asíncrono con pool de conexiones
        self.client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
        
        # Estadísticas
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_failed": 0,
            "total_latency_ms": 0.0,
            "last_success_time": None,
            "last_error_time": None
        }
        
        # Cache de health check
        self._health_cache = {"status": False, "timestamp": 0}
        self._health_cache_ttl = 5.0  # segundos
        
        logger.info(f"📡 AsyncInferenceClient inicializado: {self.server_url}")
    
    async def _ensure_client(self):
        """Asegura que el cliente HTTP esté inicializado."""
        if self.client is None:
            async with self._client_lock:
                if self.client is None:
                    # Configurar timeouts
                    timeout = httpx.Timeout(
                        connect=self.connect_timeout,
                        read=self.read_timeout,
                        write=self.write_timeout,
                        pool=self.pool_timeout
                    )
                    
                    # Configurar headers
                    headers = {
                        "User-Agent": "VisiFruit-AsyncClient/2.0",
                        "Accept": "application/json",
                    }
                    if self.auth_token:
                        headers["Authorization"] = f"Bearer {self.auth_token}"
                    
                    # Crear cliente con HTTP/2 y connection pooling
                    self.client = httpx.AsyncClient(
                        base_url=self.server_url,
                        headers=headers,
                        timeout=timeout,
                        http2=True,  # Habilitar HTTP/2
                        limits=httpx.Limits(
                            max_keepalive_connections=5,
                            max_connections=10,
                            keepalive_expiry=30
                        ),
                        follow_redirects=True,
                        verify=False  # Solo para desarrollo local
                    )
                    logger.info("✅ Cliente HTTP asíncrono inicializado con HTTP/2")
    
    async def health(self) -> bool:
        """
        Verifica la salud del servidor de manera asíncrona.
        
        Returns:
            True si el servidor está saludable, False en caso contrario.
        """
        # Verificar cache
        now = time.time()
        if (now - self._health_cache["timestamp"]) < self._health_cache_ttl:
            return self._health_cache["status"]
        
        # Circuit breaker check
        if not self.circuit_breaker.can_attempt():
            logger.debug("Health check bloqueado por circuit breaker")
            return False
        
        try:
            await self._ensure_client()
            
            start_time = time.time()
            response = await self.client.get(self.health_endpoint)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                healthy = data.get("status") == "ok"
                
                # Actualizar cache
                self._health_cache = {"status": healthy, "timestamp": now}
                
                # Registrar éxito
                self.circuit_breaker.record_success()
                
                logger.debug(f"Health check OK en {latency_ms:.1f}ms")
                return healthy
            else:
                self.circuit_breaker.record_failure()
                return False
                
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.debug(f"Health check falló: {e}")
            return False
    
    def _compress_image(self, frame: np.ndarray) -> Tuple[bytes, Dict[str, Any]]:
        """
        Comprime la imagen de manera ultra-eficiente para streaming de alto FPS.
        
        Args:
            frame: Imagen a comprimir (debe estar en BGR)
            
        Returns:
            Tupla de (imagen_comprimida, metadatos)
        """
        original_shape = frame.shape
        
        # Redimensionar agresivamente si es necesario para maximizar FPS
        h, w = frame.shape[:2]
        if max(h, w) > self.max_dimension:
            scale = self.max_dimension / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            # INTER_AREA es mejor para redimensionar a menor resolución
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Determinar calidad JPEG ultra-adaptativa para streaming
        quality = self.jpeg_quality
        if self.auto_quality:
            # Calidades más agresivas para maximizar FPS en streaming remoto
            pixels = frame.shape[0] * frame.shape[1]
            if pixels > 640*480:  # > VGA
                quality = min(quality, 60)  # Calidad baja para imágenes grandes
            elif pixels > 480*480:
                quality = min(quality, 70)
            elif pixels > 320*320:
                quality = min(quality, 75)
            # Imágenes pequeñas mantienen calidad original
        
        # Optimizaciones JPEG para velocidad
        encode_params = [
            int(cv2.IMWRITE_JPEG_QUALITY), quality,
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,  # Huffman óptimo (un poco más lento, mejor compresión)
            int(cv2.IMWRITE_JPEG_PROGRESSIVE), 0  # No progresivo (más rápido)
        ]
        success, buffer = cv2.imencode('.jpg', frame, encode_params)
        
        if not success:
            raise ValueError("Error comprimiendo imagen")
        
        metadata = {
            "original_shape": original_shape,
            "compressed_shape": frame.shape,
            "quality": quality,
            "size_bytes": len(buffer),
            "compression_ratio": (original_shape[0] * original_shape[1] * 3) / len(buffer)
        }
        
        return buffer.tobytes(), metadata
    
    async def infer(self, frame: np.ndarray, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Realiza inferencia remota de manera asíncrona.
        
        Args:
            frame: Imagen para inferencia
            params: Parámetros adicionales de IA
            
        Returns:
            Diccionario con resultados de detección o None si falla.
        """
        # Circuit breaker check
        if not self.circuit_breaker.can_attempt():
            logger.debug("Inferencia bloqueada por circuit breaker")
            return None
        
        start_time = time.time()
        self.stats["requests_total"] += 1
        
        try:
            await self._ensure_client()
            
            # Comprimir imagen
            image_data, compression_metadata = self._compress_image(frame)
            
            # Preparar datos del formulario
            files = {"image": ("frame.jpg", image_data, "image/jpeg")}
            
            data = {}
            if params:
                data.update({
                    "imgsz": params.get("input_size", 640),
                    "conf": params.get("confidence_threshold", 0.5),
                    "iou": params.get("iou_threshold", 0.45),
                    "max_det": params.get("max_detections", 100)
                })
                
                # Enviar nombres de clases si están disponibles
                if "class_names" in params:
                    data["class_names_json"] = json.dumps(params["class_names"])
            
            # Realizar petición asíncrona
            response = await self.client.post(
                self.infer_endpoint,
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Registrar éxito
                self.circuit_breaker.record_success()
                self.stats["requests_success"] += 1
                self.stats["last_success_time"] = datetime.now()
                
                # Añadir metadatos
                latency_ms = (time.time() - start_time) * 1000
                self.stats["total_latency_ms"] += latency_ms
                
                result["client_metadata"] = {
                    "latency_ms": latency_ms,
                    "compression": compression_metadata
                }
                
                logger.debug(f"Inferencia completada en {latency_ms:.1f}ms")
                return result
            else:
                logger.warning(f"Servidor respondió con código {response.status_code}")
                self.circuit_breaker.record_failure()
                self.stats["requests_failed"] += 1
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en inferencia después de {self.read_timeout}s")
            self.circuit_breaker.record_failure()
            self.stats["requests_failed"] += 1
            self.stats["last_error_time"] = datetime.now()
            return None
            
        except Exception as e:
            logger.error(f"Error en inferencia asíncrona: {e}")
            self.circuit_breaker.record_failure()
            self.stats["requests_failed"] += 1
            self.stats["last_error_time"] = datetime.now()
            return None
    
    async def batch_infer(self, frames: list[np.ndarray], params: Optional[Dict[str, Any]] = None) -> list[Optional[Dict[str, Any]]]:
        """
        Realiza inferencia en batch de manera asíncrona.
        
        Args:
            frames: Lista de imágenes para inferencia
            params: Parámetros adicionales de IA
            
        Returns:
            Lista de resultados de detección.
        """
        tasks = [self.infer(frame, params) for frame in frames]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convertir excepciones a None
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error en batch: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cliente."""
        total_requests = max(1, self.stats["requests_total"])
        
        return {
            "requests_total": self.stats["requests_total"],
            "requests_success": self.stats["requests_success"],
            "requests_failed": self.stats["requests_failed"],
            "success_rate": self.stats["requests_success"] / total_requests,
            "avg_latency_ms": self.stats["total_latency_ms"] / total_requests,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "last_success_time": self.stats["last_success_time"],
            "last_error_time": self.stats["last_error_time"]
        }
    
    async def close(self):
        """Cierra el cliente y limpia recursos."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("Cliente HTTP asíncrono cerrado")
    
    def __del__(self):
        """Limpieza al destruir el objeto."""
        if self.client:
            try:
                asyncio.create_task(self.close())
            except:
                pass
