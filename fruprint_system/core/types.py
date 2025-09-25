# fruprint_system/core/types.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List, Any, NamedTuple

# ==================== ENUMS ====================

class SystemState(Enum):
    """Estados del sistema industrial."""
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
    """Niveles de alerta detallados."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class FruitCategory(Enum):
    """Categorías de frutas con IDs específicos."""
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
        return self.labeler_group_id

class LabelerGroup(Enum):
    """Grupos de etiquetadoras."""
    GROUP_APPLE = (0, "apple", [0, 1])
    GROUP_PEAR = (1, "pear", [2, 3])
    GROUP_LEMON = (2, "lemon", [4, 5])
    
    def __init__(self, group_id: int, category: str, labeler_ids: list):
        self.group_id = group_id
        self.category = category
        self.labeler_ids = labeler_ids

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
    """Alerta avanzada del sistema."""
    id: str
    timestamp: datetime
    level: AlertLevel
    component: str
    message: str
    details: Dict[str, Any]
    category: Optional[FruitCategory] = None
    labeler_id: Optional[int] = None
    resolved: bool = False
    auto_resolution_attempted: bool = False

class FruitDetectionResult(NamedTuple):
    """Resultado de detección detallado."""
    category: FruitCategory
    confidence: float
    bbox: tuple[int, int, int, int]
    features: Dict[str, float]
    timestamp: datetime
    processing_time_ms: float

@dataclass
class UltraCategoryMetrics:
    """Métricas detalladas por categoría."""
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
    """Métricas completas del sistema."""
    timestamp: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    frames_processed: int = 0
    total_fruits_detected: int = 0
    total_labels_applied: int = 0
    error_count: int = 0
    throughput_items_per_minute: float = 0.0
    avg_processing_time_ms: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    temperature_c: float = 0.0
    category_metrics: Dict[FruitCategory, UltraCategoryMetrics] = field(default_factory=dict)
    predicted_throughput: float = 0.0
    efficiency_score: float = 0.0
    oee_percentage: float = 0.0
    active_group_id: int = 0
    group_positions: Dict[int, str] = field(default_factory=dict)
    labeler_switch_count: int = 0
    motor_runtime_hours: float = 0.0

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
