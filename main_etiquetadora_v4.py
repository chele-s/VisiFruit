# main_etiquetadora_v4.py
from __future__ import annotations
"""
Sistema Industrial de Etiquetado Múltiple de Frutas FruPrint v4.0
==================================================================

Sistema de control principal ultra-avanzado con arquitectura modular,
6 etiquetadoras automáticas (2 por categoría), IA de categorización avanzada,
motor DC de posicionamiento automático y optimización predictiva en tiempo real.

NUEVAS CARACTERÍSTICAS v4.0 - MODULAR ARCHITECTURE:
 ✨ Arquitectura modular completamente refactorizada
 📦 Módulos especializados y mantenibles
 🏭 6 Etiquetadoras Automáticas con Motor DC (MODO PROFESIONAL)
 🤖 IA de Categorización Avanzada
 📊 Sistema de Métricas y Telemetría
 🔮 Motor de Predicción y Optimización
 🌐 API Ultra-Avanzada
 💾 Sistema de Base de Datos
 🚀 Auto-inicio de Servicios Auxiliares
 🎯 MODO PROTOTIPO: 1 Etiquetadora DRV8825 + Servos MG995

MODOS DE OPERACIÓN:
 - PROFESIONAL: 6 etiquetadoras + motor DC + clasificadores industriales
 - PROTOTIPO: 1 etiquetadora DRV8825 + 3 servos MG995 para clasificación

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE EDITION
"""

import asyncio
import json
import logging
import signal
import sys
import time
import os
from pathlib import Path
from typing import Dict, Optional, List, Any, TYPE_CHECKING
from collections import Counter
from datetime import datetime

# ==================== IMPORTACIONES DE MÓDULOS PROPIOS ====================

# Tipos y constantes del sistema
from core_modules.system_types import (
    SystemState, AlertLevel, FruitCategory, ProcessingPriority,
    OptimizationMode, TOTAL_LABELERS, get_category_by_name
)

# Sistema de métricas y telemetría
from core_modules.metrics_system import MetricsManager

# Motor de optimización y predicción
from optimization_engine import (
    UltraPatternAnalyzer, UltraPredictionEngine, SystemOptimizer
)

# Sistema de etiquetado ultra
from core_modules.ultra_labeling_system import (
    UltraLinearMotorController, UltraLabelerManager
)

# Sistema de base de datos
from core_modules.database_manager import DatabaseManager

# Gestión de servicios auxiliares
from core_modules.service_manager import (
    ensure_single_instance, preflight_cleanup, check_and_start_services,
    cleanup_services
)

# Utilidades del sistema
from core_modules.system_utils import (
    setup_ultra_logging, measure_performance, retry_on_failure
)

# API Ultra-Avanzada
from core_modules.ultra_api import UltraAPIFactory, start_api_server

# ==================== IMPORTACIONES DE HARDWARE Y CONTROL ====================

try:
    from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController
    from Control_Etiquetado.sensor_interface import SensorInterface
    from Control_Etiquetado.labeler_actuator import LabelerActuator
    from Control_Etiquetado.fruit_diverter_controller import FruitDiverterController
    from utils.camera_controller import CameraController
    from utils.config_validator import ConfigValidator, ValidationLevel
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error de importación: {e}")
    print("Algunos módulos pueden no estar disponibles. Usando modos de simulación.")
    MODULES_AVAILABLE = False

# Tipos solo para chequeo estático
if TYPE_CHECKING:
    from IA_Etiquetado.Fruit_detector import EnterpriseFruitDetector, FrameAnalysisResult

# GPIO wrapper
try:
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, get_gpio_info, is_simulation_mode
    gpio_info = get_gpio_info()
    print(f"🔧 Sistema GPIO: {gpio_info['gpio_type']} ({gpio_info['mode']})")
    if is_simulation_mode():
        print("⚠️ Modo simulación GPIO activo - Ideal para desarrollo en Windows")
    else:
        print("✅ GPIO hardware activo - Raspberry Pi detectado")
except ImportError as e:
    print(f"❌ Error cargando GPIO wrapper: {e}")
    GPIO_AVAILABLE = False

logger = logging.getLogger("FruPrintUltra")

# ==================== CLASE PRINCIPAL DEL SISTEMA ====================

