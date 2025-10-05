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
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import signal
import sys

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
        
        # Parámetros de temporización
        belt_speed = self.config.get("timing", {}).get("belt_speed_mps", 0.2)
        sensor_to_camera_m = self.config.get("timing", {}).get("sensor_to_camera_distance_m", 0.1)
        camera_to_classifier_m = self.config.get("timing", {}).get("camera_to_classifier_distance_m", 0.5)
        
        self.labeling_delay_s = sensor_to_camera_m / belt_speed
        self.classification_delay_s = camera_to_classifier_m / belt_speed
        
        # Estadísticas
        self.stats = {
            "detections_total": 0,
            "detections_by_class": {"apple": 0, "pear": 0, "lemon": 0, "unknown": 0},
            "labeled_total": 0,
            "classified_total": 0,
            "classified_by_servo": {"apple": 0, "pear": 0, "lemon": 0},
            "errors": 0,
            "start_time": time.time(),
            "uptime_s": 0
        }
        
        logger.info("🧠 SmartFruitClassifier creado")
        logger.info(f"   ⏱️ Delay etiquetado: {self.labeling_delay_s:.2f}s")
        logger.info(f"   ⏱️ Delay clasificación: {self.classification_delay_s:.2f}s")
    
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
            logger.info("🔴 Sensor trigger - Programando captura...")
            # Programar captura después del delay
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
                logger.debug("⚠️ No hay cámara disponible")
                return
            
            frame = self.camera.capture_frame()
            if frame is None:
                return
            
            # 2. Detectar con IA
            if not self.ai_detector:
                logger.debug("⚠️ No hay detector de IA disponible")
                return
            
            result = await self.ai_detector.detect_fruits(frame)
            
            if not result or result.fruit_count == 0:
                return
            
            # 3. Procesar detecciones
            logger.info(f"🍎 Detectadas {result.fruit_count} frutas")
            
            for detection in result.detections[:1]:  # Solo la primera (más importante)
                fruit_class = detection.class_name.lower()
                confidence = detection.confidence
                
                # Mapear a categoría
                category = self._map_class_to_category(fruit_class)
                
                # Crear evento
                event = DetectionEvent(
                    timestamp=time.time(),
                    fruit_class=fruit_class,
                    confidence=confidence,
                    category=category,
                    bbox=detection.bbox
                )
                
                self.detection_queue.append(event)
                self.pending_classifications.append(event)
                
                # Actualizar estadísticas
                self.stats["detections_total"] += 1
                self.stats["detections_by_class"][fruit_class] = \
                    self.stats["detections_by_class"].get(fruit_class, 0) + 1
                
                logger.info(f"   📊 {fruit_class} (conf: {confidence:.2f}) → {category.value}")
                
                # 4. Activar etiquetadora inmediatamente
                await self._activate_labeler(event)
                
        except Exception as e:
            logger.error(f"❌ Error en captura y detección: {e}")
            self.stats["errors"] += 1
    
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
