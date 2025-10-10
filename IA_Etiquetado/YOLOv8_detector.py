# IA_Etiquetado/YOLOv8_detector.py
"""
FruPrint - Sistema de Detección de Frutas con YOLOv8 (Roboflow 3.0)
===================================================================

Detector de frutas optimizado para Raspberry Pi 5 usando YOLOv8.
Compatible con modelos entrenados en Roboflow 3.0 Object Detection (Fast).

Optimizaciones específicas para Raspberry Pi 5:
- Inferencia CPU optimizada sin GPU
- Gestión eficiente de memoria (8GB RAM)
- Procesamiento multi-hilo balanceado
- Caché inteligente y warmup adaptativo
- Detección de bajo consumo de recursos

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Octubre 2025
Versión: 4.0 - YOLOv8 Raspberry Pi Edition
"""

import asyncio
import logging
import time
import uuid
import statistics
import hashlib
import gc
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Union, Any, Callable
from threading import Thread, Event, RLock
from queue import Queue, Empty, Full, PriorityQueue
from pathlib import Path
from datetime import datetime
import json
import numpy as np
import cv2
import psutil

# Importar YOLOv8 de Ultralytics
try:
    from ultralytics import YOLO
    import torch
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLOv8 no disponible. Instala con: pip install ultralytics")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Importar estructuras de datos existentes
from .Fruit_detector import (
    DetectionQuality, ModelStatus, SystemAlert, ProcessingPriority,
    FruitDetection, FrameAnalysisResult, SystemMetrics, AlertMessage,
    DetectionStatistics
)

logger = logging.getLogger(__name__)


@dataclass
class YOLOv8Config:
    """Configuración específica para YOLOv8."""
    model_path: str = "weights/best.pt"
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    input_size: int = 640  # 640, 480, 320 (menor = más rápido en CPU)
    max_detections: int = 100
    device: str = "cpu"  # Para Raspberry Pi 5 sin GPU
    half_precision: bool = False  # FP16 solo en GPU
    class_names: List[str] = field(default_factory=lambda: ["apple", "pear", "lemon"])
    # Optimizaciones para Raspberry Pi
    num_threads: int = 4  # Cores de CPU
    augment: bool = False  # No aumentar en inferencia para mayor velocidad
    agnostic_nms: bool = False


class RemoteInferenceClient:
    """Cliente HTTP para inferencia remota con fallback configurable."""
    def __init__(self, cfg: Dict):
        self.server_url = str(cfg.get("server_url", "")).rstrip("/")
        self.health_endpoint = str(cfg.get("health_endpoint", "/health"))
        self.infer_endpoint = str(cfg.get("infer_endpoint", "/infer"))
        self.connect_timeout = float(cfg.get("connect_timeout_s", 0.25))
        self.read_timeout = float(cfg.get("read_timeout_s", 0.6))
        self.max_retries = int(cfg.get("max_retries", 1))
        self.jpeg_quality = int(cfg.get("jpeg_quality", 75))
        self.downscale_size = int(cfg.get("downscale_before_send", 480))
        self.enabled = bool(cfg.get("enabled", False)) and REQUESTS_AVAILABLE and len(self.server_url) > 0

    def _timeouts(self):
        return (self.connect_timeout, self.read_timeout)

    def health(self) -> bool:
        if not self.enabled:
            return False
        try:
            url = f"{self.server_url}{self.health_endpoint}"
            r = requests.get(url, timeout=self._timeouts())
            if r.status_code == 200:
                data = r.json()
                return bool(data.get("status") == "ok")
            return False
        except Exception:
            return False

    def infer(self, frame: np.ndarray, ai_params: Dict) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            # Downscale before send if configured
            img = frame
            if self.downscale_size and self.downscale_size > 0:
                try:
                    h, w = frame.shape[:2]
                    # Keep aspect ratio by resizing shorter side to downscale_size
                    if max(h, w) > self.downscale_size:
                        if h >= w:
                            new_h = self.downscale_size
                            new_w = int(w * (self.downscale_size / float(h)))
                        else:
                            new_w = self.downscale_size
                            new_h = int(h * (self.downscale_size / float(w)))
                        img = cv2.resize(frame, (new_w, new_h))
                except Exception:
                    img = frame

            # Encode as JPEG
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            ok, buf = cv2.imencode('.jpg', img, encode_params)
            if not ok:
                return None

            files = {"image": ("frame.jpg", buf.tobytes(), "image/jpeg")}
            data = {
                "imgsz": int(ai_params.get("input_size", 640)),
                "conf": float(ai_params.get("confidence_threshold", 0.5)),
                "iou": float(ai_params.get("iou_threshold", 0.45)),
                "max_det": int(ai_params.get("max_detections", 100)),
            }
            # Optional class names hint
            class_names = ai_params.get("class_names")
            if class_names:
                try:
                    # Send as JSON string to avoid list parsing issues in form
                    data["class_names_json"] = json.dumps(class_names)
                except Exception:
                    pass

            url = f"{self.server_url}{self.infer_endpoint}"
            last_exc = None
            for _ in range(max(1, self.max_retries)):
                try:
                    r = requests.post(url, files=files, data=data, timeout=self._timeouts())
                    if r.status_code == 200:
                        return r.json()
                except Exception as e:
                    last_exc = e
            if last_exc:
                raise last_exc
            return None
        except Exception:
            return None


