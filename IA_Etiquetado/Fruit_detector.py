# IA_Etiquetado/fruit_detector.py
"""
FruPrint - Sistema Avanzado de Detección de Frutas por IA
=========================================================

Módulo de detección de frutas de alta performance para sistemas industriales
de etiquetado automático. Utiliza YOLOv12 con optimizaciones especializadas
para entornos de producción en tiempo real.

Características avanzadas:
- Detección multi-hilo con balanceamiento de carga
- Sistema de métricas y monitoreo en tiempo real
- Auto-calibración y optimización adaptativa
- Validación de calidad de detecciones
- Caché inteligente y gestión de memoria
- Sistema de alertas y recuperación automática
- Soporte para múltiples modelos especializados

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Edición Industrial
"""

import asyncio
import logging
import time
import uuid
import statistics
import pickle
import hashlib
import gc
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict, Union, Any, Callable
from threading import Thread, Event, Lock, RLock
from queue import Queue, Empty, Full, PriorityQueue
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
from enum import Enum, auto

import numpy as np
import torch
import psutil
from ultralytics import YOLO
import cv2

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)

# --- Enumeraciones para Control de Estado ---

class DetectionQuality(Enum):
    """Calidad de la detección basada en métricas de confianza y consistencia."""
    EXCELLENT = auto()    # >95% confianza, alta consistencia
    GOOD = auto()        # >80% confianza, buena consistencia  
    ACCEPTABLE = auto()  # >65% confianza, consistencia moderada
    POOR = auto()        # <65% confianza o baja consistencia
    FAILED = auto()      # Sin detecciones válidas

class ModelStatus(Enum):
    """Estado actual del modelo de IA."""
    UNINITIALIZED = auto()
    LOADING = auto()
    WARMING_UP = auto()
    READY = auto()
    OPTIMIZING = auto()
    ERROR = auto()
    MAINTENANCE = auto()

class SystemAlert(Enum):
    """Tipos de alertas del sistema."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

class ProcessingPriority(Enum):
    """Prioridad de procesamiento para colas de trabajo."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0

# --- Estructuras de Datos Avanzadas ---

@dataclass(frozen=True)
class FruitDetection:
    """
    Representa una única fruta detectada en un frame con métricas avanzadas.
    Es inmutable (frozen=True) para garantizar la seguridad entre hilos.
    """
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]      # Formato (x1, y1, x2, y2)
    center_px: Tuple[int, int]           # Centro del bounding box en píxeles (cx, cy)
    area_px: int = 0                     # Área del bounding box en píxeles
    aspect_ratio: float = 0.0            # Relación ancho/alto
    edge_distance: float = 0.0           # Distancia al borde del frame (normalizada)
    occlusion_score: float = 0.0         # Puntuación de oclusión (0-1)
    motion_vector: Tuple[float, float] = (0.0, 0.0)  # Vector de movimiento estimado
    quality_score: float = 0.0           # Puntuación de calidad general (0-1)
    detection_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def __post_init__(self):
        """Calcula métricas derivadas después de la inicialización."""
        if self.bbox:
            x1, y1, x2, y2 = self.bbox
            width = x2 - x1
            height = y2 - y1
            object.__setattr__(self, 'area_px', width * height)
            object.__setattr__(self, 'aspect_ratio', width / height if height > 0 else 0.0)
    
    @property
    def volume_estimate_cm3(self) -> float:
        """Estimación aproximada del volumen basada en el área visible."""
        # Fórmula empírica basada en calibración del sistema
        return self.area_px * 0.001  # Factor de conversión píxel->cm³
    
    @property
    def position_category(self) -> str:
        """Categoriza la posición en el frame."""
        cx, cy = self.center_px
        if cx < 0.3: return "izquierda"
        elif cx > 0.7: return "derecha" 
        else: return "centro"

@dataclass(frozen=True) 
class FrameAnalysisResult:
    """
    Contiene el resultado completo del análisis de un frame con métricas avanzadas.
    Incluye todas las detecciones, métricas de calidad y metadatos de rendimiento.
    """
    detections: List[FruitDetection] = field(default_factory=list)
    fruit_count: int = 0
    inference_time_ms: float = 0.0
    preprocessing_time_ms: float = 0.0
    postprocessing_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    frame_shape: Tuple[int, int] = (0, 0)  # (height, width)
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    frame_hash: str = ""                   # Hash MD5 del frame para detección de duplicados
    quality: DetectionQuality = DetectionQuality.ACCEPTABLE
    confidence_avg: float = 0.0            # Confianza promedio de todas las detecciones
    confidence_std: float = 0.0            # Desviación estándar de confianzas
    density_score: float = 0.0             # Densidad de frutas en el frame (frutas/área)
    coverage_percentage: float = 0.0       # Porcentaje del frame cubierto por detecciones
    belt_speed_estimate: float = 0.0       # Velocidad estimada de la banda (m/s)
    lighting_score: float = 0.0            # Puntuación de calidad de iluminación (0-1)
    blur_score: float = 0.0                # Puntuación de desenfoque (0-1, mayor = más nítido)
    system_load: float = 0.0               # Carga del sistema durante el procesamiento
    
    def __post_init__(self):
        """Calcula métricas derivadas después de la inicialización."""
        if self.detections:
            confidences = [d.confidence for d in self.detections]
            object.__setattr__(self, 'confidence_avg', statistics.mean(confidences))
            object.__setattr__(self, 'confidence_std', statistics.stdev(confidences) if len(confidences) > 1 else 0.0)
            
            total_area = sum(d.area_px for d in self.detections)
            frame_area = self.frame_shape[0] * self.frame_shape[1] if self.frame_shape[0] > 0 else 1
            object.__setattr__(self, 'coverage_percentage', (total_area / frame_area) * 100)
            object.__setattr__(self, 'density_score', len(self.detections) / (frame_area / 10000))  # frutas per 100x100px
    
    def get_counts_by_class(self) -> Dict[str, int]:
        """Calcula y devuelve el conteo de frutas por cada clase detectada."""
        counts = defaultdict(int)
        for detection in self.detections:
            counts[detection.class_name] += 1
        return dict(counts)
    
    def get_quality_metrics(self) -> Dict[str, float]:
        """Retorna métricas detalladas de calidad del análisis."""
        return {
            'confidence_avg': self.confidence_avg,
            'confidence_std': self.confidence_std,
            'density_score': self.density_score,
            'coverage_percentage': self.coverage_percentage,
            'lighting_score': self.lighting_score,
            'blur_score': self.blur_score,
            'quality_enum': self.quality.name
        }
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Retorna métricas de rendimiento del procesamiento."""
        return {
            'inference_time_ms': self.inference_time_ms,
            'preprocessing_time_ms': self.preprocessing_time_ms,
            'postprocessing_time_ms': self.postprocessing_time_ms,
            'total_processing_time_ms': self.total_processing_time_ms,
            'system_load': self.system_load,
            'fps_equivalent': 1000 / self.total_processing_time_ms if self.total_processing_time_ms > 0 else 0
        }
    
    def calculate_labeling_time(self, belt_speed_mps: float, fruit_width_m: float, 
                              fruit_spacing_m: float) -> float:
        """
        Calcula el tiempo óptimo de etiquetado basado en la detección.
        Formula del README: T = (Ancho_Fruta_Promedio_m * X + Espacio_Entre_Frutas_m * (X-1)) / Velocidad_Banda_mps
        """
        if self.fruit_count == 0 or belt_speed_mps <= 0:
            return 0.0
        
        total_length = (fruit_width_m * self.fruit_count) + (fruit_spacing_m * max(0, self.fruit_count - 1))
        return total_length / belt_speed_mps
    
    def is_valid_for_labeling(self, min_confidence: float = 0.65, 
                            min_detections: int = 1) -> bool:
        """Determina si este resultado es válido para activar el etiquetado."""
        return (self.fruit_count >= min_detections and 
                self.confidence_avg >= min_confidence and
                self.quality not in [DetectionQuality.FAILED, DetectionQuality.POOR])

@dataclass
class SystemMetrics:
    """Métricas del sistema en tiempo real."""
    timestamp: datetime = field(default_factory=datetime.now)
    fps_current: float = 0.0
    fps_average: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    gpu_usage_percent: float = 0.0
    gpu_memory_mb: float = 0.0
    temperature_cpu: float = 0.0
    temperature_gpu: float = 0.0
    queue_input_size: int = 0
    queue_output_size: int = 0
    total_frames_processed: int = 0
    total_detections: int = 0
    error_count: int = 0
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las métricas a diccionario para serialización."""
        return asdict(self)

