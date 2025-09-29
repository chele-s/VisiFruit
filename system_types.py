# system_types.py
"""
Tipos, Enums y Constantes del Sistema FruPrint v4.0
====================================================

Módulo centralizado de tipos de datos, enumeraciones y constantes
para el sistema industrial de etiquetado.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

from enum import Enum, auto
from typing import NamedTuple, Tuple, Dict

# ==================== CONSTANTES DE CONFIGURACIÓN ====================
LABELERS_PER_GROUP = 2
NUM_LABELER_GROUPS = 3
TOTAL_LABELERS = LABELERS_PER_GROUP * NUM_LABELER_GROUPS

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

# ==================== NAMED TUPLES ====================

class FruitDetectionResult(NamedTuple):
    """Resultado de detección ultra-detallado."""
    category: FruitCategory
    confidence: float
    bbox: Tuple[int, int, int, int]
    features: Dict[str, float]
    timestamp: object  # datetime
    processing_time_ms: float

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

__all__ = [
    'SystemState', 'AlertLevel', 'FruitCategory', 'LabelerGroup',
    'ProcessingPriority', 'OptimizationMode', 'FruitDetectionResult',
    'LABELERS_PER_GROUP', 'NUM_LABELER_GROUPS', 'TOTAL_LABELERS',
    'DEFAULT_MOTOR_PINS', 'DEFAULT_DIVERTER_CONFIG',
    'get_category_emoji', 'get_category_by_name', 'get_group_by_category'
]
