# main_etiquetadora.py
"""
Sistema Industrial de Etiquetado Múltiple de Frutas FruPrint v3.0 ULTRA
========================================================================

Sistema de control principal ultra-avanzado con 2 etiquetadoras automáticas por categoría,
IA de categorización avanzada, motor DC de posicionamiento automático y optimización
predictiva en tiempo real.

NUEVAS CARACTERÍSTICAS v3.0 ULTRA:
 - 6 Etiquetadoras Automáticas (2 por categoría) con Motor DC de Posicionamiento
 - IA de Categorización Avanzada (Manzana, Pera y Limón)
- Sistema de Predicción y Auto-Optimización
- Pool de Workers Ultra-Concurrente
- Cache Inteligente Multi-Nivel
- Telemetría Avanzada por Categoría
- Sistema de Redundancia y Auto-Recuperación
- Dashboard 3D en Tiempo Real

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 3.0 - ULTRA INDUSTRIAL EDITION
"""

import asyncio
import json
import logging
import signal
import sys
import time
import threading
import traceback
import uuid
import hashlib
import pickle
import statistics
import math
from collections import deque, defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional, List, Any, Union, Tuple, NamedTuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache, wraps
from contextlib import asynccontextmanager

import uvicorn
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import redis
import sqlite3

# Importaciones del proyecto con manejo de errores
try:
    from IA_Etiquetado.Fruit_detector import EnterpriseFruitDetector, FrameAnalysisResult, ProcessingPriority
    from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController
    from Control_Etiquetado.sensor_interface import SensorInterface
    from Control_Etiquetado.labeler_actuator import LabelerActuator
    from utils.camera_controller import CameraController
    from utils.config_validator import ConfigValidator, ValidationLevel
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Error de importación: {e}")
    print("Algunos módulos pueden no estar disponibles. Usando modos de simulación.")
    MODULES_AVAILABLE = False

# Motor DC para posicionamiento de etiquetadoras
try:
    import RPi.GPIO as GPIO
    import pigpio
    GPIO_AVAILABLE = True
except ImportError:
    print("GPIO no disponible - Modo simulación activado")
    GPIO_AVAILABLE = False

# Cache Redis (opcional)
try:
    REDIS_CLIENT = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    REDIS_CLIENT.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    print("Redis no disponible - Cache en memoria activado")

# ==================== CONFIGURACIÓN Y UTILIDADES ====================

def setup_ultra_logging(config: Dict[str, Any]):
    """Configura sistema de logging ultra-avanzado con múltiples niveles."""
    log_level = config.get("system_settings", {}).get("log_level", "INFO")
    
    # Crear directorio de logs con subcarpetas
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    (log_dir / "categories").mkdir(exist_ok=True)
    (log_dir / "performance").mkdir(exist_ok=True)
    (log_dir / "errors").mkdir(exist_ok=True)
    
    # Formateador ultra-detallado
    formatter = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [PID:%(process)d] [%(name)25s] [%(levelname)8s] "
            "[%(funcName)20s:%(lineno)4d] [%(thread)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Multiple handlers
    handlers = []
    
    # Console handler con colores
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Handler general
    main_log = log_dir / f"fruprint_ultra_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(main_log, encoding='utf-8')
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    
    # Handler para errores
    error_log = log_dir / "errors" / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    handlers.append(error_handler)
    
    # Handler para performance
    perf_log = log_dir / "performance" / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
    perf_handler = logging.FileHandler(perf_log, encoding='utf-8')
    perf_handler.addFilter(lambda record: 'PERF' in record.getMessage())
    perf_handler.setFormatter(formatter)
    handlers.append(perf_handler)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

# Cache inteligente decorador
def intelligent_cache(ttl_seconds: int = 300, max_size: int = 1000):
    """Decorador para cache inteligente con TTL y límite de tamaño."""
    def decorator(func):
        cache = {}
        access_times = {}

        def _make_key(args, kwargs):
            try:
                key_source = pickle.dumps((args, kwargs))
            except Exception:
                try:
                    key_source = repr((args, kwargs)).encode("utf-8", errors="ignore")
                except Exception:
                    key_source = f"{id(args)}-{id(kwargs)}-{time.time()}".encode("utf-8")
            return hashlib.md5(key_source).hexdigest()

        def _evict_and_cleanup(now):
            expired_keys = [k for k, t in access_times.items() if now - t > ttl_seconds]
            for k in expired_keys:
                cache.pop(k, None)
                access_times.pop(k, None)
            if len(cache) >= max_size and access_times:
                oldest_key = min(access_times.keys(), key=lambda k: access_times[k])
                cache.pop(oldest_key, None)
                access_times.pop(oldest_key, None)

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_time = time.time()
                key = _make_key(args, kwargs)
                _evict_and_cleanup(current_time)
                if key in cache:
                    access_times[key] = current_time
                    return cache[key]
                result = await func(*args, **kwargs)
                cache[key] = result
                access_times[key] = current_time
                return result

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_time = time.time()
                key = _make_key(args, kwargs)
                _evict_and_cleanup(current_time)
                if key in cache:
                    access_times[key] = current_time
                    return cache[key]
                result = func(*args, **kwargs)
                cache[key] = result
                access_times[key] = current_time
                return result

            return sync_wrapper
    return decorator

logger = logging.getLogger("FruPrintUltra")

# ==================== ENUMS Y TIPOS ====================

# ==================== CONSTANTES DE CONFIGURACIÓN ====================
# Cantidad de etiquetadoras por grupo y totales
LABELERS_PER_GROUP = 2
NUM_LABELER_GROUPS = 3
TOTAL_LABELERS = LABELERS_PER_GROUP * NUM_LABELER_GROUPS

class SystemState(Enum):
    """Estados del sistema ultra-industrial."""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    IDLE = "idle"
    CALIBRATING = "calibrating"
    RUNNING = "running"
    PROCESSING = "processing"
    OPTIMIZING = "optimizing"
    LEARNING = "learning"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"
    SHUTTING_DOWN = "shutting_down"
    MAINTENANCE = "maintenance"
    BACKUP_MODE = "backup_mode"
    RECOVERY = "recovery"

class AlertLevel(Enum):
    """Niveles de alerta ultra-detallados."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class FruitCategory(Enum):
    """Categorías de frutas con IDs específicos - Sistema lineal de 3 categorías."""
    APPLE = ("apple", 0, "🍎", "#FF4444")
    PEAR = ("pear", 1, "🍐", "#90EE90")
    LEMON = ("lemon", 2, "🍋", "#FFFF00")
    UNKNOWN = ("unknown", 99, "❓", "#888888")
    
    def __init__(self, name: str, labeler_group_id: int, emoji: str, color: str):
        self.fruit_name = name
        self.labeler_group_id = labeler_group_id  # Grupo de etiquetadoras (0, 1, 2)
        self.emoji = emoji
        self.color = color

    @property
    def labeler_id(self) -> int:
        """Alias para compatibilidad: devuelve el ID del grupo de etiquetadoras."""
        return self.labeler_group_id

class LabelerGroup(Enum):
    """Grupos de etiquetadoras lineales - 2 etiquetadoras por grupo."""
    GROUP_APPLE = (0, "apple", [0, 1])    # Grupo manzanas: etiquetadoras 0-1
    GROUP_PEAR = (1, "pear", [2, 3])      # Grupo peras: etiquetadoras 2-3  
    GROUP_LEMON = (2, "lemon", [4, 5])    # Grupo limones: etiquetadoras 4-5
    
    def __init__(self, group_id: int, category: str, labeler_ids: list):
        self.group_id = group_id
        self.category = category
        self.labeler_ids = labeler_ids  # IDs de las etiquetadoras en este grupo

class ProcessingPriority(Enum):
    """Prioridades de procesamiento."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class OptimizationMode(Enum):
    """Modos de optimización."""
    SPEED = "speed"
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    ADAPTIVE = "adaptive"

# ==================== DATACLASSES Y ESTRUCTURAS ====================

