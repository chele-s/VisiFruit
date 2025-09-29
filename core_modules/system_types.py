# system_types.py
"""
Tipos, Enums y Constantes del Sistema FruPrint v4.0 - ENHANCED
===============================================================

Módulo centralizado de tipos de datos, enumeraciones, constantes y validaciones
para el sistema industrial de etiquetado.

MEJORAS v4.0:
- Validaciones avanzadas de datos
- Tipos adicionales para configuración
- Sistema de permisos y roles
- Constantes de rendimiento
- Utilidades de conversión mejoradas

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0.1 - MODULAR ARCHITECTURE ENHANCED
"""

from enum import Enum, auto
from typing import NamedTuple, Tuple, Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime

# ==================== CONSTANTES DE CONFIGURACIÓN ====================
LABELERS_PER_GROUP = 2
NUM_LABELER_GROUPS = 3
TOTAL_LABELERS = LABELERS_PER_GROUP * NUM_LABELER_GROUPS

# Constantes de rendimiento
MAX_THROUGHPUT_PER_MINUTE = 120
MIN_CONFIDENCE_THRESHOLD = 0.75
MAX_PROCESSING_TIME_MS = 150
OPTIMAL_BELT_SPEED_MPS = 0.5

# Constantes de hardware
GPIO_PIN_MIN = 0
GPIO_PIN_MAX = 27
PWM_FREQUENCY_HZ = 1000
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180

# ==================== ENUMERACIONES ====================

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
    UPDATING = "updating"
    SUSPENDED = "suspended"

    def is_operational(self) -> bool:
        """Verifica si el sistema está en un estado operacional."""
        return self in (SystemState.IDLE, SystemState.RUNNING, SystemState.PROCESSING)
    
    def can_transition_to(self, new_state: 'SystemState') -> bool:
        """Verifica si es posible transicionar al nuevo estado."""
        valid_transitions = {
            SystemState.OFFLINE: [SystemState.INITIALIZING],
            SystemState.INITIALIZING: [SystemState.IDLE, SystemState.ERROR],
            SystemState.IDLE: [SystemState.RUNNING, SystemState.CALIBRATING, SystemState.MAINTENANCE, SystemState.SHUTTING_DOWN],
            SystemState.RUNNING: [SystemState.PROCESSING, SystemState.IDLE, SystemState.EMERGENCY_STOP],
            SystemState.PROCESSING: [SystemState.RUNNING, SystemState.ERROR],
            SystemState.ERROR: [SystemState.RECOVERY, SystemState.SHUTTING_DOWN],
            SystemState.EMERGENCY_STOP: [SystemState.RECOVERY, SystemState.SHUTTING_DOWN],
        }
        return new_state in valid_transitions.get(self, [])

class AlertLevel(Enum):
    """Niveles de alerta ultra-detallados."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

    @property
    def severity(self) -> int:
        """Retorna el nivel de severidad numérico."""
        severity_map = {
            AlertLevel.DEBUG: 0,
            AlertLevel.INFO: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.ERROR: 3,
            AlertLevel.CRITICAL: 4,
            AlertLevel.EMERGENCY: 5
        }
        return severity_map[self]
    
    @property
    def color(self) -> str:
        """Retorna el color asociado al nivel de alerta."""
        color_map = {
            AlertLevel.DEBUG: "#888888",
            AlertLevel.INFO: "#2196F3",
            AlertLevel.WARNING: "#FFC107",
            AlertLevel.ERROR: "#FF5722",
            AlertLevel.CRITICAL: "#D32F2F",
            AlertLevel.EMERGENCY: "#B71C1C"
        }
        return color_map[self]

class FruitCategory(Enum):
    """Categorías de frutas con IDs específicos - Sistema lineal de 3 categorías."""
    APPLE = ("apple", 0, "🍎", "#FF4444")
    PEAR = ("pear", 1, "🍐", "#90EE90")
    LEMON = ("lemon", 2, "🍋", "#FFFF00")
    UNKNOWN = ("unknown", 99, "❓", "#888888")
    
    def __init__(self, name: str, labeler_group_id: int, emoji: str, color: str):
        self.fruit_name = name
        self.labeler_group_id = labeler_group_id
        self.emoji = emoji
        self.color = color

    @property
    def labeler_id(self) -> int:
        """Alias para compatibilidad: devuelve el ID del grupo de etiquetadoras."""
        return self.labeler_group_id
    
    @property
    def display_name(self) -> str:
        """Nombre para mostrar con emoji."""
        return f"{self.emoji} {self.fruit_name.capitalize()}"
    
    def is_valid_category(self) -> bool:
        """Verifica si es una categoría válida (no UNKNOWN)."""
        return self != FruitCategory.UNKNOWN

class LabelerGroup(Enum):
    """Grupos de etiquetadoras lineales - 2 etiquetadoras por grupo."""
    GROUP_APPLE = (0, "apple", [0, 1])
    GROUP_PEAR = (1, "pear", [2, 3])
    GROUP_LEMON = (2, "lemon", [4, 5])
    
    def __init__(self, group_id: int, category: str, labeler_ids: list):
        self.group_id = group_id
        self.category = category
        self.labeler_ids = labeler_ids

    @property
    def emoji(self) -> str:
        """Emoji asociado al grupo."""
        emoji_map = {"apple": "🍎", "pear": "🍐", "lemon": "🍋"}
        return emoji_map.get(self.category, "❓")

class ProcessingPriority(Enum):
    """Prioridades de procesamiento."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

    @property
    def timeout_multiplier(self) -> float:
        """Multiplicador de timeout según prioridad."""
        return {
            ProcessingPriority.LOW: 2.0,
            ProcessingPriority.NORMAL: 1.0,
            ProcessingPriority.HIGH: 0.75,
            ProcessingPriority.CRITICAL: 0.5,
            ProcessingPriority.EMERGENCY: 0.25
        }[self]

