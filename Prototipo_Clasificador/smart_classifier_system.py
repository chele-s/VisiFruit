#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Sistema Inteligente de Clasificación con IA - VisiFruit Prototipo
====================================================================

Sistema completo de clasificación automática de frutas que integra:
- Detección por IA (YOLOv8 optimizado para Raspberry Pi 5)
- Control de etiquetadora con DRV8825
- Clasificación con servomotores MG995
- Banda transportadora
- Sincronización temporal precisa

Flujo de operación:
1. Cámara captura imagen de fruta en banda
2. IA detecta y clasifica (manzana/pera/limón)
3. DRV8825 activa etiquetadora para aplicar etiqueta
4. Tras X tiempo/distancia, MG995 activa compuerta para clasificar

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 1.0 - Prototipo Edition
"""

import asyncio
import logging
import time
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import signal
import threading
import http.server
import socketserver
import sys
from datetime import datetime
try:
    import numpy as np  # type: ignore
except Exception:  # numpy no es estrictamente requerido para la vista previa
    np = None  # type: ignore

# Visualización opcional
try:
    import cv2  # type: ignore
    _CV2_AVAILABLE = True
except Exception:
    _CV2_AVAILABLE = False

# Picamera2 DRM/Qt preview availability
try:
    from picamera2 import Preview as _P2Preview  # type: ignore
    _P2_PREVIEW_AVAILABLE = True
except Exception:
    _P2_PREVIEW_AVAILABLE = False

# Importaciones propias
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from Prototipo_Clasificador.mg995_servo_controller import MG995ServoController, FruitCategory
except ImportError:
    try:
        from mg995_servo_controller import MG995ServoController, FruitCategory
    except ImportError as e:
        print(f"⚠️ MG995ServoController no disponible: {e}")
        MG995ServoController = None
        # Definir FruitCategory fallback
        class FruitCategory(Enum):
            APPLE = "apple"
            PEAR = "pear"
            LEMON = "lemon"
            UNKNOWN = "unknown"

try:
    from Control_Etiquetado.labeler_actuator import LabelerActuator
except ImportError as e:
    print(f"⚠️ LabelerActuator no disponible: {e}")
    LabelerActuator = None

try:
    from Control_Etiquetado.sensor_interface import SensorInterface
except ImportError as e:
    print(f"⚠️ SensorInterface no disponible: {e}")
    SensorInterface = None

try:
    from utils.camera_controller import CameraController
except ImportError as e:
    print(f"⚠️ CameraController no disponible: {e}")
    CameraController = None

# IA de detección - YOLOv8 optimizado para Raspberry Pi 5
try:
    from IA_Etiquetado.YOLOv8_detector import EnterpriseFruitDetector
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Detector YOLOv8 de IA no disponible: {e}")
    EnterpriseFruitDetector = None
    AI_AVAILABLE = False

# GPIO wrapper para banda
try:
    from utils.gpio_wrapper import GPIO, is_simulation_mode
except ImportError as e:
    print(f"⚠️ GPIO wrapper no disponible: {e}")
    GPIO = None
    def is_simulation_mode():
        return True

logger = logging.getLogger(__name__)
# Asegurar salida de logs en consola si el entorno no configuró logging
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%H:%M:%S'
    )

class SystemState(Enum):
    """Estados del sistema de clasificación."""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"

@dataclass
class DetectionEvent:
    """Evento de detección de fruta."""
    timestamp: float
    fruit_class: str
    confidence: float
    category: FruitCategory
    bbox: tuple = field(default_factory=tuple)
    processed: bool = False
    labeled: bool = False
    classified: bool = False
    
class SimpleBeltController:
    """Controlador simple de banda transportadora."""
    
    def __init__(self, relay1_pin=22, relay2_pin=23, enable_pin=27):
        self.relay1_pin = relay1_pin
        self.relay2_pin = relay2_pin
        self.enable_pin = enable_pin
        self.initialized = False
        self.running = False
        
    async def initialize(self) -> bool:
        """Inicializa el controlador."""
        try:
            if is_simulation_mode():
                logger.info("🎭 Banda en modo simulación")
                self.initialized = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay1_pin, GPIO.OUT)
            GPIO.setup(self.relay2_pin, GPIO.OUT)
            if self.enable_pin:
                GPIO.setup(self.enable_pin, GPIO.OUT)
                GPIO.output(self.enable_pin, GPIO.HIGH)
            
            GPIO.output(self.relay1_pin, GPIO.LOW)
            GPIO.output(self.relay2_pin, GPIO.LOW)
            
            self.initialized = True
            logger.info("✅ Banda transportadora inicializada")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando banda: {e}")
            return False
    
    async def start(self) -> bool:
        """Inicia la banda."""
        try:
            if is_simulation_mode():
                self.running = True
                logger.info("🎭 Banda iniciada (simulación)")
                return True
            
            if self.enable_pin:
                GPIO.output(self.enable_pin, GPIO.HIGH)
            GPIO.output(self.relay2_pin, GPIO.LOW)
            GPIO.output(self.relay1_pin, GPIO.HIGH)
            self.running = True
            logger.info("✅ Banda transportadora iniciada")
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando banda: {e}")
            return False
    
    async def stop(self) -> bool:
        """Detiene la banda."""
        try:
            if is_simulation_mode():
                self.running = False
                logger.info("🎭 Banda detenida (simulación)")
                return True
            
            GPIO.output(self.relay1_pin, GPIO.LOW)
            GPIO.output(self.relay2_pin, GPIO.LOW)
            self.running = False
            logger.info("✅ Banda transportadora detenida")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo banda: {e}")
            return False
    
    async def cleanup(self):
        """Limpia recursos."""
        await self.stop()
        if GPIO and not is_simulation_mode():
            GPIO.cleanup([self.relay1_pin, self.relay2_pin, self.enable_pin])

class SmartFruitClassifier:
    """
    Sistema inteligente de clasificación de frutas con IA.
    
    Integra todos los componentes del prototipo:
    - Cámara y visión por computadora
    - Detección de IA
    - Etiquetadora DRV8825
    - Servomotores MG995
    - Banda transportadora
    - Sincronización temporal
    """
    
    def __init__(self, config_path: str = "Prototipo_Clasificador/Config_Prototipo.json"):
        # Configuración
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Estado del sistema
        self.state = SystemState.OFFLINE
        self.running = False
        self.paused = False
        
        # Componentes hardware
        self.camera: Optional[CameraController] = None
        self.ai_detector: Optional[EnterpriseFruitDetector] = None
        self.labeler: Optional[LabelerActuator] = None
        self.servo_controller: Optional[MG995ServoController] = None
        self.belt: Optional[Any] = None  # Puede ser SimpleBeltController o ConveyorBeltController
        self.sensor: Optional[SensorInterface] = None
        
        # Cola de eventos de detección
        self.detection_queue: deque = deque(maxlen=100)
        self.pending_classifications: List[DetectionEvent] = []
        # Deduplicación de detecciones recientes (evitar activar por la misma fruta en frames consecutivos)
        self._recent_detections: deque = deque(maxlen=200)
        self._dedup_settings: Dict[str, Any] = self.config.get("dedup_settings", {
            "enabled": True,
            "iou_threshold": 0.5,
            "time_window_s": 0.5,
            "center_distance_px": 60,
            "max_events_per_frame": 3,
        })
        
        # Parámetros de temporización
        belt_speed = self.config.get("timing", {}).get("belt_speed_mps", 0.2)
        sensor_to_camera_m = self.config.get("timing", {}).get("sensor_to_camera_distance_m", 0.1)
        camera_to_classifier_m = self.config.get("timing", {}).get("camera_to_classifier_distance_m", 0.5)
        
        self.labeling_delay_s = sensor_to_camera_m / belt_speed
        self.classification_delay_s = camera_to_classifier_m / belt_speed
        
        # Debug y visualización
        self.debug: Dict[str, Any] = self.config.get("debug", {})
        self.show_preview: bool = bool(self.debug.get("show_preview", False)) and _CV2_AVAILABLE
        self.save_annotated_frames: bool = bool(self.debug.get("save_annotated_frames", False) or self.config.get("advanced", {}).get("save_detections", False))
        self.use_drm_preview: bool = bool(self.debug.get("drm_preview", False)) and _P2_PREVIEW_AVAILABLE
        self.preview_window_name: str = str(self.debug.get("preview_window", "VisiFruit - Preview"))
        self.no_detection_log_interval_s: float = float(self.debug.get("no_detection_log_interval_s", 5.0))
        self._last_no_detection_log: float = 0.0
        self._detections_dir: Path = Path(self.config.get("advanced", {}).get("detections_path", "logs/detections/"))
        if self.save_annotated_frames:
            try:
                self._detections_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        self._drm_preview_started: bool = False
        # Vista previa web MJPEG
        self.http_preview_enabled: bool = bool(self.debug.get("http_preview", True))
        self.http_preview_port: int = int(self.debug.get("http_preview_port", 8081))
        self._http_server: Optional[http.server.HTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._latest_jpeg: Optional[bytes] = None
        # Anotación de preview con bounding boxes (desactivada por defecto para evitar coste)
        self.annotate_preview: bool = bool(self.debug.get("annotate_preview", False))
        self.annotate_preview_only_on_detection: bool = bool(self.debug.get("annotate_preview_only_on_detection", True))

        # Estadísticas
        self.stats = {
            "detections_total": 0,
            "detections_by_class": {"apple": 0, "pear": 0, "lemon": 0, "unknown": 0},
            "labeled_total": 0,
            "classified_total": 0,
            "classified_by_servo": {"apple": 0, "pear": 0, "lemon": 0},
            "errors": 0,
            "start_time": time.time(),
            "uptime_s": 0,
            "last_detection_ts": 0.0
        }
        
        # Control en caliente vía archivo runtime
        self._control_file_path: Path = Path("runtime/runtime_control.json")
        try:
            self._control_file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        
        logger.info("🧠 SmartFruitClassifier creado")
        logger.info(f"   ⏱️ Delay etiquetado: {self.labeling_delay_s:.2f}s")
        logger.info(f"   ⏱️ Delay clasificación: {self.classification_delay_s:.2f}s")
        if self.show_preview and _CV2_AVAILABLE:
            logger.info("🖼️ Vista previa activada (cv2.imshow)")
        elif self.debug.get("show_preview", False) and not _CV2_AVAILABLE:
            logger.warning("⚠️ OpenCV GUI no disponible; vista previa deshabilitada")
        if self.save_annotated_frames:
            logger.info(f"🖼️ Guardado de frames anotados en: {self._detections_dir}")
        if self.use_drm_preview and not _CV2_AVAILABLE:
            logger.info("🖼️ Vista previa DRM planificada (Picamera2)")
        if self.http_preview_enabled:
            logger.info(f"🌐 Vista previa web MJPEG planificada en puerto {self.http_preview_port}")
        if self.annotate_preview:
            logger.info("🧩 Anotación de preview con bounding boxes activada (HTTP/DRM)")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo JSON."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ Configuración cargada desde {self.config_path}")
                return config
        except Exception as e:
            logger.warning(f"⚠️ Error cargando configuración: {e}")
        
        # Configuración por defecto
        return {
            "camera_settings": {
                "camera_id": 0,
                "resolution": [640, 480],
                "fps": 30
            },
            "ai_settings": {
                "model_path": "IA_Etiquetado/Dataset_Frutas/best.pt",
                "confidence_threshold": 0.6,
                "enable_tracking": True
            },
            "labeler_settings": {
                "enabled": True,
                "type": "stepper",
                "step_pin_bcm": 19,
                "dir_pin_bcm": 26,
                "enable_pin_bcm": 21,
                "enable_active_low": True,
                "base_speed_sps": 1500,
                "activation_duration_seconds": 0.6
            },
            "servo_settings": {
                "apple": {"pin_bcm": 17, "name": "Servo_Manzanas", "activation_angle": 90},
                "pear": {"pin_bcm": 27, "name": "Servo_Peras", "activation_angle": 90},
                "lemon": {"pin_bcm": 22, "name": "Servo_Limones", "activation_angle": 90}
            },
            "belt_settings": {
                "relay1_pin": 22,
                "relay2_pin": 23,
                "enable_pin": 27
            },
            "timing": {
                "belt_speed_mps": 0.2,
                "sensor_to_camera_distance_m": 0.1,
                "camera_to_classifier_distance_m": 0.5,
                "min_detection_interval_s": 0.5
            }
        }
    
    async def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema."""
        try:
            self.state = SystemState.INITIALIZING
            logger.info("=== 🚀 Inicializando Sistema Inteligente de Clasificación ===")
            
            # 1. Cámara
            await self._initialize_camera()
            
            # 2. IA
            await self._initialize_ai()
            
            # 3. Etiquetadora DRV8825
            await self._initialize_labeler()
            
            # 4. Servomotores MG995
            await self._initialize_servos()
            
            # 5. Banda transportadora
            await self._initialize_belt()
            
            # 6. Sensor (opcional)
            await self._initialize_sensor()
            
            self.state = SystemState.IDLE
            logger.info("=== ✅ Sistema inicializado correctamente ===")
            return True
            
        except Exception as e:
            self.state = SystemState.ERROR
            logger.error(f"❌ Error crítico durante inicialización: {e}", exc_info=True)
            return False
    
    async def _initialize_camera(self):
        """Inicializa la cámara."""
        logger.info("📷 Inicializando cámara...")
        try:
            if not CameraController:
                logger.warning("⚠️ Módulo CameraController no disponible.")
                self.camera = None
                return

            camera_config = self.config.get("camera_settings", {})
            self.camera = CameraController(camera_config)
            
            # ✨ NUEVO: Si la inicialización falla, desactiva la cámara por completo.
            if not self.camera.initialize():
                logger.error("❌ Fallo al inicializar la cámara. El sistema continuará sin ella.")
                self.camera = None # Desactivar la cámara
            else:
                logger.info("✅ Cámara inicializada correctamente.")
                # Intentar iniciar preview DRM si está habilitada y disponible
                try:
                    if self.use_drm_preview and hasattr(self.camera, 'driver') and getattr(self.camera.driver, 'picam2', None) is not None:
                        self._start_drm_preview()
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo iniciar vista previa DRM: {e}")
                # Iniciar vista previa web MJPEG
                try:
                    if self.http_preview_enabled:
                        self._start_http_preview_server()
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo iniciar vista previa web: {e}")

        except Exception as e:
            logger.error(f"❌ Error crítico inicializando cámara: {e}")
            self.camera = None
    
    async def _initialize_ai(self):
        """Inicializa el detector de IA."""
        logger.info("🤖 Inicializando detector de IA...")
        try:
            if AI_AVAILABLE and EnterpriseFruitDetector:
                # Configurar IA - forzar YOLOv8
                ai_config = self.config.copy()
                ai_settings = self.config.get("ai_model_settings", {})
                ai_settings["model_type"] = "yolov8"  # Forzar YOLOv8
                ai_config["ai_model_settings"] = ai_settings
                
                self.ai_detector = EnterpriseFruitDetector(ai_config)
                if await self.ai_detector.initialize():
                    logger.info("✅ IA inicializada correctamente")
                else:
                    logger.warning("⚠️ IA en modo simulación")
            else:
                logger.warning("⚠️ Detector de IA no disponible")
                self.ai_detector = None
        except Exception as e:
            logger.warning(f"⚠️ Error con IA: {e}")
            self.ai_detector = None
    
    async def _initialize_labeler(self):
        """Inicializa la etiquetadora DRV8825."""
        logger.info("🏷️ Inicializando etiquetadora DRV8825...")
        try:
            if LabelerActuator:
                labeler_config = self.config.get("labeler_settings", {})
                if labeler_config.get("enabled", True):
                    self.labeler = LabelerActuator(labeler_config)
                    if await self.labeler.initialize():
                        logger.info("✅ Etiquetadora DRV8825 inicializada")
                    else:
                        logger.warning("⚠️ Etiquetadora en modo simulación")
                else:
                    logger.info("ℹ️ Etiquetadora deshabilitada")
            else:
                logger.warning("⚠️ LabelerActuator no disponible")
        except Exception as e:
            logger.warning(f"⚠️ Error con etiquetadora: {e}")
    
    async def _initialize_servos(self):
        """Inicializa los servomotores MG995."""
        logger.info("🤖 Inicializando servomotores MG995...")
        try:
            if MG995ServoController:
                self.servo_controller = MG995ServoController(self.config)
                if await self.servo_controller.initialize():
                    logger.info("✅ Servomotores MG995 inicializados")
                else:
                    logger.warning("⚠️ Servomotores en modo simulación")
            else:
                logger.warning("⚠️ MG995ServoController no disponible")
        except Exception as e:
            logger.warning(f"⚠️ Error con servomotores: {e}")
    
    async def _initialize_belt(self):
        """Inicializa la banda transportadora usando controlador avanzado si es posible."""
        logger.info("🎚️ Inicializando banda transportadora...")
        try:
            belt_config = self.config.get("belt_settings", {})
            # Preferir controlador avanzado si hay configuración completa
            use_advanced = bool(belt_config.get("use_advanced_controller", True))
            advanced_cfg = {
                "control_type": belt_config.get("control_type", "relay_motor"),
                "relay1_pin_bcm": belt_config.get("relay1_pin", 22),
                "relay2_pin_bcm": belt_config.get("relay2_pin", 23),
                "enable_pin_bcm": belt_config.get("enable_pin", 27),
                "active_state_on": belt_config.get("active_state_on", "LOW"),
                "default_speed_percent": belt_config.get("default_speed_percent", 100),
                "safety_timeout_s": belt_config.get("safety_timeout_s", 10.0),
            }
            tried_advanced = False
            if use_advanced:
                try:
                    from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController
                    self.belt = ConveyorBeltController(advanced_cfg)
                    if await self.belt.initialize():
                        logger.info("✅ Banda transportadora (controlador avanzado) inicializada")
                        return
                    else:
                        tried_advanced = True
                        logger.warning("⚠️ Controlador avanzado no inicializó, probando controlador simple")
                except Exception as e:
                    tried_advanced = True
                    logger.warning(f"⚠️ Fallo importando/inicializando controlador avanzado: {e}")
            # Fallback a controlador simple
            self.belt = SimpleBeltController(
                relay1_pin=belt_config.get("relay1_pin", 22),
                relay2_pin=belt_config.get("relay2_pin", 23),
                enable_pin=belt_config.get("enable_pin", 27)
            )
            if await self.belt.initialize():
                logger.info("✅ Banda transportadora (controlador simple) inicializada")
        except Exception as e:
            logger.warning(f"⚠️ Error con banda: {e}")
    
    async def _initialize_sensor(self):
        """Inicializa el sensor de trigger (opcional)."""
        logger.info("📡 Inicializando sensor...")
        try:
            if SensorInterface:
                sensor_config = self.config.get("sensor_settings", {})
                # Respetar bandera 'enabled' del trigger del prototipo
                trigger_cfg = sensor_config.get("trigger_sensor", {})
                if trigger_cfg and not trigger_cfg.get("enabled", True):
                    logger.info("ℹ️ Sensor de trigger deshabilitado por configuración")
                    return
                if sensor_config:
                    self.sensor = SensorInterface(
                        trigger_callback=self._sensor_callback
                    )
                    if self.sensor.initialize(sensor_config):
                        self.sensor.enable_trigger_monitoring()
                        logger.info("✅ Sensor inicializado")
                else:
                    logger.info("ℹ️ Sensor no configurado")
        except Exception as e:
            logger.warning(f"⚠️ Error con sensor: {e}")
    
    def _sensor_callback(self):
        """Callback cuando el sensor detecta una fruta."""
        try:
            logger.info("🔴 Sensor trigger - Programando captura y acciones asociadas...")
            # 1) Reanudar banda si está detenida y, opcionalmente, desactivar timeout de seguridad
            try:
                behavior = self.config.get("sensor_behavior", {})
                resume_belt = bool(behavior.get("resume_belt_on_trigger", True))
                disable_timeout = bool(behavior.get("disable_belt_safety_timeout_on_trigger", True))
                if resume_belt and self.belt:
                    async def _resume_belt_task():
                        try:
                            # Desactivar/parchear timeout de seguridad si aplica
                            if disable_timeout and hasattr(self.belt, 'set_safety_timeout'):
                                await self.belt.set_safety_timeout(0.0)
                            # Iniciar o mantener corriendo
                            if hasattr(self.belt, 'start_belt'):
                                await self.belt.start_belt()
                            elif hasattr(self.belt, 'start'):
                                await self.belt.start()
                        except Exception as e:
                            logger.warning(f"⚠️ Error reanudando banda en trigger: {e}")
                    asyncio.create_task(_resume_belt_task())
            except Exception as e:
                logger.warning(f"⚠️ Error gestionando reanudación de banda: {e}")

            # 2) Activar etiquetadora (DRV8825/NEMA17) inmediatamente en trigger, configurable
            try:
                behavior = self.config.get("sensor_behavior", {})
                labeler_cfg = behavior.get("labeler_activation_on_trigger", {})
                if labeler_cfg.get("enabled", True) and self.labeler:
                    duration = float(labeler_cfg.get("duration_s", 0.6))
                    intensity = float(labeler_cfg.get("intensity_percent", 100.0))
                    asyncio.create_task(self.labeler.activate_for_duration(duration, intensity))
            except Exception as e:
                logger.warning(f"⚠️ Error activando etiquetadora en trigger: {e}")

            # 3) Programar activación de secciones por categoría detectada, no todas
            try:
                behavior = self.config.get("sensor_behavior", {})
                # Si hay eventos pendientes, usar el más reciente para decidir la sección
                if self.servo_controller and self.pending_classifications:
                    latest_event = self.pending_classifications[-1]
                    # Activar correspondiente tras el delay de clasificación normal
                    async def _activate_section_for_latest():
                        try:
                            await asyncio.sleep(self.classification_delay_s)
                            await self.servo_controller.activate_servo(latest_event.category)
                        except Exception as e:
                            logger.warning(f"⚠️ Error activando sección por categoría: {e}")
                    asyncio.create_task(_activate_section_for_latest())
            except Exception as e:
                logger.warning(f"⚠️ Error programando activación de secciones: {e}")

            # 4) Programar captura después del delay para detección IA
            asyncio.create_task(self._delayed_capture())
        except Exception as e:
            logger.error(f"❌ Error en sensor callback: {e}")
    
    async def _delayed_capture(self):
        """Captura con delay después de trigger del sensor."""
        await asyncio.sleep(self.labeling_delay_s)
        await self._capture_and_detect()
    
    async def start_production(self):
        """Inicia el proceso de producción."""
        try:
            logger.info("▶️ Iniciando producción...")
            
            # Iniciar banda (detectar API del controlador)
            if self.belt:
                try:
                    if hasattr(self.belt, 'start_belt'):
                        await self.belt.start_belt()  # Controlador avanzado
                    elif hasattr(self.belt, 'start'):
                        await self.belt.start()       # Controlador simple
                    else:
                        logger.warning("Controlador de banda sin método start/start_belt")
                except Exception as e:
                    logger.error(f"❌ Error iniciando banda: {e}")
            
            self.running = True
            self.state = SystemState.RUNNING
            self.stats["start_time"] = time.time()
            
            # Iniciar bucle de procesamiento
            asyncio.create_task(self._processing_loop())
            asyncio.create_task(self._classification_loop())
            asyncio.create_task(self._stats_loop())
            asyncio.create_task(self._control_loop())
            
            logger.info("✅ Producción iniciada")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando producción: {e}")
            self.state = SystemState.ERROR
    
    async def stop_production(self):
        """Detiene el proceso de producción."""
        try:
            logger.info("⏸️ Deteniendo producción...")
            
            self.running = False
            self.state = SystemState.IDLE
            
            # Detener banda con API segura
            if self.belt:
                try:
                    if hasattr(self.belt, 'stop_belt'):
                        await self.belt.stop_belt()
                    elif hasattr(self.belt, 'stop'):
                        await self.belt.stop()
                except Exception as e:
                    logger.error(f"❌ Error deteniendo banda: {e}")
            
            logger.info("✅ Producción detenida")
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo producción: {e}")
    
    async def _processing_loop(self):
        """Bucle principal de procesamiento con IA."""
        logger.info("🔄 Bucle de procesamiento iniciado")
        
        while self.running:
            try:
                # Si hay sensor, esperar a que active
                # Si no hay sensor, capturar continuamente
                if not self.sensor:
                    await self._capture_and_detect()
                    
                    # Esperar intervalo mínimo
                    min_interval = self.config.get("timing", {}).get("min_detection_interval_s", 0.5)
                    await asyncio.sleep(min_interval)
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en bucle de procesamiento: {e}")
                await asyncio.sleep(1)
    
    async def _capture_and_detect(self):
        """Captura imagen y detecta frutas con IA."""
        try:
            # 1. Capturar frame
            if not self.camera:
                logger.warning("⚠️ No hay cámara disponible - la IA no puede capturar frames")
                return
            
            frame = self.camera.capture_frame()
            if frame is None:
                logger.warning("⚠️ Cámara no entregó frame (None)")
                return
            
            # 2. Detectar con IA
            if not self.ai_detector:
                logger.debug("⚠️ No hay detector de IA disponible")
                return
            
            result = await self.ai_detector.detect_fruits(frame)
            
            if not result or result.fruit_count == 0:
                self._log_no_detection_if_needed()
                # Mostrar/actualizar preview sin anotaciones si está habilitado
                if self.show_preview and _CV2_AVAILABLE:
                    self._maybe_show_preview(frame)
                if self._drm_preview_started:
                    self._update_drm_overlay(frame)
                self._update_http_preview(frame)
                return
            
            # 3. Procesar detecciones
            logger.info(f"🍎 Detectadas {result.fruit_count} frutas")
            
            # Procesar múltiples detecciones con deduplicación
            processed_in_frame = 0
            max_per_frame = int(self._dedup_settings.get("max_events_per_frame", 3))
            now = time.time()
            for det in result.detections:
                if processed_in_frame >= max_per_frame:
                    break
                fruit_class = det.class_name.lower()
                confidence = det.confidence
                bbox = det.bbox

                # Mapear a categoría
                category = self._map_class_to_category(fruit_class)

                # Deduplicación temporal/espacial
                if self._dedup_settings.get("enabled", True):
                    if self._is_duplicate_detection(fruit_class, bbox, now):
                        continue

                # Crear evento aceptado
                event = DetectionEvent(
                    timestamp=now,
                    fruit_class=fruit_class,
                    confidence=confidence,
                    category=category,
                    bbox=bbox
                )

                self.detection_queue.append(event)
                self.pending_classifications.append(event)
                self.stats["last_detection_ts"] = now
                processed_in_frame += 1

                # Memorizar para dedup futura
                try:
                    self._recent_detections.append({
                        't': now,
                        'cls': fruit_class,
                        'bbox': bbox,
                        'center': ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0),
                    })
                except Exception:
                    pass

                # Actualizar estadísticas
                self.stats["detections_total"] += 1
                self.stats["detections_by_class"][fruit_class] = \
                    self.stats["detections_by_class"].get(fruit_class, 0) + 1

                logger.info(f"   📊 {fruit_class} (conf: {confidence:.2f}) → {category.value}")

                # 4. Activar etiquetadora solo si está habilitado en configuración (por defecto deshabilitado)
                labeler_cfg = self.config.get("labeler_settings", {})
                if bool(labeler_cfg.get("activate_on_detection", False)):
                    await self._activate_labeler(event)
            
            # 5. Visualización/guardado (anotar todas las detecciones)
            self._maybe_preview_or_save(frame, result.detections)
                
        except Exception as e:
            logger.error(f"❌ Error en captura y detección: {e}")
            self.stats["errors"] += 1

    # --- DEDUPLICACIÓN ---
    def _bbox_iou(self, a, b) -> float:
        try:
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            inter_x1 = max(ax1, bx1)
            inter_y1 = max(ay1, by1)
            inter_x2 = min(ax2, bx2)
            inter_y2 = min(ay2, by2)
            inter_w = max(0, inter_x2 - inter_x1)
            inter_h = max(0, inter_y2 - inter_y1)
            inter_area = inter_w * inter_h
            a_area = max(0, (ax2 - ax1)) * max(0, (ay2 - ay1))
            b_area = max(0, (bx2 - bx1)) * max(0, (by2 - by1))
            union = a_area + b_area - inter_area
            if union <= 0:
                return 0.0
            return inter_area / union
        except Exception:
            return 0.0

    def _center_distance(self, a, b) -> float:
        try:
            ax = (a[0] + a[2]) / 2.0
            ay = (a[1] + a[3]) / 2.0
            bx = (b[0] + b[2]) / 2.0
            by = (b[1] + b[3]) / 2.0
            dx = ax - bx
            dy = ay - by
            return (dx * dx + dy * dy) ** 0.5
        except Exception:
            return 1e9

    def _is_duplicate_detection(self, fruit_class: str, bbox: Any, now_ts: float) -> bool:
        try:
            time_window = float(self._dedup_settings.get("time_window_s", 0.5))
            iou_thr = float(self._dedup_settings.get("iou_threshold", 0.5))
            center_thr = float(self._dedup_settings.get("center_distance_px", 60))
            # Buscar en ventana temporal reciente
            for entry in reversed(self._recent_detections):
                if (now_ts - entry['t']) > time_window:
                    break
                if entry['cls'] != fruit_class:
                    continue
                prev_bbox = entry['bbox']
                if self._bbox_iou(bbox, prev_bbox) >= iou_thr:
                    return True
                if self._center_distance(bbox, prev_bbox) <= center_thr:
                    return True
            return False
        except Exception:
            return False

    def _log_no_detection_if_needed(self):
        """Registra un log de no detecciones con rate limiting."""
        now = time.time()
        if (now - self._last_no_detection_log) >= self.no_detection_log_interval_s:
            logger.info("🔎 No se detectaron frutas en el frame")
            self._last_no_detection_log = now

    async def _control_loop(self):
        """Bucle que aplica comandos y ajustes enviados por backend (runtime_control.json)."""
        last_applied_ts = 0.0
        while self.running:
            try:
                if self._control_file_path.exists():
                    with open(self._control_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    updated_at = float(data.get('updated_at', 0.0))
                    if updated_at > last_applied_ts:
                        await self._apply_runtime_control(data)
                        last_applied_ts = updated_at
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    async def _apply_runtime_control(self, data: Dict[str, Any]):
        """Aplica cambios recibidos desde el backend al vuelo."""
        try:
            # 1) Ajustes de activación del stepper por sensor
            sensor_labeler = data.get('sensor_labeler')
            if sensor_labeler:
                sb = self.config.setdefault('sensor_behavior', {})
                lac = sb.setdefault('labeler_activation_on_trigger', {})
                if 'duration_s' in sensor_labeler:
                    lac['duration_s'] = float(sensor_labeler['duration_s'])
                if 'intensity_percent' in sensor_labeler:
                    lac['intensity_percent'] = float(sensor_labeler['intensity_percent'])
                logger.info(f"⚙️ Actualizado labeler on trigger: {lac}")

            # 2) Deduplicación
            dedup = data.get('dedup_settings')
            if dedup:
                for k, v in dedup.items():
                    self._dedup_settings[k] = v
                logger.info(f"⚙️ Actualizado dedup_settings: {self._dedup_settings}")

            # 3) Timeout de seguridad
            if 'safety_timeout_seconds' in data and self.belt and hasattr(self.belt, 'set_safety_timeout'):
                try:
                    await self.belt.set_safety_timeout(float(data['safety_timeout_seconds']))
                    logger.info(f"🛡️ Timeout de seguridad actualizado a {data['safety_timeout_seconds']}s")
                except Exception as e:
                    logger.warning(f"⚠️ Error aplicando safety timeout: {e}")

            # 4) Comandos de banda
            belt = data.get('belt')
            if belt and self.belt:
                cmd = str(belt.get('command', '')).lower()
                if cmd == 'start':
                    if hasattr(self.belt, 'start_belt'):
                        await self.belt.start_belt()
                    elif hasattr(self.belt, 'start'):
                        await self.belt.start()
                    logger.info("▶️ Banda iniciada por control remoto")
                elif cmd == 'stop':
                    if hasattr(self.belt, 'stop_belt'):
                        await self.belt.stop_belt()
                    elif hasattr(self.belt, 'stop'):
                        await self.belt.stop()
                    logger.info("⏹️ Banda detenida por control remoto")
                elif cmd == 'emergency':
                    if hasattr(self.belt, 'emergency_stop'):
                        await self.belt.emergency_stop()
                    else:
                        if hasattr(self.belt, 'stop_belt'):
                            await self.belt.stop_belt()
                    logger.warning("🚨 Parada de emergencia de banda (control remoto)")
                # set_speed
                if 'speed_percent' in belt and hasattr(self.belt, 'set_speed'):
                    try:
                        await self.belt.set_speed(float(belt['speed_percent']))
                        logger.info(f"⚙️ Velocidad de banda seteada a {belt['speed_percent']}% por control remoto")
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"❌ Error aplicando runtime control: {e}")

    def _annotate_frame(self, frame, detections: List[Any]):
        """Devuelve una copia del frame con bounding boxes y etiquetas."""
        try:
            if not _CV2_AVAILABLE:
                return frame
            annotated = frame.copy()
            for det in detections:
                try:
                    x1, y1, x2, y2 = det.bbox
                    color = (0, 255, 0)
                    cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    label = f"{det.class_name} {det.confidence:.2f}"
                    cv2.putText(annotated, label, (int(x1), max(0, int(y1) - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                except Exception:
                    continue
            return annotated
        except Exception:
            return frame

    def _maybe_show_preview(self, frame):
        """Muestra frame en ventana si está habilitado y posible."""
        try:
            if self.show_preview and _CV2_AVAILABLE:
                cv2.imshow(self.preview_window_name, frame)
                cv2.waitKey(1)
        except Exception as e:
            logger.warning(f"⚠️ Vista previa deshabilitada: {e}")
            self.show_preview = False

    def _maybe_preview_or_save(self, frame, detections: List[Any]):
        """Maneja visualización y guardado de frames anotados según configuración."""
        try:
            # Decidir si anotar para las vistas de preview (HTTP/DRM) sin depender de show_preview
            annotate_for_preview = (
                self.annotate_preview and _CV2_AVAILABLE and (
                    (not self.annotate_preview_only_on_detection) or (detections and len(detections) > 0)
                )
            )

            # Calcular una sola versión anotada si cualquiera lo requiere
            need_annotated = (self.show_preview or self.save_annotated_frames or annotate_for_preview) and _CV2_AVAILABLE
            annotated = self._annotate_frame(frame, detections) if need_annotated else frame

            # Ventana local (cv2.imshow) según configuración
            if self.show_preview and _CV2_AVAILABLE:
                self._maybe_show_preview(annotated)

            # Preview DRM y HTTP
            preview_frame = annotated if annotate_for_preview else frame
            if self._drm_preview_started:
                self._update_drm_overlay(preview_frame)
            self._update_http_preview(preview_frame)

            # Guardado en disco si está habilitado
            if self.save_annotated_frames and _CV2_AVAILABLE:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                filename = self._detections_dir / f"det_{ts}.jpg"
                try:
                    cv2.imwrite(str(filename), annotated)
                except Exception:
                    pass
        except Exception:
            pass

    def _start_drm_preview(self):
        """Inicia la vista previa DRM de Picamera2 si es posible."""
        try:
            if not _P2_PREVIEW_AVAILABLE:
                return
            picam2 = getattr(self.camera.driver, 'picam2', None)
            if picam2 and not self._drm_preview_started:
                picam2.start_preview(_P2Preview.DRM)
                self._drm_preview_started = True
                logger.info("🖼️ Vista previa DRM activada (Picamera2)")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo iniciar vista previa DRM: {e}")
            self._drm_preview_started = False

    def _update_drm_overlay(self, frame):
        """Actualiza overlay de la vista DRM con el frame anotado."""
        try:
            picam2 = getattr(self.camera.driver, 'picam2', None)
            if not picam2 or not self._drm_preview_started:
                return
            overlay = frame
            if _CV2_AVAILABLE and frame is not None:
                try:
                    if frame.ndim == 3 and frame.shape[2] == 3:
                        overlay = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                        overlay[:, :, 3] = 160  # semitransparente
                except Exception:
                    pass
            # picamera2 acepta BGRA/RGBA como overlay
            picam2.set_overlay(overlay)
        except Exception:
            pass

    # ==================== VISTA PREVIA WEB MJPEG ====================
    def _start_http_preview_server(self):
        """Inicia servidor HTTP MJPEG simple para vista previa."""
        try:
            class MJPEGHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self_inner):  # type: ignore
                    if self_inner.path not in ('/', '/mjpeg'):
                        self_inner.send_response(404)
                        self_inner.end_headers()
                        return
                    self_inner.send_response(200)
                    self_inner.send_header('Age', 0)
                    self_inner.send_header('Cache-Control', 'no-cache, private')
                    self_inner.send_header('Pragma', 'no-cache')
                    self_inner.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                    self_inner.end_headers()
                    try:
                        while True:
                            frame_bytes = self._latest_jpeg
                            if frame_bytes is not None:
                                self_inner.wfile.write(b"--FRAME\r\n")
                                self_inner.send_header('Content-Type', 'image/jpeg')
                                self_inner.send_header('Content-Length', str(len(frame_bytes)))
                                self_inner.end_headers()
                                self_inner.wfile.write(frame_bytes)
                                self_inner.wfile.write(b"\r\n")
                            # 100 ms entre frames
                            time.sleep(0.1)
                    except Exception:
                        pass
                def log_message(self_inner, format, *args):  # type: ignore
                    return  # Silenciar logs HTTP

            class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
                daemon_threads = True

            server = ThreadingHTTPServer(("0.0.0.0", self.http_preview_port), MJPEGHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self._http_server = server
            self._http_thread = thread
            logger.info(f"🌐 Vista previa web MJPEG activa en http://localhost:{self.http_preview_port}/mjpeg")
        except Exception as e:
            logger.warning(f"⚠️ Error iniciando vista previa web MJPEG: {e}")
            self.http_preview_enabled = False

    def _update_http_preview(self, frame):
        """Codifica y guarda JPEG actual para server MJPEG."""
        try:
            if not self.http_preview_enabled or frame is None or not _CV2_AVAILABLE:
                return
            ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                self._latest_jpeg = buf.tobytes()
        except Exception:
            pass
    
    def _map_class_to_category(self, fruit_class: str) -> FruitCategory:
        """Mapea clase detectada a categoría de servo."""
        mapping = {
            "apple": FruitCategory.APPLE,
            "manzana": FruitCategory.APPLE,
            "pear": FruitCategory.PEAR,
            "pera": FruitCategory.PEAR,
            "lemon": FruitCategory.LEMON,  # Los limones no tienen servo, pasan directo
            "limon": FruitCategory.LEMON,
            "limón": FruitCategory.LEMON,
        }
        return mapping.get(fruit_class.lower(), FruitCategory.UNKNOWN)
    
    async def _activate_labeler(self, event: DetectionEvent):
        """Activa la etiquetadora para aplicar etiqueta."""
        try:
            if not self.labeler:
                logger.debug("⚠️ Etiquetadora no disponible")
                event.labeled = True
                return
            
            # Configuración de activación
            labeler_config = self.config.get("labeler_settings", {})
            duration = labeler_config.get("activation_duration_seconds", 0.6)
            intensity = labeler_config.get("intensity_percent", 80.0)
            
            logger.info(f"🏷️ Activando etiquetadora por {duration:.2f}s @ {intensity:.0f}%")
            
            success = await self.labeler.activate_for_duration(duration, intensity)
            
            if success:
                event.labeled = True
                self.stats["labeled_total"] += 1
                logger.info("✅ Etiqueta aplicada")
            else:
                logger.error("❌ Error aplicando etiqueta")
                
        except Exception as e:
            logger.error(f"❌ Error activando etiquetadora: {e}")
    
    async def _classification_loop(self):
        """Bucle de clasificación con servomotores."""
        logger.info("🔄 Bucle de clasificación iniciado")
        
        while self.running:
            try:
                # Buscar eventos pendientes de clasificación
                current_time = time.time()
                
                for event in list(self.pending_classifications):
                    if event.classified:
                        self.pending_classifications.remove(event)
                        continue
                    
                    # Verificar si ya pasó el tiempo de clasificación
                    elapsed = current_time - event.timestamp
                    if elapsed >= self.classification_delay_s:
                        await self._classify_fruit(event)
                        self.pending_classifications.remove(event)
                
                await asyncio.sleep(0.05)  # 50ms
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en bucle de clasificación: {e}")
                await asyncio.sleep(1)
    
    async def _classify_fruit(self, event: DetectionEvent):
        """Clasifica la fruta activando el servo correspondiente."""
        try:
            if not self.servo_controller:
                logger.debug("⚠️ Controlador de servos no disponible")
                event.classified = True
                return
            
            logger.info(f"🎯 Clasificando {event.fruit_class} → {event.category.value}")
            
            # Activar servo correspondiente para cada categoría
            if event.category in [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]:
                success = await self.servo_controller.activate_servo(event.category)
                
                if success:
                    event.classified = True
                    self.stats["classified_total"] += 1
                    # Actualizar contador específico del servo
                    if event.category == FruitCategory.APPLE:
                        self.stats["classified_by_servo"]["apple"] += 1
                    elif event.category == FruitCategory.PEAR:
                        self.stats["classified_by_servo"]["pear"] += 1
                    elif event.category == FruitCategory.LEMON:
                        self.stats["classified_by_servo"]["lemon"] += 1
                    logger.info(f"✅ {event.fruit_class} clasificado correctamente")
                else:
                    logger.error(f"❌ Error clasificando {event.fruit_class}")
            else:
                # Para otras categorías desconocidas, marcar como clasificado sin acción
                event.classified = True
                self.stats["classified_total"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error en clasificación: {e}")
    
    async def _stats_loop(self):
        """Bucle de actualización de estadísticas."""
        while self.running:
            try:
                self.stats["uptime_s"] = time.time() - self.stats["start_time"]
                # Rearmar timeout de seguridad de la banda si no hay detecciones por 60s
                try:
                    last_det = float(self.stats.get("last_detection_ts", 0.0))
                    if last_det > 0 and (time.time() - last_det) >= 60.0 and self.belt:
                        # Reaplicar timeout estándar (10s) si el driver lo soporta
                        if hasattr(self.belt, 'set_safety_timeout'):
                            await self.belt.set_safety_timeout(10.0)
                except Exception:
                    pass
                # Loguear FPS de cámara periódicamente si está disponible
                if self.camera:
                    try:
                        status = self.camera.get_status()
                        fps = status.get("metrics", {}).get("current_fps", 0.0)
                        if fps:
                            logger.info(f"📷 FPS cámara: {fps:.1f}")
                    except Exception:
                        pass
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception:
                pass
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema."""
        return {
            "state": self.state.value,
            "running": self.running,
            "components": {
                "camera": self.camera is not None,
                "ai": self.ai_detector is not None,
                "labeler": self.labeler is not None,
                "servos": self.servo_controller is not None,
                "belt": self.belt is not None,
                "sensor": self.sensor is not None
            },
            "stats": self.stats,
            "pending_classifications": len(self.pending_classifications),
            "timestamp": time.time()
        }
    
    async def emergency_stop(self):
        """Parada de emergencia del sistema."""
        try:
            logger.critical("🚨 PARADA DE EMERGENCIA")
            
            self.running = False
            self.state = SystemState.EMERGENCY_STOP
            
            # Detener todos los componentes
            if self.belt:
                await self.belt.stop()
            
            if self.labeler:
                await self.labeler.emergency_stop()
            
            if self.servo_controller:
                await self.servo_controller.emergency_stop()
            
            logger.info("✅ Parada de emergencia completada")
            
        except Exception as e:
            logger.error(f"❌ Error en parada de emergencia: {e}")
    
    async def shutdown(self):
        """Apaga el sistema limpiamente."""
        try:
            logger.info("🛑 Apagando sistema...")
            
            self.running = False
            self.state = SystemState.OFFLINE
            
            # Limpiar componentes
            if self.belt:
                await self.belt.cleanup()
            
            if self.servo_controller:
                await self.servo_controller.cleanup()
            
            if self.labeler:
                await self.labeler.cleanup()
            
            if self.camera:
                self.camera.shutdown()
            
            if self.ai_detector:
                await self.ai_detector.shutdown()
            
            logger.info("✅ Sistema apagado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error durante apagado: {e}")

# ==================== MAIN ====================

async def main():
    """Función principal del sistema de clasificación."""
    classifier = None
    
    try:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("=" * 70)
        logger.info("🧠 VISIFRUIT - Sistema Inteligente de Clasificación con IA")
        logger.info("=" * 70)
        
        # Crear sistema
        classifier = SmartFruitClassifier()
        
        # Configurar señales
        def signal_handler(sig, frame):
            logger.info("\n⚡ Señal de interrupción recibida")
            if classifier:
                asyncio.create_task(classifier.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicializar
        if not await classifier.initialize():
            logger.error("❌ Error en inicialización")
            return 1
        
        # Iniciar producción
        await classifier.start_production()
        
        # Mantener funcionando
        logger.info("\n✅ Sistema funcionando - Presiona Ctrl+C para detener\n")
        
        while classifier.running:
            await asyncio.sleep(1)
            
            # Mostrar estadísticas cada 10 segundos
            if int(time.time()) % 10 == 0:
                status = classifier.get_status()
                logger.info(
                    f"📊 Detectadas: {status['stats']['detections_total']} | "
                    f"Etiquetadas: {status['stats']['labeled_total']} | "
                    f"Clasificadas: {status['stats']['classified_total']}"
                )
    
    except KeyboardInterrupt:
        logger.info("\n⚡ Interrumpido por usuario")
    except Exception as e:
        logger.exception(f"❌ Error crítico: {e}")
        return 1
    finally:
        if classifier:
            await classifier.shutdown()
        logger.info("👋 Sistema terminado")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
