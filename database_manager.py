# database_manager.py
"""
Gestor de Base de Datos FruPrint v4.0
=====================================

Sistema de persistencia de datos, métricas y análisis histórico
para el sistema industrial de etiquetado.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import json
import sqlite3
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import asdict

logger = logging.getLogger(__name__)

# ==================== GESTOR DE BASE DE DATOS ====================

class DatabaseManager:
    """Gestor centralizado de base de datos SQLite para métricas y análisis."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos. Si es None, usa 'data/fruprint_ultra.db'
        """
        self.db_path = db_path or Path("data") / "fruprint_ultra.db"
        self.db_connection: Optional[sqlite3.Connection] = None
        self._initialized = False
    
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
            
            # Crear tablas
            self._create_tables()
            
            self._initialized = True
            logger.info(f"✅ Base de datos inicializada: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            return False
    
    def _create_tables(self):
        """Crea las tablas necesarias en la base de datos."""
        cursor = self.db_connection.cursor()
        
        # Tabla de detecciones
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
        
        # Tabla de etiquetados
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
        
        # Tabla de métricas del sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                metric_type TEXT,
                metric_data TEXT
            )
        """)
        
        # Tabla de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT,
                timestamp DATETIME,
                level TEXT,
                component TEXT,
                message TEXT,
                details TEXT,
                resolved BOOLEAN DEFAULT 0
            )
        """)
        
        # Tabla de clasificaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                category TEXT,
                diverter_id INTEGER,
                success BOOLEAN,
                delay_ms REAL
            )
        """)
        
        # Crear índices para mejorar rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_labelings_timestamp ON labelings(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        self.db_connection.commit()
        logger.info("✅ Tablas de base de datos creadas/verificadas")
    
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
                    INSERT INTO alerts 
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
    
    async def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene las métricas más recientes."""
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
            
            return await asyncio.to_thread(_read)
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas: {e}")
            return []
    
    async def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema para las últimas X horas."""
        try:
            def _read():
                cursor = self.db_connection.cursor()
                
                # Calcular timestamp de inicio
                cutoff_time = datetime.now().isoformat()
                
                # Detecciones
                cursor.execute("""
                    SELECT COUNT(*), AVG(confidence), category
                    FROM detections
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    GROUP BY category
                """, (hours,))
                detections = cursor.fetchall()
                
                # Etiquetados
                cursor.execute("""
                    SELECT COUNT(*), AVG(duration), labeler_id
                    FROM labelings
                    WHERE timestamp > datetime('now', '-' || ? || ' hours')
                    GROUP BY labeler_id
                """, (hours,))
                labelings = cursor.fetchall()
                
                return {
                    'detections_by_category': {row[2]: {'count': row[0], 'avg_confidence': row[1]} 
                                               for row in detections},
                    'labelings_by_labeler': {row[2]: {'count': row[0], 'avg_duration': row[1]} 
                                            for row in labelings}
                }
            
            return await asyncio.to_thread(_read)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
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