class OptimizationMode(Enum):
    """Modos de optimización."""
    SPEED = "speed"
    ACCURACY = "accuracy"
    EFFICIENCY = "efficiency"
    ADAPTIVE = "adaptive"
    BALANCED = "balanced"
    POWER_SAVING = "power_saving"

class HardwareType(Enum):
    """Tipos de hardware soportados."""
    SOLENOID = "solenoid"
    STEPPER = "stepper"
    SERVO = "servo"
    DC_MOTOR = "dc_motor"
    RELAY = "relay"
    SENSOR = "sensor"

class SensorType(Enum):
    """Tipos de sensores."""
    INFRARED = "infrared"
    LASER = "laser"
    ULTRASONIC = "ultrasonic"
    CAPACITIVE = "capacitive"
    OPTICAL = "optical"

class UserRole(Enum):
    """Roles de usuario para control de acceso."""
    ADMIN = "admin"
    OPERATOR = "operator"
    MAINTENANCE = "maintenance"
    VIEWER = "viewer"

# ==================== NAMED TUPLES Y DATACLASSES ====================

class FruitDetectionResult(NamedTuple):
    """Resultado de detección ultra-detallado."""
    category: FruitCategory
    confidence: float
    bbox: Tuple[int, int, int, int]
    features: Dict[str, float]
    timestamp: object
    processing_time_ms: float