class YOLOv8InferenceWorker(Thread):
    """
    Worker de inferencia YOLOv8 optimizado para Raspberry Pi 5.
    
    Características:
    - Inferencia CPU ultra-optimizada
    - Gestión eficiente de memoria
    - Caché inteligente de resultados
    - Sistema de métricas de rendimiento
    - Warmup adaptativo
    """
    
    def __init__(self, worker_id: int, config: Dict, input_queue: PriorityQueue, 
                 output_queue: Queue, alert_callback: Optional[Callable] = None):
        super().__init__(daemon=True, name=f"YOLOv8Worker-{worker_id}")
        
        self.worker_id = worker_id
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.alert_callback = alert_callback
        
        # Configuración YOLOv8
        self.yolo_config = YOLOv8Config(
            model_path=config.get("model_path", "weights/best.pt"),
            confidence_threshold=config.get("confidence_threshold", 0.5),
            iou_threshold=config.get("iou_threshold", 0.45),
            input_size=config.get("input_size", 640),
            class_names=config.get("class_names", ["apple", "pear", "lemon"]),
            num_threads=config.get("num_threads", 4)
        )
        
        # Estado del worker
        self.model: Optional[YOLO] = None
        self.model_status = ModelStatus.UNINITIALIZED
        
        # Control de hilos
        self._stop_event = Event()
        self._pause_event = Event()
        self._model_loaded = Event()
        self._model_lock = RLock()
        
        # Métricas y estadísticas
        self.stats = DetectionStatistics()
        self._frame_cache = {}
        self._error_count = 0
        self._last_maintenance = time.time()
        self._performance_history = deque(maxlen=100)
        
        logger.info(f"YOLOv8Worker-{worker_id} inicializado para Raspberry Pi 5")

    def _load_model(self):
        """Carga el modelo YOLOv8 con optimizaciones para Raspberry Pi 5."""
        try:
            self.model_status = ModelStatus.LOADING
            self._send_alert(SystemAlert.INFO, f"Cargando modelo YOLOv8 en Worker-{self.worker_id}")
            
            # Validar que el modelo existe
            model_path = Path(self.yolo_config.model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo YOLOv8 no encontrado: {self.yolo_config.model_path}")
            
            if not YOLO_AVAILABLE:
                raise ImportError("Ultralytics YOLOv8 no está instalado")
            
            with self._model_lock:
                logger.info(f"Worker-{self.worker_id}: Cargando YOLOv8 desde {self.yolo_config.model_path}")
                
                # Cargar modelo YOLOv8
                self.model = YOLO(str(model_path))
                
                # Configurar optimizaciones para Raspberry Pi 5 (CPU only)
                self._configure_raspberry_pi_optimizations()
                
                # Warmup del modelo
                self.model_status = ModelStatus.WARMING_UP
                self._intelligent_warmup()
                
                # Validar funcionamiento
                self._validate_model_functionality()
            
            self.model_status = ModelStatus.READY
            self._model_loaded.set()
            self._send_alert(SystemAlert.INFO, f"Modelo YOLOv8 cargado exitosamente en Worker-{self.worker_id}")
            logger.info(f"Worker-{self.worker_id}: YOLOv8 listo para inferencia")

        except Exception as e:
            self.model_status = ModelStatus.ERROR
            self._error_count += 1
            self._send_alert(SystemAlert.CRITICAL, f"Error cargando modelo YOLOv8: {e}")
            logger.exception(f"Worker-{self.worker_id}: Error crítico: {e}")
            self.model = None
            self._stop_event.set()

    def _configure_raspberry_pi_optimizations(self):
        """Configura optimizaciones específicas para Raspberry Pi 5."""
        if not self.model:
            return
        
        # Configurar PyTorch para CPU optimizado
        torch.set_num_threads(self.yolo_config.num_threads)
        torch.set_grad_enabled(False)  # No gradientes en inferencia
        
        # Configurar backend de CPU
        if hasattr(torch.backends, 'mkldnn'):
            torch.backends.mkldnn.enabled = True
        
        # Limitar uso de memoria
        gc.collect()
        
        logger.info(f"Worker-{self.worker_id}: Optimizado para Raspberry Pi 5 ({self.yolo_config.num_threads} threads)")

    def _intelligent_warmup(self):
        """Warmup inteligente del modelo con diferentes tamaños."""
        logger.info(f"Worker-{self.worker_id}: Iniciando warmup YOLOv8...")
        
        # Warmup con el tamaño de entrada configurado
        warmup_size = self.yolo_config.input_size
        
        try:
            # Crear imagen sintética
            dummy_image = np.random.randint(0, 255, (warmup_size, warmup_size, 3), dtype=np.uint8)
            
            # Ejecutar 3 inferencias de warmup
            for i in range(3):
                start_time = time.time()
                _ = self._run_inference(dummy_image)
                warmup_time = (time.time() - start_time) * 1000
                logger.info(f"Worker-{self.worker_id}: Warmup {i+1}/3: {warmup_time:.1f}ms")
            
            logger.info(f"Worker-{self.worker_id}: Warmup completado")
            
        except Exception as e:
            logger.warning(f"Worker-{self.worker_id}: Error en warmup: {e}")

    def _validate_model_functionality(self):
        """Valida que el modelo funciona correctamente."""
        try:
            # Imagen de prueba
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            # Ejecutar inferencia
            start_time = time.time()
            result = self._run_inference(test_image)
            inference_time = (time.time() - start_time) * 1000
            
            if result is None:
                raise RuntimeError("El modelo no devolvió resultados")
            
            logger.info(f"Worker-{self.worker_id}: Validación exitosa - {inference_time:.1f}ms")
            
        except Exception as e:
            raise RuntimeError(f"Validación del modelo falló: {e}")

    def _run_inference(self, image: np.ndarray) -> Optional[Any]:
        """Ejecuta inferencia con YOLOv8."""
        if not self.model:
            return None
        
        try:
            # Ejecutar predicción YOLOv8
            results = self.model.predict(
                image,
                conf=self.yolo_config.confidence_threshold,
                iou=self.yolo_config.iou_threshold,
                imgsz=self.yolo_config.input_size,
                device=self.yolo_config.device,
                half=self.yolo_config.half_precision,
                augment=self.yolo_config.augment,
                agnostic_nms=self.yolo_config.agnostic_nms,
                max_det=self.yolo_config.max_detections,
                verbose=False
            )
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error en inferencia YOLOv8: {e}")
            return None

    def _process_detections_advanced(self, yolo_result, frame_shape) -> List[FruitDetection]:
        """Procesa los resultados de YOLOv8 a objetos FruitDetection."""
        if yolo_result is None or yolo_result.boxes is None:
            return []
        
        detections = []
        frame_height, frame_width = frame_shape[:2]
        
        boxes = yolo_result.boxes
        
        for i in range(len(boxes)):
            try:
                # Extraer datos del box
                box_xyxy = boxes.xyxy[i].cpu().numpy()  # [x1, y1, x2, y2]
                confidence = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())
                
                # Coordenadas
                x1, y1, x2, y2 = map(int, box_xyxy)
                
                # Asegurar que están en rango válido
                x1 = max(0, min(x1, frame_width))
                y1 = max(0, min(y1, frame_height))
                x2 = max(x1, min(x2, frame_width))
                y2 = max(y1, min(y2, frame_height))
                
                # Calcular métricas
                width = x2 - x1
                height = y2 - y1
                area = int(width * height)
                aspect_ratio = width / height if height > 0 else 0
                
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # Distancia al borde (normalizada)
                edge_distance = min(
                    center_x / frame_width,
                    center_y / frame_height,
                    (frame_width - center_x) / frame_width,
                    (frame_height - center_y) / frame_height
                )
                
                # Nombre de clase
                class_name = self.yolo_config.class_names[class_id] if class_id < len(self.yolo_config.class_names) else "unknown"
                
                # Score de calidad
                quality_score = self._calculate_detection_quality_score(
                    confidence, area, aspect_ratio, edge_distance
                )
                
                # Crear detección
                detection = FruitDetection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    center_px=(center_x, center_y),
                    area_px=area,
                    aspect_ratio=aspect_ratio,
                    edge_distance=edge_distance,
                    quality_score=quality_score
                )
                
                detections.append(detection)
                
            except Exception as e:
                logger.warning(f"Error procesando detección {i}: {e}")
                continue
        
        return detections

    def _calculate_detection_quality_score(self, confidence: float, area: int, 
                                         aspect_ratio: float, edge_distance: float) -> float:
        """Calcula un score de calidad para la detección."""
        confidence_score = confidence
        
        # Penalizar áreas muy pequeñas o muy grandes
        area_score = 1.0
        if area < 100:
            area_score = area / 100
        elif area > 50000:
            area_score = 50000 / area
        
        # Penalizar aspect ratios extraños (frutas ~redondas)
        aspect_score = 1.0
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            aspect_score = 0.7
        
        # Penalizar detecciones cerca del borde
        edge_score = max(0.5, edge_distance * 2)
        
        # Score final
        final_score = confidence_score * area_score * aspect_score * edge_score
        return min(1.0, max(0.0, final_score))

    def _process_frame_advanced(self, frame_id: str, frame: np.ndarray, 
                              priority: ProcessingPriority) -> FrameAnalysisResult:
        """Procesa un frame con análisis avanzado usando YOLOv8."""
        start_time = time.time()
        
        try:
            # Hash del frame para caché
            frame_hash = self._calculate_frame_hash(frame)
            
            # Verificar caché
            if self._check_duplicate_frame(frame_hash):
                cached_result = self._frame_cache.get(frame_hash)
                if cached_result:
                    logger.debug(f"Frame {frame_id} encontrado en caché")
                    return cached_result
            
            # Análisis de calidad del frame
            preprocessing_start = time.time()
            lighting_score, blur_score = self._analyze_frame_quality(frame)
            preprocessing_time = (time.time() - preprocessing_start) * 1000
            
            # Inferencia YOLOv8
            inference_start = time.time()
            yolo_result = self._run_inference(frame)
            inference_time = (time.time() - inference_start) * 1000
            
            # Post-procesamiento
            postprocessing_start = time.time()
            detections = self._process_detections_advanced(yolo_result, frame.shape)
            postprocessing_time = (time.time() - postprocessing_start) * 1000
            
            total_time = (time.time() - start_time) * 1000
            
            # Métricas de confianza
            confidences = [d.confidence for d in detections]
            confidence_avg = statistics.mean(confidences) if confidences else 0.0
            confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
            
            # Evaluar calidad (no mutar dataclass congelado)
            quality_enum = self._assess_detection_quality(detections, lighting_score, blur_score)
            
            # Crear resultado (establecer quality en el constructor)
            result = FrameAnalysisResult(
                detections=detections,
                fruit_count=len(detections),
                inference_time_ms=inference_time,
                preprocessing_time_ms=preprocessing_time,
                postprocessing_time_ms=postprocessing_time,
                total_processing_time_ms=total_time,
                timestamp=start_time,
                frame_shape=frame.shape[:2],
                frame_id=frame_id,
                frame_hash=frame_hash,
                confidence_avg=confidence_avg,
                confidence_std=confidence_std,
                lighting_score=lighting_score,
                blur_score=blur_score,
                quality=quality_enum
            )
            
            # Actualizar caché
            self._update_frame_cache(frame_hash, result)
            
            logger.debug(f"Frame {frame_id}: {len(detections)} detecciones en {total_time:.1f}ms")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error procesando frame {frame_id}: {e}")
            return FrameAnalysisResult(
                frame_id=frame_id,
                timestamp=start_time,
                frame_shape=frame.shape[:2] if frame is not None else (0, 0),
                quality=DetectionQuality.FAILED
            )

    def _calculate_frame_hash(self, frame: np.ndarray) -> str:
        """Calcula hash MD5 del frame."""
        return hashlib.md5(frame.tobytes()).hexdigest()

    def _check_duplicate_frame(self, frame_hash: str) -> bool:
        """Verifica si un frame ya fue procesado."""
        return frame_hash in self._frame_cache

    def _update_frame_cache(self, frame_hash: str, result: FrameAnalysisResult):
        """Actualiza caché con límite de tamaño."""
        max_cache_size = 50  # Reducido para Raspberry Pi
        
        if len(self._frame_cache) >= max_cache_size:
            oldest_key = next(iter(self._frame_cache))
            del self._frame_cache[oldest_key]
        
        self._frame_cache[frame_hash] = result

    def _analyze_frame_quality(self, frame: np.ndarray) -> Tuple[float, float]:
        """Analiza calidad del frame (iluminación y desenfoque)."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            lighting_score = 1.0 - abs(mean_brightness - 128) / 128
            
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_score = min(1.0, laplacian_var / 500.0)
            
            return lighting_score, blur_score
        except Exception:
            return 0.5, 0.5

    def _assess_detection_quality(self, detections: List[FruitDetection], 
                                 lighting_score: float, blur_score: float) -> DetectionQuality:
        """Evalúa calidad general de las detecciones."""
        if not detections:
            return DetectionQuality.FAILED
        
        avg_confidence = statistics.mean([d.confidence for d in detections])
        avg_quality = statistics.mean([d.quality_score for d in detections])
        
        overall_score = (avg_confidence + avg_quality + lighting_score + blur_score) / 4
        
        if overall_score >= 0.95:
            return DetectionQuality.EXCELLENT
        elif overall_score >= 0.80:
            return DetectionQuality.GOOD
        elif overall_score >= 0.65:
            return DetectionQuality.ACCEPTABLE
        else:
            return DetectionQuality.POOR

    def _perform_maintenance(self):
        """Mantenimiento periódico del worker."""
        try:
            current_time = time.time()
            old_cache_keys = []
            
            for key, result in self._frame_cache.items():
                if current_time - result.timestamp > 300:  # 5 minutos
                    old_cache_keys.append(key)
            
            for key in old_cache_keys:
                del self._frame_cache[key]
            
            gc.collect()
            
            logger.debug(f"YOLOv8Worker-{self.worker_id}: Mantenimiento completado")
            
        except Exception as e:
            logger.warning(f"Error en mantenimiento: {e}")

    def _send_alert(self, alert_type: SystemAlert, message: str, details: Dict = None):
        """Envía una alerta al sistema."""
        if self.alert_callback:
            alert = AlertMessage(
                alert_type=alert_type,
                message=message,
                component=f"YOLOv8Worker-{self.worker_id}",
                details=details or {}
            )
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Error enviando alerta: {e}")

    def run(self):
        """Bucle principal del worker."""
        logger.info(f"YOLOv8Worker-{self.worker_id}: Iniciando...")
        
        try:
            # Cargar modelo
            self._load_model()
            
            if self.model_status != ModelStatus.READY:
                logger.error(f"YOLOv8Worker-{self.worker_id}: No se pudo cargar el modelo")
                return
            
            logger.info(f"YOLOv8Worker-{self.worker_id}: Listo para procesar")
            
            # Bucle principal
            while not self._stop_event.is_set():
                try:
                    if self._pause_event.is_set():
                        time.sleep(0.1)
                        continue
                    
                    # Obtener trabajo
                    try:
                        priority_item = self.input_queue.get(timeout=1.0)
                        priority, (frame_id, frame, timestamp) = priority_item
                    except Empty:
                        continue
                    
                    # Procesar frame
                    start_time = time.time()
                    result = self._process_frame_advanced(frame_id, frame, ProcessingPriority(priority))
                    processing_time = time.time() - start_time
                    
                    # Actualizar métricas
                    self._performance_history.append(time.time())
                    self.stats.update(result)
                    
                    # Enviar resultado
                    try:
                        self.output_queue.put((frame_id, result), timeout=1.0)
                    except Full:
                        logger.warning(f"YOLOv8Worker-{self.worker_id}: Cola de salida llena")
                    
                    self.input_queue.task_done()
                    
                    # Mantenimiento periódico
                    if time.time() - self._last_maintenance > 300:
                        self._perform_maintenance()
                        self._last_maintenance = time.time()
                        
                except Exception as e:
                    logger.exception(f"YOLOv8Worker-{self.worker_id}: Error procesando: {e}")
                    self._error_count += 1
                    
        except Exception as e:
            logger.exception(f"YOLOv8Worker-{self.worker_id}: Error crítico: {e}")
            self._send_alert(SystemAlert.CRITICAL, f"Worker falló: {e}")
        finally:
            logger.info(f"YOLOv8Worker-{self.worker_id}: Terminando...")

    def stop(self):
        """Detiene el worker."""
        logger.info(f"YOLOv8Worker-{self.worker_id}: Deteniendo...")
        self._stop_event.set()

    def wait_for_model(self, timeout: float = 60.0) -> bool:
        """Espera a que el modelo esté listo."""
        return self._model_loaded.wait(timeout)

    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del worker."""
        return {
            'worker_id': self.worker_id,
            'model_status': self.model_status.name,
            'device': self.yolo_config.device,
            'error_count': self._error_count,
            'frames_processed': self.stats.total_frames,
            'detections_made': self.stats.total_detections,
            'is_running': not self._stop_event.is_set(),
            'is_paused': self._pause_event.is_set(),
            'cache_size': len(self._frame_cache)
        }


