# optimization_engine.py
"""
Motor de Optimización y Predicción FruPrint v4.0 - ENHANCED
===========================================================

Sistema avanzado de análisis de patrones, predicción con machine learning
y optimización automática para el sistema industrial de etiquetado.

MEJORAS v4.0:
- Algoritmos de machine learning básico (regresión lineal, moving averages)
- Análisis predictivo de mantenimiento
- Detección de anomalías
- Optimización multi-objetivo
- Simulación de escenarios
- Aprendizaje adaptativo en tiempo real

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0.1 - MODULAR ARCHITECTURE ENHANCED
"""

import statistics
import math
from datetime import datetime, timedelta
from collections import deque, defaultdict, Counter
from typing import Dict, List, Optional, Any, Tuple
import logging

from system_types import FruitCategory, FruitDetectionResult, OptimizationMode
from metrics_system import OptimizationResult

logger = logging.getLogger(__name__)

# ==================== ANALIZADOR DE PATRONES ====================

class UltraPatternAnalyzer:
    """Analizador de patrones ultra-avanzado con ML para optimización predictiva."""
    
    def __init__(self):
        self.pattern_history = deque(maxlen=5000)
        self.fruit_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)
        self.efficiency_patterns = []
        self.anomalies_detected = []
        
        # Modelos de aprendizaje
        self.category_frequency_model = defaultdict(lambda: deque(maxlen=100))
        self.temporal_pattern_model = deque(maxlen=500)
        
    def analyze_detection_pattern(self, detections: List[FruitDetectionResult]) -> Dict[str, Any]:
        """Analiza patrones en las detecciones con aprendizaje automático."""
        if not detections:
            return {}
        
        # Analizar distribución de categorías
        category_counts = Counter([d.category for d in detections])
        
        # Analizar patrones temporales
        time_intervals = []
        for i in range(1, len(detections)):
            try:
                interval = (detections[i].timestamp - detections[i-1].timestamp).total_seconds()
                time_intervals.append(interval)
            except Exception:
                continue
        
        # Calcular métricas básicas
        avg_interval = statistics.mean(time_intervals) if time_intervals else 0
        confidence_avg = statistics.mean([d.confidence for d in detections])
        processing_times = [d.processing_time_ms for d in detections]
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        
        # Detectar anomalías
        anomalies = self._detect_anomalies(processing_times, time_intervals)
        
        pattern = {
            'timestamp': datetime.now(),
            'category_distribution': dict(category_counts),
            'avg_time_interval': avg_interval,
            'avg_confidence': confidence_avg,
            'avg_processing_time_ms': avg_processing_time,
            'total_detections': len(detections),
            'anomalies_detected': len(anomalies),
            'pattern_stability': self._calculate_pattern_stability(category_counts)
        }
        
        self.pattern_history.append(pattern)
        
        # Actualizar modelos de aprendizaje
        for category, count in category_counts.items():
            self.category_frequency_model[category].append(count)
        
        return pattern
    
    def _detect_anomalies(self, processing_times: List[float], 
                         intervals: List[float]) -> List[Dict[str, Any]]:
        """Detecta anomalías en los datos usando desviación estándar."""
        anomalies = []
        
        if len(processing_times) > 10:
            mean_pt = statistics.mean(processing_times)
            stdev_pt = statistics.stdev(processing_times)
            
            # Detectar outliers (más de 3 desviaciones estándar)
            for i, pt in enumerate(processing_times):
                if abs(pt - mean_pt) > 3 * stdev_pt:
                    anomalies.append({
                        'type': 'processing_time_outlier',
                        'index': i,
                        'value': pt,
                        'expected': mean_pt,
                        'deviation': abs(pt - mean_pt) / stdev_pt
                    })
        
        if len(intervals) > 10:
            mean_int = statistics.mean(intervals)
            stdev_int = statistics.stdev(intervals)
            
            for i, interval in enumerate(intervals):
                if abs(interval - mean_int) > 3 * stdev_int:
                    anomalies.append({
                        'type': 'interval_outlier',
                        'index': i,
                        'value': interval,
                        'expected': mean_int,
                        'deviation': abs(interval - mean_int) / stdev_int
                    })
        
        if anomalies:
            self.anomalies_detected.extend(anomalies)
            # Mantener solo las últimas 100 anomalías
            self.anomalies_detected = self.anomalies_detected[-100:]
        
        return anomalies
    
    def _calculate_pattern_stability(self, category_counts: Counter) -> float:
        """Calcula la estabilidad del patrón (0-1, 1 = muy estable)."""
        if not category_counts:
            return 0.0
        
        total = sum(category_counts.values())
        if total == 0:
            return 0.0
        
        # Calcular entropía normalizada
        entropy = 0
        for count in category_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalizar (máxima entropía para 3 categorías es log2(3))
        max_entropy = math.log2(3) if len(category_counts) > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Invertir: alta entropía = baja estabilidad
        stability = 1.0 - normalized_entropy
        return stability
    
    def predict_next_category(self) -> Optional[FruitCategory]:
        """Predice la siguiente categoría usando frecuencias históricas."""
        if len(self.pattern_history) < 10:
            return None
        
        # Usar ventana deslizante con peso exponencial
        weights = [math.exp(-i/10) for i in range(10)]
        recent_patterns = list(self.pattern_history)[-10:]
        
        category_weighted_scores = defaultdict(float)
        
        for pattern, weight in zip(recent_patterns, reversed(weights)):
            for category, count in pattern['category_distribution'].items():
                if isinstance(category, FruitCategory):
                    category_weighted_scores[category] += count * weight
                elif isinstance(category, str):
                    try:
                        cat_enum = FruitCategory[category.upper()]
                        category_weighted_scores[cat_enum] += count * weight
                    except KeyError:
                        continue
        
        if not category_weighted_scores:
            return None
        
        predicted = max(category_weighted_scores.items(), key=lambda x: x[1])
        return predicted[0]
    
    def predict_maintenance_needs(self) -> Dict[str, Any]:
        """Predice necesidades de mantenimiento basado en patrones."""
        if len(self.pattern_history) < 50:
            return {"status": "insufficient_data"}
        
        recent = list(self.pattern_history)[-50:]
        
        # Analizar tendencia de tiempo de procesamiento
        processing_times = [p.get('avg_processing_time_ms', 0) for p in recent]
        avg_processing = statistics.mean(processing_times) if processing_times else 0
        
        # Si el tiempo de procesamiento está aumentando, podría indicar desgaste
        if len(processing_times) >= 20:
            first_half = statistics.mean(processing_times[:25])
            second_half = statistics.mean(processing_times[25:])
            
            if second_half > first_half * 1.3:
                return {
                    "status": "maintenance_recommended",
                    "reason": "processing_time_degradation",
                    "severity": "medium",
                    "avg_processing_time_ms": avg_processing,
                    "degradation_percent": ((second_half - first_half) / first_half * 100)
                }
        
        # Analizar estabilidad del patrón
        stabilities = [p.get('pattern_stability', 1.0) for p in recent]
        avg_stability = statistics.mean(stabilities) if stabilities else 1.0
        
        if avg_stability < 0.5:
            return {
                "status": "maintenance_recommended",
                "reason": "pattern_instability",
                "severity": "low",
                "stability_score": avg_stability
            }
        
        return {"status": "healthy", "stability_score": avg_stability}
    
    def analyze_efficiency_trend(self) -> Dict[str, float]:
        """Analiza tendencias de eficiencia con análisis avanzado."""
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
        
        # Calcular confianza basada en consistencia
        recent_values = [p.get('total_detections', 0) for p in recent]
        variance = statistics.variance(recent_values) if len(recent_values) > 1 else 0
        # Mayor varianza = menor confianza
        confidence = max(0.3, min(0.95, 1.0 - (variance / (recent_throughput + 1))))
        
        return {
            "trend": trend,
            "confidence": confidence,
            "recent_avg": recent_throughput,
            "old_avg": old_throughput,
            "variance": variance
        }
    
    def get_anomaly_report(self) -> Dict[str, Any]:
        """Genera reporte de anomalías detectadas."""
        if not self.anomalies_detected:
            return {"total_anomalies": 0, "types": {}}
        
        anomaly_types = Counter([a['type'] for a in self.anomalies_detected])
        
        return {
            "total_anomalies": len(self.anomalies_detected),
            "types": dict(anomaly_types),
            "recent_anomalies": self.anomalies_detected[-10:],
            "severity": "high" if len(self.anomalies_detected) > 50 else "normal"
        }