@dataclass
class HardwareConfig:
    """Configuración de hardware validada."""
    type: HardwareType
    pins: Dict[str, int]
    name: str
    enabled: bool = True
    settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Valida la configuración de hardware."""
        errors = []
        
        # Validar pines
        for pin_name, pin_num in self.pins.items():
            if not isinstance(pin_num, int):
                errors.append(f"Pin {pin_name} debe ser entero, no {type(pin_num)}")
            elif not (GPIO_PIN_MIN <= pin_num <= GPIO_PIN_MAX):
                errors.append(f"Pin {pin_name}={pin_num} fuera de rango ({GPIO_PIN_MIN}-{GPIO_PIN_MAX})")
        
        # Validar nombre
        if not self.name or not isinstance(self.name, str):
            errors.append("Nombre de hardware inválido")
        
        return len(errors) == 0, errors

@dataclass
class SystemPerformanceMetrics:
    """Métricas de rendimiento del sistema."""
    throughput_target: float = MAX_THROUGHPUT_PER_MINUTE
    latency_target_ms: float = MAX_PROCESSING_TIME_MS
    accuracy_target: float = 0.95
    uptime_target: float = 0.99
    
    def check_targets(self, actual_throughput: float, actual_latency: float, 
                     actual_accuracy: float, actual_uptime: float) -> Dict[str, bool]:
        """Verifica si se cumplen los objetivos."""
        return {
            "throughput": actual_throughput >= self.throughput_target,
            "latency": actual_latency <= self.latency_target_ms,
            "accuracy": actual_accuracy >= self.accuracy_target,
            "uptime": actual_uptime >= self.uptime_target
        }

# ==================== CONSTANTES DE CONFIGURACIÓN ====================

DEFAULT_MOTOR_PINS = {
    "pwm_pin": 12,
    "dir_pin1": 20,
    "dir_pin2": 21,
    "enable_pin": 16
}

DEFAULT_DIVERTER_CONFIG = {
    "enabled": True,
    "activation_duration_seconds": 2.0,
    "return_delay_seconds": 0.5,
    "servo_response_time_s": 0.3,
    "distance_labeler_to_diverter_m": 1.0,
    "diverters": {
        0: {
            "pin": 18,
            "name": "Diverter-Apple",
            "category": "apple",
            "straight_angle": 0,
            "diverted_angle": 90
        },
        1: {
            "pin": 19,
            "name": "Diverter-Pear",
            "category": "pear", 
            "straight_angle": 0,
            "diverted_angle": 90
        }
    }
}

DEFAULT_SYSTEM_SETTINGS = {
    "installation_id": "FRUPRINT-ULTRA-001",
    "system_name": "FruPrint Ultra Industrial v4.0",
    "log_level": "INFO",
    "max_queue_size": 200,
    "alert_retention_days": 7,
    "metrics_interval_seconds": 5,
    "backup_interval_hours": 24
}

# ==================== UTILIDADES DE TIPO ====================

def get_category_emoji(category: FruitCategory) -> str:
    """Obtiene el emoji de una categoría."""
    return category.emoji

def get_category_by_name(name: str) -> FruitCategory:
    """Obtiene una categoría por nombre."""
    try:
        return FruitCategory[name.upper()]
    except KeyError:
        return FruitCategory.UNKNOWN

def get_group_by_category(category: FruitCategory) -> LabelerGroup:
    """Obtiene el grupo de etiquetadoras por categoría."""
    mapping = {
        FruitCategory.APPLE: LabelerGroup.GROUP_APPLE,
        FruitCategory.PEAR: LabelerGroup.GROUP_PEAR,
        FruitCategory.LEMON: LabelerGroup.GROUP_LEMON
    }
    return mapping.get(category, LabelerGroup.GROUP_APPLE)

def validate_category(category: Any) -> Tuple[bool, Optional[FruitCategory]]:
    """Valida y convierte una categoría a FruitCategory."""
    if isinstance(category, FruitCategory):
        return True, category
    
    if isinstance(category, str):
        try:
            cat = FruitCategory[category.upper()]
            return True, cat
        except KeyError:
            return False, None
    
    return False, None

def validate_pin_configuration(pins: Dict[str, int]) -> Tuple[bool, List[str]]:
    """Valida una configuración de pines GPIO."""
    errors = []
    
    for pin_name, pin_num in pins.items():
        if not isinstance(pin_num, int):
            errors.append(f"Pin {pin_name} debe ser entero")
        elif not (GPIO_PIN_MIN <= pin_num <= GPIO_PIN_MAX):
            errors.append(f"Pin {pin_name}={pin_num} fuera de rango válido")
    
    # Verificar duplicados
    pin_values = list(pins.values())
    if len(pin_values) != len(set(pin_values)):
        errors.append("Pines duplicados detectados")
    
    return len(errors) == 0, errors

def get_all_categories() -> List[FruitCategory]:
    """Obtiene todas las categorías válidas (sin UNKNOWN)."""
    return [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]

def get_category_distribution() -> Dict[FruitCategory, Dict[str, Any]]:
    """Obtiene la distribución de categorías con sus detalles."""
    return {
        FruitCategory.APPLE: {
            "emoji": "🍎",
            "group_id": 0,
            "labelers": [0, 1],
            "diverter_id": 0,
            "color": "#FF4444"
        },
        FruitCategory.PEAR: {
            "emoji": "🍐",
            "group_id": 1,
            "labelers": [2, 3],
            "diverter_id": 1,
            "color": "#90EE90"
        },
        FruitCategory.LEMON: {
            "emoji": "🍋",
            "group_id": 2,
            "labelers": [4, 5],
            "diverter_id": None,
            "color": "#FFFF00"
        }
    }

__all__ = [
    # Enums
    'SystemState', 'AlertLevel', 'FruitCategory', 'LabelerGroup',
    'ProcessingPriority', 'OptimizationMode', 'HardwareType', 
    'SensorType', 'UserRole',
    
    # Dataclasses y NamedTuples
    'FruitDetectionResult', 'HardwareConfig', 'SystemPerformanceMetrics',
    
    # Constantes
    'LABELERS_PER_GROUP', 'NUM_LABELER_GROUPS', 'TOTAL_LABELERS',
    'MAX_THROUGHPUT_PER_MINUTE', 'MIN_CONFIDENCE_THRESHOLD',
    'MAX_PROCESSING_TIME_MS', 'OPTIMAL_BELT_SPEED_MPS',
    'GPIO_PIN_MIN', 'GPIO_PIN_MAX', 'PWM_FREQUENCY_HZ',
    'SERVO_MIN_ANGLE', 'SERVO_MAX_ANGLE',
    'DEFAULT_MOTOR_PINS', 'DEFAULT_DIVERTER_CONFIG', 'DEFAULT_SYSTEM_SETTINGS',
    
    # Utilidades
    'get_category_emoji', 'get_category_by_name', 'get_group_by_category',
    'validate_category', 'validate_pin_configuration', 'get_all_categories',
    'get_category_distribution'
]