# metrics_system.py
"""
Sistema de Métricas y Telemetría FruPrint v4.0 - ENHANCED
=========================================================

Módulo especializado en métricas, telemetría, análisis de rendimiento
y estadísticas en tiempo real del sistema industrial de etiquetado.

MEJORAS v4.0:
- Estadísticas en tiempo real con ventanas deslizantes
- Análisis de tendencias automático
- Alertas inteligentes con auto-resolución
- Métricas de calidad y mantenimiento predictivo
- Exportación de métricas en múltiples formatos
- Agregación y resumen de métricas

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0.1 - MODULAR ARCHITECTURE ENHANCED
"""

import time
import uuid
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Any, Deque
from collections import deque
import threading
import json

from system_types import (
    FruitCategory, AlertLevel, TOTAL_LABELERS,
    LABELERS_PER_GROUP, MAX_THROUGHPUT_PER_MINUTE
)

# ==================== DATACLASSES DE MÉTRICAS ====================

@dataclass
class UltraSystemAlert:
    """Alerta ultra-avanzada del sistema con resolución automática."""
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
    resolution_time: Optional[datetime] = None
    occurrence_count: int = 1

    def can_auto_resolve(self) -> bool:
        """Verifica si la alerta puede auto-resolverse."""
        return self.level in (AlertLevel.WARNING, AlertLevel.INFO) and not self.resolved
    
    def mark_resolved(self):
        """Marca la alerta como resuelta."""
        self.resolved = True
        self.resolution_time = datetime.now()
    
    def time_since_alert(self) -> float:
        """Retorna segundos transcurridos desde la alerta."""
        return (datetime.now() - self.timestamp).total_seconds()