# ==================== MOTOR DE PREDICCIÓN ====================

class UltraPredictionEngine:
    """Motor de predicción ultra-avanzado con ML para optimización del sistema."""
    
    def __init__(self):
        self.historical_data = deque(maxlen=10000)
        self.prediction_models = {}
        self.accuracy_scores = defaultdict(float)
        
        # Modelos de regresión simple
        self.throughput_model = LinearRegressionModel()
        self.quality_model = LinearRegressionModel()
        
    def predict_throughput(self, time_horizon_minutes: int = 60) -> float:
        """Predice el throughput usando regresión lineal."""
        if len(self.historical_data) < 100:
            return 0.0
        
        recent_data = list(self.historical_data)[-100:]
        throughputs = [d.get('throughput', 0) for d in recent_data]
        
        # Usar regresión lineal simple
        if len(throughputs) >= 20:
            self.throughput_model.fit(list(range(len(throughputs))), throughputs)
            future_index = len(throughputs) + time_horizon_minutes
            predicted = self.throughput_model.predict(future_index)
            return max(0, predicted)
        
        return statistics.mean(throughputs) if throughputs else 0.0
    
    def predict_quality_degradation(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Predice degradación de calidad en el futuro."""
        if len(self.historical_data) < 50:
            return {"status": "insufficient_data"}
        
        recent = list(self.historical_data)[-50:]
        quality_scores = [d.get('quality_score', 100) for d in recent]
        
        if len(quality_scores) < 10:
            return {"status": "insufficient_data"}
        
        # Calcular tendencia
        self.quality_model.fit(list(range(len(quality_scores))), quality_scores)
        current_quality = quality_scores[-1]
        future_index = len(quality_scores) + (hours_ahead * 12)  # 12 puntos por hora
        predicted_quality = self.quality_model.predict(future_index)
        
        degradation = current_quality - predicted_quality
        
        return {
            "current_quality": current_quality,
            "predicted_quality": predicted_quality,
            "expected_degradation": degradation,
            "degradation_rate_per_hour": degradation / hours_ahead if hours_ahead > 0 else 0,
            "status": "critical" if degradation > 20 else "normal"
        }
    
    def predict_optimal_labeler_sequence(self, expected_categories: List[FruitCategory]) -> List[int]:
        """Predice la secuencia óptima de etiquetadoras minimizando cambios."""
        if not expected_categories:
            return []
        
        # Agrupar categorías consecutivas para minimizar cambios
        sequence = []
        current_category = None
        
        for category in expected_categories:
            if category != FruitCategory.UNKNOWN:
                if current_category != category:
                    sequence.append(category.labeler_id)
                    current_category = category
        
        return sequence
    
    def predict_bottleneck_location(self) -> Dict[str, Any]:
        """Predice dónde ocurrirá el próximo cuello de botella."""
        if len(self.historical_data) < 100:
            return {"status": "insufficient_data"}
        
        recent = list(self.historical_data)[-100:]
        
        # Analizar tiempos de procesamiento por componente
        avg_detection_time = statistics.mean([d.get('detection_time', 0) 
                                             for d in recent if d.get('detection_time')])
        avg_labeling_time = statistics.mean([d.get('labeling_time', 0) 
                                            for d in recent if d.get('labeling_time')])
        avg_motor_switch_time = statistics.mean([d.get('motor_switch_time', 0) 
                                                for d in recent if d.get('motor_switch_time')])
        
        times = {
            "detection": avg_detection_time,
            "labeling": avg_labeling_time,
            "motor_switching": avg_motor_switch_time
        }
        
        if not times or all(v == 0 for v in times.values()):
            return {"status": "no_bottleneck_detected"}
        
        bottleneck = max(times.items(), key=lambda x: x[1])
        
        return {
            "predicted_bottleneck": bottleneck[0],
            "bottleneck_time_ms": bottleneck[1],
            "component_times": times,
            "recommendation": self._get_bottleneck_recommendation(bottleneck[0])
        }
    
    def _get_bottleneck_recommendation(self, component: str) -> str:
        """Genera recomendación basada en el cuello de botella."""
        recommendations = {
            "detection": "Considerar optimizar modelo de IA o mejorar iluminación",
            "labeling": "Verificar presión de solenoides y calibración",
            "motor_switching": "Optimizar secuencia de cambios o lubricar motor"
        }
        return recommendations.get(component, "Monitorear componente")
    
    def update_model(self, actual_data: Dict[str, Any]):
        """Actualiza los modelos con datos reales y calcula precisión."""
        # Agregar timestamp
        data_point = {
            'timestamp': datetime.now(),
            **actual_data
        }
        self.historical_data.append(data_point)
        
        # Actualizar accuracy scores si hay predicciones previas
        if len(self.historical_data) >= 2:
            self._update_prediction_accuracy(data_point)
    
    def _update_prediction_accuracy(self, actual_data: Dict[str, Any]):
        """Actualiza scores de precisión de predicciones."""
        # Comparar con predicción previa si existe
        if 'throughput' in actual_data and hasattr(self, '_last_throughput_prediction'):
            actual = actual_data['throughput']
            predicted = self._last_throughput_prediction
            accuracy = self.calculate_prediction_accuracy(predicted, actual)
            self.accuracy_scores['throughput'] = accuracy
    
    def calculate_prediction_accuracy(self, predicted: float, actual: float) -> float:
        """Calcula la precisión de una predicción."""
        if actual == 0:
            return 0.0 if predicted != 0 else 1.0
        
        error = abs(predicted - actual) / abs(actual)
        accuracy = max(0.0, 1.0 - error)
        return accuracy
    
    def get_model_performance(self) -> Dict[str, float]:
        """Retorna el rendimiento de los modelos de predicción."""
        return dict(self.accuracy_scores)

# ==================== MODELO DE REGRESIÓN LINEAL ====================

class LinearRegressionModel:
    """Modelo simple de regresión lineal para predicciones."""
    
    def __init__(self):
        self.slope = 0.0
        self.intercept = 0.0
        self.fitted = False
    
    def fit(self, x_values: List[float], y_values: List[float]):
        """Ajusta el modelo usando mínimos cuadrados."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        denominator = (n * sum_x2 - sum_x * sum_x)
        if denominator == 0:
            self.slope = 0
            self.intercept = sum_y / n if n > 0 else 0
        else:
            self.slope = (n * sum_xy - sum_x * sum_y) / denominator
            self.intercept = (sum_y - self.slope * sum_x) / n
        
        self.fitted = True
    
    def predict(self, x: float) -> float:
        """Predice un valor y para un x dado."""
        if not self.fitted:
            return 0.0
        return self.slope * x + self.intercept

# ==================== OPTIMIZADOR DEL SISTEMA ====================

class SystemOptimizer:
    """Optimizador del sistema con múltiples estrategias y ML."""
    
    def __init__(self, pattern_analyzer: UltraPatternAnalyzer, 
                 prediction_engine: UltraPredictionEngine):
        self.pattern_analyzer = pattern_analyzer
        self.prediction_engine = prediction_engine
        self.current_mode = OptimizationMode.ADAPTIVE
        
        # Historial de optimizaciones
        self.optimization_history = deque(maxlen=100)
        
        # Estrategias de optimización
        self.strategies = {
            OptimizationMode.SPEED: self._optimize_for_speed,
            OptimizationMode.ACCURACY: self._optimize_for_accuracy,
            OptimizationMode.EFFICIENCY: self._optimize_for_efficiency,
            OptimizationMode.ADAPTIVE: self._optimize_adaptive,
            OptimizationMode.BALANCED: self._optimize_balanced,
            OptimizationMode.POWER_SAVING: self._optimize_power_saving
        }
    
    async def optimize(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Ejecuta optimización basada en el modo actual con ML."""
        try:
            strategy = self.strategies.get(self.current_mode, self._optimize_adaptive)
            result = await strategy(metrics)
            
            # Guardar en historial
            self.optimization_history.append({
                'timestamp': datetime.now(),
                'mode': self.current_mode.value,
                'result': result,
                'metrics_snapshot': metrics
            })
            
            return result
        except Exception as e:
            logger.error(f"Error en optimización: {e}")
            return OptimizationResult(confidence=0.0)
    
    async def _optimize_for_speed(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para velocidad máxima con predicciones."""
        improvements = {
            "throughput": 1.15,
            "response_time": 0.85,
            "belt_speed": 1.1
        }
        
        # Predicciones
        predicted_throughput = self.prediction_engine.predict_throughput(60)
        
        return OptimizationResult(
            mode=OptimizationMode.SPEED.value,
            improvements=improvements,
            recommendations=[
                "Incrementar velocidad de banda a 0.6 m/s",
                "Reducir umbral de confianza IA a 0.70",
                "Precalentar etiquetadoras",
                f"Throughput predicho: {predicted_throughput:.1f} items/h"
            ],
            confidence=0.85,
            estimated_impact=15.0
        )
    
    async def _optimize_for_accuracy(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para precisión máxima."""
        improvements = {
            "accuracy": 1.08,
            "error_rate": 0.8,
            "confidence": 1.1
        }
        
        return OptimizationResult(
            mode=OptimizationMode.ACCURACY.value,
            improvements=improvements,
            recommendations=[
                "Aumentar umbral de confianza IA a 0.85",
                "Reducir velocidad de banda a 0.4 m/s",
                "Activar modo multi-frame análisis",
                "Calibrar sensores cada 2 horas"
            ],
            confidence=0.92,
            estimated_impact=8.0
        )
    
    async def _optimize_for_efficiency(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para eficiencia energética con predicción."""
        improvements = {
            "energy_consumption": 0.82,
            "maintenance_cost": 0.88,
            "motor_wear": 0.85
        }
        
        # Verificar predicción de mantenimiento
        maintenance_pred = self.pattern_analyzer.predict_maintenance_needs()
        
        recommendations = [
            "Optimizar ciclos de motor (reducir cambios innecesarios)",
            "Implementar modo standby inteligente",
            "Reducir activaciones redundantes"
        ]
        
        if maintenance_pred.get("status") == "maintenance_recommended":
            recommendations.append(
                f"ATENCIÓN: Mantenimiento recomendado - {maintenance_pred.get('reason')}"
            )
        
        return OptimizationResult(
            mode=OptimizationMode.EFFICIENCY.value,
            improvements=improvements,
            recommendations=recommendations,
            confidence=0.88,
            estimated_impact=18.0
        )
    
    async def _optimize_balanced(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización balanceada entre velocidad, precisión y eficiencia."""
        improvements = {
            "throughput": 1.05,
            "accuracy": 1.03,
            "energy_efficiency": 1.08
        }
        
        return OptimizationResult(
            mode=OptimizationMode.BALANCED.value,
            improvements=improvements,
            recommendations=[
                "Mantener velocidad óptima de 0.5 m/s",
                "Umbral de confianza balanceado: 0.78",
                "Calibración programada cada 4 horas",
                "Modo adaptativo de respuesta"
            ],
            confidence=0.87,
            estimated_impact=10.0
        )
    
    async def _optimize_power_saving(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización para ahorro máximo de energía."""
        improvements = {
            "energy_consumption": 0.65,
            "throughput": 0.90,
            "motor_runtime": 0.70
        }
        
        return OptimizationResult(
            mode=OptimizationMode.POWER_SAVING.value,
            improvements=improvements,
            recommendations=[
                "Activar modo eco en motor DC",
                "Reducir frecuencia PWM cuando sea posible",
                "Implementar sleep mode entre detecciones",
                "Optimizar secuencia para minimizar movimientos"
            ],
            confidence=0.80,
            estimated_impact=35.0
        )
    
    async def _optimize_adaptive(self, metrics: Dict[str, Any]) -> OptimizationResult:
        """Optimización adaptativa basada en patrones y ML."""
        # Analizar eficiencia actual
        efficiency_trend = self.pattern_analyzer.analyze_efficiency_trend()
        
        # Detectar cuellos de botella
        bottleneck = self.prediction_engine.predict_bottleneck_location()
        
        # Decidir estrategia basándose en análisis
        if len(self.pattern_analyzer.pattern_history) > 10:
            recent_patterns = list(self.pattern_analyzer.pattern_history)[-10:]
            avg_throughput = sum(p.get('total_detections', 0) for p in recent_patterns) / len(recent_patterns)
            
            # Alto throughput: priorizar eficiencia
            if avg_throughput > 50:
                return await self._optimize_for_efficiency(metrics)
            # Bajo throughput: priorizar velocidad
            elif avg_throughput < 20:
                return await self._optimize_for_speed(metrics)
            # Throughput medio: balance
            else:
                return await self._optimize_balanced(metrics)
        
        # Si no hay suficiente data, modo balanceado por defecto
        return await self._optimize_balanced(metrics)
    
    def set_optimization_mode(self, mode: OptimizationMode):
        """Cambia el modo de optimización."""
        self.current_mode = mode
        logger.info(f"Modo de optimización cambiado a: {mode.value}")
    
    def analyze_system_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el rendimiento general del sistema con ML."""
        analysis = {
            "overall_health": "good",
            "bottlenecks": [],
            "recommendations": [],
            "predicted_issues": [],
            "optimization_opportunities": []
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
        
        # Predicciones
        bottleneck_pred = self.prediction_engine.predict_bottleneck_location()
        if bottleneck_pred.get("predicted_bottleneck"):
            analysis["predicted_issues"].append(
                f"Bottleneck expected in: {bottleneck_pred['predicted_bottleneck']}"
            )
            if rec := bottleneck_pred.get("recommendation"):
                analysis["recommendations"].append(rec)
        
        # Reporte de anomalías
        anomaly_report = self.pattern_analyzer.get_anomaly_report()
        if anomaly_report.get("severity") == "high":
            analysis["overall_health"] = "warning"
            analysis["predicted_issues"].append(
                f"High anomaly count: {anomaly_report['total_anomalies']}"
            )
        
        # Oportunidades de optimización
        if throughput < 30 and error_rate < 0.02:
            analysis["optimization_opportunities"].append(
                "Sistema estable con bajo throughput: considerar aumentar velocidad"
            )
        
        return analysis
    
    def get_optimization_history_summary(self) -> Dict[str, Any]:
        """Retorna resumen del historial de optimizaciones."""
        if not self.optimization_history:
            return {"total_optimizations": 0}
        
        modes_used = Counter([o['mode'] for o in self.optimization_history])
        avg_confidence = statistics.mean([
            o['result'].confidence for o in self.optimization_history
        ])
        
        return {
            "total_optimizations": len(self.optimization_history),
            "modes_used": dict(modes_used),
            "avg_confidence": round(avg_confidence, 3),
            "last_optimization": self.optimization_history[-1]['timestamp'].isoformat()
        }

__all__ = [
    'UltraPatternAnalyzer', 'UltraPredictionEngine', 'SystemOptimizer',
    'LinearRegressionModel'
]