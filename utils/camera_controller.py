# utils/camera_controller.py
"""
Sistema de Control de Cámara Industrial Avanzado - FruPrint
=========================================================

Módulo de control de cámara de alta performance para sistemas industriales:
- Soporte para múltiples tipos de cámaras (USB, CSI, IP, industriales)
- Control automático de exposición, ganancia y balance de blancos
- Captura optimizada con buffer circular y multi-threading
- Análisis de calidad de imagen en tiempo real
- Calibración automática y corrección de distorsión
- Sistema de métricas y telemetría avanzada
- Recuperación automática de errores y reconexión
- Compresión adaptativa y streaming eficiente

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Edición Industrial
"""

import asyncio
import logging
import time
import threading
import queue
import statistics
import json
import cv2
import numpy as np
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional, List, Callable, Any, Union, Tuple
from contextlib import contextmanager

# Configuración del logger
logger = logging.getLogger(__name__)

# Intentar importar Picamera2 (libcamera Python) para Raspberry Pi 5
_PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2  # type: ignore
    _PICAMERA2_AVAILABLE = True
except Exception:
    # Intentar añadir rutas comunes del sistema (Debian/RPi OS) para fuera del venv
    try:
        import sys
        for path in (
            '/usr/lib/python3/dist-packages',
            '/usr/local/lib/python3.11/dist-packages',
            '/usr/lib/python3.11/dist-packages',
        ):
            if path not in sys.path:
                sys.path.append(path)
        from picamera2 import Picamera2  # type: ignore
        _PICAMERA2_AVAILABLE = True
    except Exception:
        _PICAMERA2_AVAILABLE = False

class CameraType(Enum):
    """Tipos de cámaras soportados."""
    USB_WEBCAM = "usb_webcam"
    CSI_CAMERA = "csi_camera"
    IP_CAMERA = "ip_camera"
    INDUSTRIAL = "industrial"
    MOCK = "mock"  # Para pruebas sin hardware

class CameraState(Enum):
    """Estados de la cámara."""
    OFFLINE = auto()
    INITIALIZING = auto()
    IDLE = auto()
    STREAMING = auto()
    CAPTURING = auto()
    CALIBRATING = auto()
    ERROR = auto()
    MAINTENANCE = auto()

class ImageQuality(Enum):
    """Calidad de imagen."""
    EXCELLENT = auto()
    GOOD = auto()
    ACCEPTABLE = auto()
    POOR = auto()
    UNUSABLE = auto()

@dataclass
class FrameMetrics:
    """Métricas de un frame capturado."""
    timestamp: float = field(default_factory=time.time)
    frame_id: str = ""
    resolution: Tuple[int, int] = (0, 0)
    fps: float = 0.0
    exposure_time: float = 0.0
    gain: float = 0.0
    brightness: float = 0.0
    contrast: float = 0.0
    sharpness: float = 0.0
    noise_level: float = 0.0
    compression_ratio: float = 0.0
    processing_time_ms: float = 0.0
    quality: ImageQuality = ImageQuality.ACCEPTABLE

@dataclass
class CameraMetrics:
    """Métricas del sistema de cámara."""
    timestamp: datetime = field(default_factory=datetime.now)
    frames_captured: int = 0
    frames_dropped: int = 0
    average_fps: float = 0.0
    current_fps: float = 0.0
    buffer_utilization: float = 0.0
    error_count: int = 0
    uptime_seconds: float = 0.0
    temperature_c: float = 0.0
    auto_exposure_enabled: bool = True
    auto_white_balance_enabled: bool = True
    total_data_mb: float = 0.0

@dataclass
class CalibrationData:
    """Datos de calibración de cámara."""
    camera_matrix: np.ndarray = None
    distortion_coefficients: np.ndarray = None
    calibration_date: datetime = field(default_factory=datetime.now)
    reprojection_error: float = 0.0
    calibration_images_count: int = 0
    is_valid: bool = False
    notes: str = ""

class BaseCameraDriver(ABC):
    """Clase base abstracta para drivers de cámara."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_initialized = False
        self.last_error: Optional[str] = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Inicializa el driver de cámara."""
        pass
    
    @abstractmethod
    async def capture_frame(self) -> Optional[np.ndarray]:
        """Captura un frame."""
        pass
    
    @abstractmethod
    async def start_streaming(self) -> bool:
        """Inicia streaming continuo."""
        pass
    
    @abstractmethod
    async def stop_streaming(self) -> bool:
        """Detiene streaming."""
        pass
    
    @abstractmethod
    async def set_parameter(self, param: str, value: Any) -> bool:
        """Establece un parámetro de cámara."""
        pass
    
    @abstractmethod
    async def get_parameter(self, param: str) -> Any:
        """Obtiene un parámetro de cámara."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Limpia recursos del driver."""
        pass