@dataclass
class UltraCategoryMetrics:
    """Métricas ultra-detalladas por categoría con análisis de tendencias."""
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
    
    # Nuevas métricas de tendencia
    confidence_history: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    processing_time_history: Deque[float] = field(default_factory=lambda: deque(maxlen=100))
    detection_timestamps: Deque[datetime] = field(default_factory=lambda: deque(maxlen=200))
    
    def update_confidence(self, confidence: float):
        """Actualiza historial de confianza."""
        self.confidence_history.append(confidence)
        if len(self.confidence_history) > 0:
            self.avg_confidence = statistics.mean(self.confidence_history)
    
    def update_processing_time(self, time_ms: float):
        """Actualiza historial de tiempo de procesamiento."""
        self.processing_time_history.append(time_ms)
        if len(self.processing_time_history) > 0:
            self.processing_time_avg_ms = statistics.mean(self.processing_time_history)
    
    def record_detection(self):
        """Registra una nueva detección."""
        self.total_detected += 1
        now = datetime.now()
        self.last_detection = now
        self.detection_timestamps.append(now)
        self._calculate_throughput()
    
    def _calculate_throughput(self):
        """Calcula throughput basado en últimas detecciones."""
        if len(self.detection_timestamps) < 2:
            return
        
        cutoff_time = datetime.now() - timedelta(hours=1)
        recent = [t for t in self.detection_timestamps if t > cutoff_time]
        self.throughput_per_hour = len(recent)
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Analiza tendencias en las métricas."""
        analysis = {
            "confidence_trend": "stable",
            "processing_time_trend": "stable",
            "throughput_trend": "stable"
        }
        
        if len(self.confidence_history) >= 20:
            recent = list(self.confidence_history)[-10:]
            older = list(self.confidence_history)[-20:-10]
            if statistics.mean(recent) > statistics.mean(older) * 1.05:
                analysis["confidence_trend"] = "improving"
            elif statistics.mean(recent) < statistics.mean(older) * 0.95:
                analysis["confidence_trend"] = "declining"
        
        return analysis

@dataclass
class LabelerMetrics:
    """Métricas específicas de una etiquetadora con mantenimiento predictivo."""
    labeler_id: int
    category: FruitCategory
    activations_count: int = 0
    total_runtime_seconds: float = 0.0
    success_rate: float = 100.0
    last_activation: Optional[datetime] = None
    maintenance_score: float = 100.0
    wear_level: float = 0.0
    
    # Métricas de mantenimiento predictivo
    total_cycles: int = 0
    failure_count: int = 0
    avg_cycle_time: float = 0.0
    estimated_remaining_life_percent: float = 100.0
    next_maintenance_in_cycles: int = 10000
    
    def record_activation(self, duration: float, success: bool = True):
        """Registra una activación."""
        self.activations_count += 1
        self.total_cycles += 1
        self.total_runtime_seconds += duration
        self.last_activation = datetime.now()
        
        if not success:
            self.failure_count += 1
            self.success_rate = ((self.activations_count - self.failure_count) / 
                               self.activations_count * 100)
        
        self._update_wear_level()
        self._calculate_maintenance_score()
    
    def _update_wear_level(self):
        """Actualiza el nivel de desgaste."""
        # Modelo simple: cada 1000 ciclos = 1% desgaste
        self.wear_level = min(100.0, (self.total_cycles / 1000.0))
        self.estimated_remaining_life_percent = max(0.0, 100.0 - self.wear_level)
    
    def _calculate_maintenance_score(self):
        """Calcula score de mantenimiento."""
        # Factor de éxito
        success_factor = self.success_rate / 100.0
        # Factor de desgaste
        wear_factor = 1.0 - (self.wear_level / 100.0)
        # Score combinado
        self.maintenance_score = (success_factor * 0.6 + wear_factor * 0.4) * 100
    
    def needs_maintenance(self) -> bool:
        """Determina si necesita mantenimiento."""
        return (self.maintenance_score < 70.0 or 
                self.wear_level > 80.0 or
                self.success_rate < 90.0)

@dataclass
class UltraSystemMetrics:
    """Métricas ultra-completas del sistema con análisis avanzado."""
    timestamp: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    
    # Procesamiento general
    frames_processed: int = 0
    total_fruits_detected: int = 0
    total_labels_applied: int = 0
    error_count: int = 0
    
    # Performance con ventanas de tiempo
    throughput_items_per_minute: float = 0.0
    throughput_last_hour: float = 0.0
    throughput_last_24h: float = 0.0
    avg_processing_time_ms: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    temperature_c: float = 0.0
    
    # Por categoría
    category_metrics: Dict[FruitCategory, UltraCategoryMetrics] = field(default_factory=dict)
    
    # Predicciones y optimización
    predicted_throughput: float = 0.0
    efficiency_score: float = 0.0
    oee_percentage: float = 0.0
    quality_index: float = 0.0
    
    # Sistema de etiquetadoras lineales
    active_group_id: int = 0
    group_positions: Dict[int, str] = field(default_factory=dict)
    labeler_switch_count: int = 0
    motor_runtime_hours: float = 0.0
    
    # Nuevas métricas avanzadas
    peak_throughput: float = 0.0
    avg_confidence_overall: float = 0.0
    system_health_score: float = 100.0
    uptime_percentage: float = 100.0

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
    
    def calculate_overall_health(self) -> float:
        """Calcula el score de salud general del sistema."""
        factors = []
        
        # Factor de eficiencia
        if self.oee_percentage > 0:
            factors.append(self.oee_percentage / 100.0)
        
        # Factor de calidad
        if self.quality_index > 0:
            factors.append(self.quality_index / 100.0)
        
        # Factor de uptime
        factors.append(self.uptime_percentage / 100.0)
        
        # Factor de errores
        if self.frames_processed > 0:
            error_rate = self.error_count / self.frames_processed
            factors.append(1.0 - min(error_rate, 1.0))
        
        if factors:
            self.system_health_score = statistics.mean(factors) * 100
        
        return self.system_health_score

@dataclass
class OptimizationResult:
    """Resultado de optimización del sistema con métricas de impacto."""
    timestamp: datetime = field(default_factory=datetime.now)
    mode: str = "adaptive"
    improvements: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    estimated_impact: float = 0.0
    applied: bool = False
    validation_status: str = "pending"

# ==================== GESTOR DE MÉTRICAS ====================

class MetricsManager:
    """Gestor centralizado de métricas del sistema con análisis avanzado."""
    
    def __init__(self):
        self.metrics = UltraSystemMetrics()
        self.alerts: Deque[UltraSystemAlert] = deque(maxlen=5000)
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
        
        # Historial de métricas
        self._metrics_history: Deque[Dict[str, Any]] = deque(maxlen=1000)
        
        # Timestamp de inicio
        self._start_time = time.time()
        self._last_snapshot = time.time()
    
    def update_uptime(self):
        """Actualiza el tiempo de actividad y calcula uptime percentage."""
        with self._metrics_lock:
            self.metrics.uptime_seconds = time.time() - self._start_time
            self.metrics.timestamp = datetime.now()
            
            # Calcular uptime percentage (basado en errores y paradas)
            total_time = self.metrics.uptime_seconds
            if total_time > 0:
                # Asumir que errores causan pequeños downtimes
                downtime_estimate = self.metrics.error_count * 5  # 5 segundos por error
                self.metrics.uptime_percentage = ((total_time - downtime_estimate) / 
                                                  total_time * 100)
                self.metrics.uptime_percentage = max(0.0, min(100.0, 
                                                             self.metrics.uptime_percentage))
    
    def send_alert(self, level: AlertLevel, component: str, message: str, 
                   details: Dict = None, category: Optional[FruitCategory] = None) -> UltraSystemAlert:
        """Envía una alerta al sistema con deduplicación inteligente."""
        # Buscar alertas similares recientes
        similar_alert = self._find_similar_alert(component, message)
        
        if similar_alert and not similar_alert.resolved:
            # Incrementar contador en lugar de crear nueva alerta
            similar_alert.occurrence_count += 1
            similar_alert.timestamp = datetime.now()
            return similar_alert
        
        alert = UltraSystemAlert(
            level=level,
            component=component,
            message=message,
            details=details or {},
            category=category
        )
        
        self.alerts.append(alert)
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
        
        # Auto-resolución de alertas antiguas de bajo nivel
        self._auto_resolve_old_alerts()
        
        return alert
    
    def _find_similar_alert(self, component: str, message: str) -> Optional[UltraSystemAlert]:
        """Busca una alerta similar reciente."""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        for alert in reversed(self.alerts):
            if (alert.component == component and 
                alert.message == message and 
                alert.timestamp > cutoff_time):
                return alert
        
        return None
    
    def _auto_resolve_old_alerts(self):
        """Auto-resuelve alertas antiguas de bajo nivel."""
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        for alert in self.alerts:
            if (alert.can_auto_resolve() and 
                alert.timestamp < cutoff_time and 
                not alert.auto_resolution_attempted):
                alert.auto_resolution_attempted = True
                alert.mark_resolved()
    
    def update_category_metrics(self, category: FruitCategory, detected: int = 0, 
                                labeled: int = 0, confidence: float = 0.0,
                                processing_time_ms: float = 0.0):
        """Actualiza métricas de una categoría con análisis completo."""
        with self._metrics_lock:
            if category in self.category_metrics:
                metrics = self.category_metrics[category]
                
                if detected > 0:
                    for _ in range(detected):
                        metrics.record_detection()
                
                if labeled > 0:
                    metrics.total_labeled += labeled
                    # Calcular accuracy
                    if metrics.total_detected > 0:
                        metrics.accuracy_rate = (metrics.total_labeled / 
                                                metrics.total_detected * 100)
                
                if confidence > 0:
                    metrics.update_confidence(confidence)
                
                if processing_time_ms > 0:
                    metrics.update_processing_time(processing_time_ms)
                
                # Calcular quality score
                metrics.quality_score = self._calculate_quality_score(metrics)
    
    def _calculate_quality_score(self, metrics: UltraCategoryMetrics) -> float:
        """Calcula el score de calidad para una categoría."""
        factors = []
        
        # Factor de confianza
        if metrics.avg_confidence > 0:
            factors.append(metrics.avg_confidence)
        
        # Factor de accuracy
        if metrics.accuracy_rate > 0:
            factors.append(metrics.accuracy_rate / 100.0)
        
        # Factor de errores
        if metrics.total_detected > 0:
            error_rate = metrics.error_count / metrics.total_detected
            factors.append(1.0 - min(error_rate, 1.0))
        
        return statistics.mean(factors) * 100 if factors else 0.0
    
    def update_labeler_metrics(self, labeler_id: int, activated: bool = False, 
                               success: bool = True, runtime: float = 0.0):
        """Actualiza métricas de una etiquetadora con mantenimiento predictivo."""
        with self._metrics_lock:
            if labeler_id in self.labeler_metrics:
                metrics = self.labeler_metrics[labeler_id]
                
                if activated:
                    metrics.record_activation(runtime, success)
                    
                    # Verificar si necesita mantenimiento
                    if metrics.needs_maintenance():
                        self.send_alert(
                            AlertLevel.WARNING,
                            f"Labeler-{labeler_id}",
                            f"Mantenimiento requerido (Score: {metrics.maintenance_score:.1f}%)",
                            details={"wear_level": metrics.wear_level,
                                   "success_rate": metrics.success_rate}
                        )
    
    def calculate_oee(self) -> float:
        """Calcula el OEE (Overall Equipment Effectiveness) mejorado."""
        # Disponibilidad basada en uptime real
        availability = self.metrics.uptime_percentage / 100.0
        
        # Performance basado en throughput vs capacidad
        if MAX_THROUGHPUT_PER_MINUTE > 0:
            performance = min(1.0, self.metrics.throughput_items_per_minute / 
                            MAX_THROUGHPUT_PER_MINUTE)
        else:
            performance = 0.95
        
        # Calidad basada en accuracy promedio
        quality_scores = [m.accuracy_rate / 100.0 
                         for m in self.category_metrics.values() 
                         if m.accuracy_rate > 0]
        quality = statistics.mean(quality_scores) if quality_scores else 0.98
        
        oee = availability * performance * quality * 100
        return round(oee, 2)
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Obtiene un snapshot completo de todas las métricas."""
        with self._metrics_lock:
            # Calcular métricas derivadas
            self.metrics.calculate_overall_health()
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "system": asdict(self.metrics),
                "categories": {
                    cat.fruit_name: {
                        **asdict(metrics),
                        "trend_analysis": metrics.get_trend_analysis()
                    }
                    for cat, metrics in self.category_metrics.items()
                },
                "labelers": {
                    lid: {
                        **asdict(metrics),
                        "needs_maintenance": metrics.needs_maintenance()
                    }
                    for lid, metrics in self.labeler_metrics.items()
                },
                "alerts": [asdict(alert) for alert in list(self.alerts)[-50:]],
                "summary": self._generate_summary()
            }
            
            # Guardar en historial
            self._metrics_history.append(snapshot)
            
            return snapshot
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Genera un resumen ejecutivo de métricas."""
        return {
            "total_processed": self.metrics.frames_processed,
            "total_detected": self.metrics.total_fruits_detected,
            "total_labeled": self.metrics.total_labels_applied,
            "overall_health": round(self.metrics.system_health_score, 2),
            "oee": round(self.metrics.oee_percentage, 2),
            "uptime_hours": round(self.metrics.uptime_seconds / 3600, 2),
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "critical_alerts": len([a for a in self.alerts 
                                  if a.level == AlertLevel.CRITICAL and not a.resolved])
        }
    
    def get_recent_alerts(self, count: int = 50, level: Optional[AlertLevel] = None,
                         component: Optional[str] = None, unresolved_only: bool = False) -> List[UltraSystemAlert]:
        """Obtiene alertas recientes con filtros avanzados."""
        alerts = list(self.alerts)
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if component:
            alerts = [a for a in alerts if a.component == component]
        
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        
        return alerts[-count:]
    
    def clear_resolved_alerts(self):
        """Limpia alertas resueltas antiguas."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = deque(
            [a for a in self.alerts if not a.resolved or a.timestamp > cutoff_time],
            maxlen=5000
        )
    
    def export_metrics(self, format: str = "json") -> str:
        """Exporta métricas en formato especificado."""
        snapshot = self.get_metrics_snapshot()
        
        if format == "json":
            return json.dumps(snapshot, indent=2, default=str)
        elif format == "csv":
            # Simplificado para CSV
            return self._export_to_csv(snapshot)
        else:
            return json.dumps(snapshot, default=str)
    
    def _export_to_csv(self, snapshot: Dict) -> str:
        """Exporta métricas a formato CSV."""
        lines = ["timestamp,metric,value"]
        
        system_metrics = snapshot["system"]
        for key, value in system_metrics.items():
            if isinstance(value, (int, float)):
                lines.append(f"{snapshot['timestamp']},{key},{value}")
        
        return "\n".join(lines)
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Analiza tendencias de performance."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [m for m in self._metrics_history 
                         if datetime.fromisoformat(m["timestamp"]) > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        throughputs = [m["system"]["throughput_items_per_minute"] 
                      for m in recent_metrics if "system" in m]
        
        return {
            "period_hours": hours,
            "avg_throughput": statistics.mean(throughputs) if throughputs else 0,
            "peak_throughput": max(throughputs) if throughputs else 0,
            "min_throughput": min(throughputs) if throughputs else 0,
            "throughput_trend": self._calculate_trend(throughputs)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula tendencia en una lista de valores."""
        if len(values) < 10:
            return "insufficient_data"
        
        mid = len(values) // 2
        first_half = statistics.mean(values[:mid])
        second_half = statistics.mean(values[mid:])
        
        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        else:
            return "stable"

__all__ = [
    'UltraSystemAlert', 'UltraCategoryMetrics', 'LabelerMetrics',
    'UltraSystemMetrics', 'OptimizationResult', 'MetricsManager'
]