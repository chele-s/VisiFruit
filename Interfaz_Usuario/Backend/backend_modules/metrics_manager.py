"""
Sistema Ultra-Avanzado de Gestión de Métricas
============================================

Gestiona todas las métricas del sistema en tiempo real con:
- Recolección automática de métricas del sistema
- Análisis estadístico avanzado
- Predicciones basadas en tendencias
- Alertas automáticas por umbrales
- Exportación en múltiples formatos
- Dashboard de métricas en tiempo real

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import json
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
import numpy as np
import pandas as pd
import sqlite3
import pickle

logger = logging.getLogger("UltraMetricsManager")

@dataclass
class MetricPoint:
    """Punto de métrica individual."""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricSummary:
    """Resumen estadístico de una métrica."""
    metric_name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    std_dev: float
    percentiles: Dict[str, float]
    trend: str  # "increasing", "decreasing", "stable"
    prediction_1h: float
    last_updated: datetime

class UltraMetricsManager:
    """Gestor ultra-avanzado de métricas del sistema."""
    
    def __init__(self):
        self.metrics_buffer = deque(maxlen=10000)
        self.metric_summaries = {}
        self.alert_thresholds = {}
        self.prediction_models = {}
        self.db_path = "data/metrics.db"
        self.is_running = False
        
        # Métricas en tiempo real por categoría
        self.realtime_metrics = {
            "system": defaultdict(list),
            "production": defaultdict(list), 
            "labelers": defaultdict(list),
            "motor": defaultdict(list),
            "ia": defaultdict(list),
            "performance": defaultdict(list)
        }
        
        # Configuración de alertas por défaut
        self.default_thresholds = {
            "cpu_percent": {"warning": 70, "critical": 85},
            "memory_percent": {"warning": 80, "critical": 90},
            "disk_percent": {"warning": 80, "critical": 95},
            "temperature_cpu": {"warning": 70, "critical": 80},
            "error_rate": {"warning": 5, "critical": 10},
            "response_time": {"warning": 1000, "critical": 2000}
        }

    async def initialize(self, backend_system=None):
        """Inicializa el gestor de métricas."""
        try:
            # Guardar referencia al sistema backend
            self.backend_system = backend_system
            
            # Crear base de datos de métricas solo si no hay sistema backend
            if not backend_system:
                await self._init_database()
            
            # Cargar configuración de umbrales
            await self._load_thresholds()
            
            # Inicializar modelos predictivos
            await self._init_prediction_models()
            
            self.is_running = True
            logger.info("✅ Gestor de métricas inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando gestor de métricas: {e}")
            raise

    async def _init_database(self):
        """Inicializa la base de datos de métricas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla principal de métricas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                metric_name TEXT,
                value REAL,
                category TEXT,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Tabla de resúmenes estadísticos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metric_summaries (
                metric_name TEXT PRIMARY KEY,
                summary_data TEXT,
                last_updated DATETIME
            )
        """)
        
        # Tabla de alertas de métricas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metric_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                metric_name TEXT,
                alert_level TEXT,
                value REAL,
                threshold REAL,
                message TEXT
            )
        """)
        
        # Índices para rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)")
        
        conn.commit()
        conn.close()

    async def _load_thresholds(self):
        """Carga configuración de umbrales."""
        self.alert_thresholds = self.default_thresholds.copy()
        
        # Intentar cargar desde archivo de configuración
        try:
            with open("data/metric_thresholds.json", "r") as f:
                custom_thresholds = json.load(f)
                self.alert_thresholds.update(custom_thresholds)
        except FileNotFoundError:
            logger.info("No se encontró configuración personalizada de umbrales, usando valores por defecto")

    async def _init_prediction_models(self):
        """Inicializa modelos predictivos simples."""
        self.prediction_models = {
            "linear_trend": {},
            "moving_average": {},
            "exponential_smoothing": {}
        }

    async def save_metrics(self, metrics_data: Dict[str, Any], category: str = "system"):
        """Guarda métricas en el sistema."""
        try:
            timestamp = datetime.now()
            
            # Si tenemos sistema backend, usar su gestor de base de datos
            if self.backend_system and hasattr(self.backend_system, 'db_manager'):
                await self._save_metrics_to_main_db(metrics_data, category, timestamp)
            else:
                # Fallback a base de datos local
                await self._process_metrics_recursive(metrics_data, category, timestamp)
            
            # Actualizar buffer en memoria
            self._update_realtime_buffer(metrics_data, category, timestamp)
            
            # Verificar umbrales de alerta
            await self._check_alert_thresholds(metrics_data, category)
            
        except Exception as e:
            logger.error(f"Error guardando métricas: {e}")

    def _get_safe_connection(self, timeout: int = 30, retries: int = 3):
        """Obtiene una conexión SQLite segura con timeout y reintentos."""
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                conn.execute("PRAGMA journal_mode=WAL")  # Permite lecturas concurrentes
                conn.execute("PRAGMA busy_timeout=30000")  # 30 segundos de timeout
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Backoff exponencial
                    continue
                raise
        return None

    async def _process_metrics_recursive(self, data: Dict[str, Any], category: str, timestamp: datetime, prefix: str = ""):
        """Procesa métricas de forma recursiva."""
        conn = self._get_safe_connection()
        if not conn:
            logger.error("No se pudo obtener conexión a la base de datos")
            return
        cursor = conn.cursor()
        
        try:
            for key, value in data.items():
                metric_name = f"{prefix}{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Procesar diccionario anidado
                    await self._process_metrics_recursive(value, category, timestamp, f"{metric_name}.")
                elif isinstance(value, (int, float)):
                    # Guardar métrica numérica
                    cursor.execute("""
                        INSERT INTO metrics (timestamp, metric_name, value, category, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp,
                        metric_name,
                        float(value),
                        category,
                        json.dumps({}),
                        json.dumps({"type": type(value).__name__})
                    ))
                    
                    # Agregar al buffer en memoria
                    metric_point = MetricPoint(
                        timestamp=timestamp,
                        metric_name=metric_name,
                        value=float(value),
                        tags={"category": category}
                    )
                    self.metrics_buffer.append(metric_point)
            
            conn.commit()
            
        finally:
            conn.close()

    async def _save_metrics_to_main_db(self, metrics_data: Dict[str, Any], category: str, timestamp: datetime):
        """Guarda métricas en la base de datos principal del sistema."""
        try:
            if not self.backend_system or not hasattr(self.backend_system, 'db_manager'):
                return
            
            # Usar el gestor de base de datos principal
            db_manager = self.backend_system.db_manager
            
            # Preparar datos para inserción
            metrics_to_insert = []
            for key, value in self._flatten_metrics(metrics_data, prefix="").items():
                if isinstance(value, (int, float)):
                    metrics_to_insert.append({
                        "timestamp": timestamp,
                        "metric_name": key,
                        "value": float(value),
                        "category": category,
                        "tags": json.dumps({}),
                        "metadata": json.dumps({"type": type(value).__name__})
                    })
            
            # Insertar en lote usando el gestor principal
            if metrics_to_insert:
                await db_manager.save_metrics_batch(metrics_to_insert)
                
        except Exception as e:
            logger.error(f"Error guardando métricas en BD principal: {e}")

    def _flatten_metrics(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Aplana métricas anidadas en un diccionario simple."""
        flattened = {}
        for key, value in data.items():
            metric_name = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_metrics(value, f"{metric_name}."))
            elif isinstance(value, (int, float)):
                flattened[metric_name] = value
        
        return flattened

    def _update_realtime_buffer(self, metrics_data: Dict[str, Any], category: str, timestamp: datetime):
        """Actualiza buffer de métricas en tiempo real."""
        if category not in self.realtime_metrics:
            self.realtime_metrics[category] = defaultdict(list)
        
        for key, value in metrics_data.items():
            if isinstance(value, (int, float)):
                # Mantener solo los últimos 100 puntos por métrica
                metric_list = self.realtime_metrics[category][key]
                metric_list.append({
                    "timestamp": timestamp.isoformat(),
                    "value": float(value)
                })
                
                # Limitar tamaño del buffer
                if len(metric_list) > 100:
                    metric_list.pop(0)

    async def _check_alert_thresholds(self, metrics_data: Dict[str, Any], category: str):
        """Verifica umbrales de alerta para las métricas."""
        for metric_name, value in metrics_data.items():
            if isinstance(value, (int, float)):
                # Verificar si hay umbrales definidos
                thresholds = self.alert_thresholds.get(metric_name)
                if thresholds:
                    await self._evaluate_threshold(metric_name, value, thresholds, category)

    async def _evaluate_threshold(self, metric_name: str, value: float, thresholds: Dict[str, float], category: str):
        """Evalúa si una métrica supera los umbrales."""
        try:
            alert_level = None
            threshold_exceeded = None
            
            if "critical" in thresholds and value >= thresholds["critical"]:
                alert_level = "critical"
                threshold_exceeded = thresholds["critical"]
            elif "warning" in thresholds and value >= thresholds["warning"]:
                alert_level = "warning"
                threshold_exceeded = thresholds["warning"]
            
            if alert_level:
                # Registrar alerta
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO metric_alerts (timestamp, metric_name, alert_level, value, threshold, message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    metric_name,
                    alert_level,
                    value,
                    threshold_exceeded,
                    f"{metric_name} = {value:.2f} supera umbral {alert_level} ({threshold_exceeded})"
                ))
                
                conn.commit()
                conn.close()
                
                logger.warning(
                    f"🚨 ALERTA {alert_level.upper()}: {metric_name} = {value:.2f} "
                    f"(umbral: {threshold_exceeded})"
                )
                
        except Exception as e:
            logger.error(f"Error evaluando umbral: {e}")

    async def get_metric_summary(self, metric_name: str, hours: int = 24) -> Optional[MetricSummary]:
        """Obtiene resumen estadístico de una métrica."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener datos del período especificado
            start_time = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                SELECT value FROM metrics 
                WHERE metric_name = ? AND timestamp >= ?
                ORDER BY timestamp
            """, (metric_name, start_time))
            
            values = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not values:
                return None
            
            # Calcular estadísticas
            avg_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            # Calcular percentiles
            percentiles = {
                "p25": np.percentile(values, 25),
                "p50": np.percentile(values, 50),
                "p75": np.percentile(values, 75),
                "p90": np.percentile(values, 90),
                "p95": np.percentile(values, 95),
                "p99": np.percentile(values, 99)
            }
            
            # Determinar tendencia
            trend = await self._calculate_trend(values)
            
            # Predicción simple (1 hora)
            prediction_1h = await self._predict_value(metric_name, values, 60)  # 60 minutos
            
            return MetricSummary(
                metric_name=metric_name,
                count=len(values),
                min_value=min(values),
                max_value=max(values),
                avg_value=avg_value,
                std_dev=std_dev,
                percentiles=percentiles,
                trend=trend,
                prediction_1h=prediction_1h,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de métrica: {e}")
            return None

    async def _calculate_trend(self, values: List[float]) -> str:
        """Calcula la tendencia de una serie de valores."""
        if len(values) < 10:
            return "insufficient_data"
        
        # Usar regresión lineal simple
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calcular pendiente
        slope = np.polyfit(x, y, 1)[0]
        
        # Determinar tendencia basada en la pendiente
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    async def _predict_value(self, metric_name: str, values: List[float], minutes_ahead: int) -> float:
        """Predice el valor de una métrica en el futuro."""
        if len(values) < 5:
            return values[-1] if values else 0.0
        
        try:
            # Predicción simple usando promedio móvil y tendencia
            recent_values = values[-10:]  # Últimos 10 valores
            moving_avg = statistics.mean(recent_values)
            
            # Calcular tendencia reciente
            x = np.arange(len(recent_values))
            y = np.array(recent_values)
            slope = np.polyfit(x, y, 1)[0]
            
            # Predicción = promedio móvil + tendencia * tiempo
            prediction = moving_avg + (slope * minutes_ahead)
            
            return max(0, prediction)  # Evitar valores negativos
            
        except Exception as e:
            logger.error(f"Error prediciendo valor: {e}")
            return values[-1] if values else 0.0

    async def get_realtime_metrics(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene métricas en tiempo real."""
        if category:
            return dict(self.realtime_metrics.get(category, {}))
        else:
            return {cat: dict(metrics) for cat, metrics in self.realtime_metrics.items()}

    async def get_metrics_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos para el dashboard de métricas."""
        try:
            # Métricas recientes por categoría
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "categories": {},
                "alerts": await self.get_recent_alerts(10),
                "summaries": {}
            }
            
            # Procesar cada categoría
            for category, metrics in self.realtime_metrics.items():
                category_data = {}
                
                for metric_name, values in metrics.items():
                    if values:
                        latest = values[-1]
                        category_data[metric_name] = {
                            "current": latest["value"],
                            "timestamp": latest["timestamp"],
                            "history": values[-20:],  # Últimos 20 puntos
                            "trend": await self._calculate_trend([v["value"] for v in values[-10:]])
                        }
                
                dashboard_data["categories"][category] = category_data
            
            # Resúmenes de métricas principales
            main_metrics = ["cpu_percent", "memory_percent", "disk_percent", "error_rate"]
            for metric in main_metrics:
                summary = await self.get_metric_summary(metric, 1)  # Última hora
                if summary:
                    dashboard_data["summaries"][metric] = asdict(summary)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del dashboard: {e}")
            return {}

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene alertas recientes de métricas."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, metric_name, alert_level, value, threshold, message
                FROM metric_alerts
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    "timestamp": row[0],
                    "metric_name": row[1],
                    "alert_level": row[2],
                    "value": row[3],
                    "threshold": row[4],
                    "message": row[5]
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas recientes: {e}")
            return []

    async def export_metrics(self, start_time: datetime, end_time: datetime, format: str = "json") -> str:
        """Exporta métricas en el formato especificado."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Obtener datos del rango especificado
            df = pd.read_sql_query("""
                SELECT timestamp, metric_name, value, category, tags, metadata
                FROM metrics
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, conn, params=(start_time, end_time))
            
            conn.close()
            
            if df.empty:
                return ""
            
            # Exportar según el formato
            if format.lower() == "csv":
                return df.to_csv(index=False)
            elif format.lower() == "json":
                return df.to_json(orient="records", date_format="iso")
            elif format.lower() == "excel":
                filename = f"metrics_export_{int(time.time())}.xlsx"
                filepath = f"data/exports/{filename}"
                df.to_excel(filepath, index=False)
                return filepath
            else:
                raise ValueError(f"Formato no soportado: {format}")
                
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}")
            return ""

    async def save_app_metrics(self, app_metrics: Dict[str, Any]):
        """Guarda métricas específicas de la aplicación."""
        await self.save_metrics(app_metrics, "application")

    async def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Obtiene las métricas más recientes."""
        try:
            # Combinar las métricas más recientes de cada categoría
            latest_metrics = {}
            
            for category, metrics in self.realtime_metrics.items():
                category_latest = {}
                for metric_name, values in metrics.items():
                    if values:
                        category_latest[metric_name] = values[-1]["value"]
                
                if category_latest:
                    latest_metrics[category] = category_latest
            
            return latest_metrics if latest_metrics else None
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas más recientes: {e}")
            return None

    async def get_total_count(self) -> int:
        """Obtiene el total de métricas recolectadas."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM metrics")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Error obteniendo conteo total: {e}")
            return 0

    def is_healthy(self) -> bool:
        """Verifica si el gestor está funcionando correctamente."""
        try:
            # Verificar base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            # Verificar que hay métricas recientes
            recent_metrics = any(
                metrics for metrics in self.realtime_metrics.values()
                if any(values for values in metrics.values())
            )
            
            return self.is_running and recent_metrics
            
        except Exception:
            return False

    async def cleanup(self):
        """Limpia recursos y archivos antiguos."""
        try:
            # Limpiar métricas antiguas (más de 30 días)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cleanup_date = datetime.now() - timedelta(days=30)
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cleanup_date,))
            cursor.execute("DELETE FROM metric_alerts WHERE timestamp < ?", (cleanup_date,))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Limpieza de métricas completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza de métricas: {e}")

    async def shutdown(self):
        """Apaga el gestor de métricas."""
        self.is_running = False
        await self.cleanup()
        logger.info("✅ Gestor de métricas apagado")