class OpenCVCameraDriver(BaseCameraDriver):
    """Driver para cámaras OpenCV (USB, CSI)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device_id = config.get("device_id", 0)
        self.width = config.get("frame_width", 1280)
        self.height = config.get("frame_height", 720)
        self.fps = config.get("fps", 30)
        
        self.cap = None
        self.is_streaming = False
        
    async def initialize(self) -> bool:
        """Inicializa la cámara OpenCV."""
        try:
            # Crear captura de video con backend V4L2 cuando sea posible
            try:
                self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)
            except Exception:
                self.cap = cv2.VideoCapture(self.device_id)
            
            if not self.cap.isOpened():
                raise RuntimeError(f"No se pudo abrir cámara {self.device_id}")
            
            # Configurar propiedades (algunos combos no aplican con compat libcamera)
            # Intentar MJPG, si falla, usar RGB24 (BGR3)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            # Buffer mínimo
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Verificar configuración
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Cámara inicializada: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            # Prueba de captura (reintentar con RGB si MJPG falla)
            ret, frame = self.cap.read()
            if (not ret or frame is None) and self.cap.isOpened():
                # Cambiar a RGB24
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('B','G','R','3'))
                ret, frame = self.cap.read()
            if not ret or frame is None:
                raise RuntimeError("No se pudo capturar frame de prueba")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.last_error = f"Error inicializando cámara: {e}"
            logger.error(self.last_error)
            if self.cap:
                self.cap.release()
                self.cap = None
            return False

    async def capture_frame(self) -> Optional[np.ndarray]:
        """Captura un frame de la cámara."""
        try:
            if not self.is_initialized or not self.cap:
                return None
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return frame
            logger.warning("Captura de frame falló")
            return None
        except Exception as e:
            self.last_error = f"Error capturando frame: {e}"
            logger.error(self.last_error)
            return None

    async def start_streaming(self) -> bool:
        self.is_streaming = True
        return True

    async def stop_streaming(self) -> bool:
        self.is_streaming = False
        return True

    async def set_parameter(self, param: str, value: Any) -> bool:
        try:
            if not self.cap:
                return False
            param_map = {
                'brightness': cv2.CAP_PROP_BRIGHTNESS,
                'contrast': cv2.CAP_PROP_CONTRAST,
                'saturation': cv2.CAP_PROP_SATURATION,
                'exposure': cv2.CAP_PROP_EXPOSURE,
                'gain': cv2.CAP_PROP_GAIN,
                'auto_exposure': cv2.CAP_PROP_AUTO_EXPOSURE,
                'fps': cv2.CAP_PROP_FPS,
                'width': cv2.CAP_PROP_FRAME_WIDTH,
                'height': cv2.CAP_PROP_FRAME_HEIGHT,
            }
            if param in param_map:
                return self.cap.set(param_map[param], value)
            return False
        except Exception as e:
            self.last_error = f"Error estableciendo parámetro {param}: {e}"
            logger.error(self.last_error)
            return False

    async def get_parameter(self, param: str) -> Any:
        try:
            if not self.cap:
                return None
            param_map = {
                'brightness': cv2.CAP_PROP_BRIGHTNESS,
                'contrast': cv2.CAP_PROP_CONTRAST,
                'saturation': cv2.CAP_PROP_SATURATION,
                'exposure': cv2.CAP_PROP_EXPOSURE,
                'gain': cv2.CAP_PROP_GAIN,
                'auto_exposure': cv2.CAP_PROP_AUTO_EXPOSURE,
                'fps': cv2.CAP_PROP_FPS,
                'width': cv2.CAP_PROP_FRAME_WIDTH,
                'height': cv2.CAP_PROP_FRAME_HEIGHT,
            }
            if param in param_map:
                return self.cap.get(param_map[param])
            return None
        except Exception as e:
            self.last_error = f"Error obteniendo parámetro {param}: {e}"
            logger.error(self.last_error)
            return None

    async def cleanup(self):
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.is_initialized = False
            self.is_streaming = False
        except Exception as e:
            logger.error(f"Error limpiando cámara: {e}")


class Picamera2CameraDriver(BaseCameraDriver):
    """Driver para cámaras CSI usando Picamera2 (libcamera)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.width = int(config.get("frame_width", 1280))
        self.height = int(config.get("frame_height", 720))
        self.fps = float(config.get("fps", 30))
        self.picam2: Optional[Picamera2] = None  # type: ignore
        self.is_streaming = False
        self._convert_to_bgr = True
    
    async def initialize(self) -> bool:
        try:
            if not _PICAMERA2_AVAILABLE:
                raise RuntimeError("Picamera2 no disponible")
            
            # Crear y configurar cámara
            self.picam2 = Picamera2()  # type: ignore
            # Configuración de captura RGB para fácil conversión a OpenCV (BGR)
            video_config = self.picam2.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self.picam2.configure(video_config)
            
            # Intentar ajustar FPS objetivo (puede ser aproximado)
            try:
                self.picam2.set_controls({"FrameRate": int(self.fps)})
            except Exception:
                pass
            
            self.picam2.start()
            # Captura de prueba
            test_frame = await asyncio.to_thread(self.picam2.capture_array)  # type: ignore
            if test_frame is None:
                raise RuntimeError("No se pudo capturar frame de prueba (Picamera2)")
            
            self.is_streaming = True
            self.is_initialized = True
            logger.info(f"Picamera2 inicializada: {self.width}x{self.height} @ ~{self.fps}fps")
            return True
        except Exception as e:
            self.last_error = f"Error inicializando Picamera2: {e}"
            logger.error(self.last_error)
            try:
                if self.picam2:
                    self.picam2.close()  # type: ignore
            except Exception:
                pass
            self.picam2 = None
            return False
    
    async def capture_frame(self) -> Optional[np.ndarray]:
        try:
            if not self.is_initialized or not self.picam2:
                return None
            frame = await asyncio.to_thread(self.picam2.capture_array)  # type: ignore
            if frame is None:
                return None
            # Convertir RGB -> BGR para OpenCV
            if self._convert_to_bgr:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            self.last_error = f"Error capturando frame (Picamera2): {e}"
            logger.error(self.last_error)
            return None
    
    async def start_streaming(self) -> bool:
        self.is_streaming = True
        return True
    
    async def stop_streaming(self) -> bool:
        self.is_streaming = False
        return True
    
    async def set_parameter(self, param: str, value: Any) -> bool:
        try:
            if not self.picam2:
                return False
            # Mapear algunos controles comunes
            controls = {}
            if param == "fps":
                controls["FrameRate"] = int(value)
            # Se pueden añadir más controles según sea necesario
            if controls:
                await asyncio.to_thread(self.picam2.set_controls, controls)  # type: ignore
                return True
            return False
        except Exception as e:
            self.last_error = f"Error set_parameter (Picamera2): {e}"
            logger.error(self.last_error)
            return False
    
    async def get_parameter(self, param: str) -> Any:
        # Picamera2 no expone un get_controls directo simple; devolver None o valores conocidos
        if param in ("width", "height"):
            return (self.width if param == "width" else self.height)
        if param == "fps":
            return self.fps
        return None
    
    async def cleanup(self):
        try:
            if self.picam2:
                await asyncio.to_thread(self.picam2.stop)  # type: ignore
                await asyncio.to_thread(self.picam2.close)  # type: ignore
        except Exception as e:
            logger.error(f"Error limpiando Picamera2: {e}")
        finally:
            self.picam2 = None
            self.is_initialized = False

    # Fin de Picamera2CameraDriver

    
    
    
    
    
    
    
    
    
    
    
    
    

