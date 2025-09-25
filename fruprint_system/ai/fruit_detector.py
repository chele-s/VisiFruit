# fruprint_system/ai/fruit_detector.py
import asyncio
import logging
from typing import Dict, Any, List, Tuple

import numpy as np
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class FruitDetector:
    """
    Un controlador simplificado para el modelo de IA de detección de frutas.
    Se enfoca en una sola responsabilidad: cargar el modelo y realizar inferencias.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_path = self.config.get("model_path", "IA_Etiquetado/Models/best_fruit_model.pt")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.65)
        
        self.model: YOLO | None = None
        self.device: str | None = None
        self.is_initialized = False

    async def initialize(self) -> bool:
        """
        Carga el modelo de IA en el dispositivo óptimo y lo prepara para la inferencia.
        Esta operación es bloqueante y se ejecutará en un hilo separado.
        """
        def _load_model_sync():
            try:
                # 1. Detectar el mejor dispositivo disponible (GPU o CPU)
                if torch.cuda.is_available():
                    self.device = "cuda"
                    logger.info("CUDA disponible. Usando GPU para inferencia.")
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.device = "mps"
                    logger.info("Apple MPS disponible. Usando GPU de Apple para inferencia.")
                else:
                    self.device = "cpu"
                    logger.warning("GPU no detectada. Usando CPU para inferencia (rendimiento reducido).")

                # 2. Cargar el modelo YOLO
                self.model = YOLO(self.model_path)
                self.model.to(self.device)
                
                # 3. Realizar una inferencia de "calentamiento" para optimizar tiempos futuros
                logger.info("Realizando inferencia de calentamiento del modelo...")
                dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
                self.model.predict(dummy_frame, conf=self.confidence_threshold, verbose=False)
                
                self.is_initialized = True
                logger.info(f"✅ Detector de IA inicializado con modelo '{self.model_path}' en '{self.device}'.")
                return True

            except Exception as e:
                logger.critical(f"❌ Error crítico al cargar el modelo de IA: {e}", exc_info=True)
                return False

        # Ejecutar la carga (que es bloqueante) en un hilo separado
        return await asyncio.to_thread(_load_model_sync)

    async def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Realiza la detección de frutas en un frame.
        La inferencia se ejecuta en un hilo para no bloquear el bucle de asyncio.
        """
        if not self.is_initialized or self.model is None:
            logger.error("El detector de IA no está inicializado. No se puede realizar la detección.")
            return []

        def _run_inference():
            results = self.model.predict(
                frame, 
                conf=self.confidence_threshold, 
                verbose=False,
                half=self.device=="cuda" # Usar FP16 en GPU para más velocidad
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

        try:
            return await asyncio.to_thread(_run_inference)
        except Exception as e:
            logger.error(f"Error durante la inferencia de IA: {e}")
            return []

    async def shutdown(self):
        """Libera los recursos del modelo."""
        logger.info("Apagando el detector de IA...")
        self.model = None
        self.device = None
        self.is_initialized = False
        # Forzar recolección de basura para liberar memoria de la GPU si es posible
        await asyncio.to_thread(torch.cuda.empty_cache)
        logger.info("Detector de IA apagado.")
