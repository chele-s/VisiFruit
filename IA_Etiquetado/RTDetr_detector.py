# IA_Etiquetado/RTDetr_detector.py
"""
FruPrint - Sistema Avanzado de Detección de Frutas con RT-DETR
==============================================================

Módulo de detección de frutas de alta performance para sistemas industriales
de etiquetado automático. Utiliza RT-DETR (Real-Time Detection Transformer)
con optimizaciones especializadas para entornos de producción en tiempo real.

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
Versión: 3.0 - Edición RT-DETR
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
import cv2

# Importaciones específicas de RT-DETR
try:
    # Para modelos RT-DETR de PaddlePaddle
    import paddle
    from paddledet.deploy import rt_detr_predictor
    PADDLE_AVAILABLE = True
except ImportError:
    try:
        # Para modelos RT-DETR de PyTorch
        from transformers import RTDetrForObjectDetection, RTDetrImageProcessor
        import torch.nn.functional as F
        PADDLE_AVAILABLE = False
        TORCH_RTDETR_AVAILABLE = True
    except ImportError:
        # Fallback - usar implementación personalizada
        PADDLE_AVAILABLE = False
        TORCH_RTDETR_AVAILABLE = False
        print("⚠️  RT-DETR dependencies not found. Install with:")
        print("pip install paddlepaddle-gpu paddledet")
        print("or")
        print("pip install transformers torch torchvision")

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)

# Importar estructuras existentes (mantenemos compatibilidad)
from .Fruit_detector import (
    DetectionQuality, ModelStatus, SystemAlert, ProcessingPriority,
    FruitDetection, FrameAnalysisResult, SystemMetrics, AlertMessage,
    DetectionStatistics
)

class RTDetrBackend(Enum):
    """Backend de RT-DETR a utilizar."""
    PADDLE = "paddle"
    PYTORCH = "pytorch"
    AUTO = "auto"

@dataclass
class RTDetrConfig:
    """Configuración específica para RT-DETR."""
    backend: RTDetrBackend = RTDetrBackend.AUTO
    model_path: str = ""
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    input_size: Tuple[int, int] = (640, 640)
    max_detections: int = 100
    batch_size: int = 1
    use_dynamic_input: bool = True
    optimize_for_speed: bool = True
    class_names: List[str] = field(default_factory=lambda: ["apple", "pear", "lemon"])


class RTDetrInferenceWorker(Thread):
    """
    Worker de inferencia avanzado usando RT-DETR para detección de frutas.
    
    Características:
    - Soporte para múltiples backends (PaddlePaddle, PyTorch)
    - Auto-detección del mejor dispositivo (GPU/CPU)
    - Optimizaciones específicas para RT-DETR
    - Sistema de métricas y alertas
    - Caché inteligente y warmup automático
    """
    
    def __init__(self, worker_id: int, config: Dict, input_queue: PriorityQueue, 
                 output_queue: Queue, alert_callback: Optional[Callable] = None):
        super().__init__(daemon=True, name=f"RTDetrWorker-{worker_id}")
        
        self.worker_id = worker_id
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.alert_callback = alert_callback
        
        # Configuración específica de RT-DETR
        self.rtdetr_config = RTDetrConfig(
            model_path=config.get("model_path", ""),
            confidence_threshold=config.get("confidence_threshold", 0.5),
            nms_threshold=config.get("nms_threshold", 0.4),
            input_size=tuple(config.get("input_size", [640, 640])),
            class_names=config.get("class_names", ["apple", "pear", "lemon"])
        )
        
        # Estado del worker
        self.model = None
        self.image_processor = None
        self.device = "cpu"
        self.backend = self._detect_best_backend()
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
        
        logger.info(f"RTDetrInferenceWorker-{worker_id} inicializado con backend: {self.backend}")

    def _detect_best_backend(self) -> RTDetrBackend:
        """Detecta el mejor backend disponible para RT-DETR."""
        if self.rtdetr_config.backend != RTDetrBackend.AUTO:
            return self.rtdetr_config.backend
        
        if PADDLE_AVAILABLE:
            logger.info("Backend PaddlePaddle detectado para RT-DETR")
            return RTDetrBackend.PADDLE
        elif TORCH_RTDETR_AVAILABLE:
            logger.info("Backend PyTorch detectado para RT-DETR")
            return RTDetrBackend.PYTORCH
        else:
            logger.warning("Ningún backend RT-DETR disponible, usando simulación")
            return RTDetrBackend.PYTORCH

    def _load_model(self):
        """
        Carga el modelo RT-DETR con optimizaciones avanzadas y configuración inteligente.
        """
        try:
            self.model_status = ModelStatus.LOADING
            self._send_alert(SystemAlert.INFO, f"Iniciando carga del modelo RT-DETR en Worker-{self.worker_id}")
            
            # Validar que el archivo del modelo existe
            model_path = Path(self.rtdetr_config.model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo RT-DETR no encontrado en: {self.rtdetr_config.model_path}")
            
            # Detección automática del mejor dispositivo
            self.device = self._detect_optimal_device()
            
            with self._model_lock:
                logger.info(f"Worker-{self.worker_id}: Cargando modelo RT-DETR desde {self.rtdetr_config.model_path} en {self.device}")
                
                if self.backend == RTDetrBackend.PADDLE:
                    self._load_paddle_model()
                elif self.backend == RTDetrBackend.PYTORCH:
                    self._load_pytorch_model()
                else:
                    raise RuntimeError(f"Backend no soportado: {self.backend}")
                
                # Configurar optimizaciones específicas del dispositivo
                self._configure_device_optimizations()
                
                # Warmup inteligente
                self.model_status = ModelStatus.WARMING_UP
                self._intelligent_warmup()
                
                # Validar funcionamiento del modelo
                self._validate_model_functionality()
                
            self.model_status = ModelStatus.READY
            self._model_loaded.set()
            self._send_alert(SystemAlert.INFO, f"Modelo RT-DETR cargado exitosamente en Worker-{self.worker_id}")
            logger.info(f"Worker-{self.worker_id}: Modelo RT-DETR cargado y optimizado.")

        except Exception as e:
            self.model_status = ModelStatus.ERROR
            self._error_count += 1
            self._send_alert(SystemAlert.CRITICAL, f"Error crítico cargando modelo RT-DETR: {e}")
            logger.exception(f"Worker-{self.worker_id}: Error crítico al cargar modelo RT-DETR: {e}")
            self.model = None
            self._stop_event.set()

    def _load_paddle_model(self):
        """Carga modelo RT-DETR usando PaddlePaddle."""
        if not PADDLE_AVAILABLE:
            raise ImportError("PaddlePaddle no está disponible")
        
        # Configurar dispositivo de Paddle
        if self.device.startswith('cuda'):
            paddle.set_device('gpu')
        else:
            paddle.set_device('cpu')
        
        # Cargar modelo RT-DETR de PaddlePaddle
        self.model = rt_detr_predictor.RTDetrPredictor(
            model_dir=self.rtdetr_config.model_path,
            device=self.device,
            run_mode='paddle',
            batch_size=self.rtdetr_config.batch_size,
            use_dynamic_shape=self.rtdetr_config.use_dynamic_input
        )
        
        logger.info(f"Modelo RT-DETR PaddlePaddle cargado en {self.device}")

    def _load_pytorch_model(self):
        """Carga modelo RT-DETR usando PyTorch/Transformers."""
        if not TORCH_RTDETR_AVAILABLE:
            # Fallback: crear modelo simulado
            logger.warning("Transformers RT-DETR no disponible, creando modelo simulado")
            self.model = self._create_mock_model()
            self.image_processor = self._create_mock_processor()
            return
        
        # Cargar modelo RT-DETR de HuggingFace
        self.model = RTDetrForObjectDetection.from_pretrained(
            self.rtdetr_config.model_path,
            torch_dtype=torch.float16 if self.device.startswith('cuda') else torch.float32
        ).to(self.device)
        
        self.image_processor = RTDetrImageProcessor.from_pretrained(self.rtdetr_config.model_path)
        
        # Optimizaciones para PyTorch
        if self.rtdetr_config.optimize_for_speed:
            self.model.eval()
            if hasattr(torch, 'compile'):
                self.model = torch.compile(self.model)
        
        logger.info(f"Modelo RT-DETR PyTorch cargado en {self.device}")

    def _create_mock_model(self):
        """Crea un modelo simulado para pruebas."""
        class MockRTDetrModel:
            def __init__(self, device):
                self.device = device
                self.classes = ["apple", "pear", "lemon"]
            
            def __call__(self, inputs):
                # Simular detecciones
                batch_size = len(inputs['pixel_values'])
                mock_results = []
                
                for _ in range(batch_size):
                    # Generar detecciones aleatorias
                    num_detections = np.random.randint(1, 6)
                    boxes = np.random.rand(num_detections, 4) * 640
                    scores = np.random.rand(num_detections) * 0.5 + 0.5
                    labels = np.random.randint(0, len(self.classes), num_detections)
                    
                    mock_results.append({
                        'boxes': torch.tensor(boxes, device=self.device),
                        'scores': torch.tensor(scores, device=self.device),
                        'labels': torch.tensor(labels, device=self.device)
                    })
                
                return mock_results
            
            def eval(self):
                return self
            
            def to(self, device):
                self.device = device
                return self
        
        return MockRTDetrModel(self.device)

    def _create_mock_processor(self):
        """Crea un procesador de imágenes simulado."""
        class MockImageProcessor:
            def __call__(self, images, return_tensors="pt"):
                if isinstance(images, list):
                    batch_images = []
                    for img in images:
                        if isinstance(img, np.ndarray):
                            img = torch.from_numpy(img).float()
                        if img.ndim == 3:
                            img = img.permute(2, 0, 1)  # HWC -> CHW
                        img = img / 255.0  # Normalizar
                        img = F.interpolate(img.unsqueeze(0), size=(640, 640), mode='bilinear')[0]
                        batch_images.append(img)
                    
                    pixel_values = torch.stack(batch_images)
                else:
                    img = images
                    if isinstance(img, np.ndarray):
                        img = torch.from_numpy(img).float()
                    if img.ndim == 3:
                        img = img.permute(2, 0, 1)
                    img = img / 255.0
                    pixel_values = F.interpolate(img.unsqueeze(0), size=(640, 640), mode='bilinear')
                
                return {'pixel_values': pixel_values}
        
        return MockImageProcessor()

    def _detect_optimal_device(self) -> str:
        """Detecta y selecciona el dispositivo óptimo para inferencia."""
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            logger.info(f"Worker-{self.worker_id}: {gpu_count} GPU(s) detectada(s)")
            
            # Seleccionar GPU con más memoria libre
            best_gpu = 0
            max_memory = 0
            
            for i in range(gpu_count):
                props = torch.cuda.get_device_properties(i)
                free_memory = props.total_memory - torch.cuda.memory_allocated(i)
                if free_memory > max_memory:
                    max_memory = free_memory
                    best_gpu = i
            
            device = f'cuda:{best_gpu}'
            logger.info(f"Worker-{self.worker_id}: Usando GPU {best_gpu} ({max_memory/1024**3:.1f}GB libres)")
            return device
        else:
            logger.info(f"Worker-{self.worker_id}: Usando CPU")
            return 'cpu'

    def _configure_device_optimizations(self):
        """Configura optimizaciones específicas del dispositivo."""
        if self.device.startswith('cuda'):
            # Optimizaciones para GPU
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        else:
            # Optimizaciones para CPU
            torch.set_num_threads(min(4, psutil.cpu_count()))

    def _intelligent_warmup(self):
        """Realiza warmup inteligente del modelo con múltiples resoluciones."""
        logger.info(f"Worker-{self.worker_id}: Iniciando warmup inteligente RT-DETR...")
        
        warmup_sizes = [(320, 320), (640, 640), (800, 800)]
        
        for size in warmup_sizes:
            try:
                # Crear imagen sintética para warmup
                dummy_image = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
                
                # Procesar con el modelo
                start_time = time.time()
                _ = self._run_inference(dummy_image)
                warmup_time = (time.time() - start_time) * 1000
                
                logger.info(f"Worker-{self.worker_id}: Warmup {size}: {warmup_time:.1f}ms")
                
            except Exception as e:
                logger.warning(f"Worker-{self.worker_id}: Error en warmup {size}: {e}")
        
        logger.info(f"Worker-{self.worker_id}: Warmup completado")

    def _validate_model_functionality(self):
        """Valida que el modelo funciona correctamente."""
        try:
            # Crear imagen de prueba
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            # Ejecutar inferencia de prueba
            start_time = time.time()
            result = self._run_inference(test_image)
            inference_time = (time.time() - start_time) * 1000
            
            if result is None:
                raise RuntimeError("El modelo no devolvió resultados")
            
            logger.info(f"Worker-{self.worker_id}: Validación exitosa - {inference_time:.1f}ms")
            
        except Exception as e:
            raise RuntimeError(f"Validación del modelo falló: {e}")

    def _run_inference(self, image: np.ndarray) -> Optional[Dict]:
        """Ejecuta inferencia con el modelo RT-DETR."""
        try:
            if self.backend == RTDetrBackend.PADDLE:
                return self._run_paddle_inference(image)
            elif self.backend == RTDetrBackend.PYTORCH:
                return self._run_pytorch_inference(image)
            else:
                raise RuntimeError(f"Backend no soportado: {self.backend}")
                
        except Exception as e:
            logger.error(f"Error en inferencia RT-DETR: {e}")
            return None

    def _run_paddle_inference(self, image: np.ndarray) -> Optional[Dict]:
        """Ejecuta inferencia usando PaddlePaddle."""
        if not self.model:
            return None
        
        # Preparar imagen para PaddlePaddle
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        
        # Ejecutar predicción
        results = self.model.predict([image_rgb])
        
        if not results or len(results) == 0:
            return None
        
        result = results[0]
        return {
            'boxes': result.get('bbox', []),
            'scores': result.get('score', []),
            'labels': result.get('category_id', [])
        }

    def _run_pytorch_inference(self, image: np.ndarray) -> Optional[Dict]:
        """Ejecuta inferencia usando PyTorch."""
        if not self.model or not self.image_processor:
            return None
        
        try:
            # Preparar imagen
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
            
            # Procesar imagen
            inputs = self.image_processor(image_rgb, return_tensors="pt")
            
            # Mover a dispositivo
            if isinstance(inputs, dict):
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Ejecutar inferencia
            with torch.no_grad():
                outputs = self.model(inputs)
            
            # Extraer resultados
            if isinstance(outputs, list) and len(outputs) > 0:
                output = outputs[0]
            else:
                output = outputs
            
            return {
                'boxes': output.get('boxes', torch.tensor([])),
                'scores': output.get('scores', torch.tensor([])),
                'labels': output.get('labels', torch.tensor([]))
            }
            
        except Exception as e:
            logger.error(f"Error en inferencia PyTorch RT-DETR: {e}")
            return None

    def _process_detections_advanced(self, raw_results, frame_shape) -> List[FruitDetection]:
        """Procesa las detecciones de RT-DETR con análisis avanzado."""
        if not raw_results:
            return []
        
        detections = []
        frame_height, frame_width = frame_shape[:2]
        
        boxes = raw_results.get('boxes', [])
        scores = raw_results.get('scores', [])
        labels = raw_results.get('labels', [])
        
        # Convertir tensors a numpy si es necesario
        if hasattr(boxes, 'cpu'):
            boxes = boxes.cpu().numpy()
        if hasattr(scores, 'cpu'):
            scores = scores.cpu().numpy()
        if hasattr(labels, 'cpu'):
            labels = labels.cpu().numpy()
        
        # Asegurar que son arrays numpy
        boxes = np.array(boxes) if not isinstance(boxes, np.ndarray) else boxes
        scores = np.array(scores) if not isinstance(scores, np.ndarray) else scores
        labels = np.array(labels) if not isinstance(labels, np.ndarray) else labels
        
        # Filtrar por confianza
        confidence_mask = scores > self.rtdetr_config.confidence_threshold
        
        if not np.any(confidence_mask):
            return []
        
        boxes = boxes[confidence_mask]
        scores = scores[confidence_mask]
        labels = labels[confidence_mask]
        
        for i, (box, score, label_id) in enumerate(zip(boxes, scores, labels)):
            try:
                # Procesar coordenadas del bounding box
                x1, y1, x2, y2 = box
                
                # Asegurar que las coordenadas están en el rango válido
                x1 = max(0, min(x1, frame_width))
                y1 = max(0, min(y1, frame_height))
                x2 = max(x1, min(x2, frame_width))
                y2 = max(y1, min(y2, frame_height))
                
                # Calcular métricas adicionales
                width = x2 - x1
                height = y2 - y1
                area = int(width * height)
                aspect_ratio = width / height if height > 0 else 0
                
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # Calcular distancia al borde (normalizada)
                edge_distance = min(
                    center_x / frame_width,
                    center_y / frame_height,
                    (frame_width - center_x) / frame_width,
                    (frame_height - center_y) / frame_height
                )
                
                # Obtener nombre de la clase
                class_name = self.rtdetr_config.class_names[int(label_id)] if int(label_id) < len(self.rtdetr_config.class_names) else "unknown"
                
                # Calcular score de calidad
                quality_score = self._calculate_detection_quality_score(
                    float(score), area, aspect_ratio, edge_distance
                )
                
                # Crear detección
                detection = FruitDetection(
                    class_id=int(label_id),
                    class_name=class_name,
                    confidence=float(score),
                    bbox=(int(x1), int(y1), int(x2), int(y2)),
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
        # Score base de confianza
        confidence_score = confidence
        
        # Penalizar áreas muy pequeñas o muy grandes
        area_score = 1.0
        if area < 100:  # Muy pequeña
            area_score = area / 100
        elif area > 50000:  # Muy grande
            area_score = 50000 / area
        
        # Penalizar aspect ratios extraños (frutas suelen ser ~redondas)
        aspect_score = 1.0
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            aspect_score = 0.7
        
        # Penalizar detecciones muy cerca del borde
        edge_score = max(0.5, edge_distance * 2)
        
        # Combinar scores
        final_score = confidence_score * area_score * aspect_score * edge_score
        return min(1.0, max(0.0, final_score))

    def _send_alert(self, alert_type: SystemAlert, message: str, details: Dict = None):
        """Envía una alerta al sistema."""
        if self.alert_callback:
            alert = AlertMessage(
                alert_type=alert_type,
                message=message,
                component=f"RTDetrWorker-{self.worker_id}",
                details=details or {}
            )
            try:
                self.alert_callback(alert)
            except Exception as e:
                logger.error(f"Error enviando alerta: {e}")

    def get_system_metrics(self) -> SystemMetrics:
        """Obtiene métricas del sistema del worker."""
        return SystemMetrics(
            timestamp=datetime.now(),
            fps_current=self._calculate_current_fps(),
            fps_average=self.stats.get_average_fps(),
            memory_usage_mb=psutil.Process().memory_info().rss / (1024 * 1024),
            cpu_usage_percent=psutil.cpu_percent(),
            total_frames_processed=self.stats.total_frames,
            total_detections=self.stats.total_detections,
            error_count=self._error_count
        )

    def _calculate_current_fps(self) -> float:
        """Calcula el FPS actual basado en el historial reciente."""
        if len(self._performance_history) < 2:
            return 0.0
        
        recent_times = list(self._performance_history)[-10:]
        if len(recent_times) < 2:
            return 0.0
        
        time_span = recent_times[-1] - recent_times[0]
        if time_span > 0:
            return (len(recent_times) - 1) / time_span
        return 0.0

    def run(self):
        """Bucle principal del worker."""
        logger.info(f"RTDetrWorker-{self.worker_id}: Iniciando...")
        
        try:
            # Cargar modelo
            self._load_model()
            
            if self.model_status != ModelStatus.READY:
                logger.error(f"RTDetrWorker-{self.worker_id}: No se pudo cargar el modelo")
                return
            
            logger.info(f"RTDetrWorker-{self.worker_id}: Listo para procesar")
            
            # Bucle principal de procesamiento
            while not self._stop_event.is_set():
                try:
                    # Verificar pausa
                    if self._pause_event.is_set():
                        time.sleep(0.1)
                        continue
                    
                    # Obtener trabajo de la cola
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
                        logger.warning(f"RTDetrWorker-{self.worker_id}: Cola de salida llena")
                    
                    # Marcar trabajo como completado
                    self.input_queue.task_done()
                    
                    # Mantenimiento periódico
                    if time.time() - self._last_maintenance > 300:  # Cada 5 minutos
                        self._perform_maintenance()
                        self._last_maintenance = time.time()
                        
                except Exception as e:
                    logger.exception(f"RTDetrWorker-{self.worker_id}: Error procesando: {e}")
                    self._error_count += 1
                    
        except Exception as e:
            logger.exception(f"RTDetrWorker-{self.worker_id}: Error crítico: {e}")
            self._send_alert(SystemAlert.CRITICAL, f"Worker falló: {e}")
        finally:
            logger.info(f"RTDetrWorker-{self.worker_id}: Terminando...")

    def _process_frame_advanced(self, frame_id: str, frame: np.ndarray, 
                              priority: ProcessingPriority) -> FrameAnalysisResult:
        """Procesa un frame con análisis avanzado usando RT-DETR."""
        start_time = time.time()
        
        try:
            # Crear hash del frame para detección de duplicados
            frame_hash = self._calculate_frame_hash(frame)
            
            # Verificar caché
            if self._check_duplicate_frame(frame_hash):
                cached_result = self._frame_cache.get(frame_hash)
                if cached_result:
                    logger.debug(f"Frame {frame_id} encontrado en caché")
                    return cached_result
            
            preprocessing_start = time.time()
            
            # Análisis de calidad del frame
            lighting_score, blur_score = self._analyze_frame_quality(frame)
            
            preprocessing_time = (time.time() - preprocessing_start) * 1000
            
            # Inferencia principal
            inference_start = time.time()
            raw_results = self._run_inference(frame)
            inference_time = (time.time() - inference_start) * 1000
            
            # Post-procesamiento
            postprocessing_start = time.time()
            detections = self._process_detections_advanced(raw_results, frame.shape)
            postprocessing_time = (time.time() - postprocessing_start) * 1000
            
            total_time = (time.time() - start_time) * 1000
            
            # Calcular métricas adicionales
            confidences = [d.confidence for d in detections]
            confidence_avg = statistics.mean(confidences) if confidences else 0.0
            confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
            
            # Crear resultado
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
                blur_score=blur_score
            )
            
            # Evaluar calidad de detección
            result.quality = self._assess_detection_quality(detections, lighting_score, blur_score)
            
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
        """Calcula hash MD5 del frame para detección de duplicados."""
        return hashlib.md5(frame.tobytes()).hexdigest()

    def _check_duplicate_frame(self, frame_hash: str) -> bool:
        """Verifica si un frame ya fue procesado (basado en hash)."""
        return frame_hash in self._frame_cache

    def _update_frame_cache(self, frame_hash: str, result: FrameAnalysisResult):
        """Actualiza el caché de frames con límite de tamaño."""
        max_cache_size = 100
        
        if len(self._frame_cache) >= max_cache_size:
            # Eliminar el más antiguo
            oldest_key = next(iter(self._frame_cache))
            del self._frame_cache[oldest_key]
        
        self._frame_cache[frame_hash] = result

    def _analyze_frame_quality(self, frame: np.ndarray) -> Tuple[float, float]:
        """Analiza la calidad del frame (iluminación y desenfoque)."""
        try:
            # Análisis de iluminación
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            lighting_score = 1.0 - abs(mean_brightness - 128) / 128
            
            # Análisis de desenfoque (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_score = min(1.0, laplacian_var / 500.0)  # Normalizar
            
            return lighting_score, blur_score
        except Exception:
            return 0.5, 0.5  # Valores por defecto

    def _assess_detection_quality(self, detections: List[FruitDetection], 
                                 lighting_score: float, blur_score: float) -> DetectionQuality:
        """Evalúa la calidad general de las detecciones."""
        if not detections:
            return DetectionQuality.FAILED
        
        avg_confidence = statistics.mean([d.confidence for d in detections])
        avg_quality = statistics.mean([d.quality_score for d in detections])
        
        # Combinar métricas
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
        """Realiza mantenimiento periódico del worker."""
        try:
            # Limpiar caché antiguo
            current_time = time.time()
            old_cache_keys = []
            
            for key, result in self._frame_cache.items():
                if current_time - result.timestamp > 300:  # Más de 5 minutos
                    old_cache_keys.append(key)
            
            for key in old_cache_keys:
                del self._frame_cache[key]
            
            # Limpieza de memoria
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            
            gc.collect()
            
            logger.debug(f"RTDetrWorker-{self.worker_id}: Mantenimiento completado")
            
        except Exception as e:
            logger.warning(f"Error en mantenimiento: {e}")

    def stop(self):
        """Detiene el worker."""
        logger.info(f"RTDetrWorker-{self.worker_id}: Deteniendo...")
        self._stop_event.set()

    def pause(self):
        """Pausa el worker."""
        self._pause_event.set()

    def resume(self):
        """Reanuda el worker."""
        self._pause_event.clear()

    def wait_for_model(self, timeout: float = 30.0) -> bool:
        """Espera a que el modelo esté listo."""
        return self._model_loaded.wait(timeout)

    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del worker."""
        return {
            'worker_id': self.worker_id,
            'model_status': self.model_status.name,
            'device': self.device,
            'backend': self.backend.value,
            'error_count': self._error_count,
            'frames_processed': self.stats.total_frames,
            'detections_made': self.stats.total_detections,
            'is_running': not self._stop_event.is_set(),
            'is_paused': self._pause_event.is_set(),
            'cache_size': len(self._frame_cache)
        }


