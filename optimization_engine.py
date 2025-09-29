# optimization_engine.py
"""
Motor de Optimización y Predicción FruPrint v4.0
================================================

Sistema avanzado de análisis de patrones, predicción y optimización
automática para el sistema industrial de etiquetado.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import statistics
from datetime import datetime
from collections import deque, defaultdict, Counter
from typing import Dict, List, Optional, Any

from system_types import FruitCategory, FruitDetectionResult, OptimizationMode
from metrics_system import OptimizationResult

# ==================== ANALIZADOR DE PATRONES ====================

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
    
    def analyze_efficiency_trend(self) -> Dict[str, float]:
        """Analiza tendencias de eficiencia."""
        if len(self.pattern_history) < 50:
            return {"trend": 0.0, "confidence": 0.0}
        
        recent = list(self.pattern_history)[-50:]
        old = list(self.pattern_history)[-100:-50] if len(self.pattern_history) >= 100 else []
        
        if not old:
            return {"trend": 0.0, "confidence": 0.5}
        
        # Comparar throughput promedio
        recent_throughput = sum(p.get('total_detections', 0) for p in recent) / len(recent)
        old_throughput = sum(p.get('total_detections', 0) for p in old) / len(old)
        
        if old_throughput > 0:
            trend = (recent_throughput - old_throughput) / old_throughput
        else:
            trend = 0.0
        
        return {
            "trend": trend,
            "confidence": 0.8,
            "recent_avg": recent_throughput,
            "old_avg": old_throughput
        }

# ==================== MOTOR DE PREDICCIÓN ====================

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
    
    def calculate_prediction_accuracy(self, predicted: float, actual: float) -> float:
        """Calcula la precisión de una predicción."""
        if actual == 0:
            return 0.0
        
        error = abs(predicted - actual) / actual
        accuracy = max(0.0, 1.0 - error)
        return accuracy

# ==================== OPTIMIZADOR DEL SISTEMA ====================

class SystemOptimizer:
    """Optimizador del sistema con múltiples estrategias."""
    
    def __init__(self, pattern_analyzer: UltraPatternAnalyzer, 
                 prediction_engine: UltraPredictionEngine):
        self.pattern_analyzer = pattern_analyzer
        self.prediction_engine = prediction_engine
        self.current_mode = OptimizationMode.ADAPTIVE
        
        # Estrategias de optimización
        self.strategies = {
            OptimizationMode.SPEED: self._optimize_for_speed,
            OptimizationMode.ACCURACY: self._optimize_for_accuracy,
            OptimizationMode.EFFICIENCY: self._optimize_for_efficiency,
            OptimizationMode.ADAPTIVE: self._optimize_adaptive
        }
    
    async def optimize(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Ejecuta optimización basada en el modo actual."""
        strategy = self.strategies.get(self.current_mode, self._optimize_adaptive)
        return await strategy(metrics)
    
    async def _optimize_for_speed(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para velocidad máxima."""
        improvements = {"throughput": 1.15, "response_time": 0.85}
        return OptimizationResult(
            mode=OptimizationMode.SPEED.value,
            improvements=improvements,
            recommendations=[
                "Incrementar velocidad de banda",
                "Reducir tiempo de análisis IA",
                "Precalentar etiquetadoras"
            ],
            confidence=0.8
        )
    
    async def _optimize_for_accuracy(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para precisión máxima."""
        improvements = {"accuracy": 1.05, "error_rate": 0.9}
        return OptimizationResult(
            mode=OptimizationMode.ACCURACY.value,
            improvements=improvements,
            recommendations=[
                "Aumentar tiempo de análisis",
                "Usar múltiples detectores",
                "Calibrar sensores"
            ],
            confidence=0.9
        )
    
    async def _optimize_for_efficiency(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para eficiencia energética."""
        improvements = {"energy_consumption": 0.85, "maintenance_cost": 0.9}
        return OptimizationResult(
            mode=OptimizationMode.EFFICIENCY.value,
            improvements=improvements,
            recommendations=[
                "Optimizar ciclos de motor",
                "Reducir activaciones innecesarias",
                "Modo standby inteligente"
            ],
            confidence=0.85
        )
    
    async def _optimize_adaptive(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización adaptativa basada en patrones."""
        # Análisis de patrones recientes
        if len(self.pattern_analyzer.pattern_history) > 10:
            recent_patterns = list(self.pattern_analyzer.pattern_history)[-10:]
            
            # Determinar mejor estrategia basada en patrones
            avg_throughput = sum(p.get('total_detections', 0) for p in recent_patterns) / len(recent_patterns)
            
            if avg_throughput > 50:
                return await self._optimize_for_speed(metrics)
            elif avg_throughput < 20:
                return await self._optimize_for_accuracy(metrics)
            else:
                return await self._optimize_for_efficiency(metrics)
        
        return OptimizationResult(confidence=0.5)
    
    def set_optimization_mode(self, mode: OptimizationMode):
        """Cambia el modo de optimización."""
        self.current_mode = mode
    
    def analyze_system_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el rendimiento general del sistema."""
        analysis = {
            "overall_health": "good",
            "bottlenecks": [],
            "recommendations": [],
            "predicted_issues": []
        }
        
        # Analizar throughput
        throughput = metrics.get('throughput_items_per_minute', 0)
        if throughput < 10:
            analysis["bottlenecks"].append("Low throughput detected")
            analysis["recommendations"].append("Check belt speed and camera exposure")
        
        # Analizar errores
        error_rate = metrics.get('error_count', 0) / max(1, metrics.get('frames_processed', 1))
        if error_rate > 0.05:
            analysis["overall_health"] = "warning"
            analysis["bottlenecks"].append("High error rate")
            analysis["recommendations"].append("Calibrate sensors and check lighting")
        
        return analysis

__all__ = [
    'UltraPatternAnalyzer', 'UltraPredictionEngine', 'SystemOptimizer'
]