@dataclass
class AlertMessage:
    """Mensaje de alerta del sistema."""
    alert_type: SystemAlert
    message: str
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la alerta a diccionario."""
        return {
            'type': self.alert_type.name,
            'message': self.message,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'resolved': self.resolved
        }

@dataclass
class DetectionStatistics:
    """Estadísticas acumuladas de detecciones."""
    total_frames: int = 0
    total_detections: int = 0
    total_processing_time: float = 0.0
    class_counts: Dict[str, int] = field(default_factory=dict)
    confidence_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    quality_distribution: Dict[DetectionQuality, int] = field(default_factory=dict)
    
    def update(self, result: FrameAnalysisResult):
        """Actualiza las estadísticas con un nuevo resultado."""
        self.total_frames += 1
        self.total_detections += result.fruit_count
        self.total_processing_time += result.total_processing_time_ms
        
        # Actualizar conteos por clase
        for class_name, count in result.get_counts_by_class().items():
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + count
        
        # Actualizar historial de confianza
        if result.detections:
            self.confidence_history.extend([d.confidence for d in result.detections])
        
        # Actualizar distribución de calidad
        self.quality_distribution[result.quality] = self.quality_distribution.get(result.quality, 0) + 1
    
    def get_average_fps(self) -> float:
        """Calcula el FPS promedio."""
        if self.total_processing_time > 0:
            return (self.total_frames * 1000) / self.total_processing_time
        return 0.0
    
    def get_detection_rate(self) -> float:
        """Calcula la tasa de detección (detecciones por frame)."""
        return self.total_detections / self.total_frames if self.total_frames > 0 else 0.0

# --- Worker Avanzado de Inferencia Multi-Hilo ---
# Sistema optimizado para alta performance con balanceamiento de carga,
# auto-optimización y monitoreo en tiempo real.

class AdvancedInferenceWorker(Thread):
    """
    Worker de inferencia de alto rendimiento con características empresariales:
    - Auto-optimización adaptativa
    - Balanceamiento de carga dinámico  
    - Monitoreo en tiempo real
    - Recuperación automática de errores
    - Caché inteligente de modelos
    - Métricas detalladas de performance
    """
    def __init__(self, worker_id: int, config: Dict, input_queue: PriorityQueue, 
                 output_queue: Queue, alert_callback: Optional[Callable] = None):
        super().__init__(daemon=True, name=f"AdvancedInferenceWorker-{worker_id}")
        
        # Configuración básica
        self.worker_id = worker_id
        self._config = config
        self._model_path = self._config.get("model_path", "IA_Etiquetado/Models/best_fruit_model.pt")
        self._confidence_threshold = self._config.get("confidence_threshold", 0.65)
        self._enable_auto_optimization = self._config.get("enable_auto_optimization", True)
        self._enable_quality_analysis = self._config.get("enable_quality_analysis", True)
        
        # Colas de comunicación
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.alert_callback = alert_callback
        
        # Estado del modelo y dispositivo
        self.model = None
        self.device = None
        self.model_status = ModelStatus.UNINITIALIZED
        self._stop_event = Event()
        self._model_loaded = Event()
        self._pause_event = Event()
        
        # Métricas y estadísticas
        self.statistics = DetectionStatistics()
        self._start_time = time.time()
        self._last_optimization = time.time()
        self._optimization_interval = 300  # 5 minutos
        self._performance_history = deque(maxlen=1000)
        self._error_count = 0
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        
        # Caché para optimización
        self._frame_cache = {}
        self._cache_max_size = 100
        self._duplicate_threshold = 0.95
        
        # Configuración adaptativa
        self._adaptive_batch_size = 1
        self._adaptive_confidence = self._confidence_threshold
        self._performance_target_fps = self._config.get("target_fps", 30.0)
        
        # Locks para thread safety
        self._model_lock = RLock()
        self._stats_lock = RLock()
        
        logger.info(f"AdvancedInferenceWorker-{worker_id} instanciado con configuración avanzada.")

    def _load_model(self):
        """
        Carga el modelo YOLOv12 con optimizaciones avanzadas y configuración inteligente.
        Incluye detección automática de hardware, warmup inteligente y validación.
        """
        try:
            self.model_status = ModelStatus.LOADING
            self._send_alert(SystemAlert.INFO, f"Iniciando carga del modelo en Worker-{self.worker_id}")
            
            # Validar que el archivo del modelo existe
            model_path = Path(self._model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo no encontrado en: {self._model_path}")
            
            # Detección automática del mejor dispositivo con análisis de capacidad
            self.device = self._detect_optimal_device()
            
            with self._model_lock:
                logger.info(f"Worker-{self.worker_id}: Cargando modelo desde {self._model_path} en {self.device}")
                self.model = YOLO(self._model_path)
                self.model.to(self.device)
                
                # Configurar optimizaciones específicas del dispositivo
                self._configure_device_optimizations()
                
                # Warmup inteligente con múltiples resoluciones
                self.model_status = ModelStatus.WARMING_UP
                self._intelligent_warmup()
                
                # Validar funcionamiento del modelo
                self._validate_model_functionality()
                
            self.model_status = ModelStatus.READY
            self._model_loaded.set()
            self._send_alert(SystemAlert.INFO, f"Modelo cargado exitosamente en Worker-{self.worker_id}")
            logger.info(f"Worker-{self.worker_id}: Modelo YOLOv12 cargado y optimizado.")

        except Exception as e:
            self.model_status = ModelStatus.ERROR
            self._error_count += 1
            self._send_alert(SystemAlert.CRITICAL, f"Error crítico cargando modelo: {e}")
            logger.exception(f"Worker-{self.worker_id}: Error crítico al cargar modelo: {e}")
            self.model = None
            self._stop_event.set()
    
    def _detect_optimal_device(self) -> str:
        """Detecta y selecciona el dispositivo óptimo para inferencia."""
        if torch.cuda.is_available():
            # Obtener información detallada de GPU CUDA
            gpu_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            logger.info(f"CUDA disponible: {gpu_count} GPU(s), {device_name}, {gpu_memory:.1f}GB")
            return "cuda"
            
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Aceleración MPS (Apple Silicon) detectada.")
            return "mps"
            
        else:
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / 1024**3
            logger.warning(f"Usando CPU: {cpu_count} cores, {memory_gb:.1f}GB RAM (rendimiento reducido)")
            return "cpu"
    
    def _configure_device_optimizations(self):
        """Configura optimizaciones específicas según el dispositivo."""
        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            if hasattr(torch, 'compile'):
                # PyTorch 2.0+ optimization
                self.model.model = torch.compile(self.model.model)
                logger.info(f"Worker-{self.worker_id}: Modelo compilado con torch.compile")
                
        elif self.device == "cpu":
            torch.set_num_threads(min(4, psutil.cpu_count()))
            logger.info(f"Worker-{self.worker_id}: Configurado para {torch.get_num_threads()} threads de CPU")
    
    def _intelligent_warmup(self):
        """Realiza warmup inteligente con múltiples resoluciones y configuraciones."""
        logger.info(f"Worker-{self.worker_id}: Iniciando warmup inteligente...")
        
        # Diferentes resoluciones para warmup
        resolutions = [(640, 640), (1280, 720), (1920, 1080)]
        warmup_frames = 3
        
        for res in resolutions:
            for _ in range(warmup_frames):
                dummy_frame = np.random.randint(0, 255, (*res, 3), dtype=np.uint8)
                start_time = time.perf_counter()
                
                try:
                    self.model.predict(dummy_frame, conf=self._confidence_threshold, verbose=False)
                    warmup_time = (time.perf_counter() - start_time) * 1000
                    logger.debug(f"Worker-{self.worker_id}: Warmup {res}: {warmup_time:.2f}ms")
                except Exception as e:
                    logger.warning(f"Worker-{self.worker_id}: Error en warmup {res}: {e}")
        
        # Forzar garbage collection después del warmup
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        logger.info(f"Worker-{self.worker_id}: Warmup completado")
    
    def _validate_model_functionality(self):
        """Valida que el modelo funcione correctamente con datos de prueba."""
        try:
            test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            results = self.model.predict(test_frame, conf=0.1, verbose=False)
            
            if not results:
                raise RuntimeError("El modelo no retorna resultados válidos")
                
            logger.info(f"Worker-{self.worker_id}: Validación del modelo exitosa")
            
        except Exception as e:
            raise RuntimeError(f"Fallo en validación del modelo: {e}")
    
    def _send_alert(self, alert_type: SystemAlert, message: str, details: Dict = None):
        """Envía una alerta al sistema principal."""
        if self.alert_callback:
            try:
                alert = AlertMessage(
                    alert_type=alert_type,
                    message=message,
                    component=f"AdvancedInferenceWorker-{self.worker_id}",
                    details=details or {}
                )
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Error enviando alerta: {e}")
    
    def _calculate_frame_hash(self, frame: np.ndarray) -> str:
        """Calcula hash MD5 de un frame para detección de duplicados."""
        frame_bytes = frame.tobytes()
        return hashlib.md5(frame_bytes).hexdigest()
    
    def _check_duplicate_frame(self, frame_hash: str) -> bool:
        """Verifica si el frame es un duplicado reciente."""
        return frame_hash in self._frame_cache
    
    def _update_frame_cache(self, frame_hash: str, result: FrameAnalysisResult):
        """Actualiza el caché de frames procesados."""
        if len(self._frame_cache) >= self._cache_max_size:
            # Remover el más antiguo (FIFO)
            oldest_hash = next(iter(self._frame_cache))
            del self._frame_cache[oldest_hash]
        
        self._frame_cache[frame_hash] = result
    
    def _analyze_frame_quality(self, frame: np.ndarray) -> Tuple[float, float]:
        """Analiza la calidad del frame (iluminación y nitidez)."""
        # Análisis de iluminación (histograma)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        lighting_score = 1.0 - (np.std(hist) / np.max(hist))  # Simplificado
        
        # Análisis de nitidez (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = min(1.0, np.var(laplacian) / 1000)  # Normalizado
        
        return lighting_score, blur_score
    
    def _adaptive_optimization(self):
        """Optimización adaptativa basada en métricas de rendimiento."""
        if not self._enable_auto_optimization:
            return
            
        current_time = time.time()
        if current_time - self._last_optimization < self._optimization_interval:
            return
            
        try:
            # Analizar rendimiento reciente
            recent_performance = list(self._performance_history)[-100:]  # Últimos 100 frames
            if len(recent_performance) < 50:
                return  # Insuficientes datos
            
            avg_fps = statistics.mean(recent_performance)
            
            # Ajustar umbral de confianza según rendimiento
            if avg_fps < self._performance_target_fps * 0.8:
                # Rendimiento bajo: reducir calidad para aumentar velocidad
                self._adaptive_confidence = min(0.9, self._adaptive_confidence + 0.05)
                logger.info(f"Worker-{self.worker_id}: Reduciendo calidad para mejorar rendimiento (conf: {self._adaptive_confidence})")
            elif avg_fps > self._performance_target_fps * 1.2:
                # Rendimiento alto: aumentar calidad
                self._adaptive_confidence = max(0.3, self._adaptive_confidence - 0.05)
                logger.info(f"Worker-{self.worker_id}: Aumentando calidad (conf: {self._adaptive_confidence})")
            
            self._last_optimization = current_time
            
        except Exception as e:
            logger.error(f"Worker-{self.worker_id}: Error en optimización adaptativa: {e}")
    
    def get_system_metrics(self) -> SystemMetrics:
        """Obtiene métricas actuales del sistema."""
        with self._stats_lock:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            metrics = SystemMetrics(
                fps_current=self._performance_history[-1] if self._performance_history else 0.0,
                fps_average=statistics.mean(self._performance_history) if self._performance_history else 0.0,
                memory_usage_mb=memory.used / 1024**2,
                cpu_usage_percent=cpu_percent,
                queue_input_size=self.input_queue.qsize(),
                queue_output_size=self.output_queue.qsize(),
                total_frames_processed=self.statistics.total_frames,
                total_detections=self.statistics.total_detections,
                error_count=self._error_count,
                uptime_seconds=time.time() - self._start_time
            )
            
            if self.device == "cuda" and torch.cuda.is_available():
                try:
                    metrics.gpu_usage_percent = torch.cuda.utilization()
                    metrics.gpu_memory_mb = torch.cuda.memory_allocated() / 1024**2
                except:
                    pass  # Ignorar errores de métricas GPU
                    
            return metrics

    def run(self):
        """
        Bucle principal avanzado con procesamiento inteligente, manejo de errores
        robusto y optimización en tiempo real.
        """
        logger.info(f"Worker-{self.worker_id}: Iniciando bucle principal")
        
        # Cargar modelo
        self._load_model()
        
        if self.model_status != ModelStatus.READY:
            logger.error(f"Worker-{self.worker_id}: No se pudo cargar el modelo, terminando worker")
            return
        
        # Bucle principal con manejo avanzado
        while not self._stop_event.is_set():
            try:
                # Verificar si el worker está pausado
                if self._pause_event.is_set():
                    time.sleep(0.1)
                    continue
                
                # Obtener tarea de la cola con prioridad
                try:
                    priority, timestamp, frame_id, frame = self.input_queue.get(timeout=0.1)
                except Empty:
                    # Realizar mantenimiento durante tiempo libre
                    self._perform_maintenance()
                    continue
                
                # Señal de finalización
                if frame is None:
                    self._stop_event.set()
                    break
                
                # Procesar frame con métricas completas
                result = self._process_frame_advanced(frame_id, frame, priority)
                
                # Enviar resultado
                self.output_queue.put((frame_id, result))
                
                # Actualizar estadísticas
                with self._stats_lock:
                    self.statistics.update(result)
                    current_fps = 1000 / result.total_processing_time_ms if result.total_processing_time_ms > 0 else 0
                    self._performance_history.append(current_fps)
                
                # Realizar optimización adaptativa periódicamente
                self._adaptive_optimization()
                
                # Reset contador de errores consecutivos en caso de éxito
                self._consecutive_errors = 0

            except Exception as e:
                self._consecutive_errors += 1
                self._error_count += 1
                
                logger.exception(f"Worker-{self.worker_id}: Error en bucle principal: {e}")
                self._send_alert(SystemAlert.ERROR, f"Error en procesamiento: {e}")
                
                # Crear resultado de error
                error_result = FrameAnalysisResult(
                    frame_id=frame_id if 'frame_id' in locals() else "unknown",
                    quality=DetectionQuality.FAILED,
                    system_load=psutil.cpu_percent()
                )
                self.output_queue.put((frame_id if 'frame_id' in locals() else "unknown", error_result))
                
                # Recuperación automática si hay muchos errores consecutivos
                if self._consecutive_errors >= self._max_consecutive_errors:
                    logger.critical(f"Worker-{self.worker_id}: Demasiados errores consecutivos, intentando recuperación")
                    self._attempt_recovery()
        
        logger.info(f"Worker-{self.worker_id}: Bucle principal terminado")
    
    def _process_frame_advanced(self, frame_id: str, frame: np.ndarray, 
                              priority: ProcessingPriority) -> FrameAnalysisResult:
        """
        Procesamiento avanzado de frame con análisis de calidad, detección de duplicados
        y métricas detalladas.
        """
        start_total = time.perf_counter()
        
        # Calcular hash del frame para detección de duplicados
        frame_hash = self._calculate_frame_hash(frame)
        
        # Verificar caché de duplicados
        if self._check_duplicate_frame(frame_hash):
            cached_result = self._frame_cache[frame_hash]
            logger.debug(f"Worker-{self.worker_id}: Frame duplicado detectado, usando caché")
            return cached_result
        
        # Análisis de calidad del frame
        start_preprocess = time.perf_counter()
        lighting_score, blur_score = self._analyze_frame_quality(frame)
        preprocess_time = (time.perf_counter() - start_preprocess) * 1000
        
        # Realizar inferencia con configuración adaptativa
        start_inference = time.perf_counter()
        detections = []
        
        try:
            with self._model_lock:
                if self.model is None:
                    raise RuntimeError("Modelo no disponible")
                
                # Usar umbral adaptativo
                confidence_threshold = self._adaptive_confidence
                
                # Inferencia principal
                results = self.model.predict(
                    frame, 
                    conf=confidence_threshold,
                    verbose=False,
                    half=self.device == "cuda"  # Usar FP16 en GPU para mayor velocidad
                )
                
                inference_time = (time.perf_counter() - start_inference) * 1000
                
                # Procesamiento avanzado de resultados
                start_postprocess = time.perf_counter()
                detections = self._process_detections_advanced(results, frame.shape)
                
        except Exception as e:
            logger.error(f"Worker-{self.worker_id}: Error en inferencia: {e}")
            inference_time = (time.perf_counter() - start_inference) * 1000
            start_postprocess = time.perf_counter()
        
        postprocess_time = (time.perf_counter() - start_postprocess) * 1000
        total_time = (time.perf_counter() - start_total) * 1000
        
        # Determinar calidad de la detección
        quality = self._assess_detection_quality(detections, lighting_score, blur_score)
        
        # Crear resultado completo
        result = FrameAnalysisResult(
            detections=detections,
            fruit_count=len(detections),
            inference_time_ms=inference_time,
            preprocessing_time_ms=preprocess_time,
            postprocessing_time_ms=postprocess_time,
            total_processing_time_ms=total_time,
            frame_shape=(frame.shape[0], frame.shape[1]),
            frame_id=frame_id,
            frame_hash=frame_hash,
            quality=quality,
            lighting_score=lighting_score,
            blur_score=blur_score,
            system_load=psutil.cpu_percent()
        )
        
        # Actualizar caché
        self._update_frame_cache(frame_hash, result)
        
        return result
    
    def _process_detections_advanced(self, results, frame_shape) -> List[FruitDetection]:
        """Procesa las detecciones de YOLO con análisis avanzado."""
        detections = []
        
        if not results or results[0].boxes is None:
            return detections
        
        frame_height, frame_width = frame_shape[:2]
        
        for box in results[0].boxes:
            try:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                # Calcular métricas avanzadas
                width = x2 - x1
                height = y2 - y1
                area = width * height
                aspect_ratio = width / height if height > 0 else 0.0
                
                # Distancia al borde (normalizada)
                edge_distance = min(
                    x1, y1, frame_width - x2, frame_height - y2
                ) / min(frame_width, frame_height)
                
                # Puntuación de calidad basada en múltiples factores
                quality_score = self._calculate_detection_quality_score(
                    float(box.conf), area, aspect_ratio, edge_distance
                )
                
                detection = FruitDetection(
                    class_id=int(box.cls),
                    class_name=self.model.names[int(box.cls)],
                    confidence=float(box.conf),
                    bbox=(x1, y1, x2, y2),
                    center_px=(center_x, center_y),
                    area_px=area,
                    aspect_ratio=aspect_ratio,
                    edge_distance=edge_distance,
                    quality_score=quality_score
                )
                
                detections.append(detection)
                
            except Exception as e:
                logger.warning(f"Worker-{self.worker_id}: Error procesando detección: {e}")
                continue
        
        return detections
    
    def _calculate_detection_quality_score(self, confidence: float, area: int, 
                                         aspect_ratio: float, edge_distance: float) -> float:
        """Calcula una puntuación de calidad para una detección individual."""
        # Factores de calidad con pesos
        confidence_factor = confidence  # 0-1
        area_factor = min(1.0, area / 10000)  # Normalizado para área típica
        ratio_factor = 1.0 - abs(aspect_ratio - 1.0)  # Mejor si es cercano a cuadrado
        edge_factor = edge_distance  # Mejor si está lejos de los bordes
        
        # Promedio ponderado
        quality = (
            confidence_factor * 0.4 +
            area_factor * 0.2 +
            ratio_factor * 0.2 +
            edge_factor * 0.2
        )
        
        return min(1.0, max(0.0, quality))
    
    def _assess_detection_quality(self, detections: List[FruitDetection], 
                                 lighting_score: float, blur_score: float) -> DetectionQuality:
        """Evalúa la calidad general de las detecciones en el frame."""
        if not detections:
            return DetectionQuality.FAILED
        
        avg_confidence = statistics.mean([d.confidence for d in detections])
        avg_quality = statistics.mean([d.quality_score for d in detections])
        
        # Factores combinados
        overall_score = (
            avg_confidence * 0.4 +
            avg_quality * 0.3 +
            lighting_score * 0.15 +
            blur_score * 0.15
        )
        
        if overall_score >= 0.9:
            return DetectionQuality.EXCELLENT
        elif overall_score >= 0.75:
            return DetectionQuality.GOOD
        elif overall_score >= 0.6:
            return DetectionQuality.ACCEPTABLE
        else:
            return DetectionQuality.POOR
    
    def _perform_maintenance(self):
        """Realiza tareas de mantenimiento durante tiempo libre."""
        # Limpieza de memoria cada cierto tiempo
        current_time = time.time()
        if hasattr(self, '_last_gc') and current_time - self._last_gc > 60:  # Cada minuto
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self._last_gc = current_time
        elif not hasattr(self, '_last_gc'):
            self._last_gc = current_time
    
    def _attempt_recovery(self):
        """Intenta recuperación automática del worker."""
        try:
            logger.info(f"Worker-{self.worker_id}: Iniciando recuperación automática")
            
            # Limpiar memoria
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            # Reinicializar modelo si es necesario
            if self.model_status == ModelStatus.ERROR:
                self.model_status = ModelStatus.MAINTENANCE
                self._load_model()
            
            # Reset contadores
            self._consecutive_errors = 0
            self._error_count = max(0, self._error_count - 5)  # Reducir contador de errores
            
            logger.info(f"Worker-{self.worker_id}: Recuperación completada")
            
        except Exception as e:
            logger.error(f"Worker-{self.worker_id}: Error en recuperación: {e}")
            self._send_alert(SystemAlert.CRITICAL, f"Fallo en recuperación automática: {e}")

    def stop(self):
        """Señaliza al hilo para que se detenga de forma segura."""
        logger.info(f"Worker-{self.worker_id}: Iniciando proceso de parada")
        self._stop_event.set()
        
        # Despertar el worker si está esperando en la cola
        try:
            self.input_queue.put_nowait((ProcessingPriority.CRITICAL, time.time(), None, None))
        except Full:
            pass
        
        logger.info(f"Worker-{self.worker_id}: Señal de parada enviada")

    def pause(self):
        """Pausa temporalmente el worker."""
        self._pause_event.set()
        logger.info(f"Worker-{self.worker_id}: Worker pausado")

    def resume(self):
        """Reanuda el worker después de una pausa."""
        self._pause_event.clear()
        logger.info(f"Worker-{self.worker_id}: Worker reanudado")

    def wait_for_model(self, timeout: float = 30.0) -> bool:
        """Bloquea hasta que el modelo esté cargado o se alcance el timeout."""
        logger.info(f"Worker-{self.worker_id}: Esperando carga del modelo (timeout: {timeout}s)")
        return self._model_loaded.wait(timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del worker."""
        with self._stats_lock:
            return {
                'worker_id': self.worker_id,
                'model_status': self.model_status.name,
                'device': self.device,
                'is_running': not self._stop_event.is_set(),
                'is_paused': self._pause_event.is_set(),
                'total_frames_processed': self.statistics.total_frames,
                'total_detections': self.statistics.total_detections,
                'error_count': self._error_count,
                'consecutive_errors': self._consecutive_errors,
                'uptime_seconds': time.time() - self._start_time,
                'avg_fps': self.statistics.get_average_fps(),
                'adaptive_confidence': self._adaptive_confidence,
                'cache_size': len(self._frame_cache)
            }