class EnterpriseFruitDetector:
    """
    Detector empresarial de frutas usando YOLOv8.
    Optimizado para Raspberry Pi 5 con inferencia CPU.
    
    Interfaz compatible con el sistema existente.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Extraer configuración del modelo
        ai_config = config.get("ai_model_settings", {})
        
        self.yolo_config = YOLOv8Config(
            model_path=ai_config.get("model_path", "weights/best.pt"),
            confidence_threshold=ai_config.get("confidence_threshold", 0.5),
            iou_threshold=ai_config.get("iou_threshold", 0.45),
            input_size=ai_config.get("input_size", 640),
            max_detections=ai_config.get("max_detections", 100),
            class_names=ai_config.get("class_names", ["apple", "pear", "lemon"]),
            num_threads=ai_config.get("num_threads", 4)
        )
        
        # Configuración de inferencia remota
        self.remote_cfg: Dict[str, Any] = config.get("remote_inference", {})
        self.remote_client = RemoteInferenceClient(self.remote_cfg) if self.remote_cfg else RemoteInferenceClient({})
        self.fallback_to_local: bool = bool(self.remote_cfg.get("fallback_to_local", True))
        self._use_remote: bool = bool(self.remote_cfg.get("enabled", False)) and self.remote_client.enabled

        # Workers y colas
        self.workers = []
        self.input_queue = PriorityQueue(maxsize=500)  # Reducido para Raspberry Pi
        self.output_queue = Queue(maxsize=500)
        
        # Control del sistema
        self._is_initialized = False
        self._alert_callbacks = []
        self._local_started = False
        
        mode = "REMOTO" if self._use_remote else "LOCAL"
        logger.info(f"EnterpriseFruitDetector (YOLOv8) inicializado para Raspberry Pi 5 - Modo {mode}")

    async def initialize(self) -> bool:
        """Inicializa el detector YOLOv8. Usa remoto si está saludable; si no, arranca local."""
        try:
            logger.info("🤖 Inicializando detector YOLOv8...")

            # Intentar modo remoto si está habilitado
            if self._use_remote:
                healthy = self.remote_client.health()
                if healthy:
                    self._is_initialized = True
                    logger.info("✅ Modo REMOTO habilitado y saludable; no se cargará modelo local en la Pi")
                    return True
                else:
                    logger.warning("⚠️ Servidor remoto no disponible; activando fallback a modelo local")

            # Fallback a workers locales
            num_workers = int(self.config.get("ai_model_settings", {}).get("num_workers", 2))
            ok = await self._start_local_workers(num_workers)
            if ok:
                self._is_initialized = True
                logger.info(f"✅ YOLOv8 Detector LOCAL inicializado con {len(self.workers)} workers")
                return True
            return False

        except Exception as e:
            logger.exception(f"❌ Error inicializando YOLOv8 Detector: {e}")
            return False

    async def _start_local_workers(self, num_workers: int) -> bool:
        """Arranca los workers locales (CPU en Pi5)."""
        try:
            if self._local_started:
                return True
            self.workers = []
            for i in range(num_workers):
                worker = YOLOv8InferenceWorker(
                    worker_id=i,
                    config={
                        "model_path": self.yolo_config.model_path,
                        "confidence_threshold": self.yolo_config.confidence_threshold,
                        "iou_threshold": self.yolo_config.iou_threshold,
                        "input_size": self.yolo_config.input_size,
                        "class_names": self.yolo_config.class_names,
                        "num_threads": self.yolo_config.num_threads
                    },
                    input_queue=self.input_queue,
                    output_queue=self.output_queue,
                    alert_callback=self._handle_worker_alert
                )
                self.workers.append(worker)
                worker.start()

            # Esperar readiness
            for worker in self.workers:
                if not worker.wait_for_model(timeout=120.0):
                    raise RuntimeError(f"Worker {worker.worker_id} no se inicializó")
            self._local_started = True
            return True
        except Exception as e:
            logger.exception(f"Error iniciando workers locales: {e}")
            self.workers = []
            self._local_started = False
            return False

    async def detect_fruits(self, frame: np.ndarray,
                            priority: ProcessingPriority = ProcessingPriority.NORMAL) -> Optional[FrameAnalysisResult]:
        """Detecta frutas en un frame. Intenta remoto primero si está habilitado; cae a local si falla."""
        if not self._is_initialized:
            logger.error("Detector YOLOv8 no inicializado")
            return None

        frame_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 1) Intentar remoto
        if self._use_remote and self.remote_client.health():
            try:
                ai_params = {
                    "input_size": self.yolo_config.input_size,
                    "confidence_threshold": self.yolo_config.confidence_threshold,
                    "iou_threshold": self.yolo_config.iou_threshold,
                    "max_detections": self.yolo_config.max_detections,
                    "class_names": self.yolo_config.class_names,
                }
                remote = self.remote_client.infer(frame, ai_params)
                if remote:
                    # Mapear a FrameAnalysisResult
                    detections = []
                    frame_h, frame_w = frame.shape[:2]
                    for d in remote.get("detections", []):
                        try:
                            cls_name = str(d.get("class_name", "unknown"))
                            conf = float(d.get("confidence", 0.0))
                            bbox = d.get("bbox", [0, 0, 0, 0])
                            x1, y1, x2, y2 = map(int, bbox)
                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)
                            try:
                                cls_id = self.yolo_config.class_names.index(cls_name)
                            except ValueError:
                                cls_id = 0
                            detections.append(FruitDetection(
                                class_id=cls_id,
                                class_name=cls_name,
                                confidence=conf,
                                bbox=(x1, y1, x2, y2),
                                center_px=(cx, cy)
                            ))
                        except Exception:
                            continue

                    inference_ms = float(remote.get("inference_ms", 0.0))
                    preprocessing_ms = float(remote.get("pre_ms", 0.0))
                    postprocessing_ms = float(remote.get("post_ms", 0.0))
                    total_ms = float(remote.get("total_ms", (time.time() - start_time) * 1000))

                    result = FrameAnalysisResult(
                        detections=detections,
                        fruit_count=len(detections),
                        inference_time_ms=inference_ms,
                        preprocessing_time_ms=preprocessing_ms,
                        postprocessing_time_ms=postprocessing_ms,
                        total_processing_time_ms=total_ms,
                        timestamp=start_time,
                        frame_shape=(frame_h, frame_w),
                        frame_id=frame_id
                    )
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Inferencia remota falló: {e}")

        # 2) Fallback a local si está permitido
        try:
            if not self._local_started:
                if not self.fallback_to_local:
                    return None
                num_workers = int(self.config.get("ai_model_settings", {}).get("num_workers", 2))
                ok = await self._start_local_workers(num_workers)
                if not ok:
                    return None

            # Enviar a cola local
            self.input_queue.put((priority.value, (frame_id, frame, start_time)), timeout=5.0)
            result_frame_id, result = self.output_queue.get(timeout=30.0)
            self.output_queue.task_done()
            return result
        except Exception as e:
            logger.error(f"Error en detect_fruits (local): {e}")
            return None

    def _handle_worker_alert(self, alert: AlertMessage):
        """Maneja alertas de workers."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")

    def register_alert_callback(self, callback: Callable[[AlertMessage], None]):
        """Registra callback para alertas."""
        self._alert_callbacks.append(callback)

    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado del sistema."""
        if not self.workers:
            status = {
                "status": "running" if self._is_initialized else "initializing",
                "mode": "remote" if self._use_remote else "local",
                "remote_enabled": self._use_remote,
                "remote_healthy": self.remote_client.health() if self._use_remote else False,
                "num_workers": 0,
                "model": "YOLOv8",
                "device": "REMOTE" if self._use_remote else "CPU (Raspberry Pi 5)",
                "workers": [],
                "queue_sizes": {"input": self.input_queue.qsize(), "output": self.output_queue.qsize()}
            }
            return status
        
        worker_statuses = [worker.get_status() for worker in self.workers]
        
        return {
            "status": "running" if self._is_initialized else "initializing",
            "mode": "remote" if self._use_remote and not self._local_started else "local",
            "remote_enabled": self._use_remote,
            "remote_healthy": self.remote_client.health() if self._use_remote else False,
            "num_workers": len(self.workers),
            "model": "YOLOv8",
            "device": "CPU (Raspberry Pi 5)",
            "workers": worker_statuses,
            "queue_sizes": {
                "input": self.input_queue.qsize(),
                "output": self.output_queue.qsize()
            }
        }

    async def shutdown(self):
        """Apaga el detector."""
        logger.info("🛑 Apagando YOLOv8 Detector...")
        
        # Detener workers
        for worker in self.workers:
            worker.stop()
        
        # Esperar a que terminen
        for worker in self.workers:
            worker.join(timeout=10.0)
        
        self._is_initialized = False
        logger.info("✅ YOLOv8 Detector apagado")

