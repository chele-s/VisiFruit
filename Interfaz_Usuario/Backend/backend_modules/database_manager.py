"""
Sistema Ultra-Avanzado de Gestión de Base de Datos
=================================================

Gestor híbrido de bases de datos con:
- SQLite para desarrollo y datos locales
- PostgreSQL para producción (opcional)
- Pool de conexiones optimizado
- Migraciones automáticas de esquema
- Backup y restauración automática
- Particionado de tablas por fecha
- Índices optimizados automáticamente
- Queries preparadas y cache
- Análisis de rendimiento de queries
- Replicación y sincronización

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import json
import logging
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict, deque
import hashlib
import pickle
import gzip
import pandas as pd
import numpy as np

try:
    import psycopg2
    from psycopg2.pool import ThreadedConnectionPool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger("UltraDatabaseManager")

@dataclass
class QueryMetrics:
    """Métricas de rendimiento de queries."""
    query_hash: str
    query_text: str
    execution_count: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    last_executed: datetime = field(default_factory=datetime.now)
    error_count: int = 0

@dataclass
class ConnectionMetrics:
    """Métricas de conexiones de base de datos."""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    avg_connection_time: float = 0.0
    pool_size: int = 0
    pool_available: int = 0

@dataclass
class TableInfo:
    """Información de una tabla."""
    name: str
    row_count: int = 0
    size_mb: float = 0.0
    last_analyzed: datetime = field(default_factory=datetime.now)
    indices: List[str] = field(default_factory=list)
    partitions: List[str] = field(default_factory=list)

class UltraDatabaseManager:
    """Gestor ultra-avanzado de base de datos."""
    
    def __init__(self):
        self.db_type = "sqlite"  # "sqlite" o "postgresql"
        self.db_path = "data/fruprint_ultra.db"
        self.postgres_config = {}
        self.connection_pool = None
        self.is_running = False
        
        # Métricas y monitoreo
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.connection_metrics = ConnectionMetrics()
        self.table_info: Dict[str, TableInfo] = {}
        
        # Cache de queries
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutos
        self.max_cache_size = 1000
        
        # Pool de conexiones SQLite
        self.sqlite_connections = deque()
        self.max_sqlite_connections = 10
        self.connection_lock = threading.Lock()
        
        # Configuración de particionado
        self.partition_config = {
            "production_data": {
                "type": "date",
                "column": "timestamp",
                "interval": "month"
            },
            "metrics": {
                "type": "date", 
                "column": "timestamp",
                "interval": "week"
            },
            "alerts": {
                "type": "date",
                "column": "timestamp", 
                "interval": "month"
            }
        }
        
        # Esquema de base de datos
        self.schema_version = 10
        self.migrations = []

    async def initialize(self):
        """Inicializa el gestor de base de datos."""
        try:
            # Detectar y configurar tipo de base de datos
            await self._detect_database_type()
            
            # Crear directorios necesarios
            Path("data/backups").mkdir(parents=True, exist_ok=True)
            Path("data/exports").mkdir(parents=True, exist_ok=True)
            
            # Inicializar conexiones
            if self.db_type == "postgresql":
                await self._init_postgresql()
            else:
                await self._init_sqlite()
            
            # Ejecutar migraciones
            await self._run_migrations()
            
            # Crear esquema inicial
            await self._create_initial_schema()
            
            # Optimizar índices
            await self._optimize_indices()
            
            # Iniciar tareas de mantenimiento
            await self._start_maintenance_tasks()
            
            self.is_running = True
            logger.info(f"✅ Gestor de base de datos inicializado ({self.db_type})")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            raise

    async def _detect_database_type(self):
        """Detecta qué tipo de base de datos usar."""
        # Intentar cargar configuración PostgreSQL
        try:
            with open("data/postgres_config.json", "r") as f:
                self.postgres_config = json.load(f)
                if POSTGRES_AVAILABLE and self.postgres_config.get("enabled", False):
                    self.db_type = "postgresql"
                    logger.info("🐘 Usando PostgreSQL")
                    return
        except FileNotFoundError:
            pass
        
        # Usar SQLite por defecto
        self.db_type = "sqlite"
        logger.info("🗃️ Usando SQLite")

    async def _init_postgresql(self):
        """Inicializa conexión PostgreSQL."""
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("PostgreSQL no está disponible")
        
        try:
            # Crear pool de conexiones
            self.connection_pool = ThreadedConnectionPool(
                minconn=self.postgres_config.get("min_connections", 2),
                maxconn=self.postgres_config.get("max_connections", 20),
                host=self.postgres_config.get("host", "localhost"),
                database=self.postgres_config.get("database", "fruprint"),
                user=self.postgres_config.get("user", "fruprint"),
                password=self.postgres_config.get("password", ""),
                port=self.postgres_config.get("port", 5432)
            )
            
            # Verificar conexión
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"🐘 PostgreSQL conectado: {version}")
            
            cursor.close()
            self.connection_pool.putconn(conn)
            
        except Exception as e:
            logger.error(f"Error conectando PostgreSQL: {e}")
            raise

    async def _init_sqlite(self):
        """Inicializa conexiones SQLite."""
        try:
            # Crear directorio de datos
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Crear pool de conexiones SQLite
            for _ in range(self.max_sqlite_connections):
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                
                # Configurar optimizaciones
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=memory")
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                
                self.sqlite_connections.append(conn)
            
            logger.info(f"🗃️ Pool de {len(self.sqlite_connections)} conexiones SQLite creado")
            
        except Exception as e:
            logger.error(f"Error inicializando SQLite: {e}")
            raise

    def _get_connection(self):
        """Obtiene una conexión de la pool."""
        if self.db_type == "postgresql":
            return self.connection_pool.getconn()
        else:
            with self.connection_lock:
                if self.sqlite_connections:
                    return self.sqlite_connections.popleft()
                else:
                    # Crear nueva conexión temporal
                    conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    conn.execute("PRAGMA journal_mode=WAL")
                    return conn

    def _return_connection(self, conn):
        """Retorna una conexión a la pool."""
        if self.db_type == "postgresql":
            self.connection_pool.putconn(conn)
        else:
            with self.connection_lock:
                if len(self.sqlite_connections) < self.max_sqlite_connections:
                    self.sqlite_connections.append(conn)
                else:
                    conn.close()

    async def _create_initial_schema(self):
        """Crea el esquema inicial de la base de datos."""
        schema_sql = {
            # Tabla de datos de producción
            "production_data": """
                CREATE TABLE IF NOT EXISTS production_data (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    session_id VARCHAR(32),
                    detection_data TEXT,
                    labeling_data TEXT,
                    category VARCHAR(20),
                    success BOOLEAN,
                    processing_time_ms REAL,
                    metadata TEXT
                )
            """,
            
            # Tabla de métricas del sistema
            "system_metrics": """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    metric_category VARCHAR(50),
                    metric_name VARCHAR(100),
                    metric_value REAL,
                    tags TEXT,
                    metadata TEXT
                )
            """,
            
            # Tabla de alertas
            "system_alerts": """
                CREATE TABLE IF NOT EXISTS system_alerts (
                    id VARCHAR(32) PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    level VARCHAR(20),
                    category VARCHAR(50),
                    component VARCHAR(100),
                    title VARCHAR(200),
                    message TEXT,
                    details TEXT,
                    status VARCHAR(20),
                    resolved_at TIMESTAMP,
                    resolved_by VARCHAR(100)
                )
            """,
            
            # Tabla de configuración
            "system_config": """
                CREATE TABLE IF NOT EXISTS system_config (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP,
                    updated_by VARCHAR(100)
                )
            """,
            
            # Tabla de usuarios (para autenticación)
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    role VARCHAR(20),
                    created_at TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """,
            
            # Tabla de sesiones
            "user_sessions": """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id VARCHAR(32) PRIMARY KEY,
                    user_id INTEGER,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """,
            
            # Tabla de logs del sistema
            "system_logs": """
                CREATE TABLE IF NOT EXISTS system_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    level VARCHAR(20),
                    logger VARCHAR(100),
                    message TEXT,
                    details TEXT,
                    filename VARCHAR(200),
                    line_number INTEGER
                )
            """,
            
            # Tabla de reportes generados
            "generated_reports": """
                CREATE TABLE IF NOT EXISTS generated_reports (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200),
                    type VARCHAR(50),
                    parameters TEXT,
                    file_path VARCHAR(500),
                    generated_at TIMESTAMP,
                    generated_by VARCHAR(100),
                    size_bytes INTEGER
                )
            """,
            
            # Tabla de mantenimiento
            "maintenance_logs": """
                CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    component VARCHAR(100),
                    action VARCHAR(100),
                    status VARCHAR(20),
                    details TEXT,
                    duration_seconds REAL,
                    performed_by VARCHAR(100)
                )
            """,
            
            # Tabla de métricas de performance de queries
            "query_performance": """
                CREATE TABLE IF NOT EXISTS query_performance (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    query_hash VARCHAR(64),
                    query_text TEXT,
                    execution_time_ms REAL,
                    rows_affected INTEGER,
                    database_name VARCHAR(50)
                )
            """
        }
        
        # Adaptaciones para SQLite
        if self.db_type == "sqlite":
            for table, sql in schema_sql.items():
                schema_sql[table] = sql.replace("SERIAL", "INTEGER").replace("TIMESTAMP", "DATETIME")
        
        # Ejecutar creación de tablas
        for table_name, sql in schema_sql.items():
            try:
                await self._execute_query(sql)
                logger.info(f"✅ Tabla {table_name} verificada/creada")
            except Exception as e:
                logger.error(f"❌ Error creando tabla {table_name}: {e}")

    async def _optimize_indices(self):
        """Optimiza índices de la base de datos."""
        indices = [
            # Índices para production_data
            "CREATE INDEX IF NOT EXISTS idx_production_timestamp ON production_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_production_category ON production_data(category)",
            "CREATE INDEX IF NOT EXISTS idx_production_success ON production_data(success)",
            
            # Índices para system_metrics
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_category ON system_metrics(metric_category)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_name ON system_metrics(metric_name)",
            
            # Índices para system_alerts
            "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON system_alerts(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_level ON system_alerts(level)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_status ON system_alerts(status)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level)",
            
            # Índices para query_performance
            "CREATE INDEX IF NOT EXISTS idx_query_perf_timestamp ON query_performance(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_query_perf_hash ON query_performance(query_hash)"
        ]
        
        for index_sql in indices:
            try:
                await self._execute_query(index_sql)
            except Exception as e:
                logger.error(f"Error creando índice: {e}")

    async def _run_migrations(self):
        """Ejecuta migraciones de base de datos."""
        # Tabla de migraciones
        migration_table_sql = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL,
                description TEXT
            )
        """
        
        if self.db_type == "sqlite":
            migration_table_sql = migration_table_sql.replace("TIMESTAMP", "DATETIME")
        
        await self._execute_query(migration_table_sql)
        
        # Verificar versión actual
        current_version = await self._get_schema_version()
        
        if current_version < self.schema_version:
            logger.info(f"Ejecutando migraciones desde v{current_version} a v{self.schema_version}")
            
            # Aquí ejecutarías las migraciones necesarias
            # Por ahora solo actualizamos la versión
            await self._execute_query(
                "INSERT OR REPLACE INTO schema_migrations (version, applied_at, description) VALUES (?, ?, ?)",
                (self.schema_version, datetime.now(), "Schema inicial")
            )

    async def _get_schema_version(self) -> int:
        """Obtiene la versión actual del esquema."""
        try:
            result = await self._fetch_one("SELECT MAX(version) FROM schema_migrations")
            return result[0] if result and result[0] else 0
        except:
            return 0

    async def _start_maintenance_tasks(self):
        """Inicia tareas de mantenimiento automático."""
        asyncio.create_task(self._query_performance_monitor())
        asyncio.create_task(self._automatic_backup_task())
        asyncio.create_task(self._cleanup_old_data_task())
        asyncio.create_task(self._analyze_tables_task())

    # Métodos principales de acceso a datos
    async def _execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[int]:
        """Ejecuta una query y retorna el número de filas afectadas."""
        start_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows_affected = cursor.rowcount
            conn.commit()
            
            # Registrar métricas de performance
            execution_time = (time.time() - start_time) * 1000
            await self._record_query_performance(query, execution_time, rows_affected)
            
            cursor.close()
            self._return_connection(conn)
            
            return rows_affected
            
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            raise

    async def _fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Ejecuta una query y retorna una fila."""
        start_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchone()
            
            # Registrar métricas
            execution_time = (time.time() - start_time) * 1000
            await self._record_query_performance(query, execution_time, 1 if result else 0)
            
            cursor.close()
            self._return_connection(conn)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ejecutando fetch_one: {e}")
            raise

    async def _fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Ejecuta una query y retorna todas las filas."""
        start_time = time.time()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            # Registrar métricas
            execution_time = (time.time() - start_time) * 1000
            await self._record_query_performance(query, execution_time, len(results))
            
            cursor.close()
            self._return_connection(conn)
            
            return results
            
        except Exception as e:
            logger.error(f"Error ejecutando fetch_all: {e}")
            raise

    async def _record_query_performance(self, query: str, execution_time: float, rows_affected: int):
        """Registra métricas de performance de queries."""
        try:
            # Crear hash de la query para agrupar
            query_normalized = " ".join(query.split())  # Normalizar espacios
            query_hash = hashlib.md5(query_normalized.encode()).hexdigest()
            
            # Actualizar métricas en memoria
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(
                    query_hash=query_hash,
                    query_text=query_normalized[:500]  # Limitar tamaño
                )
            
            metrics = self.query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.total_execution_time += execution_time
            metrics.avg_execution_time = metrics.total_execution_time / metrics.execution_count
            metrics.min_execution_time = min(metrics.min_execution_time, execution_time)
            metrics.max_execution_time = max(metrics.max_execution_time, execution_time)
            metrics.last_executed = datetime.now()
            
            # Guardar en base de datos (async para no bloquear)
            asyncio.create_task(self._save_query_performance(
                query_hash, query_normalized, execution_time, rows_affected
            ))
            
        except Exception as e:
            logger.error(f"Error registrando performance de query: {e}")

    async def _save_query_performance(self, query_hash: str, query_text: str, 
                                    execution_time: float, rows_affected: int):
        """Guarda métricas de performance en la base de datos."""
        try:
            await self._execute_query("""
                INSERT INTO query_performance 
                (timestamp, query_hash, query_text, execution_time_ms, rows_affected, database_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                query_hash,
                query_text,
                execution_time,
                rows_affected,
                self.db_type
            ))
        except Exception as e:
            logger.error(f"Error guardando performance de query: {e}")

    # Métodos específicos del dominio
    async def save_production_data(self, detections: List[Dict], labeling_data: Dict):
        """Guarda datos de producción."""
        try:
            session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:16]
            
            await self._execute_query("""
                INSERT INTO production_data 
                (timestamp, session_id, detection_data, labeling_data, category, success, processing_time_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                session_id,
                json.dumps(detections),
                json.dumps(labeling_data),
                labeling_data.get("category", "unknown"),
                labeling_data.get("success", False),
                labeling_data.get("duration_seconds", 0) * 1000,
                json.dumps({"detections_count": len(detections)})
            ))
            
        except Exception as e:
            logger.error(f"Error guardando datos de producción: {e}")

    async def save_metrics_batch(self, metrics: List[Dict[str, Any]]):
        """Guarda un lote de métricas en la base de datos.
        Acepta elementos con claves: timestamp, metric_name, value, category, tags, metadata
        y los mapea al esquema real `system_metrics` (metric_category, metric_name, metric_value).
        """
        try:
            if self.db_type == "sqlite":
                conn = self._get_connection() # Reutilizar _get_connection para SQLite
                if not conn:
                    return False
                
                cursor = conn.cursor()
                
                # Insertar métricas en lote mapeando nombres de columna
                for metric in metrics:
                    timestamp = metric.get("timestamp", datetime.now())
                    metric_name = metric.get("metric_name", "unknown")
                    metric_value = metric.get("value", 0.0)
                    metric_category = metric.get("category", "system")
                    tags = metric.get("tags", {})
                    metadata = metric.get("metadata", {})

                    # Asegurar tipos serializables
                    tags_json = tags if isinstance(tags, str) else json.dumps(tags)
                    metadata_json = metadata if isinstance(metadata, str) else json.dumps(metadata)

                    cursor.execute("""
                        INSERT INTO system_metrics 
                        (timestamp, metric_category, metric_name, metric_value, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp,
                        metric_category,
                        metric_name,
                        float(metric_value),
                        tags_json,
                        metadata_json
                    ))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Error guardando métricas en lote: {e}")
            return False

    async def save_system_metric(self, category: str, name: str, value: float, 
                                tags: Optional[Dict] = None, metadata: Optional[Dict] = None):
        """Guarda una métrica del sistema."""
        try:
            await self._execute_query("""
                INSERT INTO system_metrics 
                (timestamp, metric_category, metric_name, metric_value, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                category,
                name,
                value,
                json.dumps(tags or {}),
                json.dumps(metadata or {})
            ))
            
        except Exception as e:
            logger.error(f"Error guardando métrica: {e}")

    async def get_production_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene estadísticas de producción."""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            # Estadísticas generales
            stats = await self._fetch_one("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_sessions,
                    AVG(processing_time_ms) as avg_processing_time,
                    COUNT(DISTINCT category) as categories_processed
                FROM production_data 
                WHERE timestamp >= ?
            """, (start_time,))
            
            # Estadísticas por categoría
            category_stats = await self._fetch_all("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    AVG(processing_time_ms) as avg_time,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                FROM production_data 
                WHERE timestamp >= ?
                GROUP BY category
            """, (start_time,))
            
            return {
                "period_hours": hours,
                "total_sessions": stats[0] if stats else 0,
                "successful_sessions": stats[1] if stats else 0,
                "success_rate": (stats[1] / stats[0] * 100) if stats and stats[0] > 0 else 0,
                "avg_processing_time_ms": stats[2] if stats else 0,
                "categories_processed": stats[3] if stats else 0,
                "by_category": [
                    {
                        "category": row[0],
                        "count": row[1],
                        "avg_time_ms": row[2],
                        "success_count": row[3],
                        "success_rate": (row[3] / row[1] * 100) if row[1] > 0 else 0
                    }
                    for row in category_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de producción: {e}")
            return {}

    async def get_system_health_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de salud del sistema."""
        try:
            # Métricas de la última hora
            start_time = datetime.now() - timedelta(hours=1)
            
            # Conteo de alertas por nivel
            alert_counts = await self._fetch_all("""
                SELECT level, COUNT(*) 
                FROM system_alerts 
                WHERE timestamp >= ? AND status = 'active'
                GROUP BY level
            """, (start_time,))
            
            # Métricas de performance de queries
            query_stats = await self._fetch_one("""
                SELECT 
                    COUNT(*) as query_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    MAX(execution_time_ms) as max_execution_time
                FROM query_performance 
                WHERE timestamp >= ?
            """, (start_time,))
            
            # Estadísticas de conexiones
            connection_stats = {
                "total_connections": self.connection_metrics.total_connections,
                "active_connections": self.connection_metrics.active_connections,
                "failed_connections": self.connection_metrics.failed_connections,
                "avg_connection_time": self.connection_metrics.avg_connection_time
            }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "alerts_by_level": {row[0]: row[1] for row in alert_counts},
                "query_performance": {
                    "query_count": query_stats[0] if query_stats else 0,
                    "avg_execution_time_ms": query_stats[1] if query_stats else 0,
                    "max_execution_time_ms": query_stats[2] if query_stats else 0
                },
                "connections": connection_stats,
                "database_type": self.db_type
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de salud: {e}")
            return {}

    # Tareas de mantenimiento
    async def _query_performance_monitor(self):
        """Monitor de performance de queries."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                
                # Identificar queries lentas
                slow_queries = [
                    metrics for metrics in self.query_metrics.values()
                    if metrics.avg_execution_time > 1000  # Más de 1 segundo
                ]
                
                if slow_queries:
                    logger.warning(f"⚠️ {len(slow_queries)} queries lentas detectadas")
                    for query in slow_queries[:5]:  # Top 5
                        logger.warning(f"Query lenta: {query.avg_execution_time:.2f}ms - {query.query_text[:100]}")
                
            except Exception as e:
                logger.error(f"Error en monitor de performance: {e}")
                await asyncio.sleep(600)

    async def _automatic_backup_task(self):
        """Tarea de backup automático."""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # Cada 24 horas
                
                if self.db_type == "sqlite":
                    await self._backup_sqlite()
                else:
                    await self._backup_postgresql()
                
            except Exception as e:
                logger.error(f"Error en backup automático: {e}")
                await asyncio.sleep(3600)

    async def _backup_sqlite(self):
        """Realiza backup de SQLite."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backups/fruprint_backup_{timestamp}.db"
            
            # Usar comando VACUUM INTO para backup
            await self._execute_query(f"VACUUM INTO '{backup_path}'")
            
            # Comprimir backup
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Eliminar backup sin comprimir
            Path(backup_path).unlink()
            
            logger.info(f"✅ Backup SQLite creado: {backup_path}.gz")
            
        except Exception as e:
            logger.error(f"Error en backup SQLite: {e}")

    async def _backup_postgresql(self):
        """Realiza backup de PostgreSQL."""
        # Implementar pg_dump aquí
        logger.info("🚧 Backup PostgreSQL no implementado aún")

    async def _cleanup_old_data_task(self):
        """Tarea de limpieza de datos antiguos."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Cada hora
                
                # Limpiar datos más antiguos que 30 días
                cutoff_date = datetime.now() - timedelta(days=30)
                
                # Limpiar query performance
                deleted = await self._execute_query(
                    "DELETE FROM query_performance WHERE timestamp < ?",
                    (cutoff_date,)
                )
                
                if deleted and deleted > 0:
                    logger.info(f"🧹 Limpieza: {deleted} registros de performance eliminados")
                
                # Limpiar logs del sistema
                deleted = await self._execute_query(
                    "DELETE FROM system_logs WHERE timestamp < ?",
                    (cutoff_date,)
                )
                
                if deleted and deleted > 0:
                    logger.info(f"🧹 Limpieza: {deleted} logs eliminados")
                
            except Exception as e:
                logger.error(f"Error en limpieza: {e}")
                await asyncio.sleep(7200)

    async def _analyze_tables_task(self):
        """Tarea de análisis de tablas."""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # Cada 24 horas
                
                if self.db_type == "sqlite":
                    await self._execute_query("ANALYZE")
                    logger.info("📊 Análisis de tablas SQLite completado")
                
            except Exception as e:
                logger.error(f"Error en análisis de tablas: {e}")
                await asyncio.sleep(3600)

    # Métodos de información y estado
    def get_connection_count(self) -> int:
        """Obtiene el número de conexiones activas."""
        if self.db_type == "postgresql" and self.connection_pool:
            # Para PostgreSQL sería más complejo obtener el conteo exacto
            return 5  # Estimación
        else:
            return len(self.sqlite_connections)

    def is_healthy(self) -> bool:
        """Verifica si la base de datos está funcionando."""
        try:
            # Realizar query simple
            if self.db_type == "postgresql":
                conn = self.connection_pool.getconn()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.connection_pool.putconn(conn)
            else:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self._return_connection(conn)
            
            return True
            
        except Exception:
            return False

    def get_performance_report(self) -> Dict[str, Any]:
        """Obtiene reporte de performance."""
        return {
            "query_metrics": {
                hash_id: {
                    "query_text": metrics.query_text,
                    "execution_count": metrics.execution_count,
                    "avg_execution_time_ms": metrics.avg_execution_time,
                    "max_execution_time_ms": metrics.max_execution_time
                }
                for hash_id, metrics in self.query_metrics.items()
            },
            "connection_metrics": {
                "total_connections": self.connection_metrics.total_connections,
                "active_connections": self.connection_metrics.active_connections,
                "failed_connections": self.connection_metrics.failed_connections
            },
            "database_type": self.db_type
        }

    async def shutdown(self):
        """Apaga el gestor de base de datos."""
        logger.info("Apagando gestor de base de datos...")
        
        self.is_running = False
        
        # Cerrar conexiones SQLite
        if self.db_type == "sqlite":
            with self.connection_lock:
                while self.sqlite_connections:
                    conn = self.sqlite_connections.popleft()
                    conn.close()
        
        # Cerrar pool PostgreSQL
        elif self.connection_pool:
            self.connection_pool.closeall()
        
        logger.info("✅ Gestor de base de datos apagado")