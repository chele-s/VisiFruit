# metrics_system.py
"""
Sistema de Métricas y Telemetría FruPrint v4.0
==============================================

Módulo especializado en métricas, telemetría y análisis de rendimiento
del sistema industrial de etiquetado.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Any
from collections import deque
import threading

from system_types import (
    FruitCategory, AlertLevel, TOTAL_LABELERS,
    LABELERS_PER_GROUP
)

# ==================== DATACLASSES DE MÉTRICAS ====================

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

    # Aliases para compatibilidad
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
class OptimizationResult:
    """Resultado de optimización del sistema."""
    timestamp: datetime = field(default_factory=datetime.now)
    mode: str = "adaptive"
    improvements: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    estimated_impact: float = 0.0

# ==================== GESTOR DE MÉTRICAS ====================

class MetricsManager:
    """Gestor centralizado de métricas del sistema."""
    
    def __init__(self):
        self.metrics = UltraSystemMetrics()
        self.alerts = deque(maxlen=5000)
        self.alert_callbacks: List = []
        
        # Métricas por categoría
        self.category_metrics = {
            FruitCategory.APPLE: UltraCategoryMetrics(category=FruitCategory.APPLE),
            FruitCategory.PEAR: UltraCategoryMetrics(category=FruitCategory.PEAR),
            FruitCategory.LEMON: UltraCategoryMetrics(category=FruitCategory.LEMON)
        }
        
        # Métricas por etiquetadora
        self.labeler_metrics = {}
        categories = [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]
        for i in range(TOTAL_LABELERS):
            group_id = i // LABELERS_PER_GROUP
            category = categories[group_id] if group_id < len(categories) else FruitCategory.UNKNOWN
            self.labeler_metrics[i] = LabelerMetrics(labeler_id=i, category=category)
        
        # Thread safety
        self._metrics_lock = threading.RLock()
        
        # Timestamp de inicio
        self._start_time = time.time()
    
    def update_uptime(self):
        """Actualiza el tiempo de actividad."""
        with self._metrics_lock:
            self.metrics.uptime_seconds = time.time() - self._start_time
            self.metrics.timestamp = datetime.now()
    
    def send_alert(self, level: AlertLevel, component: str, message: str, details: Dict = None):
        """Envía una alerta al sistema."""
        alert = UltraSystemAlert(
            level=level,
            component=component,
            message=message,
            details=details or {}
        )
        
        self.alerts.append(alert)
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
        
        return alert
    
    def update_category_metrics(self, category: FruitCategory, detected: int = 0, 
                                labeled: int = 0, confidence: float = 0.0):
        """Actualiza métricas de una categoría."""
        with self._metrics_lock:
            if category in self.category_metrics:
                metrics = self.category_metrics[category]
                
                if detected > 0:
                    metrics.total_detected += detected
                    metrics.last_detection = datetime.now()
                
                if labeled > 0:
                    metrics.total_labeled += labeled
                
                if confidence > 0:
                    # Promedio móvil de confianza
                    metrics.avg_confidence = (metrics.avg_confidence + confidence) / 2
    
    def update_labeler_metrics(self, labeler_id: int, activated: bool = False, 
                               success: bool = True, runtime: float = 0.0):
        """Actualiza métricas de una etiquetadora."""
        with self._metrics_lock:
            if labeler_id in self.labeler_metrics:
                metrics = self.labeler_metrics[labeler_id]
                
                if activated:
                    metrics.activations_count += 1
                    metrics.last_activation = datetime.now()
                
                if runtime > 0:
                    metrics.total_runtime_seconds += runtime
                
                if not success:
                    metrics.success_rate = (metrics.success_rate * 0.95)  # Decay
    
    def calculate_oee(self) -> float:
        """Calcula el OEE (Overall Equipment Effectiveness)."""
        availability = 0.95  # 95% disponibilidad (simulado)
        performance = min(1.0, self.metrics.throughput_items_per_minute / 60.0)
        quality = 0.98  # 98% calidad (simulado)
        
        oee = availability * performance * quality * 100
        return round(oee, 2)
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Obtiene un snapshot de todas las métricas."""
        with self._metrics_lock:
            return {
                "system": asdict(self.metrics),
                "categories": {cat.fruit_name: asdict(metrics) 
                             for cat, metrics in self.category_metrics.items()},
                "labelers": {lid: asdict(metrics) 
                           for lid, metrics in self.labeler_metrics.items()},
                "alerts": [asdict(alert) for alert in list(self.alerts)[-50:]]
            }
    
    def get_recent_alerts(self, count: int = 50, level: Optional[AlertLevel] = None) -> List[UltraSystemAlert]:
        """Obtiene alertas recientes, opcionalmente filtradas por nivel."""
        alerts = list(self.alerts)
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[-count:]
    
    def clear_resolved_alerts(self):
        """Limpia alertas resueltas antiguas."""
        # Mantener solo alertas no resueltas o recientes (últimas 24h)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = deque(
            [a for a in self.alerts if not a.resolved or a.timestamp > cutoff_time],
            maxlen=5000
        )

__all__ = [
    'UltraSystemAlert', 'UltraCategoryMetrics', 'LabelerMetrics',
    'UltraSystemMetrics', 'OptimizationResult', 'MetricsManager'
]
