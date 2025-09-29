# database_manager.py
"""
Gestor de Base de Datos FruPrint v4.0 - ENHANCED
================================================

Sistema de persistencia de datos, métricas, análisis histórico
y exportación avanzada para el sistema industrial de etiquetado.

MEJORAS v4.0:
- Queries optimizadas con índices
- Exportación a múltiples formatos (JSON, CSV, Excel)
- Agregación de datos con ventanas temporales
- Backup automático
- Compresión de datos históricos
- Análisis de tendencias con SQL
- Cache de queries frecuentes

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0.1 - MODULAR ARCHITECTURE ENHANCED
"""

import json
import sqlite3
import asyncio
import logging
import gzip
import csv as csv_module
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

# ==================== GESTOR DE BASE DE DATOS ====================

class DatabaseManager:
    """Gestor centralizado de base de datos SQLite con características avanzadas."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos. Si es None, usa 'data/fruprint_ultra.db'
        """
        self.db_path = db_path or Path("data") / "fruprint_ultra.db"
        self.db_connection: Optional[sqlite3.Connection] = None
        self._initialized = False
        
        # Cache de queries
        self._query_cache = {}
        self._cache_ttl = 60  # segundos
        self._cache_timestamps = {}
        
        # Backup
        self.backup_dir = Path("data") / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def initialize(self) -> bool:
        """Inicializa la base de datos y crea las tablas necesarias."""
        try:
            # Crear directorio si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Conectar a la base de datos
            self.db_connection = sqlite3.connect(
                str(self.db_path), 
                check_same_thread=False
            )
            
            # Configurar para mejor rendimiento
            self._configure_database()
            
            # Crear tablas
            self._create_tables()
            
            self._initialized = True
            logger.info(f"✅ Base de datos inicializada: {self.db_path}")
            
            # Realizar backup inicial si no existe
            if not list(self.backup_dir.glob("*.db")):
                self.backup_database()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            return False
    
    def _configure_database(self):
        """Configura la base de datos para mejor rendimiento."""
        cursor = self.db_connection.cursor()
        
        # Habilitar WAL mode para mejor concurrencia
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Configurar cache
        cursor.execute("PRAGMA cache_size=10000")
        
        # Optimizar para lecturas y escrituras mixtas
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Habilitar auto-vacuum para mantener DB compacta
        cursor.execute("PRAGMA auto_vacuum=INCREMENTAL")
        
        self.db_connection.commit()
        logger.debug("✅ Base de datos configurada para rendimiento óptimo")
    
    def _create_tables(self):
        """Crea las tablas necesarias en la base de datos."""
        cursor = self.db_connection.cursor()
        
        # Tabla de detecciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                category TEXT NOT NULL,
                confidence REAL,
                processing_time_ms REAL,
                bbox_x INTEGER,
                bbox_y INTEGER,
                bbox_w INTEGER,
                bbox_h INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de etiquetados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS labelings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                labeler_id INTEGER NOT NULL,
                category TEXT,
                duration REAL,
                success BOOLEAN DEFAULT 1,
                motor_position REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de métricas del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                metric_type TEXT NOT NULL,
                metric_data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                timestamp DATETIME NOT NULL,
                level TEXT NOT NULL,
                component TEXT,
                message TEXT,
                details TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolution_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de clasificaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                category TEXT NOT NULL,
                diverter_id INTEGER,
                success BOOLEAN DEFAULT 1,
                delay_ms REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Nueva tabla de sesiones de producción
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS production_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                total_detected INTEGER DEFAULT 0,
                total_labeled INTEGER DEFAULT 0,
                total_classified INTEGER DEFAULT 0,
                avg_throughput REAL,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # Tabla de eventos del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                severity TEXT DEFAULT 'info'
            )
        """)
        
        # Crear índices para mejorar rendimiento
        self._create_indexes(cursor)
        
        self.db_connection.commit()
        logger.info("✅ Tablas de base de datos creadas/verificadas")
    
    def _create_indexes(self, cursor):
        """Crea índices para optimizar queries."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_detections_category ON detections(category)",
            "CREATE INDEX IF NOT EXISTS idx_labelings_timestamp ON labelings(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_labelings_labeler ON labelings(labeler_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)",
            "CREATE INDEX IF NOT EXISTS idx_classifications_timestamp ON classifications(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_classifications_category ON classifications(category)",
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON system_events(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        logger.debug(f"✅ {len(indexes)} índices creados")
    
    # ==================== OPERACIONES BÁSICAS ====================
    
    async def save_detection(self, detection_data: Dict[str, Any]) -> bool:
        """Guarda una detección en la base de datos."""
        try:
            def _write():
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO detections 
                    (timestamp, category, confidence, processing_time_ms, bbox_x, bbox_y, bbox_w, bbox_h)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection_data.get('timestamp', datetime.now().isoformat()),
                    detection_data.get('category', 'unknown'),
                    detection_data.get('confidence', 0.0),
                    detection_data.get('processing_time_ms', 0.0),
                    detection_data.get('bbox_x', 0),
                    detection_data.get('bbox_y', 0),
                    detection_data.get('bbox_w', 0),
                    detection_data.get('bbox_h', 0)
                ))
                self.db_connection.commit()
            
            await asyncio.to_thread(_write)
            self._invalidate_cache()
            return True
            
        except Exception as e:
            logger.error(f"Error guardando detección: {e}")
            return False
    
    async def save_labeling(self, labeling_data: Dict[str, Any]) -> bool:
        """Guarda un evento de etiquetado en la base de datos."""
        try:
            def _write():
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO labelings 
                    (timestamp, labeler_id, category, duration, success, motor_position)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    labeling_data.get('timestamp', datetime.now().isoformat()),
                    labeling_data.get('labeler_id', 0),
                    labeling_data.get('category', 'unknown'),
                    labeling_data.get('duration', 0.0),
                    labeling_data.get('success', True),
                    labeling_data.get('motor_position', 0.0)
                ))
                self.db_connection.commit()
            
            await asyncio.to_thread(_write)
            return True
            
        except Exception as e:
            logger.error(f"Error guardando etiquetado: {e}")
            return False
    
    async def save_metrics(self, metrics_data: Any) -> bool:
        """Guarda métricas del sistema en la base de datos."""
        try:
            # Convertir dataclass a dict si es necesario
            if hasattr(metrics_data, '__dataclass_fields__'):
                metrics_dict = asdict(metrics_data)
            elif isinstance(metrics_data, dict):
                metrics_dict = metrics_data
            else:
                metrics_dict = {"data": str(metrics_data)}
            
            metrics_json = json.dumps(metrics_dict, default=str)
            timestamp = datetime.now().isoformat()
            
            def _write():
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO metrics (timestamp, metric_type, metric_data)
                    VALUES (?, ?, ?)
                """, (timestamp, "system_metrics", metrics_json))
                self.db_connection.commit()
            
            await asyncio.to_thread(_write)
            return True
            
        except Exception as e:
            logger.error(f"Error guardando métricas: {e}")
            return False
    
    async def save_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Guarda una alerta en la base de datos."""
        try:
            def _write():
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (alert_id, timestamp, level, component, message, details, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_data.get('id', 'unknown'),
                    alert_data.get('timestamp', datetime.now().isoformat()),
                    alert_data.get('level', 'info'),
                    alert_data.get('component', ''),
                    alert_data.get('message', ''),
                    json.dumps(alert_data.get('details', {})),
                    alert_data.get('resolved', False)
                ))
                self.db_connection.commit()
            
            await asyncio.to_thread(_write)
            return True
            
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")
            return False
    
    # ==================== CONSULTAS OPTIMIZADAS ====================
    
    async def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene las métricas más recientes con cache."""
        cache_key = f"recent_metrics_{limit}"
        
        # Verificar cache
        if cached := self._get_from_cache(cache_key):
            return cached
        
        try:
            def _read():
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT timestamp, metric_type, metric_data
                    FROM metrics
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [
                    {
                        'timestamp': row[0],
                        'metric_type': row[1],
                        'metric_data': json.loads(row[2])
                    }
                    for row in rows
                ]
            
            result = await asyncio.to_thread(_read)
            self._save_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
            return []
    
    async def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema con agregación optimizada."""
        cache_key = f"statistics_{hours}h"
        
        if cached := self._get_from_cache(cache_key):
            return cached
        
        try:
            def _read():
                cursor = self.db_connection.cursor()
                
                # Detecciones por categoría
                cursor.execute("""
                    SELECT 
                        category,
                        COUNT(*) as count,
                        AVG(confidence) as avg_confidence,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM detections
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    GROUP BY category
                """, (hours,))
                detections = cursor.fetchall()
                
                # Etiquetados por labeler
                cursor.execute("""
                    SELECT 
                        labeler_id,
                        COUNT(*) as count,
                        AVG(duration) as avg_duration,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                    FROM labelings
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    GROUP BY labeler_id
                """, (hours,))
                labelings = cursor.fetchall()
                
                # Throughput por hora
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        COUNT(*) as count
                    FROM detections
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    GROUP BY hour
                    ORDER BY hour
                """, (hours,))
                throughput = cursor.fetchall()
                
                return {
                    'detections_by_category': {
                        row[0]: {
                            'count': row[1],
                            'avg_confidence': round(row[2], 3) if row[2] else 0,
                            'avg_processing_time_ms': round(row[3], 2) if row[3] else 0
                        } for row in detections
                    },
                    'labelings_by_labeler': {
                        row[0]: {
                            'count': row[1],
                            'avg_duration': round(row[2], 3) if row[2] else 0,
                            'success_rate': round(row[3], 2) if row[3] else 100.0
                        } for row in labelings
                    },
                    'hourly_throughput': [
                        {'hour': row[0], 'count': row[1]} for row in throughput
                    ]
                }
            
            result = await asyncio.to_thread(_read)
            self._save_to_cache(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Analiza tendencias en los últimos N días."""
        try:
            def _read():
                cursor = self.db_connection.cursor()
                
                # Tendencia de throughput diario
                cursor.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as detections,
                        AVG(confidence) as avg_confidence
                    FROM detections
                    WHERE timestamp > datetime('now', '-' || ? || ' days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (days,))
                daily_data = cursor.fetchall()
                
                # Tendencia de errores
                cursor.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as error_count
                    FROM alerts
                    WHERE timestamp > datetime('now', '-' || ? || ' days')
                      AND level IN ('error', 'critical')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, (days,))
                error_data = cursor.fetchall()
                
                return {
                    'daily_performance': [
                        {
                            'date': row[0],
                            'detections': row[1],
                            'avg_confidence': round(row[2], 3) if row[2] else 0
                        } for row in daily_data
                    ],
                    'daily_errors': [
                        {'date': row[0], 'errors': row[1]} for row in error_data
                    ]
                }
            
            return await asyncio.to_thread(_read)
            
        except Exception as e:
            logger.error(f"Error en análisis de tendencias: {e}")
            return {}
    
    # ==================== EXPORTACIÓN AVANZADA ====================
    
    async def export_to_json(self, output_path: Path, table: str = "all", 
                            days: int = 7) -> bool:
        """Exporta datos a JSON."""
        try:
            data = await self._get_export_data(table, days)
            
            def _write():
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            
            await asyncio.to_thread(_write)
            logger.info(f"✅ Datos exportados a JSON: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a JSON: {e}")
            return False
    
    async def export_to_csv(self, output_path: Path, table: str = "detections", 
                           days: int = 7) -> bool:
        """Exporta datos a CSV."""
        try:
            data = await self._get_export_data(table, days)
            
            def _write():
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if not data:
                        return
                    
                    # Obtener columnas del primer registro
                    if table == "all":
                        # Exportar solo detecciones para CSV
                        records = data.get('detections', [])
                    else:
                        records = data.get(table, [])
                    
                    if not records:
                        return
                    
                    writer = csv_module.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
            
            await asyncio.to_thread(_write)
            logger.info(f"✅ Datos exportados a CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            return False
    
    async def _get_export_data(self, table: str, days: int) -> Dict[str, Any]:
        """Obtiene datos para exportación."""
        def _read():
            cursor = self.db_connection.cursor()
            result = {}
            
            tables_to_export = ['detections', 'labelings', 'alerts', 'classifications'] if table == "all" else [table]
            
            for tbl in tables_to_export:
                try:
                    cursor.execute(f"""
                        SELECT * FROM {tbl}
                        WHERE timestamp > datetime('now', '-' || ? || ' days')
                        ORDER BY timestamp DESC
                    """, (days,))
                    
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    
                    result[tbl] = [
                        dict(zip(columns, row)) for row in rows
                    ]
                except Exception as e:
                    logger.error(f"Error exportando tabla {tbl}: {e}")
            
            return result
        
        return await asyncio.to_thread(_read)
    
    # ==================== BACKUP Y MANTENIMIENTO ====================
    
    def backup_database(self, compress: bool = True) -> Optional[Path]:
        """Crea un backup de la base de datos."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"fruprint_backup_{timestamp}.db"
            
            if compress:
                backup_name += ".gz"
            
            backup_path = self.backup_dir / backup_name
            
            # Crear backup
            if compress:
                with gzip.open(backup_path, 'wb') as f_out:
                    with open(self.db_path, 'rb') as f_in:
                        f_out.writelines(f_in)
            else:
                import shutil
                shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"✅ Backup creado: {backup_path}")
            
            # Limpiar backups antiguos (mantener últimos 30 días)
            self._cleanup_old_backups(days=30)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return None
    
    def _cleanup_old_backups(self, days: int = 30):
        """Limpia backups antiguos."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for backup_file in self.backup_dir.glob("fruprint_backup_*.db*"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.debug(f"Backup antiguo eliminado: {backup_file.name}")
        except Exception as e:
            logger.error(f"Error limpiando backups: {e}")
    
    async def vacuum_database(self) -> bool:
        """Optimiza la base de datos (VACUUM)."""
        try:
            def _vacuum():
                self.db_connection.execute("VACUUM")
                self.db_connection.execute("ANALYZE")
                logger.info("✅ Base de datos optimizada (VACUUM + ANALYZE)")
            
            await asyncio.to_thread(_vacuum)
            return True
        except Exception as e:
            logger.error(f"Error en VACUUM: {e}")
            return False
    
    # ==================== CACHE ====================
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Obtiene un valor del cache si es válido."""
        if key not in self._query_cache:
            return None
        
        # Verificar TTL
        if key in self._cache_timestamps:
            age = (datetime.now() - self._cache_timestamps[key]).total_seconds()
            if age > self._cache_ttl:
                # Cache expirado
                del self._query_cache[key]
                del self._cache_timestamps[key]
                return None
        
        return self._query_cache[key]
    
    def _save_to_cache(self, key: str, value: Any):
        """Guarda un valor en cache."""
        self._query_cache[key] = value
        self._cache_timestamps[key] = datetime.now()
    
    def _invalidate_cache(self):
        """Invalida todo el cache."""
        self._query_cache.clear()
        self._cache_timestamps.clear()
    
    # ==================== CIERRE ====================
    
    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.db_connection:
            try:
                self.db_connection.close()
                logger.info("✅ Base de datos cerrada correctamente")
            except Exception as e:
                logger.error(f"Error cerrando base de datos: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

__all__ = ['DatabaseManager']