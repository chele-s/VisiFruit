# utils/camera_controller.py
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import cv2
import numpy as np

# Configuración del logger
logger = logging.getLogger(__name__)

# Intentar importar Picamera2 para RPi 5
try:
    from picamera2 import Picamera2
    _PICAMERA2_AVAILABLE = True
except ImportError:
    _PICAMERA2_AVAILABLE = False

class BaseCameraDriver:
    """Clase base abstracta para drivers de cámara."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_initialized = False

    async def initialize(self) -> bool:
        raise NotImplementedError

    async def capture_frame(self) -> Optional[np.ndarray]:
        raise NotImplementedError

    async def cleanup(self):
        raise NotImplementedError

class OpenCVCameraDriver(BaseCameraDriver):
    """Driver para cámaras OpenCV (USB, CSI)."""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device_id = config.get("source", 0)
        self.width = config.get("width", 1280)
        self.height = config.get("height", 720)
        self.fps = config.get("fps", 30)
        self.cap = None

    async def initialize(self) -> bool:
        """Inicializa la cámara OpenCV de forma asíncrona."""
        def _init():
            try:
                self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(self.device_id)
                
                if not self.cap.isOpened():
                    raise RuntimeError(f"No se pudo abrir la cámara {self.device_id}")

                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    raise RuntimeError("No se pudo capturar un frame de prueba.")
                
                self.is_initialized = True
                logger.info(f"Cámara OpenCV inicializada: {self.width}x{self.height} @ {self.fps}fps")
                return True
            except Exception as e:
                logger.error(f"Error inicializando cámara OpenCV: {e}")
                if self.cap: self.cap.release()
                return False

        return await asyncio.to_thread(_init)

    async def capture_frame(self) -> Optional[np.ndarray]:
        """Captura un frame usando un hilo para no bloquear."""
        if not self.is_initialized or not self.cap:
            return None
            
        def _read_frame():
            ret, frame = self.cap.read()
            return frame if ret else None
            
        return await asyncio.to_thread(_read_frame)

    async def cleanup(self):
        if self.cap:
            await asyncio.to_thread(self.cap.release)
            self.cap = None
        self.is_initialized = False

class Picamera2CameraDriver(BaseCameraDriver):
    """Driver para cámaras CSI usando Picamera2 (libcamera)."""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.width = config.get("width", 1280)
        self.height = config.get("height", 720)
        self.picam2: Optional[Picamera2] = None

    async def initialize(self) -> bool:
        if not _PICAMERA2_AVAILABLE:
            logger.error("Picamera2 no está disponible, no se puede usar este driver.")
            return False
        
        def _init():
            try:
                self.picam2 = Picamera2()
                config = self.picam2.create_video_configuration(main={"size": (self.width, self.height)})
                self.picam2.configure(config)
                self.picam2.start()
                # Captura de prueba
                frame = self.picam2.capture_array()
                if frame is None:
                    raise RuntimeError("No se pudo capturar un frame de prueba con Picamera2.")
                self.is_initialized = True
                logger.info(f"Picamera2 inicializada: {self.width}x{self.height}")
                return True
            except Exception as e:
                logger.error(f"Error inicializando Picamera2: {e}")
                if self.picam2: self.picam2.close()
                return False

        return await asyncio.to_thread(_init)

    async def capture_frame(self) -> Optional[np.ndarray]:
        if not self.is_initialized or not self.picam2: return None
        # La captura es bloqueante, así que la movemos a un hilo
        def _capture():
            frame = self.picam2.capture_array()
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if frame is not None else None
        return await asyncio.to_thread(_capture)

    async def cleanup(self):
        if self.picam2:
            await asyncio.to_thread(self.picam2.close)
            self.picam2 = None
        self.is_initialized = False

class MockCameraDriver(BaseCameraDriver):
    """Driver mock para pruebas sin hardware."""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.width = config.get("width", 1280)
        self.height = config.get("height", 720)

    async def initialize(self) -> bool:
        self.is_initialized = True
        logger.info("Cámara Mock inicializada.")
        return True

    async def capture_frame(self) -> Optional[np.ndarray]:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        ts = str(datetime.now())
        cv2.putText(frame, ts, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        await asyncio.sleep(0.03) # Simular latencia de captura
        return frame

    async def cleanup(self):
        self.is_initialized = False

class CameraController:
    """Controlador de cámara simplificado para la nueva arquitectura."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver: BaseCameraDriver | None = None

    async def initialize(self) -> bool:
        """Inicializa el driver de la cámara de forma asíncrona."""
        camera_type = self.config.get("type", "usb_webcam")
        
        # Seleccionar driver basado en la configuración y disponibilidad
        if camera_type == "csi_camera" and _PICAMERA2_AVAILABLE:
            self.driver = Picamera2CameraDriver(self.config)
        elif camera_type in ["usb_webcam", "csi_camera"]:
            self.driver = OpenCVCameraDriver(self.config)
        else: # "mock" o por defecto
            logger.info("Usando driver de cámara Mock.")
            self.driver = MockCameraDriver(self.config)
            
        return await self.driver.initialize()

    async def capture_frame(self) -> Optional[np.ndarray]:
        """Captura un frame de forma asíncrona."""
        if not self.driver or not self.driver.is_initialized:
            logger.warning("Intento de captura sin cámara inicializada.")
            return None
        return await self.driver.capture_frame()

    async def shutdown(self):
        """Apaga la cámara de forma segura."""
        if self.driver:
            await self.driver.cleanup()