# Clase principal de detección compatible con la interfaz existente
class EnterpriseRTDetrDetector:
    """
    Detector empresarial de frutas usando RT-DETR.
    Mantiene compatibilidad con la interfaz existente de EnterpriseFruitDetector.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.rtdetr_config = RTDetrConfig(
            model_path=config.get("model_path", ""),
            confidence_threshold=config.get("confidence_threshold", 0.5),
            class_names=config.get("class_names", ["apple", "pear", "lemon"])
        )
        
        # Workers y colas
        self.workers = []
        self.input_queue = PriorityQueue(maxsize=1000)
        self.output_queue = Queue(maxsize=1000)
        
        # Control del sistema
        self._is_initialized = False
        self._alert_callbacks = []
        self._metrics_callbacks = []
        
        logger.info("EnterpriseRTDetrDetector inicializado")

    async def initialize(self) -> bool:
        """Inicializa el detector RT-DETR."""
        try:
            logger.info("Inicializando EnterpriseRTDetrDetector...")
            
            # Crear workers
            num_workers = self.config.get("num_workers", 2)
            
            for i in range(num_workers):
                worker = RTDetrInferenceWorker(
                    worker_id=i,
                    config=self.config,
                    input_queue=self.input_queue,
                    output_queue=self.output_queue,
                    alert_callback=self._handle_worker_alert
                )
                
                self.workers.append(worker)
                worker.start()
            
            # Esperar a que todos los workers estén listos
            for worker in self.workers:
                if not worker.wait_for_model(timeout=60.0):
                    raise RuntimeError(f"Worker {worker.worker_id} no se inicializó correctamente")
            
            self._is_initialized = True
            logger.info(f"EnterpriseRTDetrDetector inicializado con {len(self.workers)} workers")
            return True
            
        except Exception as e:
            logger.exception(f"Error inicializando EnterpriseRTDetrDetector: {e}")
            return False

    async def detect_fruits(self, frame: np.ndarray, 
                          priority: ProcessingPriority = ProcessingPriority.NORMAL) -> Optional[FrameAnalysisResult]:
        """Detecta frutas en un frame (interfaz compatible)."""
        if not self._is_initialized:
            logger.error("Detector no inicializado")
            return None
        
        frame_id = str(uuid.uuid4())[:8]
        timestamp = time.time()
        
        try:
            # Enviar a cola de procesamiento
            self.input_queue.put((priority.value, (frame_id, frame, timestamp)), timeout=5.0)
            
            # Esperar resultado
            result_frame_id, result = self.output_queue.get(timeout=30.0)
            self.output_queue.task_done()
            
            return result
            
        except Exception as e:
            logger.error(f"Error en detect_fruits: {e}")
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
            return {"status": "not_initialized"}
        
        worker_statuses = [worker.get_status() for worker in self.workers]
        
        return {
            "status": "running" if self._is_initialized else "initializing",
            "num_workers": len(self.workers),
            "backend": self.workers[0].backend.value if self.workers else "unknown",
            "workers": worker_statuses,
            "queue_sizes": {
                "input": self.input_queue.qsize(),
                "output": self.output_queue.qsize()
            }
        }

    async def shutdown(self):
        """Apaga el detector."""
        logger.info("Apagando EnterpriseRTDetrDetector...")
        
        # Detener workers
        for worker in self.workers:
            worker.stop()
        
        # Esperar a que terminen
        for worker in self.workers:
            worker.join(timeout=10.0)
        
        self._is_initialized = False
        logger.info("EnterpriseRTDetrDetector apagado")


# Función de compatibilidad
def create_fruit_detector(config: Dict, enterprise_mode: bool = True) -> EnterpriseRTDetrDetector:
    """Crea un detector de frutas RT-DETR (función de compatibilidad)."""
    return EnterpriseRTDetrDetector(config)