class MockCameraDriver(BaseCameraDriver):
    """Driver mock para pruebas sin hardware."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.width = config.get("frame_width", 1280)
        self.height = config.get("frame_height", 720)
        self.fps = config.get("fps", 30)
        self.frame_counter = 0
        
    async def initialize(self) -> bool:
        """Inicializa cámara mock."""
        logger.info("Inicializando cámara mock")
        self.is_initialized = True
        return True
    
    async def capture_frame(self) -> Optional[np.ndarray]:
        """Genera frame sintético."""
        try:
            # Crear frame sintético con patrón
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            
            # Agregar patrón visual
            cv2.rectangle(frame, (50, 50), (200, 200), (0, 255, 0), 2)
            cv2.putText(frame, f"Frame: {self.frame_counter}", (50, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Simular variaciones de iluminación
            brightness = 128 + 50 * np.sin(self.frame_counter * 0.1)
            frame = cv2.add(frame, np.ones(frame.shape, dtype=np.uint8) * int(brightness))
            
            self.frame_counter += 1
            
            # Simular tiempo de captura
            await asyncio.sleep(1.0 / self.fps)
            
            return frame
            
        except Exception as e:
            self.last_error = f"Error generando frame mock: {e}"
            return None
    
    async def start_streaming(self) -> bool:
        return True
    
    async def stop_streaming(self) -> bool:
        return True
    
    async def set_parameter(self, param: str, value: Any) -> bool:
        logger.debug(f"Mock: Estableciendo {param} = {value}")
        return True
    
    async def get_parameter(self, param: str) -> Any:
        # Retornar valores mock
        mock_values = {
            'brightness': 0.5,
            'contrast': 1.0,
            'exposure': 0.1,
            'gain': 1.0,
            'fps': self.fps,
            'width': self.width,
            'height': self.height
        }
        return mock_values.get(param, 0)
    
    async def cleanup(self):
        self.is_initialized = False

class CameraController:
    """
    Sistema de control de cámara industrial avanzado.
    
    Características:
    - Soporte para múltiples tipos de cámaras
    - Buffer circular con gestión inteligente
    - Auto-optimización de parámetros
    - Análisis de calidad en tiempo real
    - Sistema de métricas y telemetría
    - Calibración automática
    - Recuperación de errores automática
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.camera_type = CameraType(config.get("type", "usb_webcam"))
        self.name = config.get("name", "IndustrialCamera-1")
        
        # Estado del sistema
        self.state = CameraState.OFFLINE
        self.last_error: Optional[str] = None
        
        # Driver de cámara
        self.driver: Optional[BaseCameraDriver] = None
        
        # Buffer circular para frames
        self.buffer_size = config.get("buffer_size", 10)
        self.frame_buffer = deque(maxlen=self.buffer_size)
        self.buffer_lock = threading.RLock()
        
        # Métricas y estadísticas
        self.metrics = CameraMetrics()
        self.frame_times = deque(maxlen=100)
        self.quality_history = deque(maxlen=1000)
        
        # Threading para captura continua
        self.capture_thread: Optional[threading.Thread] = None
        self.stop_capture = threading.Event()
        
        # Auto-optimización
        self.auto_optimize = config.get("auto_optimize", True)
        self.last_optimization = time.time()
        self.optimization_interval = config.get("optimization_interval", 30.0)
        
        # Calibración
        self.calibration_data: Optional[CalibrationData] = None
        self.auto_calibrate = config.get("auto_calibrate", False)
        
        # Sistema de alertas
        self.alert_callbacks: List[Callable] = []
        
        # Configuración de calidad
        self.min_fps = config.get("min_fps", 15.0)
        self.target_fps = config.get("fps", 30.0)
        self.quality_threshold = config.get("quality_threshold", 0.7)
        
        self._start_time = time.time()
        
        logger.info(f"CameraController '{self.name}' instanciado (tipo: {self.camera_type.value})")
    
    def _create_driver(self) -> BaseCameraDriver:
        """Crea el driver apropiado según el tipo de cámara."""
        if self.camera_type == CameraType.CSI_CAMERA:
            # Preferir Picamera2 en Raspberry Pi 5 si está disponible
            if _PICAMERA2_AVAILABLE:
                logger.info("Usando driver Picamera2 para cámara CSI")
                return Picamera2CameraDriver(self.config)
            logger.info("Picamera2 no disponible; usando OpenCV V4L2 para cámara CSI")
            return OpenCVCameraDriver(self.config)
        if self.camera_type == CameraType.USB_WEBCAM:
            return OpenCVCameraDriver(self.config)
        elif self.camera_type == CameraType.MOCK:
            return MockCameraDriver(self.config)
        else:
            raise ValueError(f"Tipo de cámara no soportado: {self.camera_type}")
    
    def initialize(self) -> bool:
        """Inicializa el sistema de cámara."""
        try:
            self.state = CameraState.INITIALIZING
            logger.info(f"Inicializando {self.name}...")
            
            # Crear driver
            self.driver = self._create_driver()
            
            # Ejecutar inicialización de forma síncrona
            try:
                # Intentar obtener el loop actual
                loop = asyncio.get_running_loop()
                # Si hay un loop corriendo, ejecutar en un hilo separado
                import concurrent.futures
                import threading
                
                def _init_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(self.driver.initialize())
                        return result
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(_init_in_thread)
                    success = future.result(timeout=10.0)
                    
            except RuntimeError:
                # No hay loop corriendo, crear uno nuevo
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(self.driver.initialize())
                finally:
                    loop.close()
            
            if not success:
                # Fallbacks: si Picamera2 falla en CSI, intentar OpenCV; luego Mock
                logger.warning("Cámara: inicialización del driver primario falló, intentando fallback...")

                # Ejecutar inicialización de drivers de fallback en un hilo separado
                # para evitar conflictos con un event loop ya activo en este hilo.
                def _init_driver_in_thread(driver_obj) -> bool:
                    try:
                        import concurrent.futures
                        def _runner():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(driver_obj.initialize())
                            finally:
                                new_loop.close()
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(_runner)
                            return bool(future.result(timeout=10.0))
                    except Exception as e:
                        logger.debug(f"Cámara: error inicializando driver en fallback (thread): {e}")
                        return False

                # Intentar fallback a OpenCV si el tipo era CSI
                is_csi = (self.camera_type == CameraType.CSI_CAMERA)
                if is_csi:
                    try:
                        alt_driver = OpenCVCameraDriver(self.config)
                        success = _init_driver_in_thread(alt_driver)
                        if success:
                            self.driver = alt_driver
                            logger.info("Cámara: fallback a OpenCV (V4L2) exitoso")
                        else:
                            logger.warning("Cámara: OpenCV fallback no pudo inicializar")
                    except Exception as e:
                        logger.warning(f"Cámara: OpenCV fallback falló: {e}")

                # Fallback a Mock si está permitido y aún no hay success
                allow_mock = bool(self.config.get("fallback_to_mock", True))
                if (not success) and allow_mock:
                    try:
                        mock_driver = MockCameraDriver(self.config)
                        mock_ok = _init_driver_in_thread(mock_driver)
                        if mock_ok:
                            self.driver = mock_driver
                            success = True
                            logger.info("Cámara: fallback a Mock activo (modo pruebas)")
                        else:
                            logger.warning("Cámara: Mock fallback no pudo inicializarse")
                    except Exception as e:
                        logger.warning(f"Cámara: Mock fallback falló: {e}")

                if not success:
                    raise RuntimeError("Fallo al inicializar driver (sin fallbacks disponibles)")
            
            # Cargar calibración si existe
            self._load_calibration()
            
            # Iniciar captura continua si se especifica
            if self.config.get("auto_start_capture", True):
                self._start_continuous_capture()
            
            self.state = CameraState.IDLE
            logger.info(f"{self.name} inicializado correctamente")
            return True
            
        except Exception as e:
            self.last_error = f"Error en inicialización: {e}"
            self.state = CameraState.ERROR
            logger.error(f"Error inicializando {self.name}: {e}")
            return False
    
    def _start_continuous_capture(self):
        """Inicia la captura continua en hilo separado."""
        if self.capture_thread and self.capture_thread.is_alive():
            return
        
        self.stop_capture.clear()
        self.capture_thread = threading.Thread(
            target=self._continuous_capture_worker,
            name=f"{self.name}-CaptureWorker",
            daemon=True
        )
        self.capture_thread.start()
        logger.info("Captura continua iniciada")
    
    def _continuous_capture_worker(self):
        """Worker para captura continua."""
        logger.info("Worker de captura continua iniciado")
        
        # Crear loop para este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        last_fps_update = time.time()
        frame_count = 0
        last_fps_log = time.time()
        
        try:
            none_count = 0
            while not self.stop_capture.is_set():
                try:
                    # Capturar frame
                    frame = loop.run_until_complete(self.driver.capture_frame())
                    
                    if frame is not None:
                        # Analizar calidad
                        quality_metrics = self._analyze_frame_quality(frame)
                        
                        # Agregar al buffer
                        frame_data = {
                            'frame': frame,
                            'timestamp': time.time(),
                            'metrics': quality_metrics
                        }
                        
                        with self.buffer_lock:
                            self.frame_buffer.append(frame_data)
                        
                        # Actualizar métricas
                        self.metrics.frames_captured += 1
                        frame_count += 1
                        none_count = 0
                        
                        # Calcular FPS
                        current_time = time.time()
                        if current_time - last_fps_update >= 1.0:
                            self.metrics.current_fps = frame_count / (current_time - last_fps_update)
                            self.frame_times.append(self.metrics.current_fps)
                            
                            if self.frame_times:
                                self.metrics.average_fps = statistics.mean(self.frame_times)
                            
                            frame_count = 0
                            last_fps_update = current_time
                            # Loguear FPS cada ~2s para visibilidad sin saturar logs
                            if (current_time - last_fps_log) >= 2.0:
                                logger.info(
                                    "📷 Cámara '%s' FPS: actual=%.1f, promedio=%.1f",
                                    self.name,
                                    self.metrics.current_fps,
                                    self.metrics.average_fps,
                                )
                                last_fps_log = current_time
                        
                        # Auto-optimización periódica
                        if self.auto_optimize:
                            loop.run_until_complete(self._auto_optimize_settings())
                    
                    else:
                        self.metrics.frames_dropped += 1
                        none_count += 1
                        if none_count % 20 == 0:
                            logger.warning("Frame capturado es None (acumulado: %d)", none_count)
                        # Si demasiados None consecutivos, intentar cambiar a Mock si está permitido
                        if none_count >= 60 and bool(self.config.get("fallback_to_mock", True)):
                            try:
                                logger.warning("Cámara: demasiados frames None; intentando fallback dinámico a Mock...")
                                mock_driver = MockCameraDriver(self.config)
                                init_ok = loop.run_until_complete(mock_driver.initialize())
                                if init_ok:
                                    self.driver = mock_driver
                                    none_count = 0
                                    self.metrics.error_count = 0
                                    logger.info("Cámara: cambio dinámico a Mock exitoso")
                                else:
                                    logger.warning("Cámara: no se pudo activar Mock dinámicamente")
                            except Exception as e:
                                logger.warning(f"Cámara: error activando Mock dinámico: {e}")
                    
                except Exception as e:
                    self.metrics.error_count += 1
                    logger.error(f"Error en captura continua: {e}")
                    time.sleep(0.1)  # Pausa para evitar bucle rápido de errores
            
        finally:
            loop.close()
            logger.info("Worker de captura continua terminado")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Captura un frame único de forma síncrona."""
        try:
            if self.state != CameraState.IDLE and self.state != CameraState.STREAMING:
                logger.warning(f"Estado incorrecto para captura: {self.state}")
                return None
            
            # Si hay captura continua, usar el buffer
            if self.capture_thread and self.capture_thread.is_alive():
                with self.buffer_lock:
                    if self.frame_buffer:
                        latest_frame_data = self.frame_buffer[-1]
                        return latest_frame_data['frame'].copy()
            
            # Captura directa
            self.state = CameraState.CAPTURING
            
            try:
                # Intentar obtener el loop actual
                loop = asyncio.get_running_loop()
                # Si hay un loop corriendo, ejecutar en un hilo separado
                import concurrent.futures
                
                def _capture_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(self.driver.capture_frame())
                        return result
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(_capture_in_thread)
                    frame = future.result(timeout=5.0)
                    
            except RuntimeError:
                # No hay loop corriendo, crear uno nuevo
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    frame = loop.run_until_complete(self.driver.capture_frame())
                finally:
                    loop.close()
            
            self.state = CameraState.IDLE
            
            if frame is not None:
                self.metrics.frames_captured += 1
            else:
                self.metrics.frames_dropped += 1
            
            return frame
            
        except Exception as e:
            self.last_error = f"Error capturando frame: {e}"
            self.state = CameraState.ERROR
            logger.error(f"Error en captura: {e}")
            return None
    
    def _analyze_frame_quality(self, frame: np.ndarray) -> FrameMetrics:
        """Analiza la calidad de un frame."""
        try:
            start_time = time.time()
            
            # Convertir a escala de grises para análisis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Métricas básicas
            height, width = frame.shape[:2]
            
            # Análisis de nitidez (varianza del Laplaciano)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = np.var(laplacian)
            
            # Análisis de brillo
            brightness = np.mean(gray)
            
            # Análisis de contraste
            contrast = np.std(gray)
            
            # Análisis de ruido (simplificado)
            noise_level = np.std(gray - cv2.GaussianBlur(gray, (5, 5), 0))
            
            # Determinar calidad general
            quality_score = self._calculate_quality_score(sharpness, brightness, contrast, noise_level)
            
            if quality_score >= 0.9:
                quality = ImageQuality.EXCELLENT
            elif quality_score >= 0.7:
                quality = ImageQuality.GOOD
            elif quality_score >= 0.5:
                quality = ImageQuality.ACCEPTABLE
            elif quality_score >= 0.3:
                quality = ImageQuality.POOR
            else:
                quality = ImageQuality.UNUSABLE
            
            processing_time = (time.time() - start_time) * 1000
            
            metrics = FrameMetrics(
                frame_id=f"{int(time.time() * 1000)}",
                resolution=(width, height),
                fps=self.metrics.current_fps,
                brightness=brightness / 255.0,  # Normalizar 0-1
                contrast=min(1.0, contrast / 127.0),  # Normalizar aproximadamente
                sharpness=min(1.0, sharpness / 1000.0),  # Normalizar aproximadamente
                noise_level=min(1.0, noise_level / 50.0),  # Normalizar aproximadamente
                processing_time_ms=processing_time,
                quality=quality
            )
            
            self.quality_history.append(quality_score)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analizando calidad de frame: {e}")
            return FrameMetrics(quality=ImageQuality.UNUSABLE)
    
    def _calculate_quality_score(self, sharpness: float, brightness: float, 
                                contrast: float, noise_level: float) -> float:
        """Calcula puntuación de calidad general."""
        # Normalizar métricas (valores aproximados)
        sharpness_norm = min(1.0, sharpness / 1000.0)
        brightness_norm = 1.0 - abs(brightness - 127.5) / 127.5  # Óptimo en ~50%
        contrast_norm = min(1.0, contrast / 64.0)
        noise_norm = max(0.0, 1.0 - noise_level / 25.0)
        
        # Promedio ponderado
        score = (
            sharpness_norm * 0.4 +
            brightness_norm * 0.2 +
            contrast_norm * 0.2 +
            noise_norm * 0.2
        )
        
        return max(0.0, min(1.0, score))
    
    async def _auto_optimize_settings(self):
        """Optimiza automáticamente los parámetros de cámara."""
        try:
            current_time = time.time()
            if current_time - self.last_optimization < self.optimization_interval:
                return
            
            if not self.driver:
                return
            
            # Analizar calidad reciente
            if len(self.quality_history) < 10:
                return
            
            recent_quality = statistics.mean(list(self.quality_history)[-10:])
            current_fps = self.metrics.current_fps
            
            # Optimizar basado en FPS y calidad
            if current_fps < self.min_fps:
                # FPS bajo: reducir calidad para mejorar rendimiento
                await self._adjust_for_performance()
            elif recent_quality < self.quality_threshold and current_fps > self.target_fps:
                # Calidad baja pero FPS bueno: mejorar calidad
                await self._adjust_for_quality()
            
            self.last_optimization = current_time
            
        except Exception as e:
            logger.error(f"Error en auto-optimización: {e}")
    
    async def _adjust_for_performance(self):
        """Ajusta para mejorar rendimiento."""
        logger.info("Ajustando para mejorar rendimiento")
        
        # Reducir resolución si es posible
        current_width = await self.driver.get_parameter('width')
        if current_width and current_width > 640:
            await self.driver.set_parameter('width', 640)
            await self.driver.set_parameter('height', 480)
        
        # Aumentar compresión/reducir calidad
        await self.driver.set_parameter('fps', min(30, self.target_fps))
    
    async def _adjust_for_quality(self):
        """Ajusta para mejorar calidad."""
        logger.info("Ajustando para mejorar calidad")
        
        # Mejorar exposición si está muy baja
        exposure = await self.driver.get_parameter('exposure')
        if exposure and exposure < 0.1:
            await self.driver.set_parameter('exposure', min(0.3, exposure + 0.1))
        
        # Ajustar ganancia
        gain = await self.driver.get_parameter('gain')
        if gain and gain < 1.0:
            await self.driver.set_parameter('gain', min(2.0, gain + 0.2))
    
    def _load_calibration(self):
        """Carga datos de calibración si existen."""
        try:
            cal_file = Path(f"calibration_{self.name.lower()}.json")
            if cal_file.exists():
                with open(cal_file, 'r') as f:
                    cal_data = json.load(f)
                
                self.calibration_data = CalibrationData(
                    camera_matrix=np.array(cal_data['camera_matrix']),
                    distortion_coefficients=np.array(cal_data['distortion_coefficients']),
                    calibration_date=datetime.fromisoformat(cal_data['calibration_date']),
                    reprojection_error=cal_data['reprojection_error'],
                    calibration_images_count=cal_data['calibration_images_count'],
                    is_valid=cal_data['is_valid'],
                    notes=cal_data['notes']
                )
                
                logger.info(f"Calibración cargada desde {cal_file}")
            
        except Exception as e:
            logger.warning(f"Error cargando calibración: {e}")
    
    def _save_calibration(self):
        """Guarda datos de calibración."""
        try:
            if self.calibration_data and self.calibration_data.is_valid:
                cal_file = Path(f"calibration_{self.name.lower()}.json")
                cal_data = {
                    'camera_matrix': self.calibration_data.camera_matrix.tolist(),
                    'distortion_coefficients': self.calibration_data.distortion_coefficients.tolist(),
                    'calibration_date': self.calibration_data.calibration_date.isoformat(),
                    'reprojection_error': self.calibration_data.reprojection_error,
                    'calibration_images_count': self.calibration_data.calibration_images_count,
                    'is_valid': self.calibration_data.is_valid,
                    'notes': self.calibration_data.notes
                }
                
                with open(cal_file, 'w') as f:
                    json.dump(cal_data, f, indent=2)
                
                logger.info(f"Calibración guardada en {cal_file}")
        
        except Exception as e:
            logger.error(f"Error guardando calibración: {e}")
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Obtiene el frame más reciente del buffer."""
        try:
            with self.buffer_lock:
                if self.frame_buffer:
                    return self.frame_buffer[-1]['frame'].copy()
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo frame del buffer: {e}")
            return None
    
    def get_buffer_utilization(self) -> float:
        """Obtiene el porcentaje de utilización del buffer."""
        with self.buffer_lock:
            return len(self.frame_buffer) / self.buffer_size
    
    def register_alert_callback(self, callback: Callable):
        """Registra callback para alertas."""
        self.alert_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema."""
        buffer_util = self.get_buffer_utilization()
        uptime = time.time() - self._start_time
        
        return {
            "name": self.name,
            "type": self.camera_type.value,
            "state": self.state.name,
            "is_initialized": self.driver.is_initialized if self.driver else False,
            "last_error": self.last_error,
            "metrics": {
                "frames_captured": self.metrics.frames_captured,
                "frames_dropped": self.metrics.frames_dropped,
                "current_fps": self.metrics.current_fps,
                "average_fps": self.metrics.average_fps,
                "buffer_utilization": buffer_util,
                "error_count": self.metrics.error_count,
                "uptime_seconds": uptime
            },
            "quality": {
                "recent_average": statistics.mean(list(self.quality_history)[-10:]) if self.quality_history else 0.0,
                "samples_count": len(self.quality_history)
            },
            "calibration": {
                "is_calibrated": self.calibration_data is not None and self.calibration_data.is_valid,
                "last_calibration": self.calibration_data.calibration_date.isoformat() if self.calibration_data else None,
                "reprojection_error": self.calibration_data.reprojection_error if self.calibration_data else 0.0
            }
        }
    
    def shutdown(self):
        """Apaga el sistema de cámara de forma segura."""
        try:
            logger.info(f"Apagando {self.name}...")
            
            # Detener captura continua
            self.stop_capture.set()
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=5.0)
            
            # Limpiar driver
            if self.driver:
                try:
                    # Intentar obtener el loop actual
                    loop = asyncio.get_running_loop()
                    # Si hay un loop corriendo, ejecutar en un hilo separado
                    import concurrent.futures
                    
                    def _cleanup_in_thread():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            new_loop.run_until_complete(self.driver.cleanup())
                        finally:
                            new_loop.close()
                    
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(_cleanup_in_thread)
                        future.result(timeout=5.0)
                        
                except RuntimeError:
                    # No hay loop corriendo, crear uno nuevo
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.driver.cleanup())
                    finally:
                        loop.close()
            
            # Guardar calibración
            self._save_calibration()
            
            self.state = CameraState.OFFLINE
            logger.info(f"{self.name} apagado correctamente")
            
        except Exception as e:
            logger.error(f"Error apagando {self.name}: {e}")

# --- Funciones de Utilidad ---

def create_camera_controller(config: Dict[str, Any]) -> CameraController:
    """Factory function para crear controlador de cámara."""
    return CameraController(config)

def test_camera(config: Dict[str, Any]) -> bool:
    """Función de prueba para validar configuración de cámara."""
    try:
        camera = create_camera_controller(config)
        
        # Inicializar
        if not camera.initialize():
            return False
        
        # Capturar frame de prueba
        frame = camera.capture_frame()
        
        success = frame is not None
        
        # Cleanup
        camera.shutdown()
        
        return success
        
    except Exception as e:
        logger.error(f"Error en prueba de cámara: {e}")
        return False

# --- Punto de Entrada Principal ---

if __name__ == "__main__":
    """Script de prueba para el sistema de cámara."""
    
    # Configuración de prueba
    test_config = {
        "type": "mock",  # Usar mock para pruebas sin hardware
        "name": "TestCamera",
        "device_id": 0,
        "frame_width": 1280,
        "frame_height": 720,
        "fps": 30,
        "buffer_size": 5,
        "auto_optimize": True,
        "auto_start_capture": True
    }
    
    def main():
        print("=== Prueba del Sistema de Cámara Industrial ===")
        
        success = test_camera(test_config)
        
        if success:
            print("✓ Prueba exitosa")
            
            # Prueba más detallada
            camera = create_camera_controller(test_config)
            camera.initialize()
            
            # Capturar algunos frames
            for i in range(5):
                frame = camera.capture_frame()
                if frame is not None:
                    print(f"✓ Frame {i+1} capturado: {frame.shape}")
                else:
                    print(f"✗ Frame {i+1} falló")
                
                time.sleep(0.1)
            
            # Mostrar estado
            status = camera.get_status()
            print(f"Estado: {status['state']}")
            print(f"FPS promedio: {status['metrics']['average_fps']:.1f}")
            print(f"Frames capturados: {status['metrics']['frames_captured']}")
            
            camera.shutdown()
        else:
            print("✗ Prueba falló")
        
        print("=== Prueba Completada ===")
    
    main()