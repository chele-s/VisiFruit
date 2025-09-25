# fruprint_system/ai/fruit_detector.py
import asyncio
import logging
import time
import hashlib
from collections import deque
from typing import Dict, Any, List, Optional, Callable
from threading import Thread, Event
from queue import Queue, Empty, Full

import numpy as np
import torch
from ultralytics import YOLO
from circuitbreaker import circuit

from fruprint_system.core.exceptions import AIError

logger = logging.getLogger(__name__)

# --- Clases de Datos y Enums ---

class ModelStatus(Enum):
    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    WARMING_UP = "warming_up"
    READY = "ready"
    ERROR = "error"

# --- Worker de Inferencia ---

class InferenceWorker(Thread):
    """
    Worker dedicado para ejecutar inferencias de IA en un hilo separado,
    evitando bloquear el bucle principal de asyncio.
    """
    def __init__(self, worker_id: int, config: Dict[str, Any], input_queue: Queue, output_queue: Queue):
        super().__init__(daemon=True, name=f"InferenceWorker-{worker_id}")
        self.worker_id = worker_id
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        
        self.model_path = self.config.get("model_path")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.65)
        
        self.model: Optional[YOLO] = None
        self.device: Optional[str] = None
        self.status = ModelStatus.UNINITIALIZED
        self._stop_event = Event()

    def run(self):
        """Bucle principal del worker."""
        try:
            self._load_model()
            while not self._stop_event.is_set():
                try:
                    frame, frame_hash = self.input_queue.get(timeout=1.0)
                    detections = self._run_inference(frame)
                    self.output_queue.put((frame_hash, detections))
                    self.input_queue.task_done()
                except Empty:
                    continue
        except Exception as e:
            self.status = ModelStatus.ERROR
            logger.critical(f"Worker de IA {self.worker_id} ha fallado: {e}", exc_info=True)

    def _load_model(self):
        """Carga el modelo de IA y lo prepara para la inferencia."""
        self.status = ModelStatus.LOADING
        if not self.model_path or not Path(self.model_path).exists():
            raise AIError(f"Ruta del modelo no válida o no encontrada: {self.model_path}")

        # Auto-detección del mejor dispositivo
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        
        logger.info(f"Worker {self.worker_id} cargando modelo en dispositivo: {self.device}")
        self.model = YOLO(self.model_path)
        self.model.to(self.device)

        # Warmup
        self.status = ModelStatus.WARMING_UP
        dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
        self.model.predict(dummy_frame, conf=self.confidence_threshold, verbose=False)
        
        self.status = ModelStatus.READY
        logger.info(f"✅ Worker de IA {self.worker_id} listo.")

    def _run_inference(self, frame: np.ndarray) -> List[Dict]:
        """Ejecuta la inferencia en un frame."""
        if not self.model or self.status != ModelStatus.READY:
            return []
            
        results = self.model.predict(
            frame, conf=self.confidence_threshold, verbose=False,
            half=self.device=="cuda" # Optimización para GPU
        )
        
        detections = []
        if results and results[0].boxes:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append({
                    "class_id": int(box.cls),
                    "class_name": self.model.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": (x1, y1, x2, y2),
                })
        return detections

    def stop(self):
        self._stop_event.set()

# --- Clase Principal del Detector ---

class FruitDetector:
    """
    Controlador avanzado para el modelo de IA, ahora con un pool de workers.
    Gestiona la distribución de trabajo y la recolección de resultados.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.num_workers = self.config.get("num_workers", 2)
        
        self.input_queue = Queue(maxsize=self.num_workers * 2)
        self.output_queue = Queue(maxsize=self.num_workers * 2)
        self.workers: List[InferenceWorker] = []
        
        self.is_initialized = False
        self.frame_cache = {}
        self.pending_futures: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
        self._result_handler_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Inicializa y arranca el pool de workers de inferencia."""
        logger.info(f"Inicializando detector de frutas con {self.num_workers} workers...")
        if self.is_initialized: return True

        for i in range(self.num_workers):
            worker = InferenceWorker(i, self.config, self.input_queue, self.output_queue)
            worker.start()
            self.workers.append(worker)

        # Esperar a que los workers estén listos
        await asyncio.sleep(5) # Dar tiempo a que los modelos carguen

        all_ready = all(w.status == ModelStatus.READY for w in self.workers)
        if not all_ready:
            raise AIError("No todos los workers de IA se inicializaron correctamente.")

        self._result_handler_task = asyncio.create_task(self._result_handler())
        self.is_initialized = True
        logger.info("✅ Pool de workers de IA inicializado y listo.")
        return True
    
    @circuit(failure_threshold=5, recovery_timeout=30)
    async def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Distribuye un frame al pool de workers para detección y espera el resultado.
        """
        if not self.is_initialized:
            raise AIError("El detector de IA no está inicializado.")

        frame_hash = hashlib.md5(frame.tobytes()).hexdigest()

        async with self._lock:
            if frame_hash in self.frame_cache:
                return self.frame_cache[frame_hash]
            
            future = asyncio.get_running_loop().create_future()
            self.pending_futures[frame_hash] = future
        
        try:
            self.input_queue.put((frame, frame_hash), block=False)
        except Full:
            async with self._lock:
                self.pending_futures.pop(frame_hash, None)
            raise AIError("La cola de inferencia de IA está llena.")

        return await asyncio.wait_for(future, timeout=10.0)

    async def _result_handler(self):
        """Maneja los resultados de la cola de salida de forma asíncrona."""
        loop = asyncio.get_running_loop()
        while self.is_initialized:
            try:
                # Usar to_thread para no bloquear el loop de asyncio
                frame_hash, detections = await asyncio.to_thread(self.output_queue.get, timeout=1.0)
                
                async with self._lock:
                    if frame_hash in self.pending_futures:
                        future = self.pending_futures.pop(frame_hash)
                        # Usar call_soon_threadsafe si el hilo del worker no es el mismo que el del loop
                        loop.call_soon_threadsafe(future.set_result, detections)
                        
                        # Cache
                        if len(self.frame_cache) > 100:
                            self.frame_cache.pop(next(iter(self.frame_cache)))
                        self.frame_cache[frame_hash] = detections
                
                self.output_queue.task_done()
            except Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error en el manejador de resultados de IA: {e}")

    async def shutdown(self):
        """Detiene todos los workers y limpia los recursos."""
        logger.info("Apagando el detector de IA y sus workers...")
        self.is_initialized = False
        if self._result_handler_task:
            self._result_handler_task.cancel()
        
        for worker in self.workers:
            worker.stop()
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        
        logger.info("Detector de IA apagado.")