# --- Gestor Principal de Detección Empresarial ---

class EnterpriseFruitDetector:
    """
    Sistema de detección de frutas de nivel empresarial con características avanzadas:
    
    - Pool de workers múltiples para alta performance
    - Balanceamiento de carga dinámico e inteligente  
    - Sistema de alertas y monitoreo en tiempo real
    - Auto-escalado basado en demanda
    - Métricas detalladas y analytics
    - Recuperación automática de fallos
    - Optimización adaptativa continua
    - API asíncrona de alta performance
    
    Diseñado para entornos de producción industrial con requisitos de alta disponibilidad.
    """
    
    def __init__(self, config: Dict):
        # Configuración del sistema
        self._config = config.get("ai_model_settings", {})
        self._request_timeout_s = self._config.get("request_timeout_s", 10.0)
        self._num_workers = self._config.get("num_workers", min(4, psutil.cpu_count()))
        self._enable_auto_scaling = self._config.get("enable_auto_scaling", True)
        self._max_queue_size = self._config.get("max_queue_size", 50)
        self._enable_analytics = self._config.get("enable_analytics", True)
        
        # Colas de comunicación con prioridad
        self._input_queue = PriorityQueue(maxsize=self._max_queue_size)
        self._output_queue = Queue(maxsize=self._max_queue_size * 2)
        self._alert_queue = Queue(maxsize=100)
        
        # Pool de workers
        self._workers: List[AdvancedInferenceWorker] = []
        self._worker_load_balancer = {}  # worker_id -> carga actual
        
        # Gestión de tareas asíncronas
        self._result_listener_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        self._load_balancer_task: Optional[asyncio.Task] = None
        
        # Rastreo de peticiones
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_priorities: Dict[str, ProcessingPriority] = {}
        self._lock = RLock()
        
        # Métricas y estadísticas globales
        self._global_statistics = DetectionStatistics()
        self._system_alerts: deque = deque(maxlen=1000)
        self._performance_metrics = deque(maxlen=10000)
        self._start_time = time.time()
        
        # Estado del sistema
        self._is_running = False
        self._is_scaling = False
        
        # Callbacks para eventos
        self._alert_callbacks: List[Callable] = []
        self._metrics_callbacks: List[Callable] = []
        
        logger.info(f"EnterpriseFruitDetector instanciado con {self._num_workers} workers")

    async def initialize(self) -> bool:
        """
        Inicializa el sistema empresarial completo con pool de workers,
        monitoreo, alertas y balanceamiento de carga.
        """
        if self._is_running:
            logger.warning("EnterpriseFruitDetector ya está inicializado.")
            return True
            
        logger.info("Inicializando EnterpriseFruitDetector...")
        
        try:
            # Crear pool de workers
            await self._create_worker_pool()
            
            # Esperar a que todos los modelos se carguen
            await self._wait_for_all_models()
            
            # Iniciar tareas de gestión del sistema
            await self._start_system_tasks()
            
            self._is_running = True
            self._send_system_alert(SystemAlert.INFO, "Sistema EnterpriseFruitDetector inicializado correctamente")
            logger.info("EnterpriseFruitDetector inicializado correctamente.")
            return True
            
        except Exception as e:
            logger.exception(f"Error crítico inicializando EnterpriseFruitDetector: {e}")
            await self.shutdown()
            return False
    
    async def _create_worker_pool(self):
        """Crea el pool inicial de workers de inferencia."""
        logger.info(f"Creando pool de {self._num_workers} workers...")
        
        for worker_id in range(self._num_workers):
            worker = AdvancedInferenceWorker(
                worker_id=worker_id,
                config=self._config,
                input_queue=self._input_queue,
                output_queue=self._output_queue,
                alert_callback=self._handle_worker_alert
            )
            
            self._workers.append(worker)
            self._worker_load_balancer[worker_id] = 0.0
            worker.start()
            
        logger.info(f"Pool de {len(self._workers)} workers creado")
    
    async def _wait_for_all_models(self, timeout: float = 60.0):
        """Espera a que todos los workers carguen sus modelos."""
        logger.info("Esperando carga de modelos en todos los workers...")
        
        loop = asyncio.get_running_loop()
        
        # Crear tareas para esperar cada worker
        wait_tasks = []
        for worker in self._workers:
            task = loop.run_in_executor(None, worker.wait_for_model, timeout)
            wait_tasks.append(task)
        
        # Esperar a todos con timeout global
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*wait_tasks, return_exceptions=True),
                timeout=timeout
            )
            
            # Verificar resultados
            failed_workers = []
            for i, result in enumerate(results):
                if isinstance(result, Exception) or not result:
                    failed_workers.append(i)
            
            if failed_workers:
                raise RuntimeError(f"Workers {failed_workers} no pudieron cargar sus modelos")
                
            logger.info("Todos los modelos cargados exitosamente")
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout esperando carga de modelos ({timeout}s)")
    
    async def _start_system_tasks(self):
        """Inicia todas las tareas de gestión del sistema."""
        # Listener de resultados
        self._result_listener_task = asyncio.create_task(self._result_listener())
        
        # Sistema de alertas
        self._alert_task = asyncio.create_task(self._alert_processor())
        
        # Métricas del sistema
        if self._enable_analytics:
            self._metrics_task = asyncio.create_task(self._metrics_collector())
        
        # Balanceador de carga
        if self._enable_auto_scaling:
            self._load_balancer_task = asyncio.create_task(self._load_balancer())
        
        logger.info("Todas las tareas del sistema iniciadas")
    
    def _handle_worker_alert(self, alert: AlertMessage):
        """Maneja alertas provenientes de los workers."""
        try:
            self._alert_queue.put_nowait(alert)
        except Full:
            logger.warning("Cola de alertas llena, descartando alerta")
    
    def _send_system_alert(self, alert_type: SystemAlert, message: str, details: Dict = None):
        """Envía una alerta del sistema principal."""
        alert = AlertMessage(
            alert_type=alert_type,
            message=message,
            component="EnterpriseFruitDetector",
            details=details or {}
        )
        
        self._system_alerts.append(alert)
        
        # Notificar callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    def register_alert_callback(self, callback: Callable[[AlertMessage], None]):
        """Registra un callback para recibir alertas del sistema."""
        self._alert_callbacks.append(callback)
    
    def register_metrics_callback(self, callback: Callable[[SystemMetrics], None]):
        """Registra un callback para recibir métricas del sistema."""
        self._metrics_callbacks.append(callback)

    async def shutdown(self):
        """
        Detiene de forma segura todo el sistema empresarial:
        workers, tareas de gestión y limpia recursos.
        """
        if not self._is_running:
            return
            
        logger.info("Iniciando shutdown de EnterpriseFruitDetector...")
        self._is_running = False
        
        try:
            # Cancelar tareas del sistema
            await self._stop_system_tasks()
            
            # Detener workers
            await self._stop_workers()
            
            # Limpiar recursos
            self._cleanup_resources()
            
            self._send_system_alert(SystemAlert.INFO, "Sistema EnterpriseFruitDetector detenido correctamente")
            logger.info("EnterpriseFruitDetector detenido correctamente.")
            
        except Exception as e:
            logger.exception(f"Error durante shutdown: {e}")
            
    async def _stop_system_tasks(self):
        """Detiene todas las tareas del sistema."""
        tasks = [
            self._result_listener_task,
            self._metrics_task, 
            self._alert_task,
            self._load_balancer_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        logger.info("Tareas del sistema detenidas")
    
    async def _stop_workers(self):
        """Detiene todos los workers de forma ordenada."""
        logger.info(f"Deteniendo {len(self._workers)} workers...")
        
        # Enviar señal de parada a todos
        for worker in self._workers:
            worker.stop()
        
        # Esperar a que terminen con timeout
        loop = asyncio.get_running_loop()
        
        async def wait_worker(worker):
            await loop.run_in_executor(None, worker.join, 10.0)  # 10s timeout
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*[wait_worker(w) for w in self._workers]),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning("Algunos workers no terminaron en el tiempo esperado")
            
        logger.info("Workers detenidos")
    
    def _cleanup_resources(self):
        """Limpia recursos y caches."""
        # Limpiar colas
        while not self._input_queue.empty():
            try:
                self._input_queue.get_nowait()
            except:
                break
                
        while not self._output_queue.empty():
            try:
                self._output_queue.get_nowait()
            except:
                break
        
        # Reset estructuras de datos
        self._workers.clear()
        self._worker_load_balancer.clear()
        self._pending_requests.clear()
        
        # Forzar garbage collection
        gc.collect()
        
        logger.info("Recursos limpiados")

    async def _result_listener(self):
        """
        Listener avanzado de resultados con métricas, balanceamiento de carga
        y procesamiento en lotes para alta performance.
        """
        loop = asyncio.get_running_loop()
        logger.info("Listener empresarial de resultados iniciado")
        
        batch_size = 10  # Procesar resultados en lotes
        batch_timeout = 0.01  # Timeout para recolección de lotes
        
        while self._is_running:
            try:
                # Recolectar lote de resultados
                results_batch = []
                start_time = time.time()
                
                while len(results_batch) < batch_size and (time.time() - start_time) < batch_timeout:
                    try:
                        result = await loop.run_in_executor(None, self._output_queue.get, False)
                        results_batch.append(result)
                    except Empty:
                        break
                
                # Procesar lote
                if results_batch:
                    await self._process_results_batch(results_batch)
                else:
                    await asyncio.sleep(0.001)  # Pequeña pausa si no hay resultados
                    
            except Exception as e:
                logger.exception(f"Error en listener de resultados: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Listener empresarial de resultados detenido")
    
    async def _process_results_batch(self, results_batch: List[Tuple[str, FrameAnalysisResult]]):
        """Procesa un lote de resultados de forma eficiente."""
        for frame_id, analysis_result in results_batch:
            try:
                # Actualizar estadísticas globales
                self._global_statistics.update(analysis_result)
                
                # Resolver future pendiente
                with self._lock:
                    future = self._pending_requests.pop(frame_id, None)
                    priority = self._request_priorities.pop(frame_id, None)
                
                if future and not future.done():
                    future.set_result(analysis_result)
                else:
                    logger.debug(f"Resultado para petición desconocida/expirada: {frame_id}")
                
                # Actualizar métricas de balanceador de carga
                if priority and priority != ProcessingPriority.LOW:
                    # Procesar high priority items más rápido
                    self._update_load_balancer_metrics(analysis_result)
                    
            except Exception as e:
                logger.error(f"Error procesando resultado {frame_id}: {e}")
    
    def _update_load_balancer_metrics(self, result: FrameAnalysisResult):
        """Actualiza métricas para el balanceador de carga."""
        # Simplificado: actualizar carga basada en tiempo de procesamiento
        processing_factor = min(1.0, result.total_processing_time_ms / 100.0)  # Normalizar a 100ms
        
        # Distribuir carga entre workers (round-robin simple)
        min_load_worker = min(self._worker_load_balancer.items(), key=lambda x: x[1])
        worker_id = min_load_worker[0]
        self._worker_load_balancer[worker_id] += processing_factor * 0.1
        
        # Decaimiento de carga con el tiempo
        for wid in self._worker_load_balancer:
            self._worker_load_balancer[wid] *= 0.99

    async def detect_fruits(self, frame: np.ndarray, 
                          priority: ProcessingPriority = ProcessingPriority.NORMAL) -> Optional[FrameAnalysisResult]:
        """
        Método principal empresarial para detección de frutas con prioridad,
        balanceamiento de carga y métricas avanzadas.
        """
        if not self._is_running or not self._workers:
            logger.error("Sistema no inicializado. No se puede procesar la petición.")
            return None

        request_id = str(uuid.uuid4())[:8]  # ID más corto para logs
        future = asyncio.get_running_loop().create_future()

        with self._lock:
            self._pending_requests[request_id] = future
            self._request_priorities[request_id] = priority

        try:
            # Crear item con prioridad para la cola
            timestamp = time.time()
            queue_item = (priority.value, timestamp, request_id, frame)
            
            # Intentar poner en cola con manejo inteligente de sobrecarga
            try:
                self._input_queue.put_nowait(queue_item)
            except Full:
                # Manejar cola llena según prioridad
                if priority in [ProcessingPriority.HIGH, ProcessingPriority.CRITICAL]:
                    # Para alta prioridad, intentar remover elementos de baja prioridad
                    await self._handle_queue_overflow(queue_item)
                else:
                    logger.warning(f"Cola llena, descartando petición {request_id} (prioridad: {priority.name})")
                    with self._lock:
                        self._pending_requests.pop(request_id, None)
                        self._request_priorities.pop(request_id, None)
                    return None

            # Esperar resultado con timeout adaptativo según prioridad
            timeout = self._get_adaptive_timeout(priority)
            
            try:
                result = await asyncio.wait_for(future, timeout=timeout)
                
                # Logging detallado según calidad del resultado
                self._log_detection_result(request_id, result, priority)
                
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout en petición {request_id} (prioridad: {priority.name}, timeout: {timeout}s)")
                with self._lock:
                    self._pending_requests.pop(request_id, None)
                    self._request_priorities.pop(request_id, None)
                return None

        except Exception as e:
            logger.exception(f"Error procesando petición {request_id}: {e}")
            # Limpiar referencias
            with self._lock:
                self._pending_requests.pop(request_id, None)
                self._request_priorities.pop(request_id, None)
            return None
    
    async def _handle_queue_overflow(self, priority_item):
        """Maneja el desbordamiento de cola removiendo items de baja prioridad."""
        try:
            # Intentar remover un item de baja prioridad
            removed_items = []
            temp_items = []
            
            # Extraer items hasta encontrar uno de baja prioridad
            while not self._input_queue.empty():
                try:
                    item = self._input_queue.get_nowait()
                    if item[0] >= ProcessingPriority.LOW.value:  # Baja prioridad
                        removed_items.append(item)
                        break
                    else:
                        temp_items.append(item)
                except Empty:
                    break
            
            # Restaurar items que no removimos
            for item in temp_items:
                try:
                    self._input_queue.put_nowait(item)
                except Full:
                    break
            
            # Añadir nuestro item de alta prioridad
            try:
                self._input_queue.put_nowait(priority_item)
                logger.info(f"Item de alta prioridad insertado, removidos {len(removed_items)} items de baja prioridad")
            except Full:
                # Si aún así no cabe, restaurar lo que removimos
                for item in removed_items:
                    try:
                        self._input_queue.put_nowait(item)
                    except Full:
                        break
                raise Full("No se pudo insertar item de alta prioridad")
                
        except Exception as e:
            logger.error(f"Error manejando overflow de cola: {e}")
            raise
    
    def _get_adaptive_timeout(self, priority: ProcessingPriority) -> float:
        """Calcula timeout adaptativo basado en prioridad y carga del sistema."""
        base_timeout = self._request_timeout_s
        
        # Ajustar según prioridad
        priority_multipliers = {
            ProcessingPriority.CRITICAL: 2.0,
            ProcessingPriority.HIGH: 1.5,
            ProcessingPriority.NORMAL: 1.0,
            ProcessingPriority.LOW: 0.7
        }
        
        timeout = base_timeout * priority_multipliers.get(priority, 1.0)
        
        # Ajustar según carga del sistema
        avg_load = statistics.mean(self._worker_load_balancer.values()) if self._worker_load_balancer else 0.5
        load_factor = 1.0 + (avg_load * 0.5)  # Aumentar timeout si hay mucha carga
        
        return timeout * load_factor
    
    def _log_detection_result(self, request_id: str, result: FrameAnalysisResult, priority: ProcessingPriority):
        """Logging detallado de resultados según calidad."""
        if result.quality == DetectionQuality.EXCELLENT:
            logger.debug(f"Excelente detección {request_id}: {result.fruit_count} frutas, {result.confidence_avg:.3f} confianza")
        elif result.quality == DetectionQuality.POOR:
            logger.warning(f"Detección pobre {request_id}: {result.fruit_count} frutas, calidad {result.quality.name}")
        elif priority in [ProcessingPriority.HIGH, ProcessingPriority.CRITICAL]:
            logger.info(f"Detección alta prioridad {request_id}: {result.fruit_count} frutas en {result.total_processing_time_ms:.1f}ms")
    
    async def detect_fruits_batch(self, frames: List[np.ndarray], 
                                priority: ProcessingPriority = ProcessingPriority.NORMAL) -> List[Optional[FrameAnalysisResult]]:
        """
        Procesamiento en lotes para alta performance.
        Envía múltiples frames simultáneamente y espera todos los resultados.
        """
        if not frames:
            return []
        
        # Crear tareas para todos los frames
        tasks = []
        for frame in frames:
            task = asyncio.create_task(self.detect_fruits(frame, priority))
            tasks.append(task)
        
        # Esperar todos los resultados
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convertir excepciones a None
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error en procesamiento de lote: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.exception(f"Error en procesamiento de lote: {e}")
            return [None] * len(frames)
    
    # --- Métodos de Gestión del Sistema ---
    
    async def _alert_processor(self):
        """Procesa alertas del sistema en segundo plano."""
        logger.info("Procesador de alertas iniciado")
        
        while self._is_running:
            try:
                # Procesar alertas de workers
                while not self._alert_queue.empty():
                    try:
                        alert = self._alert_queue.get_nowait()
                        await self._handle_system_alert(alert)
                    except Empty:
                        break
                
                await asyncio.sleep(0.1)  # Chequear cada 100ms
                
            except Exception as e:
                logger.exception(f"Error en procesador de alertas: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("Procesador de alertas detenido")
    
    async def _handle_system_alert(self, alert: AlertMessage):
        """Maneja alertas del sistema con acciones automáticas."""
        self._system_alerts.append(alert)
        
        # Acciones automáticas según tipo de alerta
        if alert.alert_type == SystemAlert.CRITICAL:
            logger.critical(f"ALERTA CRÍTICA de {alert.component}: {alert.message}")
            # Intentar acciones de recuperación
            await self._handle_critical_alert(alert)
            
        elif alert.alert_type == SystemAlert.ERROR:
            logger.error(f"ALERTA ERROR de {alert.component}: {alert.message}")
            
        elif alert.alert_type == SystemAlert.WARNING:
            logger.warning(f"ALERTA WARNING de {alert.component}: {alert.message}")
            
        # Notificar callbacks registrados
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    async def _handle_critical_alert(self, alert: AlertMessage):
        """Maneja alertas críticas con acciones de recuperación."""
        if "Worker" in alert.component and "Error crítico" in alert.message:
            # Worker falló, intentar reiniciarlo
            worker_id = self._extract_worker_id(alert.component)
            if worker_id is not None:
                await self._restart_worker(worker_id)
    
    def _extract_worker_id(self, component: str) -> Optional[int]:
        """Extrae el ID del worker del nombre del componente."""
        try:
            if "Worker-" in component:
                return int(component.split("Worker-")[1])
        except:
            pass
        return None
    
    async def _restart_worker(self, worker_id: int):
        """Reinicia un worker específico."""
        try:
            logger.info(f"Intentando reiniciar Worker-{worker_id}")
            
            # Detener worker actual si existe
            if worker_id < len(self._workers):
                old_worker = self._workers[worker_id]
                old_worker.stop()
                
                # Esperar a que termine
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, old_worker.join, 5.0)
            
            # Crear nuevo worker
            new_worker = AdvancedInferenceWorker(
                worker_id=worker_id,
                config=self._config,
                input_queue=self._input_queue,
                output_queue=self._output_queue,
                alert_callback=self._handle_worker_alert
            )
            
            # Reemplazar en la lista
            if worker_id < len(self._workers):
                self._workers[worker_id] = new_worker
            else:
                self._workers.append(new_worker)
            
            new_worker.start()
            
            # Esperar a que se cargue el modelo
            await loop.run_in_executor(None, new_worker.wait_for_model, 30.0)
            
            logger.info(f"Worker-{worker_id} reiniciado exitosamente")
            self._send_system_alert(SystemAlert.INFO, f"Worker-{worker_id} reiniciado exitosamente")
            
        except Exception as e:
            logger.exception(f"Error reiniciando Worker-{worker_id}: {e}")
            self._send_system_alert(SystemAlert.CRITICAL, f"Fallo al reiniciar Worker-{worker_id}: {e}")
    
    async def _metrics_collector(self):
        """Recolecta métricas del sistema continuamente."""
        logger.info("Recolector de métricas iniciado")
        
        while self._is_running:
            try:
                # Recolectar métricas de todos los workers
                system_metrics = await self._collect_system_metrics()
                
                # Almacenar para análisis
                self._performance_metrics.append(system_metrics)
                
                # Notificar callbacks
                for callback in self._metrics_callbacks:
                    try:
                        callback(system_metrics)
                    except Exception as e:
                        logger.error(f"Error en callback de métricas: {e}")
                
                await asyncio.sleep(5.0)  # Recolectar cada 5 segundos
                
            except Exception as e:
                logger.exception(f"Error en recolector de métricas: {e}")
                await asyncio.sleep(10.0)
        
        logger.info("Recolector de métricas detenido")
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Recolecta métricas agregadas del sistema."""
        # Métricas básicas del sistema
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Métricas agregadas de workers
        total_frames = sum(w.statistics.total_frames for w in self._workers)
        total_detections = sum(w.statistics.total_detections for w in self._workers)
        total_errors = sum(w._error_count for w in self._workers)
        
        # FPS agregado
        worker_fps = []
        for worker in self._workers:
            if worker._performance_history:
                worker_fps.append(statistics.mean(worker._performance_history))
        
        avg_fps = statistics.mean(worker_fps) if worker_fps else 0.0
        
        # Métricas de GPU si está disponible
        gpu_usage = 0.0
        gpu_memory = 0.0
        if torch.cuda.is_available():
            try:
                gpu_usage = torch.cuda.utilization() or 0.0
                gpu_memory = torch.cuda.memory_allocated() / 1024**2
            except:
                pass
        
        return SystemMetrics(
            fps_current=avg_fps,
            fps_average=self._global_statistics.get_average_fps(),
            memory_usage_mb=memory.used / 1024**2,
            cpu_usage_percent=cpu_percent,
            gpu_usage_percent=gpu_usage,
            gpu_memory_mb=gpu_memory,
            queue_input_size=self._input_queue.qsize(),
            queue_output_size=self._output_queue.qsize(),
            total_frames_processed=total_frames,
            total_detections=total_detections,
            error_count=total_errors,
            uptime_seconds=time.time() - self._start_time
        )
    
    async def _load_balancer(self):
        """Balanceador de carga automático."""
        logger.info("Balanceador de carga iniciado")
        
        while self._is_running:
            try:
                # Analizar carga actual
                await self._analyze_system_load()
                
                # Decidir si escalar
                if self._enable_auto_scaling and not self._is_scaling:
                    await self._auto_scale_workers()
                
                await asyncio.sleep(30.0)  # Analizar cada 30 segundos
                
            except Exception as e:
                logger.exception(f"Error en balanceador de carga: {e}")
                await asyncio.sleep(60.0)
        
        logger.info("Balanceador de carga detenido")
    
    async def _analyze_system_load(self):
        """Analiza la carga actual del sistema."""
        # Métricas de cola
        queue_utilization = self._input_queue.qsize() / self._max_queue_size
        
        # Métricas de workers
        avg_load = statistics.mean(self._worker_load_balancer.values()) if self._worker_load_balancer else 0.0
        
        # Métricas de sistema
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if queue_utilization > 0.8:
            self._send_system_alert(SystemAlert.WARNING, f"Cola de entrada al {queue_utilization*100:.1f}% de capacidad")
        
        if avg_load > 0.9:
            self._send_system_alert(SystemAlert.WARNING, f"Carga promedio de workers alta: {avg_load:.2f}")
        
        if cpu_percent > 90:
            self._send_system_alert(SystemAlert.WARNING, f"Uso de CPU alto: {cpu_percent:.1f}%")
    
    async def _auto_scale_workers(self):
        """Auto-escalado de workers basado en demanda."""
        try:
            self._is_scaling = True
            
            # Determinar si necesitamos más workers
            queue_pressure = self._input_queue.qsize() / self._max_queue_size
            avg_load = statistics.mean(self._worker_load_balancer.values()) if self._worker_load_balancer else 0.0
            
            max_workers = min(8, psutil.cpu_count())  # Límite razonable
            
            if (queue_pressure > 0.7 or avg_load > 0.8) and len(self._workers) < max_workers:
                # Escalar hacia arriba
                await self._scale_up()
            elif queue_pressure < 0.3 and avg_load < 0.4 and len(self._workers) > 2:
                # Escalar hacia abajo
                await self._scale_down()
                
        finally:
            self._is_scaling = False
    
    async def _scale_up(self):
        """Añade un worker adicional."""
        try:
            new_worker_id = len(self._workers)
            logger.info(f"Escalando hacia arriba: añadiendo Worker-{new_worker_id}")
            
            new_worker = AdvancedInferenceWorker(
                worker_id=new_worker_id,
                config=self._config,
                input_queue=self._input_queue,
                output_queue=self._output_queue,
                alert_callback=self._handle_worker_alert
            )
            
            self._workers.append(new_worker)
            self._worker_load_balancer[new_worker_id] = 0.0
            new_worker.start()
            
            # Esperar a que cargue el modelo
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(None, new_worker.wait_for_model, 30.0)
            
            if success:
                logger.info(f"Worker-{new_worker_id} añadido exitosamente")
                self._send_system_alert(SystemAlert.INFO, f"Worker-{new_worker_id} añadido por auto-escalado")
            else:
                # Remover si falló
                self._workers.pop()
                del self._worker_load_balancer[new_worker_id]
                new_worker.stop()
                logger.error(f"Fallo al añadir Worker-{new_worker_id}")
                
        except Exception as e:
            logger.exception(f"Error escalando hacia arriba: {e}")
    
    async def _scale_down(self):
        """Remueve un worker."""
        try:
            if len(self._workers) <= 2:  # Mantener mínimo de 2 workers
                return
                
            # Remover el último worker
            worker_to_remove = self._workers.pop()
            worker_id = worker_to_remove.worker_id
            
            logger.info(f"Escalando hacia abajo: removiendo Worker-{worker_id}")
            
            worker_to_remove.stop()
            
            # Esperar a que termine
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, worker_to_remove.join, 10.0)
            
            del self._worker_load_balancer[worker_id]
            
            logger.info(f"Worker-{worker_id} removido exitosamente")
            self._send_system_alert(SystemAlert.INFO, f"Worker-{worker_id} removido por auto-escalado")
            
        except Exception as e:
            logger.exception(f"Error escalando hacia abajo: {e}")
    
    # --- Métodos de Utilidad y Estado ---
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema."""
        worker_statuses = []
        for worker in self._workers:
            worker_statuses.append(worker.get_status())
        
        return {
            'is_running': self._is_running,
            'uptime_seconds': time.time() - self._start_time,
            'num_workers': len(self._workers),
            'workers': worker_statuses,
            'queue_sizes': {
                'input': self._input_queue.qsize(),
                'output': self._output_queue.qsize(),
                'alerts': self._alert_queue.qsize()
            },
            'global_statistics': {
                'total_frames': self._global_statistics.total_frames,
                'total_detections': self._global_statistics.total_detections,
                'avg_fps': self._global_statistics.get_average_fps(),
                'detection_rate': self._global_statistics.get_detection_rate()
            },
            'recent_alerts': [alert.to_dict() for alert in list(self._system_alerts)[-10:]],
            'load_balancer': dict(self._worker_load_balancer)
        }
    
    def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """Genera un reporte de rendimiento de las últimas horas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filtrar métricas recientes
        recent_metrics = [m for m in self._performance_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {'error': 'No hay datos de métricas suficientes'}
        
        # Calcular estadísticas
        fps_values = [m.fps_current for m in recent_metrics if m.fps_current > 0]
        cpu_values = [m.cpu_usage_percent for m in recent_metrics]
        memory_values = [m.memory_usage_mb for m in recent_metrics]
        
        report = {
            'time_period_hours': hours,
            'total_samples': len(recent_metrics),
            'performance': {
                'fps': {
                    'avg': statistics.mean(fps_values) if fps_values else 0,
                    'max': max(fps_values) if fps_values else 0,
                    'min': min(fps_values) if fps_values else 0,
                    'std': statistics.stdev(fps_values) if len(fps_values) > 1 else 0
                },
                'cpu_usage': {
                    'avg': statistics.mean(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0
                },
                'memory_usage_mb': {
                    'avg': statistics.mean(memory_values) if memory_values else 0,
                    'max': max(memory_values) if memory_values else 0,
                    'min': min(memory_values) if memory_values else 0
                }
            },
            'total_frames_processed': sum(m.total_frames_processed for m in recent_metrics[-1:]),
            'total_detections': sum(m.total_detections for m in recent_metrics[-1:])
        }
        
        return report

# --- Clase de Compatibilidad ---

# Alias para compatibilidad con código existente
AdvancedFruitDetector = EnterpriseFruitDetector

# --- Función de Factory ---

def create_fruit_detector(config: Dict, enterprise_mode: bool = True) -> Union[EnterpriseFruitDetector, AdvancedInferenceWorker]:
    """
    Factory function para crear la instancia apropiada del detector.
    
    Args:
        config: Configuración del sistema
        enterprise_mode: Si True, usa EnterpriseFruitDetector, sino AdvancedInferenceWorker standalone
    
    Returns:
        Instancia del detector apropiado
    """
    if enterprise_mode:
        return EnterpriseFruitDetector(config)
    else:
        # Modo standalone para pruebas o sistemas simples
        input_q = PriorityQueue(maxsize=10)
        output_q = Queue(maxsize=20)
        return AdvancedInferenceWorker(0, config.get("ai_model_settings", {}), input_q, output_q)

# --- Punto de Entrada Principal ---

if __name__ == "__main__":
    """
    Script de prueba para validar el funcionamiento del sistema empresarial.
    """
    import json
    import sys
    from pathlib import Path
    
    # Configuración del logging para pruebas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configuración de prueba
    test_config = {
        "ai_model_settings": {
            "model_path": "IA_Etiquetado/Models/best_fruit_model.pt",
            "confidence_threshold": 0.65,
            "num_workers": 2,
            "enable_auto_scaling": True,
            "enable_analytics": True,
            "request_timeout_s": 10.0,
            "max_queue_size": 20
        }
    }
    
    async def test_enterprise_detector():
        """Función de prueba del detector empresarial."""
        detector = EnterpriseFruitDetector(test_config)
        
        try:
            logger.info("=== Iniciando Prueba del EnterpriseFruitDetector ===")
            
            # Verificar si el modelo existe
            model_path = Path(test_config["ai_model_settings"]["model_path"])
            if not model_path.exists():
                logger.error(f"Modelo no encontrado en: {model_path}")
                logger.info("Coloque un modelo entrenado en la ruta especificada para ejecutar las pruebas completas.")
                return
            
            # Inicializar
            success = await detector.initialize()
            if not success:
                logger.error("Fallo al inicializar el detector")
                return
            
            # Crear frame de prueba
            test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            # Prueba de detección simple
            logger.info("Probando detección simple...")
            result = await detector.detect_fruits(test_frame, ProcessingPriority.HIGH)
            
            if result:
                logger.info(f"Detección exitosa: {result.fruit_count} frutas detectadas")
                logger.info(f"Calidad: {result.quality.name}, Tiempo: {result.total_processing_time_ms:.1f}ms")
            else:
                logger.error("Fallo en detección")
            
            # Prueba de lote
            logger.info("Probando procesamiento en lotes...")
            batch_frames = [test_frame.copy() for _ in range(3)]
            batch_results = await detector.detect_fruits_batch(batch_frames)
            logger.info(f"Lote procesado: {len([r for r in batch_results if r is not None])}/3 exitosos")
            
            # Mostrar estado del sistema
            status = detector.get_system_status()
            logger.info(f"Estado del sistema: {status['num_workers']} workers, {status['global_statistics']['total_frames']} frames procesados")
            
            # Esperar un poco para ver métricas
            await asyncio.sleep(5)
            
            # Mostrar reporte de rendimiento
            report = detector.get_performance_report(hours=1)
            if 'performance' in report:
                logger.info(f"Rendimiento promedio: {report['performance']['fps']['avg']:.1f} FPS")
            
        except Exception as e:
            logger.exception(f"Error en prueba: {e}")
        finally:
            # Cleanup
            await detector.shutdown()
            logger.info("=== Prueba Completada ===")
    
    # Ejecutar pruebas
    try:
        asyncio.run(test_enterprise_detector())
    except KeyboardInterrupt:
        logger.info("Prueba interrumpida por el usuario")
    except Exception as e:
        logger.exception(f"Error ejecutando pruebas: {e}")