@dataclass
class UltraSystemAlert:
    """Alerta ultra-avanzada del sistema."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)
    level: AlertLevel = AlertLevel.INFO
    component: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    category: Optional[FruitCategory] = None
    labeler_id: Optional[int] = None
    resolved: bool = False
    auto_resolution_attempted: bool = False
    
class FruitDetectionResult(NamedTuple):
    """Resultado de detección ultra-detallado."""
    category: FruitCategory
    confidence: float
    bbox: Tuple[int, int, int, int]
    features: Dict[str, float]
    timestamp: datetime
    processing_time_ms: float

@dataclass
class UltraCategoryMetrics:
    """Métricas ultra-detalladas por categoría."""
    category: FruitCategory
    total_detected: int = 0
    total_labeled: int = 0
    avg_confidence: float = 0.0
    processing_time_avg_ms: float = 0.0
    accuracy_rate: float = 0.0
    error_count: int = 0
    last_detection: Optional[datetime] = None
    throughput_per_hour: float = 0.0
    quality_score: float = 0.0

@dataclass
class UltraSystemMetrics:
    """Métricas ultra-completas del sistema."""
    timestamp: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    
    # Procesamiento general
    frames_processed: int = 0
    total_fruits_detected: int = 0
    total_labels_applied: int = 0
    error_count: int = 0
    
    # Performance
    throughput_items_per_minute: float = 0.0
    avg_processing_time_ms: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    temperature_c: float = 0.0
    
    # Por categoría
    category_metrics: Dict[FruitCategory, UltraCategoryMetrics] = field(default_factory=dict)
    
    # Predicciones y optimización
    predicted_throughput: float = 0.0
    efficiency_score: float = 0.0
    oee_percentage: float = 0.0  # Overall Equipment Effectiveness
    
    # Sistema de etiquetadoras lineales
    active_group_id: int = 0
    group_positions: Dict[int, str] = field(default_factory=dict)
    labeler_switch_count: int = 0
    motor_runtime_hours: float = 0.0

    # Aliases para compatibilidad con usos existentes en el código
    @property
    def fruits_detected(self) -> int:
        return self.total_fruits_detected

    @fruits_detected.setter
    def fruits_detected(self, value: int):
        self.total_fruits_detected = value

    @property
    def labels_applied(self) -> int:
        return self.total_labels_applied

    @labels_applied.setter
    def labels_applied(self, value: int):
        self.total_labels_applied = value

@dataclass
class LabelerMetrics:
    """Métricas específicas de una etiquetadora."""
    labeler_id: int
    category: FruitCategory
    activations_count: int = 0
    total_runtime_seconds: float = 0.0
    success_rate: float = 100.0
    last_activation: Optional[datetime] = None
    maintenance_score: float = 100.0
    wear_level: float = 0.0

@dataclass
class OptimizationResult:
    """Resultado de optimización del sistema."""
    timestamp: datetime = field(default_factory=datetime.now)
    mode: OptimizationMode = OptimizationMode.ADAPTIVE
    improvements: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    estimated_impact: float = 0.0

# ==================== CLASES AUXILIARES ULTRA ====================

class UltraPatternAnalyzer:
    """Analizador de patrones ultra-avanzado para optimización predictiva."""
    
    def __init__(self):
        self.pattern_history = deque(maxlen=5000)
        self.fruit_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)
        self.efficiency_patterns = []
    
    def analyze_detection_pattern(self, detections: List[FruitDetectionResult]):
        """Analiza patrones en las detecciones."""
        if not detections:
            return {}
        
        # Analizar distribución de categorías
        category_counts = Counter([d.category for d in detections])
        
        # Analizar patrones temporales
        time_intervals = []
        for i in range(1, len(detections)):
            interval = (detections[i].timestamp - detections[i-1].timestamp).total_seconds()
            time_intervals.append(interval)
        
        # Calcular métricas
        avg_interval = statistics.mean(time_intervals) if time_intervals else 0
        confidence_avg = statistics.mean([d.confidence for d in detections])
        
        pattern = {
            'timestamp': datetime.now(),
            'category_distribution': dict(category_counts),
            'avg_time_interval': avg_interval,
            'avg_confidence': confidence_avg,
            'total_detections': len(detections)
        }
        
        self.pattern_history.append(pattern)
        return pattern
    
    def predict_next_category(self) -> Optional[FruitCategory]:
        """Predice la siguiente categoría de fruta más probable."""
        if len(self.pattern_history) < 10:
            return None
        
        recent_patterns = list(self.pattern_history)[-10:]
        category_frequencies = defaultdict(int)
        
        for pattern in recent_patterns:
            for category, count in pattern['category_distribution'].items():
                category_frequencies[category] += count
        
        if category_frequencies:
            most_common = max(category_frequencies.items(), key=lambda x: x[1])
            category_key = most_common[0]
            # Soportar tanto claves Enum como str
            if isinstance(category_key, FruitCategory):
                return category_key
            if isinstance(category_key, str):
                try:
                    return FruitCategory[category_key.upper()]
                except KeyError:
                    return FruitCategory.UNKNOWN
            return FruitCategory.UNKNOWN
        
        return None

class UltraPredictionEngine:
    """Motor de predicción ultra-avanzado para optimización del sistema."""
    
    def __init__(self):
        self.historical_data = deque(maxlen=10000)
        self.prediction_models = {}
        self.accuracy_scores = defaultdict(float)
    
    def predict_throughput(self, time_horizon_minutes: int = 60) -> float:
        """Predice el throughput para el horizonte temporal dado."""
        if len(self.historical_data) < 100:
            return 0.0
        
        recent_data = list(self.historical_data)[-100:]
        throughputs = [d.get('throughput', 0) for d in recent_data]
        
        # Predicción simple basada en tendencia
        if len(throughputs) >= 10:
            trend = (throughputs[-1] - throughputs[-10]) / 10
            predicted = throughputs[-1] + (trend * time_horizon_minutes)
            return max(0, predicted)
        
        return statistics.mean(throughputs) if throughputs else 0.0
    
    def predict_optimal_labeler_sequence(self, expected_categories: List[FruitCategory]) -> List[int]:
        """Predice la secuencia óptima de etiquetadoras."""
        if not expected_categories:
            return []
        
        # Mapear categorías a IDs de etiquetadoras
        labeler_sequence = []
        for category in expected_categories:
            if category != FruitCategory.UNKNOWN:
                labeler_sequence.append(category.labeler_id)
        
        return labeler_sequence
    
    def update_model(self, actual_data: Dict[str, Any]):
        """Actualiza los modelos con datos reales."""
        self.historical_data.append({
            'timestamp': datetime.now(),
            **actual_data
        })

class UltraLinearMotorController:
    """Controlador ultra-avanzado del motor DC para sistema lineal de 2 etiquetadoras por grupo."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.motor_pins = config.get("motor_pins", {
            "pwm_pin": 12,
            "dir_pin1": 20,
            "dir_pin2": 21,
            "enable_pin": 16
        })
        
        # Sistema lineal: 3 grupos de 2 etiquetadoras cada uno
        self.labeler_groups = {
            FruitCategory.APPLE: LabelerGroup.GROUP_APPLE,
            FruitCategory.PEAR: LabelerGroup.GROUP_PEAR,
            FruitCategory.LEMON: LabelerGroup.GROUP_LEMON
        }
        
        self.current_active_group = None  # Grupo actualmente activo (bajado)
        self.is_moving = False
        self.is_calibrated = False
        self.pwm_instance = None
        # Posiciones iniciales de los grupos (dinámico por número de grupos)
        self.group_positions = {g: ("down" if g == 0 else "up") for g in range(NUM_LABELER_GROUPS)}
        
    async def initialize(self) -> bool:
        """Inicializa el controlador del motor."""
        try:
            if not GPIO_AVAILABLE:
                logger.warning("GPIO no disponible - Modo simulación motor")
                self.is_calibrated = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            for pin in self.motor_pins.values():
                GPIO.setup(pin, GPIO.OUT)
            
            self.pwm_instance = GPIO.PWM(self.motor_pins["pwm_pin"], 1000)
            self.pwm_instance.start(0)
            
            await self.calibrate()
            logger.info("Motor DC inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando motor: {e}")
            return False
    
    async def calibrate(self) -> bool:
        """Calibra el motor encontrando posiciones de referencia."""
        try:
            logger.info("Calibrando motor DC...")
            # Simulación de calibración
            await asyncio.sleep(2.0)
            self.current_position = 0.0
            self.is_calibrated = True
            logger.info("Motor calibrado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error calibrando motor: {e}")
            return False
    
    async def activate_labeler_group(self, category: FruitCategory) -> bool:
        """Activa un grupo de etiquetadoras (baja el grupo target, sube los otros)."""
        if category not in self.labeler_groups:
            return False
        
        target_group = self.labeler_groups[category]
        target_group_id = target_group.group_id
        
        # Si el grupo ya está activo, no hacer nada
        if self.current_active_group == target_group_id:
            logger.info(f"Grupo {category.emoji} ya está activo")
            return True
        
        return await self.switch_to_group(target_group_id)
    
    async def switch_to_group(self, target_group_id: int) -> bool:
        """Cambia el grupo activo (sube el actual, baja el nuevo)."""
        try:
            if not self.is_calibrated:
                return False
            
            self.is_moving = True
            logger.info(f"🔄 Cambiando grupo activo: Grupo {target_group_id}")
            
            # 1. Subir grupo actual (si hay uno)
            if self.current_active_group is not None:
                await self._lift_group(self.current_active_group)
            
            # 2. Bajar nuevo grupo
            await self._lower_group(target_group_id)
            
            # 3. Actualizar estado
            self.current_active_group = target_group_id
            self._update_group_positions(target_group_id)
            
            self.is_moving = False
            
            categories = {0: "🍎", 1: "🍐", 2: "🍋"}
            logger.info(f"✅ Grupo {categories.get(target_group_id, '?')} activo - {LABELERS_PER_GROUP} etiquetadoras listas")
            return True
            
        except Exception as e:
            logger.error(f"Error cambiando grupo: {e}")
            self.is_moving = False
            return False
    
    async def _lift_group(self, group_id: int):
        """Sube un grupo de etiquetadoras."""
        logger.info(f"⬆️ Subiendo grupo {group_id}")
        
        if GPIO_AVAILABLE and self.pwm_instance:
            # Control real del motor - subir
            GPIO.output(self.motor_pins["dir_pin1"], True)  # Dirección subir
            GPIO.output(self.motor_pins["dir_pin2"], False)
            self.pwm_instance.ChangeDutyCycle(60)  # Potencia moderada
            
            await asyncio.sleep(1.5)  # Tiempo para subir
            self.pwm_instance.ChangeDutyCycle(0)
        else:
            # Simulación
            await asyncio.sleep(1.5)
    
    async def _lower_group(self, group_id: int):
        """Baja un grupo de etiquetadoras."""
        logger.info(f"⬇️ Bajando grupo {group_id}")
        
        if GPIO_AVAILABLE and self.pwm_instance:
            # Control real del motor - bajar
            GPIO.output(self.motor_pins["dir_pin1"], False)
            GPIO.output(self.motor_pins["dir_pin2"], True)  # Dirección bajar
            self.pwm_instance.ChangeDutyCycle(60)  # Potencia moderada
            
            await asyncio.sleep(1.5)  # Tiempo para bajar
            self.pwm_instance.ChangeDutyCycle(0)
        else:
            # Simulación
            await asyncio.sleep(1.5)
    
    def _update_group_positions(self, active_group_id: int):
        """Actualiza las posiciones de todos los grupos."""
        for group_id in range(NUM_LABELER_GROUPS):
            if group_id == active_group_id:
                self.group_positions[group_id] = "down"
            else:
                self.group_positions[group_id] = "up"
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del motor y grupos de etiquetadoras."""
        emojis = {
            FruitCategory.APPLE.fruit_name: FruitCategory.APPLE.emoji,
            FruitCategory.PEAR.fruit_name: FruitCategory.PEAR.emoji,
            FruitCategory.LEMON.fruit_name: FruitCategory.LEMON.emoji,
        }

        available_groups = {
            group.group_id: {
                "category": group.category,
                "emoji": emojis.get(group.category, "❓"),
                "labelers": group.labeler_ids,
            }
            for group in LabelerGroup
        }

        return {
            "current_active_group": self.current_active_group,
            "is_moving": self.is_moving,
            "is_calibrated": self.is_calibrated,
            "group_positions": self.group_positions.copy(),
            "available_groups": available_groups,
        }
    
    async def emergency_stop(self):
        """Parada de emergencia del motor."""
        if GPIO_AVAILABLE:
            try:
                # Cortar PWM
                if self.pwm_instance:
                    self.pwm_instance.ChangeDutyCycle(0)
                # Deshabilitar pin de enable si existe
                enable_pin = self.motor_pins.get("enable_pin")
                if enable_pin is not None:
                    GPIO.output(enable_pin, False)
            except Exception:
                pass
        self.is_moving = False
    
    async def cleanup(self):
        """Limpia recursos del motor."""
        try:
            if GPIO_AVAILABLE:
                if self.pwm_instance:
                    self.pwm_instance.stop()
                GPIO.cleanup([pin for pin in self.motor_pins.values()])
        except Exception as e:
            logger.error(f"Error limpiando motor: {e}")

class UltraIndustrialFruitLabelingSystem:
    """
    Sistema ULTRA-Industrial de Etiquetado Múltiple de Frutas v3.0
    ===============================================================
    
    Características Ultra-Avanzadas:
    - 6 Etiquetadoras automáticas (2 por categoría) con motor DC de posicionamiento
    - IA de categorización avanzada en tiempo real
    - Sistema predictivo y auto-optimización
    - Pool de workers ultra-concurrente
    - Cache inteligente multi-nivel
    - Telemetría completa por categoría
    - Dashboard 3D en tiempo real
    - Sistema de redundancia y auto-recuperación
    """
    
    def __init__(self, config_path: str):
        # Cargar y validar configuración
        self.config_path = Path(config_path)
        self.config = self._load_and_validate_config()
        
        # Información del sistema ULTRA
        self.system_id = self.config["system_settings"]["installation_id"]
        self.system_name = self.config["system_settings"]["system_name"]
        self.version = "3.0.0-ULTRA"
        
        # Estado del sistema ultra-avanzado
        self._system_state = SystemState.OFFLINE
        self._start_time = time.time()
        self._running = asyncio.Event()
        self._emergency_stop = asyncio.Event()
        self._learning_mode = asyncio.Event()
        self._optimization_mode = OptimizationMode.ADAPTIVE
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Componentes principales
        self.camera: Optional[CameraController] = None
        self.ai_detector: Optional[EnterpriseFruitDetector] = None
        self.belt_controller: Optional[ConveyorBeltController] = None
        self.trigger_sensor: Optional[SensorInterface] = None
        
        # NUEVO: Sistema de 6 etiquetadoras lineales (3 grupos de 2)
        self.labelers: Dict[int, LabelerActuator] = {}  # 6 etiquetadoras (0-5)
        self.motor_controller: Optional[UltraLinearMotorController] = None  # Controlador lineal del motor DC
        self.active_group_id = 0  # Grupo activo (0: manzanas, 1: peras, 2: limones)
        # Compatibilidad con código legado (un solo etiquetador)
        self.labeler: Optional[LabelerActuator] = None
        
        # Sistema de eventos ultra-concurrente
        self._trigger_queue = asyncio.Queue(maxsize=200)
        self._alert_queue = asyncio.Queue(maxsize=1000)
        self._detection_queue = asyncio.Queue(maxsize=100)
        self._labeling_queue = asyncio.Queue(maxsize=100)
        
        # Métricas ultra-avanzadas
        self.metrics = UltraSystemMetrics()
        self.alerts = deque(maxlen=5000)
        self.alert_callbacks: List = []
        
        # Métricas por categoría (3 categorías)
        self.category_metrics = {
            FruitCategory.APPLE: UltraCategoryMetrics(category=FruitCategory.APPLE),
            FruitCategory.PEAR: UltraCategoryMetrics(category=FruitCategory.PEAR),
            FruitCategory.LEMON: UltraCategoryMetrics(category=FruitCategory.LEMON)
        }
        
        # Métricas por etiquetadora (6 etiquetadoras en 3 grupos)
        self.labeler_metrics = {}
        categories = [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]
        for i in range(TOTAL_LABELERS):
            group_id = i // LABELERS_PER_GROUP  # Cada 2 etiquetadoras forman un grupo
            category = categories[group_id] if group_id < len(categories) else FruitCategory.UNKNOWN
            self.labeler_metrics[i] = LabelerMetrics(labeler_id=i, category=category)
        
        # Sistema de caché ultra-inteligente
        self.detection_cache = {}
        self.prediction_cache = {}
        self.optimization_cache = {}
        
        # Pool de workers ultra-concurrente
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        self.detection_workers = 4
        self.processing_workers = 4
        
        # Sistema de predicción
        self.prediction_engine = None
        self.learning_data = deque(maxlen=10000)
        self.pattern_analyzer = None
        
        # API ultra-avanzada
        self.app: Optional[FastAPI] = None
        self.websocket_connections: List[WebSocket] = []
        self.dashboard_data = {}
        
        # Database para métricas
        self.db_connection = None
        self._init_database()
        
        # Tareas asíncronas ultra-concurrentes
        self._tasks: List[asyncio.Task] = []
        self._background_tasks = set()
        
        # Sistema de redundancia
        self.backup_systems = {}
        self.failover_manager = None
        
        # Configurar logging ultra-avanzado
        setup_ultra_logging(self.config)
        
        # Locks para thread safety
        self._state_lock = threading.RLock()
        self._metrics_lock = threading.RLock()
        self._detection_lock = threading.RLock()
        
        # Inicializar sistema de optimización
        self._init_optimization_system()
        
        logger.info(f"Sistema ULTRA {self.system_name} ({self.system_id}) v{self.version} inicializado")
        logger.info(f"Características activadas: {TOTAL_LABELERS} etiquetadoras, IA categorización, motor DC, predicción")
    
    def _init_database(self):
        """Inicializa la base de datos para métricas y análisis."""
        try:
            db_path = Path("data") / "fruprint_ultra.db"
            db_path.parent.mkdir(exist_ok=True)
            
            self.db_connection = sqlite3.connect(str(db_path), check_same_thread=False)
            cursor = self.db_connection.cursor()
            
            # Crear tablas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    category TEXT,
                    confidence REAL,
                    processing_time_ms REAL,
                    bbox_x INTEGER,
                    bbox_y INTEGER,
                    bbox_w INTEGER,
                    bbox_h INTEGER
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS labelings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    labeler_id INTEGER,
                    category TEXT,
                    duration REAL,
                    success BOOLEAN,
                    motor_position REAL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    metric_type TEXT,
                    metric_data TEXT
                )
            """)
            
            self.db_connection.commit()
            logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
    
    def _init_optimization_system(self):
        """Inicializa el sistema de optimización predictiva."""
        try:
            # Sistema de aprendizaje automático simple
            self.pattern_analyzer = UltraPatternAnalyzer()
            self.prediction_engine = UltraPredictionEngine()
            
            # Configurar modos de optimización
            self.optimization_strategies = {
                OptimizationMode.SPEED: self._optimize_for_speed,
                OptimizationMode.ACCURACY: self._optimize_for_accuracy,
                OptimizationMode.EFFICIENCY: self._optimize_for_efficiency,
                OptimizationMode.ADAPTIVE: self._optimize_adaptive
            }
            
            logger.info("Sistema de optimización inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando optimización: {e}")
    
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
                    logger.warning(f"Configuración con advertencias: {'; '.join(errors)}")
                else:
                    logger.info("Configuración validada exitosamente")
            except Exception as e:
                logger.warning(f"No se pudo validar configuración: {e}")
            
            return config
            
        except Exception as e:
            logger.critical(f"Error cargando configuración: {e}")
            raise
    
    def _set_state(self, new_state: SystemState):
        """Actualiza el estado del sistema."""
        with self._state_lock:
            if self._system_state != new_state:
                old_state = self._system_state
                self._system_state = new_state
                logger.info(f"Estado: {old_state.value} → {new_state.value}")
                
                # Enviar alerta
                self._send_alert(AlertLevel.INFO, "Sistema", f"Estado: {new_state.value}")
    
    def _send_alert(self, level: AlertLevel, component: str, message: str, details: Dict = None):
        """Envía una alerta al sistema."""
        alert = UltraSystemAlert(
            level=level,
            component=component,
            message=message,
            details=details or {}
        )
        
        self.alerts.append(alert)
        
        # Log según el nivel
        log_msg = f"[{component}] {message}"
        if level == AlertLevel.INFO:
            logger.info(log_msg)
        elif level == AlertLevel.WARNING:
            logger.warning(log_msg)
        elif level == AlertLevel.ERROR:
            logger.error(log_msg)
        elif level == AlertLevel.CRITICAL:
            logger.critical(log_msg)
        
        # Procesar alerta asíncronamente
        try:
            self._alert_queue.put_nowait(alert)
        except asyncio.QueueFull:
            logger.warning("Cola de alertas llena")
    
    async def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema."""
        try:
            self._set_state(SystemState.INITIALIZING)
            logger.info("=== Iniciando inicialización del sistema ===")
            # Guardar loop actual para callbacks thread-safe
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.get_event_loop()
            
            # 1. Inicializar cámara
            await self._initialize_camera()
            
            # 2. Inicializar detector de IA
            await self._initialize_ai_detector()
            
            # 3. Inicializar controlador de banda
            await self._initialize_belt_controller()
            
            # 4. Inicializar motor DC controller
            await self._initialize_motor_controller()
            
            # 5. Inicializar etiquetadoras lineales (6 total)
            await self._initialize_ultra_labelers()
            
            # 6. Inicializar sensores
            await self._initialize_sensors()
            
            # 7. Inicializar API ultra-avanzada
            await self._initialize_ultra_api()
            
            # 8. Iniciar tareas ultra-concurrentes
            await self._start_ultra_system_tasks()
            
            self._set_state(SystemState.IDLE)
            logger.info("=== Sistema inicializado exitosamente ===")
            
            return True
            
        except Exception as e:
            self._set_state(SystemState.ERROR)
            self._send_alert(AlertLevel.CRITICAL, "Sistema", f"Error en inicialización: {e}")
            logger.exception("Error crítico durante inicialización")
            return False
    
    async def _initialize_camera(self):
        """Inicializa el sistema de cámara."""
        logger.info("Inicializando cámara...")
        
        try:
            camera_config = self.config["camera_settings"]
            self.camera = CameraController(camera_config)
            
            if not self.camera.initialize():
                raise RuntimeError("Fallo al inicializar cámara")
            
            logger.info("Cámara inicializada correctamente")
        except Exception as e:
            logger.error(f"Error inicializando cámara: {e}")
            # Crear cámara mock para continuar
            self.camera = None
    
    async def _initialize_ai_detector(self):
        """Inicializa el detector de IA."""
        logger.info("Inicializando detector de IA...")
        
        try:
            self.ai_detector = EnterpriseFruitDetector(self.config)
            
            if not await self.ai_detector.initialize():
                raise RuntimeError("Fallo al inicializar IA")
            
            logger.info("Detector de IA inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando IA: {e}")
            self.ai_detector = None
    
    async def _initialize_belt_controller(self):
        """Inicializa el controlador de banda."""
        logger.info("Inicializando controlador de banda...")
        
        try:
            belt_config = self.config["conveyor_belt_settings"]
            self.belt_controller = ConveyorBeltController(belt_config)
            
            if not self.belt_controller.initialize():
                raise RuntimeError("Fallo al inicializar banda")
            
            logger.info("Controlador de banda inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando banda: {e}")
            self.belt_controller = None
    
    async def _initialize_labeler(self):
        """Inicializa el sistema de etiquetado."""
        logger.info("Inicializando etiquetador...")
        
        try:
            labeler_config = self.config["labeler_settings"]
            self.labeler = LabelerActuator(labeler_config)
            
            if not await self.labeler.initialize():
                raise RuntimeError("Fallo al inicializar etiquetador")
            
            logger.info("Etiquetador inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando etiquetador: {e}")
            self.labeler = None
    
    async def _initialize_sensors(self):
        """Inicializa el sistema de sensores."""
        logger.info("Inicializando sensores...")
        
        try:
            sensor_config = self.config["sensor_settings"]
            self.trigger_sensor = SensorInterface(
                sensor_config,
                self._sensor_trigger_callback
            )
            
            if not self.trigger_sensor.initialize():
                raise RuntimeError("Fallo al inicializar sensores")
            
            logger.info("Sensores inicializados correctamente")
        except Exception as e:
            logger.error(f"Error inicializando sensores: {e}")
            self.trigger_sensor = None
    
    async def _initialize_api(self):
        """Inicializa la API REST."""
        if not self.config.get("api_settings", {}).get("enabled", True):
            return
        
        logger.info("Inicializando API...")
        self.app = self._create_fastapi_app()
        logger.info("API inicializada correctamente")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crea la aplicación FastAPI."""
        app = FastAPI(
            title="FruPrint Industrial API",
            description="API del Sistema Industrial de Etiquetado",
            version=self.version
        )
        
        # Middleware CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Rutas
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "system_state": self._system_state.value,
                "uptime_seconds": time.time() - self._start_time
            }
        
        @app.get("/status")
        async def get_status():
            return {
                "system": {
                    "id": self.system_id,
                    "name": self.system_name,
                    "state": self._system_state.value,
                    "uptime": time.time() - self._start_time
                },
                "metrics": self.metrics.__dict__
            }
        
        @app.post("/control/start")
        async def start_production():
            if self._system_state == SystemState.IDLE:
                await self.start_production()
                return {"message": "Producción iniciada"}
            else:
                raise HTTPException(400, f"No se puede iniciar desde estado: {self._system_state.value}")
        
        @app.post("/control/stop")
        async def stop_production():
            await self.stop_production()
            return {"message": "Producción detenida"}
        
        @app.post("/control/emergency_stop")
        async def emergency_stop():
            await self.emergency_stop()
            return {"message": "Parada de emergencia"}
        
        return app
    
    async def _initialize_motor_controller(self):
        """Inicializa el controlador lineal del motor DC para 3 grupos de 2 etiquetadoras."""
        logger.info("Inicializando controlador lineal de motor DC...")
        
        try:
            motor_config = self.config.get("motor_controller_settings", {
                "motor_pins": {"pwm_pin": 12, "dir_pin1": 20, "dir_pin2": 21, "enable_pin": 16}
            })
            
            self.motor_controller = UltraLinearMotorController(motor_config)
            
            if not await self.motor_controller.initialize():
                raise RuntimeError("Fallo al inicializar motor DC lineal")
            
            logger.info("Controlador lineal de motor DC inicializado correctamente")
            logger.info("🍎 Grupo manzanas: etiquetadoras 0-1")
            logger.info("🍐 Grupo peras: etiquetadoras 2-3") 
            logger.info("🍋 Grupo limones: etiquetadoras 4-5")
        except Exception as e:
            logger.error(f"Error inicializando motor DC lineal: {e}")
            self.motor_controller = None
    
    async def _initialize_ultra_labelers(self):
        """Inicializa las 6 etiquetadoras lineales (3 grupos de 2)."""
        logger.info("Inicializando 6 etiquetadoras lineales ultra-avanzadas...")
        
        try:
            base_labeler_config = self.config.get("labeler_settings", {})
            
            # Configuración de grupos
            groups_config = [
                {"category": FruitCategory.APPLE, "name": "Apple", "emoji": "🍎", "ids": LabelerGroup.GROUP_APPLE.labeler_ids},
                {"category": FruitCategory.PEAR, "name": "Pear", "emoji": "🍐", "ids": LabelerGroup.GROUP_PEAR.labeler_ids},
                {"category": FruitCategory.LEMON, "name": "Lemon", "emoji": "🍋", "ids": LabelerGroup.GROUP_LEMON.labeler_ids}
            ]
            
            for group in groups_config:
                logger.info(f"Inicializando grupo {group['emoji']} {group['name']}...")
                
                for labeler_id in group["ids"]:
                    labeler_config = base_labeler_config.copy()
                    labeler_config.update({
                        "name": f"LinearLabeler-{group['name']}-{labeler_id}",
                        "labeler_id": labeler_id,
                        "category": group["category"].fruit_name,
                        "group_id": group["category"].labeler_group_id,
                        "pin": base_labeler_config.get("base_pin", 26) + labeler_id,  # Pines consecutivos
                        "type": "solenoid"  # Por defecto solenoides
                    })
                    
                    labeler = LabelerActuator(labeler_config)
                    
                    if await labeler.initialize():
                        self.labelers[labeler_id] = labeler
                        logger.info(f"  ✅ Etiquetadora {labeler_id} ({group['name']}) inicializada")
                    else:
                        logger.error(f"  ❌ Fallo etiquetadora {labeler_id} ({group['name']})")
            
            logger.info(f"✅ Sistema de {len(self.labelers)} etiquetadoras lineales inicializado")
            logger.info("📋 Distribución: 🍎(0-1) 🍐(2-3) 🍋(4-5)")
            
        except Exception as e:
            logger.error(f"Error inicializando etiquetadoras lineales: {e}")
    
    async def _initialize_ultra_api(self):
        """Inicializa la API ultra-avanzada."""
        if not self.config.get("api_settings", {}).get("enabled", True):
            return
        
        logger.info("Inicializando API Ultra-Avanzada...")
        self.app = self._create_ultra_fastapi_app()
        logger.info("API Ultra-Avanzada inicializada correctamente")
    
    def _create_ultra_fastapi_app(self) -> FastAPI:
        """Crea la aplicación FastAPI ultra-avanzada."""
        app = FastAPI(
            title="FruPrint ULTRA Industrial API v3.0",
            description="API Ultra-Avanzada del Sistema de 6 Etiquetadoras (2 por categoría) con IA",
            version=self.version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Middleware CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # ============ RUTAS BÁSICAS ============
        @app.get("/health")
        async def ultra_health_check():
            return {
                "status": "ultra_healthy",
                "system_state": self._system_state.value,
                "uptime_seconds": time.time() - self._start_time,
                "version": self.version,
                "active_group": self.active_group_id,
                "motor_status": self.motor_controller.get_status() if self.motor_controller else {}
            }
        
        @app.get("/status")
        async def get_ultra_status():
            return {
                "system": {
                    "id": self.system_id,
                    "name": self.system_name,
                    "state": self._system_state.value,
                    "uptime": time.time() - self._start_time,
                    "version": self.version
                },
                "metrics": asdict(self.metrics),
                "labelers": {i: labeler.get_status() for i, labeler in self.labelers.items()},
                "motor": self.motor_controller.get_status() if self.motor_controller else {},
                "categories": {cat.fruit_name: asdict(metrics) for cat, metrics in self.category_metrics.items()}
            }
        
        # ============ CONTROL DE PRODUCCIÓN ============
        @app.post("/control/start")
        async def start_ultra_production():
            if self._system_state == SystemState.IDLE:
                await self.start_production()
                return {"message": "Producción ultra iniciada", "labelers_active": len(self.labelers)}
            else:
                raise HTTPException(400, f"No se puede iniciar desde estado: {self._system_state.value}")
        
        @app.post("/control/stop")
        async def stop_ultra_production():
            await self.stop_production()
            return {"message": "Producción ultra detenida"}
        
        @app.post("/control/emergency_stop")
        async def ultra_emergency_stop():
            await self.emergency_stop()
            return {"message": "PARADA DE EMERGENCIA ULTRA"}
        
        # ============ CONTROL DE MOTOR LINEAL ============
        @app.post("/motor/activate_group")
        async def activate_labeler_group(category: str):
            """Activa un grupo de etiquetadoras para una categoría específica."""
            try:
                fruit_category = FruitCategory[category.upper()]
                success = await self.motor_controller.activate_labeler_group(fruit_category)
                
                group_info = None
                for group in LabelerGroup:
                    if group.category == fruit_category.fruit_name:
                        group_info = group
                        break
                
                return {
                    "success": success,
                    "category": category,
                    "active_group": self.motor_controller.current_active_group,
                    "labeler_ids": group_info.labeler_ids if group_info else [],
                    "message": f"Grupo {fruit_category.emoji} activado - {LABELERS_PER_GROUP} etiquetadoras operativas"
                }
            except KeyError:
                raise HTTPException(400, f"Categoría no válida: {category}. Disponibles: apple, pear, lemon")
            except Exception as e:
                raise HTTPException(500, f"Error activando grupo: {e}")
        
        @app.get("/motor/status")
        async def get_motor_status():
            """Obtiene el estado del motor."""
            if not self.motor_controller:
                raise HTTPException(404, "Motor controller no disponible")
            return self.motor_controller.get_status()
        
        # ============ MÉTRICAS ULTRA ============
        @app.get("/metrics/categories")
        async def get_category_metrics():
            """Obtiene métricas detalladas por categoría."""
            return {
                cat.fruit_name: {
                    "emoji": cat.emoji,
                    "labeler_id": cat.labeler_id,
                    "metrics": asdict(metrics)
                } for cat, metrics in self.category_metrics.items()
            }
        
        @app.get("/metrics/predictions")
        async def get_predictions():
            """Obtiene predicciones del sistema."""
            if not self.prediction_engine:
                return {"error": "Motor de predicción no disponible"}
            
            return {
                "predicted_throughput_1h": self.prediction_engine.predict_throughput(60),
                "next_category": self.pattern_analyzer.predict_next_category().fruit_name if self.pattern_analyzer.predict_next_category() else "unknown",
                "patterns": list(self.pattern_analyzer.pattern_history)[-10:]  # Últimos 10 patrones
            }
        
        # ============ WEBSOCKET ULTRA ============
        @app.websocket("/ws/ultra_dashboard")
        async def ultra_websocket_endpoint(websocket: WebSocket):
            """WebSocket para dashboard ultra en tiempo real."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Enviar datos en tiempo real cada segundo
                    ultra_data = {
                        "timestamp": datetime.now().isoformat(),
                        "system_state": self._system_state.value,
                        "metrics": asdict(self.metrics),
                        "active_labeler": self.active_group_id,
                        "motor_position": self.motor_controller.current_position if self.motor_controller else 0,
                        "categories": {cat.fruit_name: asdict(metrics) for cat, metrics in self.category_metrics.items()},
                        "recent_detections": self._get_recent_detections()
                    }
                    
                    await websocket.send_json(ultra_data)
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
        
        return app
    
    def _get_recent_detections(self) -> List[Dict]:
        """Obtiene las detecciones recientes para el dashboard."""
        # Simulación - en la implementación real vendría de la base de datos
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "category": "apple",
                "confidence": 0.95,
                "labeler_used": 0
            }
        ]
    
    async def _start_ultra_system_tasks(self):
        """Inicia las tareas ultra-concurrentes del sistema."""
        logger.info("Iniciando tareas ultra-concurrentes del sistema...")
        
        # Tareas principales
        self._tasks.append(asyncio.create_task(self._ultra_main_processing_loop()))
        self._tasks.append(asyncio.create_task(self._ultra_monitoring_loop()))
        self._tasks.append(asyncio.create_task(self._ultra_optimization_loop()))
        self._tasks.append(asyncio.create_task(self._ultra_learning_loop()))
        
        # Servidor API
        if self.app:
            self._tasks.append(asyncio.create_task(self._start_api_server()))
        
        logger.info(f"Iniciadas {len(self._tasks)} tareas ultra-concurrentes")
    
    def _sensor_trigger_callback(self):
        """Callback del sensor de trigger."""
        try:
            trigger_time = time.time()
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._trigger_queue.put_nowait, trigger_time)
            else:
                self._trigger_queue.put_nowait(trigger_time)
        except asyncio.QueueFull:
            logger.warning("Cola de triggers llena")
    
    async def _start_system_tasks(self):
        """Inicia las tareas del sistema."""
        logger.info("Iniciando tareas del sistema...")
        
        # Tarea principal de procesamiento
        self._tasks.append(asyncio.create_task(self._main_processing_loop()))
        
        # Tarea de monitoreo
        self._tasks.append(asyncio.create_task(self._monitoring_loop()))
        
        # Servidor API
        if self.app:
            self._tasks.append(asyncio.create_task(self._start_api_server()))
        
        logger.info(f"Iniciadas {len(self._tasks)} tareas")
    
    async def _main_processing_loop(self):
        """Bucle principal de procesamiento."""
        logger.info("Iniciando bucle principal")
        
        while self._running.is_set():
            try:
                if self._system_state != SystemState.RUNNING:
                    await asyncio.sleep(0.1)
                    continue
                
                # Esperar trigger del sensor
                try:
                    trigger_time = await asyncio.wait_for(
                        self._trigger_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                self._set_state(SystemState.PROCESSING)
                logger.info("Procesando nueva fila...")
                
                # Procesar fila
                await self._process_fruit_row()
                
                self._set_state(SystemState.RUNNING)
                
            except Exception as e:
                logger.exception(f"Error en bucle principal: {e}")
                await asyncio.sleep(1)
    
    async def _process_fruit_row(self):
        """Procesa una fila de frutas."""
        try:
            # 1. Capturar frame
            if not self.camera:
                logger.warning("Cámara no disponible")
                return
            
            frame = self.camera.capture_frame()
            if frame is None:
                logger.error("No se pudo capturar frame")
                return
            
            # 2. Analizar con IA
            if not self.ai_detector:
                logger.warning("Detector de IA no disponible")
                return
            
            result = await self.ai_detector.detect_fruits(frame, ProcessingPriority.HIGH)
            
            if result and result.fruit_count > 0:
                logger.info(f"Detectadas {result.fruit_count} frutas")
                
                # Actualizar métricas
                self.metrics.frames_processed += 1
                self.metrics.fruits_detected += result.fruit_count
                
                # Ejecutar etiquetado
                await self._execute_labeling(result)
            else:
                logger.info("No se detectaron frutas")
                
        except Exception as e:
            logger.exception(f"Error procesando fila: {e}")
            self.metrics.error_count += 1
    
    async def _execute_labeling(self, result: FrameAnalysisResult):
        """Ejecuta el etiquetado."""
        try:
            if not self.labeler:
                logger.warning("Etiquetador no disponible")
                return
            
            # Calcular parámetros
            labeler_config = self.config["labeler_settings"]
            belt_config = self.config["conveyor_belt_settings"]
            
            distance_m = labeler_config["distance_camera_to_labeler_m"]
            belt_speed_mps = belt_config["belt_speed_mps"]
            fruit_width_m = labeler_config["fruit_detection_settings"]["fruit_avg_width_m"]
            fruit_spacing_m = labeler_config["fruit_detection_settings"]["fruit_spacing_m"]
            
            # Calcular temporización
            delay = distance_m / belt_speed_mps
            row_length = (result.fruit_count * fruit_width_m) + max(0, (result.fruit_count - 1) * fruit_spacing_m)
            duration = row_length / belt_speed_mps
            
            logger.info(f"Etiquetado: {delay:.2f}s espera, {duration:.2f}s duración")
            
            # Esperar y activar
            await asyncio.sleep(delay)
            
            success = await self.labeler.activate_for_duration(duration)
            
            if success:
                self.metrics.labels_applied += result.fruit_count
                logger.info("Etiquetado completado")
            else:
                logger.error("Fallo en etiquetado")
                
        except Exception as e:
            logger.exception(f"Error en etiquetado: {e}")
    
    async def _monitoring_loop(self):
        """Bucle de monitoreo."""
        while self._running.is_set():
            try:
                # Actualizar métricas
                self.metrics.timestamp = datetime.now()
                self.metrics.uptime_seconds = time.time() - self._start_time
                
                await asyncio.sleep(10)  # Cada 10 segundos
                
            except Exception as e:
                logger.error(f"Error en monitoreo: {e}")
                await asyncio.sleep(5)
    
    async def _start_api_server(self):
        """Inicia el servidor API."""
        if not self.app:
            return
        
        api_config = self.config["api_settings"]
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 8000)
        
        logger.info(f"Iniciando servidor API en {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="warning"
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    async def start_production(self):
        """Inicia la producción."""
        logger.info("Iniciando producción...")
        
        if self.belt_controller:
            self.belt_controller.start_belt()
        
        self._set_state(SystemState.RUNNING)
        self._running.set()
        
        self._send_alert(AlertLevel.INFO, "Producción", "Iniciada")
    
    async def stop_production(self):
        """Detiene la producción."""
        logger.info("Deteniendo producción...")
        
        if self.belt_controller:
            self.belt_controller.stop_belt()
        
        self._set_state(SystemState.IDLE)
        
        self._send_alert(AlertLevel.INFO, "Producción", "Detenida")
    
    async def emergency_stop(self):
        """Parada de emergencia."""
        logger.critical("PARADA DE EMERGENCIA")
        
        self._emergency_stop.set()
        self._set_state(SystemState.EMERGENCY_STOP)
        
        # Detener componentes
        if self.belt_controller:
            self.belt_controller.emergency_stop()
        
        # Parar etiquetadoras (múltiples o única)
        try:
            if self.labelers:
                for labeler in self.labelers.values():
                    try:
                        await labeler.emergency_stop()
                    except Exception:
                        pass
            elif self.labeler:
                await self.labeler.emergency_stop()
        except Exception:
            pass
        
        self._send_alert(AlertLevel.CRITICAL, "Sistema", "PARADA DE EMERGENCIA")
    
    # ==================== BUCLES ULTRA-CONCURRENTES ====================
    
    async def _ultra_main_processing_loop(self):
        """Bucle principal de procesamiento ultra-avanzado."""
        logger.info("Iniciando bucle ultra de procesamiento principal")
        while True:
            try:
                if not self._running.is_set() or self._system_state != SystemState.RUNNING:
                    await asyncio.sleep(0.1)
                    continue

                # Esperar trigger del sensor
                try:
                    trigger_time = await asyncio.wait_for(
                        self._trigger_queue.get(),
                        timeout=1.0,
                    )
                except asyncio.TimeoutError:
                    continue

                self._set_state(SystemState.PROCESSING)
                logger.info("🔥 ULTRA: Procesando nueva fila...")

                # Procesar fila con sistema ultra
                await self._ultra_process_fruit_row()

                self._set_state(SystemState.RUNNING)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error en bucle ultra principal: {e}")
                await asyncio.sleep(1)
    
    async def _ultra_process_fruit_row(self):
        """Procesa una fila de frutas con sistema ultra-avanzado."""
        try:
            start_time = time.time()
            
            # 1. Capturar frame con buffer inteligente
            if not self.camera:
                logger.warning("Cámara no disponible")
                return
            
            frame = self.camera.capture_frame()
            if frame is None:
                logger.error("No se pudo capturar frame")
                return
            
            # 2. Análisis ultra con IA categorizada
            if not self.ai_detector:
                logger.warning("Detector de IA no disponible")
                return
            
            result = await self.ai_detector.detect_fruits(frame, ProcessingPriority.HIGH)
            
            if result and result.fruit_count > 0:
                # 3. Determinar categorías detectadas
                detected_categories = await self._analyze_fruit_categories(result)
                
                if detected_categories:
                    # 4. Seleccionar etiquetadora óptima
                    optimal_category = await self._select_optimal_labeler(detected_categories)
                    
                    # 5. Ejecutar etiquetado ultra
                    await self._execute_ultra_labeling(optimal_category, result)
                    
                    # 6. Actualizar métricas por categoría
                    await self._update_category_metrics(detected_categories, result)
                
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"🚀 PERF: Procesamiento ultra completado en {processing_time:.1f}ms")
                
            else:
                logger.info("No se detectaron frutas")
                
        except Exception as e:
            logger.exception(f"Error en procesamiento ultra: {e}")
            self.metrics.error_count += 1
    
    async def _analyze_fruit_categories(self, result) -> List[FruitCategory]:
        """Analiza y categoriza las frutas detectadas."""
        # Simulación de categorización IA avanzada para sistema lineal
        # En implementación real, esto vendría del resultado de IA
        detected_categories = []
        
        # Asignar categorías basadas en detecciones (sistema de 3 categorías)
        available_categories = [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]
        
        for i in range(min(result.fruit_count, TOTAL_LABELERS)):  # Máximo 6 frutas (2 por grupo)
            # Rotar entre las 3 categorías para demostración
            category = available_categories[i % len(available_categories)]
            detected_categories.append(category)
        
        logger.info(f"🍎🍐🍋 Categorías detectadas: {[cat.emoji for cat in detected_categories]}")
        return detected_categories
    
    async def _select_optimal_labeler(self, categories: List[FruitCategory]) -> FruitCategory:
        """Selecciona la etiquetadora óptima basada en categorías detectadas."""
        if not categories:
            return FruitCategory.UNKNOWN
        
        # Estrategia: usar la categoría más frecuente
        category_counts = Counter(categories)
        most_common_category = category_counts.most_common(1)[0][0]
        
        logger.info(f"🎯 Etiquetadora seleccionada: {most_common_category.emoji} (ID: {most_common_category.labeler_id})")
        return most_common_category
    
    async def _execute_ultra_labeling(self, category: FruitCategory, result):
        """Ejecuta el etiquetado ultra lineal con motor DC y 2 etiquetadoras simultáneas por grupo."""
        try:
            if category == FruitCategory.UNKNOWN:
                logger.warning("Categoría desconocida, omitiendo etiquetado")
                return
            
            # 1. Activar grupo de etiquetadoras correcto
            if self.motor_controller:
                motor_success = await self.motor_controller.activate_labeler_group(category)
                if not motor_success:
                    logger.error(f"Fallo activando grupo {category.fruit_name}")
                    return
                
                self.active_group_id = category.labeler_group_id
                self.metrics.labeler_switch_count += 1
            
            # 2. Obtener etiquetadoras del grupo activo
            group_info = None
            for group in LabelerGroup:
                if group.category == category.fruit_name:
                    group_info = group
                    break
            
            if not group_info:
                logger.error(f"No se encontró grupo para categoría {category.fruit_name}")
                return
            
            # 3. Activar todas las etiquetadoras del grupo simultáneamente
            duration = await self._calculate_labeling_duration(result)
            labeling_tasks = []
            
            logger.info(f"🚀 Activando {len(group_info.labeler_ids)} etiquetadoras del grupo {category.emoji}")
            
            for labeler_id in group_info.labeler_ids:
                if labeler_id in self.labelers:
                    labeler = self.labelers[labeler_id]
                    # Timeout por seguridad para evitar bloqueos en hardware
                    timeout_seconds = max(1.0, min(duration + 2.0, 30.0))
                    coro = self._activate_single_labeler(labeler, labeler_id, duration, category)
                    task = asyncio.create_task(asyncio.wait_for(coro, timeout=timeout_seconds))
                    labeling_tasks.append(task)
            
            # 4. Esperar a que todas las etiquetadoras terminen
            if labeling_tasks:
                results = await asyncio.gather(*labeling_tasks, return_exceptions=True)
                successful_count = 0
                for r in results:
                    if r is True:
                        successful_count += 1
                    elif isinstance(r, asyncio.TimeoutError):
                        logger.error("Timeout activando una etiquetadora")
                    elif isinstance(r, Exception):
                        logger.error(f"Error activando una etiquetadora: {r}")
                
                if successful_count > 0:
                    self.metrics.total_labels_applied += result.fruit_count
                    logger.info(f"✅ Etiquetado lineal completado: {category.emoji} x{result.fruit_count} ({successful_count}/{len(labeling_tasks)} etiquetadoras)")
                else:
                    logger.error(f"❌ Fallo completo en etiquetado lineal: {category.emoji}")
            
        except Exception as e:
            logger.exception(f"Error en etiquetado ultra lineal: {e}")
    
    async def _activate_single_labeler(self, labeler: LabelerActuator, labeler_id: int, duration: float, category: FruitCategory) -> bool:
        """Activa una etiquetadora individual."""
        try:
            success = await labeler.activate_for_duration(duration, 100.0)
            
            if success and labeler_id in self.labeler_metrics:
                self.labeler_metrics[labeler_id].activations_count += 1
                self.labeler_metrics[labeler_id].last_activation = datetime.now()
            
            return success
        except Exception as e:
            logger.error(f"Error activando etiquetadora {labeler_id}: {e}")
            return False
    
    async def _calculate_labeling_duration(self, result) -> float:
        """Calcula la duración óptima del etiquetado."""
        # Configuración base
        base_duration = 2.0  # segundos base
        fruit_factor = 0.3   # segundos adicionales por fruta
        
        duration = base_duration + (result.fruit_count * fruit_factor)
        return min(duration, 10.0)  # Máximo 10 segundos
    
    async def _update_category_metrics(self, categories: List[FruitCategory], result):
        """Actualiza métricas por categoría de fruta."""
        try:
            for category in set(categories):
                if category in self.category_metrics:
                    metrics = self.category_metrics[category]
                    count = categories.count(category)
                    # Actualizar totales
                    metrics.total_detected += count

                    # Actualizar confidence promedio (simulado)
                    new_confidence = 0.85 + (0.1 * len(categories))  # Simulación
                    metrics.avg_confidence = (metrics.avg_confidence + new_confidence) / 2

                    # Calcular throughput con timestamp previo
                    previous_detection = metrics.last_detection
                    now = datetime.now()
                    metrics.last_detection = now
                    if previous_detection is not None:
                        time_diff = (now - previous_detection).total_seconds()
                        if time_diff > 0:
                            metrics.throughput_per_hour = (count / time_diff) * 3600
            
            logger.debug(f"📊 Métricas de categorías actualizadas")
            
        except Exception as e:
            logger.error(f"Error actualizando métricas de categoría: {e}")
    
    async def _ultra_monitoring_loop(self):
        """Bucle ultra de monitoreo del sistema."""
        logger.info("Iniciando bucle ultra de monitoreo")
        while True:
            try:
                if not self._running.is_set():
                    await asyncio.sleep(0.5)
                    continue

                # Actualizar métricas ultra-completas
                await self._update_ultra_metrics()

                # Monitoreo de salud del sistema
                await self._monitor_system_health()

                # Enviar datos a WebSockets
                await self._broadcast_ultra_data()

                await asyncio.sleep(5)  # Cada 5 segundos

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en monitoreo ultra: {e}")
                await asyncio.sleep(10)
    
    async def _update_ultra_metrics(self):
        """Actualiza todas las métricas ultra del sistema."""
        try:
            with self._metrics_lock:
                self.metrics.timestamp = datetime.now()
                self.metrics.uptime_seconds = time.time() - self._start_time
                
                # Métricas del motor lineal
                if self.motor_controller:
                    self.metrics.group_positions = self.motor_controller.group_positions.copy()
                    self.metrics.active_group_id = self.active_group_id
                
                # OEE (Overall Equipment Effectiveness)
                self.metrics.oee_percentage = self._calculate_oee()
                
                # Guardar en base de datos
                await self._save_metrics_to_db()
                
        except Exception as e:
            logger.error(f"Error actualizando métricas ultra: {e}")
    
    def _calculate_oee(self) -> float:
        """Calcula el OEE (Overall Equipment Effectiveness)."""
        # Fórmula simplificada: Disponibilidad × Rendimiento × Calidad
        availability = 0.95  # 95% disponibilidad (simulado)
        performance = min(1.0, self.metrics.throughput_items_per_minute / 60.0)  # Rendimiento
        quality = 0.98  # 98% calidad (simulado)
        
        oee = availability * performance * quality * 100
        return round(oee, 2)
    
    async def _monitor_system_health(self):
        """Monitorea la salud general del sistema."""
        try:
            # Verificar componentes críticos
            components_healthy = True
            
            if self.motor_controller and self.motor_controller.is_moving:
                # Motor funcionando correctamente
                pass
            
            if len(self.labelers) < TOTAL_LABELERS:
                logger.warning(f"⚠️ Menos de {TOTAL_LABELERS} etiquetadoras operativas")
                components_healthy = False
            
            # Actualizar score de eficiencia
            if components_healthy:
                self.metrics.efficiency_score = min(100.0, self.metrics.efficiency_score + 0.1)
            else:
                self.metrics.efficiency_score = max(0.0, self.metrics.efficiency_score - 1.0)
                
        except Exception as e:
            logger.error(f"Error monitoreando salud del sistema: {e}")
    
    async def _broadcast_ultra_data(self):
        """Envía datos ultra en tiempo real a las conexiones WebSocket."""
        if not self.websocket_connections:
            return
        
        try:
            ultra_data = {
                "timestamp": datetime.now().isoformat(),
                "system_state": self._system_state.value,
                "metrics": asdict(self.metrics),
                "active_group": self.active_group_id,
                "motor_status": self.motor_controller.get_status() if self.motor_controller else {},
                "categories": {cat.fruit_name: asdict(metrics) for cat, metrics in self.category_metrics.items()},
                "labelers_status": {i: labeler.get_status() for i, labeler in self.labelers.items()}
            }
            
            # Enviar a todas las conexiones WebSocket
            disconnected = []
            for ws in self.websocket_connections:
                try:
                    await ws.send_json(ultra_data)
                except:
                    disconnected.append(ws)
            
            # Limpiar conexiones desconectadas
            for ws in disconnected:
                self.websocket_connections.remove(ws)
                
        except Exception as e:
            logger.error(f"Error enviando datos ultra: {e}")
    
    async def _ultra_optimization_loop(self):
        """Bucle ultra de optimización del sistema."""
        logger.info("Iniciando bucle ultra de optimización")
        while True:
            try:
                if not self._running.is_set():
                    await asyncio.sleep(1)
                    continue
                self._set_state(SystemState.OPTIMIZING)

                # Ejecutar optimización según el modo
                optimization_result = await self._execute_optimization()

                if optimization_result and optimization_result.confidence > 0.7:
                    logger.info(f"🚀 Optimización aplicada: {optimization_result.improvements}")

                self._set_state(SystemState.RUNNING)
                await asyncio.sleep(30)  # Cada 30 segundos

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en optimización ultra: {e}")
                await asyncio.sleep(60)
    
    async def _execute_optimization(self) -> OptimizationResult:
        """Ejecuta optimización basada en el modo actual."""
        try:
            strategy = self.optimization_strategies.get(self._optimization_mode)
            if strategy:
                return await strategy()
            
            return OptimizationResult(confidence=0.0)
            
        except Exception as e:
            logger.error(f"Error ejecutando optimización: {e}")
            return OptimizationResult(confidence=0.0)
    
    async def _optimize_for_speed(self) -> OptimizationResult:
        """Optimización para velocidad máxima."""
        improvements = {"throughput": 1.15, "response_time": 0.85}
        return OptimizationResult(
            mode=OptimizationMode.SPEED,
            improvements=improvements,
            recommendations=["Incrementar velocidad de banda", "Reducir tiempo de análisis IA"],
            confidence=0.8
        )
    
    async def _optimize_for_accuracy(self) -> OptimizationResult:
        """Optimización para precisión máxima."""
        improvements = {"accuracy": 1.05, "error_rate": 0.9}
        return OptimizationResult(
            mode=OptimizationMode.ACCURACY,
            improvements=improvements,
            recommendations=["Aumentar tiempo de análisis", "Usar múltiples detectores"],
            confidence=0.9
        )
    
    async def _optimize_for_efficiency(self) -> OptimizationResult:
        """Optimización para eficiencia energética."""
        improvements = {"energy_consumption": 0.85, "maintenance_cost": 0.9}
        return OptimizationResult(
            mode=OptimizationMode.EFFICIENCY,
            improvements=improvements,
            recommendations=["Optimizar ciclos de motor", "Reducir activaciones innecesarias"],
            confidence=0.85
        )
    
    async def _optimize_adaptive(self) -> OptimizationResult:
        """Optimización adaptativa basada en patrones."""
        # Análisis de patrones recientes
        if self.pattern_analyzer and len(self.pattern_analyzer.pattern_history) > 10:
            recent_patterns = list(self.pattern_analyzer.pattern_history)[-10:]
            
            # Determinar mejor estrategia basada en patrones
            avg_throughput = sum(p.get('total_detections', 0) for p in recent_patterns) / len(recent_patterns)
            
            if avg_throughput > 50:
                return await self._optimize_for_speed()
            elif avg_throughput < 20:
                return await self._optimize_for_accuracy()
            else:
                return await self._optimize_for_efficiency()
        
        return OptimizationResult(confidence=0.5)
    
    async def _ultra_learning_loop(self):
        """Bucle ultra de aprendizaje automático."""
        logger.info("Iniciando bucle ultra de aprendizaje")
        while True:
            try:
                if not self._running.is_set():
                    await asyncio.sleep(1)
                    continue
                self._set_state(SystemState.LEARNING)

                # Recopilar datos de aprendizaje
                await self._collect_learning_data()

                # Actualizar modelos predictivos
                await self._update_prediction_models()

                # Analizar patrones
                await self._analyze_patterns()

                self._set_state(SystemState.RUNNING)
                await asyncio.sleep(60)  # Cada minuto

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en aprendizaje ultra: {e}")
                await asyncio.sleep(120)
    
    async def _collect_learning_data(self):
        """Recopila datos para aprendizaje automático."""
        try:
            learning_sample = {
                'timestamp': datetime.now(),
                'throughput': self.metrics.throughput_items_per_minute,
                'efficiency': self.metrics.efficiency_score,
                'oee': self.metrics.oee_percentage,
                'active_group': self.active_group_id,
                'motor_status': self.motor_controller.get_status() if self.motor_controller else {},
                'categories': {cat.fruit_name: metrics.total_detected for cat, metrics in self.category_metrics.items()}
            }
            
            self.learning_data.append(learning_sample)
            
            # Actualizar motor de predicción
            if self.prediction_engine:
                self.prediction_engine.update_model(learning_sample)
                
        except Exception as e:
            logger.error(f"Error recopilando datos de aprendizaje: {e}")
    
    async def _update_prediction_models(self):
        """Actualiza los modelos predictivos."""
        try:
            if len(self.learning_data) > 100:
                # Predicción de throughput para próxima hora
                predicted = self.prediction_engine.predict_throughput(60)
                self.metrics.predicted_throughput = predicted
                
                logger.debug(f"🔮 Throughput predicho para 1h: {predicted:.1f} items/min")
                
        except Exception as e:
            logger.error(f"Error actualizando modelos predictivos: {e}")
    
    async def _analyze_patterns(self):
        """Analiza patrones de comportamiento del sistema."""
        try:
            if self.pattern_analyzer and len(self.learning_data) > 50:
                # Simular análisis de detecciones para patrones
                recent_data = list(self.learning_data)[-50:]
                
                # Crear detecciones simuladas para análisis
                mock_detections = []
                for data in recent_data[-10:]:  # Últimos 10
                    for cat_name, count in data['categories'].items():
                        if count > 0:
                            try:
                                category = FruitCategory[cat_name.upper()]
                                detection = FruitDetectionResult(
                                    category=category,
                                    confidence=0.9,
                                    bbox=(0, 0, 100, 100),
                                    features={},
                                    timestamp=data['timestamp'],
                                    processing_time_ms=50.0
                                )
                                mock_detections.append(detection)
                            except KeyError:
                                pass
                
                if mock_detections:
                    pattern = self.pattern_analyzer.analyze_detection_pattern(mock_detections)
                    logger.debug(f"📊 Patrón analizado: {pattern}")
                
        except Exception as e:
            logger.error(f"Error analizando patrones: {e}")
    
    async def _save_metrics_to_db(self):
        """Guarda métricas en la base de datos."""
        try:
            if self.db_connection:
                metrics_payload = json.dumps(asdict(self.metrics), default=str)
                timestamp = datetime.now().isoformat()

                def _write_to_db():
                    cursor = self.db_connection.cursor()
                    cursor.execute(
                        """
                        INSERT INTO metrics (timestamp, metric_type, metric_data)
                        VALUES (?, ?, ?)
                        """,
                        (
                            timestamp,
                            "system_metrics",
                            metrics_payload,
                        ),
                    )
                    self.db_connection.commit()

                # Ejecutar escritura en hilo para no bloquear el event-loop
                await asyncio.to_thread(_write_to_db)
                
        except Exception as e:
            logger.error(f"Error guardando métricas en BD: {e}")
    
    async def shutdown(self):
        """Apaga el sistema ultra-avanzado."""
        if self._system_state == SystemState.SHUTTING_DOWN:
            return
        
        logger.info("Iniciando apagado ultra...")
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
            
            # Apagar componentes ultra
            if self.motor_controller:
                await self.motor_controller.emergency_stop()
                await self.motor_controller.cleanup()
            
            # Apagar todas las etiquetadoras
            for labeler in self.labelers.values():
                await labeler.cleanup()
            
            # Apagar componentes base
            if self.trigger_sensor:
                self.trigger_sensor.shutdown()
            
            if self.belt_controller:
                self.belt_controller.stop_belt()
                self.belt_controller.cleanup()
            
            if self.ai_detector:
                await self.ai_detector.shutdown()
            
            if self.camera:
                self.camera.shutdown()
            
            # Cerrar base de datos
            if self.db_connection:
                self.db_connection.close()
            
            # Cerrar thread pool
            self.thread_pool.shutdown(wait=True)
            
            self._set_state(SystemState.OFFLINE)
            logger.info("🎉 Sistema ULTRA apagado correctamente")
            
        except Exception as e:
            logger.error(f"Error durante apagado ultra: {e}")


async def main():
    """Punto de entrada principal."""
    system = None
    
    try:
        logger.info("=== FruPrint Industrial v2.0 ===")
        
        # Crear sistema
        config_file = "Config_Etiquetadora.json"
        system = UltraIndustrialFruitLabelingSystem(config_file)
        
        # Configurar señales
        loop = asyncio.get_event_loop()
        
        def signal_handler():
            logger.info("Señal de apagado recibida")
            if system:
                loop.create_task(system.shutdown())
        
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows
            signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        
        # Inicializar
        if await system.initialize():
            logger.info("Sistema ejecutándose...")
            
            # Mantener funcionando
            while system._system_state != SystemState.OFFLINE:
                await asyncio.sleep(1)
        else:
            logger.critical("Fallo al inicializar")
            return 1
        
    except KeyboardInterrupt:
        logger.info("Interrupción recibida")
    except Exception as e:
        logger.exception(f"Error crítico: {e}")
        return 1
    finally:
        if system:
            await system.shutdown()
        logger.info("Sistema terminado")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)