class UltraIndustrialFruitLabelingSystem:
    """
    Sistema ULTRA-Industrial de Etiquetado Múltiple de Frutas v4.0
    ===============================================================
    
    Sistema modular con arquitectura limpia y mantenible.
    """
    
    def __init__(self, config_path: str):
        # Cargar configuración
        self.config_path = Path(config_path)
        self.config = self._load_and_validate_config()
        
        # Información del sistema
        self.system_id = self.config["system_settings"]["installation_id"]
        self.system_name = self.config["system_settings"]["system_name"]
        self.version = "4.0.0-MODULAR"
        
        # Estado del sistema
        self._system_state = SystemState.OFFLINE
        self._running = asyncio.Event()
        self._emergency_stop = asyncio.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Componentes de hardware
        self.camera: Optional[CameraController] = None
        self.ai_detector: Optional[EnterpriseFruitDetector] = None
        self.belt_controller: Optional[ConveyorBeltController] = None
        self.trigger_sensor: Optional[SensorInterface] = None
        self.diverter_controller: Optional[FruitDiverterController] = None
        
        # Sistema de etiquetado ultra (6 etiquetadoras + motor DC)
        self.motor_controller: Optional[UltraLinearMotorController] = None
        self.labeler_manager: Optional[UltraLabelerManager] = None
        self.active_group_id = 0
        
        # Stepper láser (aplicador controlado por sensor YK0008)
        self.laser_stepper: Optional[LabelerActuator] = None
        self.laser_stepper_settings = self.config.get("laser_stepper_settings", {})
        self._last_laser_activation_time: float = 0.0
        
        # Gestores modulares
        self.metrics_manager = MetricsManager()
        self.db_manager = DatabaseManager()
        self.pattern_analyzer = UltraPatternAnalyzer()
        self.prediction_engine = UltraPredictionEngine()
        self.optimizer = SystemOptimizer(self.pattern_analyzer, self.prediction_engine)
        
        # Colas de eventos
        self._trigger_queue = asyncio.Queue(maxsize=200)
        self._alert_queue = asyncio.Queue(maxsize=1000)
        
        # API y WebSocket
        self.app = None
        self.api_factory = None
        
        # Tareas asíncronas
        self._tasks: List[asyncio.Task] = []
        
        # Configurar logging
        setup_ultra_logging(self.config)
        
        logger.info(f"🚀 Sistema ULTRA {self.system_name} v{self.version} inicializado")
        logger.info(f"📋 ID: {self.system_id} | Etiquetadoras: {TOTAL_LABELERS}")
    
    def _load_and_validate_config(self) -> Dict[str, Any]:
        """Carga y valida la configuración del sistema."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuración no encontrada: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validar configuración
            try:
                validator = ConfigValidator(ValidationLevel.INDUSTRIAL)
                is_valid, errors = validator.validate_config_dict(config)
                
                if not is_valid:
                    logger.warning(f"⚠️ Configuración con advertencias: {'; '.join(errors)}")
                else:
                    logger.info("✅ Configuración validada exitosamente")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo validar configuración: {e}")
            
            return config
            
        except Exception as e:
            logger.critical(f"❌ Error cargando configuración: {e}")
            raise
    
    def _set_state(self, new_state: SystemState):
        """Actualiza el estado del sistema."""
        if self._system_state != new_state:
            old_state = self._system_state
            self._system_state = new_state
            logger.info(f"📊 Estado: {old_state.value} → {new_state.value}")
            self.metrics_manager.send_alert(AlertLevel.INFO, "Sistema", f"Estado: {new_state.value}")
    
    # ==================== INICIALIZACIÓN ====================
    
    async def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema."""
        try:
            self._set_state(SystemState.INITIALIZING)
            logger.info("=== 🚀 Iniciando inicialización del sistema ===")
            
            # Guardar event loop
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.get_event_loop()
            
            # Inicializar componentes en orden
            await self._initialize_camera()
            await self._initialize_ai_detector()
            await self._initialize_belt_controller()
            await self._initialize_motor_controller()
            await self._initialize_ultra_labelers()
            await self._initialize_laser_stepper()
            await self._initialize_sensors()
            await self._initialize_diverter_system()
            
            # Inicializar base de datos
            self.db_manager.initialize()
            
            # Inicializar API
            await self._initialize_ultra_api()
            
            # Iniciar tareas del sistema
            await self._start_system_tasks()
            
            self._set_state(SystemState.IDLE)
            logger.info("=== ✅ Sistema inicializado exitosamente ===")
            
            return True
            
        except Exception as e:
            self._set_state(SystemState.ERROR)
            self.metrics_manager.send_alert(
                AlertLevel.CRITICAL, "Sistema", f"Error en inicialización: {e}"
            )
            logger.exception("❌ Error crítico durante inicialización")
            return False
    
    async def _initialize_camera(self):
        """Inicializa el sistema de cámara."""
        logger.info("📷 Inicializando cámara...")
        try:
            camera_config = self.config["camera_settings"]
            self.camera = CameraController(camera_config)
            
            if not self.camera.initialize():
                raise RuntimeError("Fallo al inicializar cámara")
            
            logger.info("✅ Cámara inicializada correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando cámara: {e}")
            self.camera = None
    
    async def _initialize_ai_detector(self):
        """Inicializa el detector de IA YOLOv8."""
        logger.info("🤖 Inicializando detector de IA YOLOv8...")
        try:
            # Importar detector YOLOv8 optimizado para Raspberry Pi 5
            from IA_Etiquetado.YOLOv8_detector import EnterpriseFruitDetector
            
            # Si inferencia remota está habilitada, omitir verificación de archivo local
            remote_cfg = self.config.get("remote_inference", {})
            remote_enabled = bool(remote_cfg.get("enabled", False))
            model_path = self.config.get("ai_model_settings", {}).get("model_path", "weights/best.pt")
            if not remote_enabled:
                if not model_path or not Path(model_path).exists():
                    raise FileNotFoundError(
                        f"Modelo YOLOv8 no encontrado: {model_path}\n"
                        f"   Por favor, descarga tu modelo desde Roboflow y colócalo en weights/best.pt"
                    )

            self.ai_detector = EnterpriseFruitDetector(self.config)
            
            if not await self.ai_detector.initialize():
                raise RuntimeError("Fallo al inicializar el detector YOLOv8")
            
            logger.info("✅ Detector YOLOv8 inicializado correctamente")
            try:
                status = self.ai_detector.get_system_status() if hasattr(self.ai_detector, 'get_system_status') else {}
                mode = status.get("mode", "local")
                device = status.get("device", "CPU (Raspberry Pi 5)")
                if mode == "remote":
                    logger.info("   🌐 Modo: REMOTO (GPU en laptop/servidor)")
                else:
                    logger.info("   🖥️ Modo: LOCAL (CPU Raspberry Pi 5)")
                logger.info(f"   📦 Modelo: {model_path}")
                logger.info(f"   🧩 Dispositivo: {device}")
            except Exception:
                logger.info(f"   📦 Modelo: {model_path}")
                logger.info(f"   🖥️ Dispositivo: CPU (Raspberry Pi 5 optimizado)")
            
        except (FileNotFoundError, RuntimeError) as e:
            logger.warning(f"⚠️ ADVERTENCIA: {e}")
            logger.warning("   El sistema continuará sin la funcionalidad de IA.")
            self.ai_detector = None
        except Exception as e:
            logger.error(f"❌ Error inesperado inicializando IA: {e}")
            self.ai_detector = None
    
    async def _initialize_belt_controller(self):
        """Inicializa el controlador de banda."""
        logger.info("🎚️ Inicializando controlador de banda...")
        try:
            belt_config = self.config["conveyor_belt_settings"]
            self.belt_controller = ConveyorBeltController(belt_config)
            
            if not await self.belt_controller.initialize():
                raise RuntimeError("Fallo al inicializar banda")
            
            logger.info("✅ Controlador de banda inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando banda: {e}")
            self.belt_controller = None
    
    async def _initialize_motor_controller(self):
        """Inicializa el controlador lineal del motor DC."""
        logger.info("🔩 Inicializando controlador lineal de motor DC...")
        try:
            motor_config = self.config.get("motor_controller_settings", {
                "motor_pins": {"pwm_pin": 12, "dir_pin1": 20, "dir_pin2": 21, "enable_pin": 16}
            })
            
            self.motor_controller = UltraLinearMotorController(motor_config)
            
            if not await self.motor_controller.initialize():
                raise RuntimeError("Fallo al inicializar motor DC lineal")
            
            logger.info("✅ Controlador lineal de motor DC inicializado")
            logger.info("   🍎 Grupo manzanas: etiquetadoras 0-1")
            logger.info("   🍐 Grupo peras: etiquetadoras 2-3")
            logger.info("   🍋 Grupo limones: etiquetadoras 4-5")
        except Exception as e:
            logger.error(f"❌ Error inicializando motor DC: {e}")
            self.motor_controller = None
    
    async def _initialize_ultra_labelers(self):
        """Inicializa las 6 etiquetadoras lineales."""
        logger.info("🏭 Inicializando sistema de 6 etiquetadoras lineales...")
        try:
            base_config = self.config.get("labeler_settings", {})
            self.labeler_manager = UltraLabelerManager(base_config)
            
            if not await self.labeler_manager.initialize():
                raise RuntimeError("Fallo al inicializar etiquetadoras")
            
            logger.info("✅ Sistema de etiquetadoras lineales inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando etiquetadoras: {e}")
            self.labeler_manager = None
    
    async def _initialize_laser_stepper(self):
        """Inicializa el stepper DRV8825 para aplicador láser."""
        try:
            stepper_cfg = self.laser_stepper_settings
            if not stepper_cfg or not stepper_cfg.get("enabled", True):
                logger.info("ℹ️ Stepper láser deshabilitado")
                return
            
            cfg = stepper_cfg.copy()
            cfg["type"] = "stepper"
            cfg.setdefault("name", "LabelApplicatorStepper")
            
            self.laser_stepper = LabelerActuator(cfg)
            if await self.laser_stepper.initialize():
                logger.info("✅ Stepper DRV8825 para aplicador inicializado")
            else:
                logger.error("❌ Fallo al inicializar stepper DRV8825")
                self.laser_stepper = None
        except Exception as e:
            logger.error(f"❌ Error inicializando stepper: {e}")
            self.laser_stepper = None
    
    async def _initialize_sensors(self):
        """Inicializa el sistema de sensores."""
        logger.info("📡 Inicializando sensores...")
        try:
            sensor_config = self.config["sensor_settings"]
            self.trigger_sensor = SensorInterface(
                trigger_callback=self._sensor_trigger_callback
            )
            
            if not self.trigger_sensor.initialize(sensor_config):
                raise RuntimeError("Fallo al inicializar sensores")
            
            try:
                self.trigger_sensor.enable_trigger_monitoring()
            except Exception:
                pass
            
            logger.info("✅ Sensores inicializados correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando sensores: {e}")
            self.trigger_sensor = None
    
    async def _initialize_diverter_system(self):
        """Inicializa el sistema de desviadores para clasificación."""
        logger.info("🔀 Inicializando sistema de desviadores...")
        try:
            from core_modules.system_types import DEFAULT_DIVERTER_CONFIG
            diverter_config = self.config.get("diverter_settings", DEFAULT_DIVERTER_CONFIG)
            
            if not diverter_config.get("enabled", True):
                logger.info("ℹ️ Sistema de desviadores deshabilitado")
                return
            
            self.diverter_controller = FruitDiverterController(diverter_config)
            
            if not await self.diverter_controller.initialize():
                raise RuntimeError("Fallo al inicializar desviadores")
            
            logger.info("✅ Sistema de desviadores inicializado")
            logger.info("   🍎 Manzanas → Desviador 0 (MG995) → Caja manzanas")
            logger.info("   🍐 Peras → Desviador 1 (MG995) → Caja peras")
            logger.info("   🍋 Limones → Desviador 2 (MG995) → Caja limones")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando desviadores: {e}")
            self.diverter_controller = None
    
    async def _initialize_ultra_api(self):
        """Inicializa la API ultra-avanzada."""
        if not self.config.get("api_settings", {}).get("enabled", True):
            return
        
        logger.info("🌐 Inicializando API Ultra-Avanzada...")
        self.api_factory = UltraAPIFactory(self)
        self.app = self.api_factory.create_app()
        logger.info("✅ API Ultra-Avanzada inicializada")
    
    async def _start_system_tasks(self):
        """Inicia las tareas del sistema."""
        logger.info("⚙️ Iniciando tareas del sistema...")
        
        # Tareas principales
        self._tasks.append(asyncio.create_task(self._main_processing_loop()))
        self._tasks.append(asyncio.create_task(self._monitoring_loop()))
        self._tasks.append(asyncio.create_task(self._optimization_loop()))
        self._tasks.append(asyncio.create_task(self._learning_loop()))
        
        # Servidor API
        if self.app:
            api_config = self.config["api_settings"]
            host = api_config.get("host", "0.0.0.0")
            port = api_config.get("port", 8000)
            server_task = await start_api_server(self.app, host, port)
            self._tasks.append(server_task)
        
        logger.info(f"✅ {len(self._tasks)} tareas iniciadas")
    
    # ==================== CALLBACKS Y TRIGGERS ====================
    
    def _sensor_trigger_callback(self):
        """Callback del sensor de trigger."""
        try:
            trigger_time = time.time()
            if self._loop:
                self._loop.call_soon_threadsafe(self._trigger_queue.put_nowait, trigger_time)
            
            # Activación del stepper láser si está habilitado
            if self.laser_stepper and self.laser_stepper_settings.get("activation_on_laser", {}).get("enabled", True):
                min_interval = float(self.laser_stepper_settings.get("activation_on_laser", {}).get("min_interval_seconds", 0.15))
                if (trigger_time - self._last_laser_activation_time) >= min_interval:
                    self._last_laser_activation_time = trigger_time
                    duration = float(self.laser_stepper_settings.get("activation_on_laser", {}).get("activation_duration_seconds", 0.6))
                    intensity = float(self.laser_stepper_settings.get("activation_on_laser", {}).get("intensity_percent", 80.0))
                    if self._loop:
                        self._loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(self.laser_stepper.activate_for_duration(duration, intensity))
                        )
        except asyncio.QueueFull:
            logger.warning("⚠️ Cola de triggers llena")
    
    # ==================== BUCLES DE PROCESAMIENTO ====================
    
    async def _main_processing_loop(self):
        """Bucle principal de procesamiento."""
        logger.info("🔄 Bucle principal iniciado")
        
        while True:
            try:
                if not self._running.is_set() or self._system_state != SystemState.RUNNING:
                    await asyncio.sleep(0.1)
                    continue
                
                # Esperar trigger
                try:
                    trigger_time = await asyncio.wait_for(
                        self._trigger_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                self._set_state(SystemState.PROCESSING)
                await self._process_fruit_detection()
                self._set_state(SystemState.RUNNING)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"❌ Error en bucle principal: {e}")
                await asyncio.sleep(1)
    
    @measure_performance
    async def _process_fruit_detection(self):
        """Procesa detección y etiquetado de frutas."""
        try:
            # 1. Capturar frame
            if not self.camera:
                logger.warning("⚠️ Cámara no disponible")
                return
            
            frame = self.camera.capture_frame()
            if frame is None:
                logger.error("❌ No se pudo capturar frame")
                return
            
            # 2. Analizar con IA
            if not self.ai_detector:
                logger.warning("⚠️ Detector de IA no disponible")
                return
            
            result = await self.ai_detector.detect_fruits(frame, ProcessingPriority.HIGH)
            
            if result and result.fruit_count > 0:
                logger.info(f"🍎 Detectadas {result.fruit_count} frutas")
                
                # 3. Determinar categorías
                categories = await self._analyze_fruit_categories(result)
                
                if categories:
                    # 4. Seleccionar etiquetadora óptima
                    optimal_category = self._select_optimal_category(categories)
                    
                    # 5. Ejecutar etiquetado
                    await self._execute_labeling(optimal_category, result)
                    
                    # 6. Ejecutar clasificación
                    await self._execute_classification(optimal_category, result)
                    
                    # 7. Actualizar métricas
                    self.metrics_manager.update_category_metrics(
                        optimal_category, 
                        detected=result.fruit_count,
                        labeled=result.fruit_count
                    )
                    
                    # 8. NUEVO: Broadcast evento de detección en tiempo real
                    if self.api_factory:
                        try:
                            # Obtener confianza promedio de las detecciones
                            avg_confidence = 0.95
                            if hasattr(result, 'detections') and result.detections:
                                confidences = [d.confidence for d in result.detections if hasattr(d, 'confidence')]
                                if confidences:
                                    avg_confidence = sum(confidences) / len(confidences)
                            
                            # Enviar evento de detección
                            await self.api_factory.broadcast_detection_event(
                                category=optimal_category.fruit_name.lower(),
                                count=result.fruit_count,
                                confidence=avg_confidence
                            )
                            
                            logger.debug(f"📡 Evento de detección enviado: {optimal_category.fruit_name} x{result.fruit_count}")
                        except Exception as e:
                            logger.debug(f"No se pudo enviar evento de detección: {e}")
                
                self.metrics_manager.metrics.frames_processed += 1
                self.metrics_manager.metrics.total_fruits_detected += result.fruit_count
                
        except Exception as e:
            logger.exception(f"❌ Error procesando detección: {e}")
            self.metrics_manager.metrics.error_count += 1
    
    def _map_class_name_to_category(self, class_name: str) -> FruitCategory:
        """Mapea el nombre de clase del modelo YOLOv8 a FruitCategory."""
        class_name_lower = class_name.lower().strip()
        
        # Mapeo directo y variantes comunes
        category_map = {
            'apple': FruitCategory.APPLE,
            'manzana': FruitCategory.APPLE,
            'pear': FruitCategory.PEAR,
            'pera': FruitCategory.PEAR,
            'lemon': FruitCategory.LEMON,
            'limon': FruitCategory.LEMON,
            'limón': FruitCategory.LEMON,
        }
        
        # Buscar coincidencia exacta
        if class_name_lower in category_map:
            return category_map[class_name_lower]
        
        # Buscar coincidencia parcial
        for key, category in category_map.items():
            if key in class_name_lower or class_name_lower in key:
                return category
        
        # Si no hay coincidencia, retornar UNKNOWN
        logger.warning(f"⚠️ Clase desconocida detectada por IA: '{class_name}' - marcada como UNKNOWN")
        return FruitCategory.UNKNOWN
    
    async def _analyze_fruit_categories(self, result) -> List[FruitCategory]:
        """Analiza y categoriza las frutas detectadas usando las clases reales de la IA."""
        if not result or not result.detections:
            logger.warning("⚠️ No hay detecciones en el resultado de la IA")
            return []
        
        categories = []
        detections_by_class = {}
        
        # Procesar cada detección real de la IA
        for detection in result.detections:
            # Mapear el class_name de YOLOv8 a nuestra FruitCategory
            category = self._map_class_name_to_category(detection.class_name)
            
            if category != FruitCategory.UNKNOWN:
                categories.append(category)
                
                # Agrupar por clase para logging detallado
                if category not in detections_by_class:
                    detections_by_class[category] = []
                detections_by_class[category].append({
                    'confidence': detection.confidence,
                    'bbox': detection.bbox,
                    'class_name': detection.class_name
                })
        
        # Log detallado de lo que se detectó
        if categories:
            summary = {cat: len([c for c in categories if c == cat]) for cat in set(categories)}
            logger.info(f"🎯 IA detectó: {', '.join([f'{count} {cat.emoji} {cat.fruit_name}(s)' for cat, count in summary.items()])}")
            
            # Log de confianza promedio por categoría
            for category, detections in detections_by_class.items():
                avg_conf = sum(d['confidence'] for d in detections) / len(detections)
                logger.debug(f"   {category.emoji} Confianza promedio: {avg_conf:.2%}")
        else:
            logger.warning("⚠️ No se detectaron frutas válidas (todas UNKNOWN)")
        
        return categories
    
    def _select_optimal_category(self, categories: List[FruitCategory]) -> FruitCategory:
        """
        Selecciona la categoría óptima para etiquetado.
        
        Estrategia: Selecciona la categoría más frecuente en las detecciones.
        Si hay empate, prioriza en orden: APPLE > PEAR > LEMON
        """
        if not categories:
            logger.warning("⚠️ No hay categorías para seleccionar")
            return FruitCategory.UNKNOWN
        
        # Contar frecuencias
        category_counts = Counter(categories)
        
        # Obtener la categoría más común
        most_common_count = category_counts.most_common(1)[0][1]
        
        # Si hay empate, aplicar prioridad
        tied_categories = [cat for cat, count in category_counts.items() if count == most_common_count]
        
        if len(tied_categories) > 1:
            # Orden de prioridad para desempate
            priority_order = [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]
            for priority_cat in priority_order:
                if priority_cat in tied_categories:
                    logger.info(f"✨ Categoría seleccionada: {priority_cat.emoji} {priority_cat.fruit_name} "
                              f"(empate resuelto por prioridad, {most_common_count} detección/es)")
                    return priority_cat
        
        # Sin empate, retornar la más común
        most_common = category_counts.most_common(1)[0][0]
        total = len(categories)
        percentage = (most_common_count / total) * 100
        
        logger.info(f"✨ Categoría seleccionada: {most_common.emoji} {most_common.fruit_name} "
                   f"({most_common_count}/{total} detecciones, {percentage:.1f}%)")
        
        return most_common
    
    async def _execute_labeling(self, category: FruitCategory, result):
        """Ejecuta el etiquetado ultra con motor DC."""
        try:
            if category == FruitCategory.UNKNOWN:
                return
            
            # 1. Activar grupo correcto
            if self.motor_controller:
                success = await self.motor_controller.activate_labeler_group(category)
                if not success:
                    logger.error(f"❌ Fallo activando grupo {category.emoji}")
                    return
                
                self.active_group_id = category.labeler_group_id
                self.metrics_manager.metrics.labeler_switch_count += 1
            
            # 2. Activar etiquetadoras del grupo
            if self.labeler_manager:
                duration = 2.0 + (result.fruit_count * 0.3)
                success = await self.labeler_manager.activate_group(
                    category.labeler_group_id, 
                    duration
                )
                
                if success:
                    self.metrics_manager.metrics.total_labels_applied += result.fruit_count
                    logger.info(f"✅ Etiquetado completado: {category.emoji} x{result.fruit_count}")
                    
        except Exception as e:
            logger.exception(f"❌ Error en etiquetado: {e}")
    
    async def _execute_classification(self, category: FruitCategory, result):
        """Ejecuta clasificación con desviadores."""
        try:
            if not self.diverter_controller or not self.diverter_controller.is_initialized:
                return
            
            # Calcular timing
            belt_config = self.config.get("conveyor_belt_settings", {})
            diverter_config = self.config.get("diverter_settings", {})
            
            belt_speed = belt_config.get("belt_speed_mps", 0.5)
            distance = diverter_config.get("distance_labeler_to_diverter_m", 1.0)
            servo_response = diverter_config.get("servo_response_time_s", 0.3)
            
            delay = max(0.1, (distance / belt_speed) - servo_response)
            
            # Ejecutar clasificación
            success = await self.diverter_controller.classify_fruit(category, delay)
            
            if success:
                logger.info(f"📦 Clasificación exitosa: {category.emoji}")
            
        except Exception as e:
            logger.error(f"❌ Error en clasificación: {e}")
    
    async def _monitoring_loop(self):
        """Bucle de monitoreo del sistema."""
        logger.info("📊 Bucle de monitoreo iniciado")
        
        while True:
            try:
                if not self._running.is_set():
                    await asyncio.sleep(0.5)
                    continue
                
                # Actualizar métricas
                self.metrics_manager.update_uptime()
                self.metrics_manager.metrics.oee_percentage = self.metrics_manager.calculate_oee()
                
                # Guardar en base de datos
                await self.db_manager.save_metrics(self.metrics_manager.metrics)
                
                # Broadcast a WebSockets
                if self.api_factory and self.api_factory.websocket_connections:
                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "metrics": self.metrics_manager.get_metrics_snapshot()
                    }
                    await self.api_factory.broadcast_to_websockets(data)
                
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")
                await asyncio.sleep(10)
    
    async def _optimization_loop(self):
        """Bucle de optimización del sistema."""
        logger.info("🔮 Bucle de optimización iniciado")
        
        while True:
            try:
                if not self._running.is_set():
                    await asyncio.sleep(1)
                    continue
                
                # Ejecutar optimización
                metrics_data = self.metrics_manager.get_metrics_snapshot()
                result = await self.optimizer.optimize(metrics_data['system'])
                
                if result.confidence > 0.7:
                    logger.info(f"🚀 Optimización aplicada: {result.improvements}")
                
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en optimización: {e}")
                await asyncio.sleep(60)
    
    async def _learning_loop(self):
        """Bucle de aprendizaje automático."""
        logger.info("🧠 Bucle de aprendizaje iniciado")
        
        while True:
            try:
                if not self._running.is_set():
                    await asyncio.sleep(1)
                    continue
                
                # Recopilar datos de aprendizaje
                learning_sample = {
                    'timestamp': datetime.now(),
                    'throughput': self.metrics_manager.metrics.throughput_items_per_minute,
                    'efficiency': self.metrics_manager.metrics.efficiency_score,
                    'active_group': self.active_group_id
                }
                
                self.prediction_engine.update_model(learning_sample)
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error en aprendizaje: {e}")
                await asyncio.sleep(120)
    
    # ==================== CONTROL DE PRODUCCIÓN ====================
    
    async def start_production(self):
        """Inicia la producción."""
        logger.info("▶️ Iniciando producción...")
        
        if self.belt_controller:
            await self.belt_controller.start_belt()
        
        self._set_state(SystemState.RUNNING)
        self._running.set()
        
        self.metrics_manager.send_alert(AlertLevel.INFO, "Producción", "Iniciada")
    
    async def stop_production(self):
        """Detiene la producción."""
        logger.info("⏸️ Deteniendo producción...")
        
        if self.belt_controller:
            await self.belt_controller.stop_belt()
        
        self._running.clear()
        self._set_state(SystemState.IDLE)
        
        self.metrics_manager.send_alert(AlertLevel.INFO, "Producción", "Detenida")
    
    async def emergency_stop(self):
        """Parada de emergencia."""
        logger.critical("🚨 PARADA DE EMERGENCIA")
        
        self._emergency_stop.set()
        self._set_state(SystemState.EMERGENCY_STOP)
        
        # Detener componentes
        if self.belt_controller:
            await self.belt_controller.emergency_stop()
        
        if self.labeler_manager:
            await self.labeler_manager.emergency_stop_all()
        
        if self.laser_stepper:
            await self.laser_stepper.emergency_stop()
        
        if self.diverter_controller:
            await self.diverter_controller.emergency_stop()
        
        self.metrics_manager.send_alert(
            AlertLevel.CRITICAL, "Sistema", "PARADA DE EMERGENCIA"
        )
    
    # ==================== APAGADO ====================
    
    async def shutdown(self):
        """Apaga el sistema."""
        if self._system_state == SystemState.SHUTTING_DOWN:
            return
        
        logger.info("🛑 Iniciando apagado del sistema...")
        self._set_state(SystemState.SHUTTING_DOWN)
        
        try:
            # Detener bucle principal
            self._running.clear()
            
            # Cancelar tareas
            for task in self._tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Apagar componentes
            if self.motor_controller:
                await self.motor_controller.emergency_stop()
                await self.motor_controller.cleanup()
            
            if self.labeler_manager:
                await self.labeler_manager.cleanup_all()
            
            if self.diverter_controller:
                await self.diverter_controller.cleanup()
            
            if self.trigger_sensor:
                self.trigger_sensor.shutdown()
            
            if self.belt_controller:
                await self.belt_controller.stop_belt()
                await self.belt_controller.cleanup()
            
            if self.ai_detector:
                await self.ai_detector.shutdown()
            
            if self.camera:
                self.camera.shutdown()
            
            if self.laser_stepper:
                await self.laser_stepper.cleanup()
            
            # Cerrar base de datos
            self.db_manager.close()
            
            self._set_state(SystemState.OFFLINE)
            logger.info("✅ Sistema apagado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error durante apagado: {e}")

# ==================== PUNTO DE ENTRADA ====================

async def run_prototype_mode():
    """Ejecuta el sistema en modo PROTOTIPO."""
    classifier = None
    services = {}
    
    try:
        logger.info("=" * 70)
        logger.info("🎯 MODO PROTOTIPO - Sistema de Clasificación con IA")
        logger.info("=" * 70)
        logger.info("   Hardware:")
        logger.info("   - 1 Etiquetadora Solenoide (Pin 26)")
        logger.info("   - 3 Servomotores MG995 (Clasificación)")
        logger.info("     • Manzanas: Pin 5")
        logger.info("     • Peras: Pin 6")
        logger.info("     • Limones: Pin 7")
        logger.info("   - IA YOLOv8 para detección")
        logger.info("   - Sensor MH Flying Fish (Pin 4)")
        logger.info("=" * 70)
        
        # Iniciar servicios auxiliares (backend solamente - frontend opcional)
        logger.info("📡 Iniciando servicios auxiliares...")
        services = await check_and_start_services(start_frontend=False)
        
        # Importar sistema de prototipo
        from Prototipo_Clasificador.smart_classifier_system import SmartFruitClassifier
        
        # Crear y ejecutar sistema de prototipo
        classifier = SmartFruitClassifier()
        
        # Configurar señales
        def signal_handler(sig, frame):
            logger.info("\n⚡ Señal de interrupción recibida")
            asyncio.create_task(classifier.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicializar
        if not await classifier.initialize():
            logger.error("❌ Error en inicialización del prototipo")
            return 1
        
        # Iniciar producción
        await classifier.start_production()
        
        logger.info("")
        logger.info("🌐 === URLS DEL SISTEMA PROTOTIPO ===")
        if "backend" in services:
            logger.info("   📊 Dashboard Backend: http://localhost:8001")
        if "frontend" in services:
            logger.info("   🎨 Interfaz Frontend: http://localhost:3000")
        logger.info("🌐 ====================================")
        logger.info("")
        logger.info("✅ Sistema PROTOTIPO funcionando - Presiona Ctrl+C para detener")
        logger.info("")
        
        # Mantener funcionando
        while classifier.running:
            await asyncio.sleep(1)
            
            # Mostrar estadísticas cada 30 segundos
            if int(time.time()) % 30 == 0:
                status = classifier.get_status()
                logger.info(
                    f"📊 Detectadas: {status['stats']['detections_total']} | "
                    f"Etiquetadas: {status['stats']['labeled_total']} | "
                    f"Clasificadas: {status['stats']['classified_total']}"
                )
        
        await classifier.shutdown()
        return 0
        
    except Exception as e:
        logger.exception(f"❌ Error en modo prototipo: {e}")
        return 1
    finally:
        if services:
            logger.info("🧹 Limpiando servicios auxiliares...")
            await cleanup_services(services)

def select_operation_mode() -> str:
    """Selector interactivo de modo de operación."""
    print("\n" + "=" * 70)
    print("🏭 VISIFRUIT - SISTEMA DE ETIQUETADO INDUSTRIAL")
    print("=" * 70)
    print("\nSelecciona el modo de operación:\n")
    print("  [1] 🏭 MODO PROFESIONAL")
    print("      - 6 etiquetadoras automáticas (2 por categoría)")
    print("      - Motor DC L298N para posicionamiento")
    print("      - 2 desviadores industriales (Servos MG995)")
    print("      - IA YOLOv8 optimizada (dual-worker)")
    print("")
    print("  [2] 🎯 MODO PROTOTIPO")
    print("      - 1 etiquetadora DRV8825 + Motor NEMA 17")
    print("      - 3 servomotores MG995 para clasificación")
    print("      - IA YOLOv8 optimizada (dual-worker)")
    print("")
    print("  [3] 🚪 SALIR")
    print("=" * 70)
    
    while True:
        try:
            choice = input("\n👉 Ingresa tu opción (1, 2 o 3): ").strip()
            
            if choice == "1":
                print("\n✅ Modo PROFESIONAL seleccionado")
                return "professional"
            elif choice == "2":
                print("\n✅ Modo PROTOTIPO seleccionado")
                return "prototype"
            elif choice == "3":
                print("\n👋 Saliendo del sistema...")
                return "exit"
            else:
                print("❌ Opción inválida. Por favor, ingresa 1, 2 o 3.")
        except (EOFError, KeyboardInterrupt):
            print("\n\n⚡ Interrupción detectada. Saliendo...")
            return "exit"

async def main():
    """Punto de entrada principal con selección de modo y auto-inicio de servicios."""
    
    # Detectar modo de operación
    mode = os.getenv("VISIFRUIT_MODE", "interactive").lower()
    
    # Selector interactivo (por defecto)
    if mode == "interactive":
        mode = select_operation_mode()
        if mode == "exit":
            return 0
    
    # Auto-detectar basándose en la existencia de configuración
    elif mode == "auto":
        prototype_config = Path("Prototipo_Clasificador/Config_Prototipo.json")
        professional_config = Path("Config_Etiquetadora.json")
        
        if prototype_config.exists() and not professional_config.exists():
            mode = "prototype"
            logger.info("🔍 Auto-detección: Modo PROTOTIPO")
        else:
            mode = "professional"
            logger.info("🔍 Auto-detección: Modo PROFESIONAL")
    
    # Ejecutar modo correspondiente
    if mode == "prototype" or mode == "prototipo":
        return await run_prototype_mode()
    
    # MODO PROFESIONAL (código original)
    system = None
    services = {}
    
    try:
        logger.info("=" * 70)
        logger.info("🏭 MODO PROFESIONAL - Sistema Industrial Completo")
        logger.info("=" * 70)
        logger.info("   Hardware:")
        logger.info("   - 6 Etiquetadoras Automáticas (2 por categoría)")
        logger.info("   - Motor DC Lineal para posicionamiento")
        logger.info("   - Sistema de desviadores industriales")
        logger.info("   - IA RT-DETR avanzada")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Iniciando sistema completo con frontend y backend")
        
        # Instancia única y limpieza preventiva
        ensure_single_instance()
        if os.getenv("AUTO_CLEAN_ON_START", "true").lower() == "true":
            logger.info("🧹 Limpieza preventiva...")
            preflight_cleanup()
        
        # Iniciar servicios auxiliares
        logger.info("📡 Iniciando servicios auxiliares...")
        services = await check_and_start_services()
        
        # Crear sistema principal
        config_file = "Config_Etiquetadora.json"
        system = UltraIndustrialFruitLabelingSystem(config_file)
        
        # Configurar señales
        loop = asyncio.get_event_loop()
        
        def signal_handler():
            logger.info("📡 Señal de apagado recibida")
            if system:
                loop.create_task(system.shutdown())
        
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        
        # Inicializar sistema principal
        logger.info("🔧 Inicializando sistema principal...")
        if await system.initialize():
            logger.info("✅ Sistema inicializado correctamente")
            logger.info("")
            logger.info("🌐 === URLS DEL SISTEMA COMPLETO ===")
            logger.info("   🏷️ Sistema Principal: http://localhost:8000")
            if "backend" in services:
                logger.info("   📊 Dashboard Backend: http://localhost:8001")
            if "frontend" in services:
                logger.info("   🎨 Interfaz Frontend: http://localhost:3000")
            logger.info("🌐 ===================================")
            logger.info("")
            logger.info("🚀 Sistema ejecutándose - Presiona Ctrl+C para detener")
            
            # Mantener funcionando
            while system._system_state != SystemState.OFFLINE:
                await asyncio.sleep(1)
        else:
            logger.critical("❌ Fallo al inicializar sistema")
            return 1
        
    except KeyboardInterrupt:
        logger.info("⚡ Interrupción recibida - Apagando...")
    except Exception as e:
        logger.exception(f"❌ Error crítico: {e}")
        return 1
    finally:
        if system:
            logger.info("🛑 Apagando sistema principal...")
            await system.shutdown()
        
        if services:
            logger.info("🧹 Limpiando servicios auxiliares...")
            await cleanup_services(services)
        
        logger.info("✅ Sistema terminado correctamente")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
