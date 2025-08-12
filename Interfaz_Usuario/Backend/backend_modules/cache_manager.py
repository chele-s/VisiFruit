"""
Sistema Ultra-Avanzado de Gestión de Cache
==========================================

Sistema completo de cache multinivel con:
- Cache en memoria con TTL configurable
- Cache Redis distribuido (opcional)
- Cache de archivos para datos pesados
- Estrategias de invalidación inteligente
- Compresión automática
- Estadísticas de hit/miss en tiempo real
- Limpieza automática y optimización
- Cache warmup para datos críticos
- Particionado por tipos de datos

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import gzip
import hashlib
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
import os
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, OrderedDict
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger("UltraCacheManager")

class CacheType(Enum):
    """Tipos de cache disponibles."""
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"
    HYBRID = "hybrid"

class CacheStrategy(Enum):
    """Estrategias de cache."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out

@dataclass
class CacheEntry:
    """Entrada de cache."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 1
    ttl_seconds: Optional[int] = None
    compressed: bool = False
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds
    
    @property
    def age_seconds(self) -> float:
        """Edad de la entrada en segundos."""
        return (datetime.now() - self.created_at).total_seconds()

@dataclass
class CacheStats:
    """Estadísticas del cache."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    
    def update_hit_rate(self):
        """Actualiza la tasa de aciertos."""
        total_requests = self.hits + self.misses
        self.hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

class UltraCacheManager:
    """Gestor ultra-avanzado de cache multinivel."""
    
    def __init__(self):
        # Configuración
        self.max_memory_entries = 10000
        self.max_memory_size_mb = 500
        self.default_ttl_seconds = 3600  # 1 hora
        self.compression_threshold_bytes = 1024  # Comprimir si > 1KB
        self.cache_dir = Path("data/cache")
        
        # Cache en memoria (principal)
        self.memory_cache: Dict[str, CacheEntry] = OrderedDict()
        self.memory_lock = threading.RLock()
        
        # Cache Redis (distribuido)
        self.redis_client = None
        self.redis_available = False
        # Flag de configuración para habilitar/disablear Redis (por defecto: deshabilitado)
        self.redis_enabled = os.environ.get("VISIFRUIT_REDIS_ENABLED", "0").lower() in ("1", "true", "yes", "y")
        
        # Cache de archivos
        self.file_cache_enabled = True
        
        # Estadísticas por tipo
        self.stats = {
            CacheType.MEMORY: CacheStats(),
            CacheType.REDIS: CacheStats(),
            CacheType.FILE: CacheStats()
        }
        
        # Configuración por namespace
        self.namespace_configs = {
            "metrics": {"ttl": 300, "strategy": CacheStrategy.TTL},
            "config": {"ttl": 3600, "strategy": CacheStrategy.LRU},
            "users": {"ttl": 1800, "strategy": CacheStrategy.LRU},
            "reports": {"ttl": 7200, "strategy": CacheStrategy.LFU},
            "production": {"ttl": 60, "strategy": CacheStrategy.TTL},
            "alerts": {"ttl": 300, "strategy": CacheStrategy.FIFO}
        }
        
        # Callbacks para eventos
        self.eviction_callbacks: List[Callable] = []
        self.miss_callbacks: List[Callable] = []
        
        # Tareas de mantenimiento
        self.is_running = False
        self.maintenance_tasks = []

    async def initialize(self):
        """Inicializa el gestor de cache."""
        try:
            # Crear directorio de cache
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Inicializar Redis si está disponible y habilitado por configuración
            if REDIS_AVAILABLE and self.redis_enabled:
                await self._init_redis()
            else:
                # Mensaje informativo único para evitar spam en logs
                if not self.redis_enabled:
                    logger.info("Redis desactivado por configuración (VISIFRUIT_REDIS_ENABLED=0) - modo standalone")
                elif not REDIS_AVAILABLE:
                    logger.info("Redis no instalado - modo standalone")
            
            # Cargar cache de archivos existente
            await self._load_file_cache()
            
            # Iniciar tareas de mantenimiento
            await self._start_maintenance_tasks()
            
            self.is_running = True
            logger.info("✅ Gestor de cache inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando gestor de cache: {e}")
            raise

    async def _init_redis(self):
        """Inicializa conexión Redis."""
        try:
            redis_host = os.environ.get("VISIFRUIT_REDIS_HOST", "localhost")
            redis_port = int(os.environ.get("VISIFRUIT_REDIS_PORT", "6379"))
            redis_db = int(os.environ.get("VISIFRUIT_REDIS_DB_CACHE", "2"))

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,  # Base de datos específica para cache
                decode_responses=False  # Para manejar datos binarios
            )
            
            # Verificar conexión
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )
            
            self.redis_available = True
            logger.info("🔗 Redis conectado para cache distribuido")
            
        except Exception as e:
            # Log suave e ir a modo standalone
            logger.info(f"Redis no disponible: {e}. Usando cache en memoria/archivos")
            self.redis_available = False

    async def _load_file_cache(self):
        """Carga entradas de cache desde archivos."""
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            loaded_count = 0
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'rb') as f:
                        data = f.read()
                        
                    # Descomprimir si es necesario
                    if cache_file.suffix == '.gz':
                        data = gzip.decompress(data)
                    
                    # Deserializar
                    entry_data = pickle.loads(data)
                    
                    # Crear entrada de cache
                    entry = CacheEntry(**entry_data)
                    
                    # Verificar si no ha expirado
                    if not entry.is_expired:
                        self.memory_cache[entry.key] = entry
                        loaded_count += 1
                    else:
                        # Eliminar archivo expirado
                        cache_file.unlink()
                        
                except Exception as e:
                    logger.error(f"Error cargando cache file {cache_file}: {e}")
            
            if loaded_count > 0:
                logger.info(f"📁 {loaded_count} entradas de cache cargadas desde archivos")
                
        except Exception as e:
            logger.error(f"Error cargando cache de archivos: {e}")

    # Métodos principales de cache
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Obtiene valor del cache."""
        full_key = f"{namespace}:{key}"
        start_time = time.time()
        
        try:
            # 1. Buscar en cache de memoria
            value = await self._get_from_memory(full_key)
            if value is not None:
                self.stats[CacheType.MEMORY].hits += 1
                return value
            
            # 2. Buscar en Redis si está disponible
            if self.redis_available:
                value = await self._get_from_redis(full_key)
                if value is not None:
                    # Guardar en memoria para próxima vez
                    await self._set_to_memory(full_key, value, self._get_namespace_ttl(namespace))
                    self.stats[CacheType.REDIS].hits += 1
                    return value
            
            # 3. Buscar en cache de archivos
            if self.file_cache_enabled:
                value = await self._get_from_file(full_key)
                if value is not None:
                    # Guardar en niveles superiores
                    await self._set_to_memory(full_key, value, self._get_namespace_ttl(namespace))
                    if self.redis_available:
                        await self._set_to_redis(full_key, value, self._get_namespace_ttl(namespace))
                    self.stats[CacheType.FILE].hits += 1
                    return value
            
            # Cache miss
            await self._record_miss(namespace, key)
            return None
            
        finally:
            # Actualizar tiempo de respuesta
            response_time = (time.time() - start_time) * 1000
            self._update_response_time(response_time)

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
                 namespace: str = "default", tags: List[str] = None) -> bool:
        """Establece valor en el cache."""
        full_key = f"{namespace}:{key}"
        ttl = ttl_seconds or self._get_namespace_ttl(namespace)
        tags = tags or []
        
        try:
            # Guardar en todos los niveles disponibles
            success_memory = await self._set_to_memory(full_key, value, ttl, tags)
            
            success_redis = True
            if self.redis_available:
                success_redis = await self._set_to_redis(full_key, value, ttl)
            
            success_file = True
            if self.file_cache_enabled and self._should_cache_to_file(value):
                success_file = await self._set_to_file(full_key, value, ttl, tags)
            
            # Actualizar estadísticas
            if success_memory:
                self.stats[CacheType.MEMORY].sets += 1
            if success_redis:
                self.stats[CacheType.REDIS].sets += 1
            if success_file:
                self.stats[CacheType.FILE].sets += 1
            
            return success_memory  # El cache de memoria es crítico
            
        except Exception as e:
            logger.error(f"Error estableciendo cache {full_key}: {e}")
            return False

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Elimina valor del cache."""
        full_key = f"{namespace}:{key}"
        
        try:
            # Eliminar de todos los niveles
            deleted_memory = await self._delete_from_memory(full_key)
            deleted_redis = True
            deleted_file = True
            
            if self.redis_available:
                deleted_redis = await self._delete_from_redis(full_key)
            
            if self.file_cache_enabled:
                deleted_file = await self._delete_from_file(full_key)
            
            # Actualizar estadísticas
            if deleted_memory:
                self.stats[CacheType.MEMORY].deletes += 1
            if deleted_redis:
                self.stats[CacheType.REDIS].deletes += 1
            if deleted_file:
                self.stats[CacheType.FILE].deletes += 1
            
            return deleted_memory or deleted_redis or deleted_file
            
        except Exception as e:
            logger.error(f"Error eliminando cache {full_key}: {e}")
            return False

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalida todas las entradas con las tags especificadas."""
        invalidated_count = 0
        
        try:
            # Invalidar en memoria
            with self.memory_lock:
                keys_to_delete = []
                for key, entry in self.memory_cache.items():
                    if any(tag in entry.tags for tag in tags):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    invalidated_count += 1
            
            # Invalidar en Redis (más complejo, requiere scan)
            if self.redis_available:
                # Para simplificar, implementar solo si es necesario
                pass
            
            # Invalidar archivos
            if self.file_cache_enabled:
                cache_files = list(self.cache_dir.glob("*.cache"))
                for cache_file in cache_files:
                    try:
                        # Cargar metadata del archivo para verificar tags
                        # Implementación simplificada
                        pass
                    except:
                        continue
            
            logger.info(f"🧹 {invalidated_count} entradas invalidadas por tags: {tags}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Error invalidando por tags: {e}")
            return 0

    async def clear_namespace(self, namespace: str) -> int:
        """Limpia todas las entradas de un namespace."""
        cleared_count = 0
        prefix = f"{namespace}:"
        
        try:
            # Limpiar memoria
            with self.memory_lock:
                keys_to_delete = [key for key in self.memory_cache.keys() if key.startswith(prefix)]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    cleared_count += 1
            
            # Limpiar Redis
            if self.redis_available:
                redis_keys = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.keys, f"{prefix}*"
                )
                if redis_keys:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.delete, *redis_keys
                    )
            
            # Limpiar archivos
            if self.file_cache_enabled:
                cache_files = list(self.cache_dir.glob(f"*{namespace}*.cache"))
                for cache_file in cache_files:
                    try:
                        cache_file.unlink()
                    except:
                        pass
            
            logger.info(f"🧽 Namespace '{namespace}' limpiado: {cleared_count} entradas")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Error limpiando namespace {namespace}: {e}")
            return 0

    # Métodos de cache específicos por nivel
    async def _get_from_memory(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache de memoria."""
        try:
            with self.memory_lock:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    
                    # Verificar expiración
                    if entry.is_expired:
                        del self.memory_cache[key]
                        self.stats[CacheType.MEMORY].evictions += 1
                        return None
                    
                    # Actualizar estadísticas de acceso
                    entry.last_accessed = datetime.now()
                    entry.access_count += 1
                    
                    # Mover al final (LRU)
                    self.memory_cache.move_to_end(key)
                    
                    return entry.value
                
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo de memoria {key}: {e}")
            return None

    async def _set_to_memory(self, key: str, value: Any, ttl_seconds: int, tags: List[str] = None) -> bool:
        """Establece valor en cache de memoria."""
        try:
            with self.memory_lock:
                # Verificar espacio disponible
                await self._ensure_memory_space()
                
                # Serializar para calcular tamaño
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)
                
                # Comprimir si es necesario
                compressed = False
                if size_bytes > self.compression_threshold_bytes:
                    compressed_data = gzip.compress(serialized)
                    if len(compressed_data) < size_bytes:
                        serialized = compressed_data
                        compressed = True
                
                # Crear entrada
                entry = CacheEntry(
                    key=key,
                    value=value,
                    ttl_seconds=ttl_seconds,
                    compressed=compressed,
                    size_bytes=len(serialized),
                    tags=tags or []
                )
                
                self.memory_cache[key] = entry
                
                # Actualizar estadísticas
                self.stats[CacheType.MEMORY].total_size_bytes += entry.size_bytes
                self.stats[CacheType.MEMORY].entry_count += 1
                
                return True
                
        except Exception as e:
            logger.error(f"Error estableciendo en memoria {key}: {e}")
            return False

    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache Redis."""
        if not self.redis_available:
            return None
        
        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, key
            )
            
            if data:
                # Deserializar
                return pickle.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo de Redis {key}: {e}")
            return None

    async def _set_to_redis(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Establece valor en cache Redis."""
        if not self.redis_available:
            return False
        
        try:
            # Serializar
            data = pickle.dumps(value)
            
            # Establecer con TTL
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.setex, key, ttl_seconds, data
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error estableciendo en Redis {key}: {e}")
            return False

    async def _get_from_file(self, key: str) -> Optional[Any]:
        """Obtiene valor del cache de archivos."""
        try:
            # Generar nombre de archivo seguro
            file_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = self.cache_dir / f"{file_key}.cache"
            
            if not cache_file.exists():
                return None
            
            # Leer archivo
            with open(cache_file, 'rb') as f:
                data = f.read()
            
            # Verificar si está comprimido
            if cache_file.with_suffix('.cache.gz').exists():
                data = gzip.decompress(data)
            
            # Deserializar
            entry_data = pickle.loads(data)
            entry = CacheEntry(**entry_data)
            
            # Verificar expiración
            if entry.is_expired:
                cache_file.unlink()
                return None
            
            return entry.value
            
        except Exception as e:
            logger.error(f"Error obteniendo de archivo {key}: {e}")
            return None

    async def _set_to_file(self, key: str, value: Any, ttl_seconds: int, tags: List[str] = None) -> bool:
        """Establece valor en cache de archivos."""
        try:
            # Crear entrada
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds,
                tags=tags or []
            )
            
            # Serializar
            data = pickle.dumps(asdict(entry))
            
            # Comprimir si es grande
            compressed = False
            if len(data) > self.compression_threshold_bytes:
                compressed_data = gzip.compress(data)
                if len(compressed_data) < len(data):
                    data = compressed_data
                    compressed = True
            
            # Generar nombre de archivo
            file_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = self.cache_dir / f"{file_key}.cache{'gz' if compressed else ''}"
            
            # Escribir archivo
            with open(cache_file, 'wb') as f:
                f.write(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error estableciendo en archivo {key}: {e}")
            return False

    async def _delete_from_memory(self, key: str) -> bool:
        """Elimina valor del cache de memoria."""
        try:
            with self.memory_lock:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    del self.memory_cache[key]
                    
                    # Actualizar estadísticas
                    self.stats[CacheType.MEMORY].total_size_bytes -= entry.size_bytes
                    self.stats[CacheType.MEMORY].entry_count -= 1
                    
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando de memoria {key}: {e}")
            return False

    async def _delete_from_redis(self, key: str) -> bool:
        """Elimina valor del cache Redis."""
        if not self.redis_available:
            return False
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.delete, key
            )
            return result > 0
            
        except Exception as e:
            logger.error(f"Error eliminando de Redis {key}: {e}")
            return False

    async def _delete_from_file(self, key: str) -> bool:
        """Elimina valor del cache de archivos."""
        try:
            file_key = hashlib.md5(key.encode()).hexdigest()
            cache_file = self.cache_dir / f"{file_key}.cache"
            cache_file_gz = self.cache_dir / f"{file_key}.cache.gz"
            
            deleted = False
            
            if cache_file.exists():
                cache_file.unlink()
                deleted = True
            
            if cache_file_gz.exists():
                cache_file_gz.unlink()
                deleted = True
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error eliminando archivo de cache {key}: {e}")
            return False

    # Métodos auxiliares
    def _get_namespace_ttl(self, namespace: str) -> int:
        """Obtiene TTL configurado para un namespace."""
        config = self.namespace_configs.get(namespace, {})
        return config.get("ttl", self.default_ttl_seconds)

    def _should_cache_to_file(self, value: Any) -> bool:
        """Determina si un valor debe guardarse en cache de archivos."""
        try:
            # Calcular tamaño estimado
            serialized = pickle.dumps(value)
            size_mb = len(serialized) / (1024 * 1024)
            
            # Cachear en archivos si es > 1MB
            return size_mb > 1.0
            
        except:
            return False

    async def _ensure_memory_space(self):
        """Asegura que hay espacio en el cache de memoria."""
        try:
            # Verificar límites
            current_size_mb = self.stats[CacheType.MEMORY].total_size_bytes / (1024 * 1024)
            
            while (len(self.memory_cache) >= self.max_memory_entries or 
                   current_size_mb >= self.max_memory_size_mb):
                
                # Aplicar estrategia de eviction (LRU por defecto)
                await self._evict_entry()
                current_size_mb = self.stats[CacheType.MEMORY].total_size_bytes / (1024 * 1024)
                
        except Exception as e:
            logger.error(f"Error asegurando espacio en memoria: {e}")

    async def _evict_entry(self):
        """Elimina una entrada del cache usando la estrategia configurada."""
        try:
            with self.memory_lock:
                if not self.memory_cache:
                    return
                
                # LRU - eliminar el más antiguo accedido
                key_to_evict = next(iter(self.memory_cache))
                entry = self.memory_cache[key_to_evict]
                
                # Guardar en archivo si es valioso
                if self._should_cache_to_file(entry.value):
                    await self._set_to_file(key_to_evict, entry.value, 
                                           entry.ttl_seconds, entry.tags)
                
                # Eliminar de memoria
                del self.memory_cache[key_to_evict]
                
                # Actualizar estadísticas
                self.stats[CacheType.MEMORY].total_size_bytes -= entry.size_bytes
                self.stats[CacheType.MEMORY].entry_count -= 1
                self.stats[CacheType.MEMORY].evictions += 1
                
                # Notificar callbacks
                await self._notify_eviction_callbacks(key_to_evict, entry.value)
                
        except Exception as e:
            logger.error(f"Error en eviction: {e}")

    async def _record_miss(self, namespace: str, key: str):
        """Registra un cache miss."""
        # Actualizar estadísticas
        self.stats[CacheType.MEMORY].misses += 1
        
        # Notificar callbacks
        await self._notify_miss_callbacks(namespace, key)

    def _update_response_time(self, response_time_ms: float):
        """Actualiza tiempo de respuesta promedio."""
        for stats in self.stats.values():
            if stats.avg_response_time_ms == 0:
                stats.avg_response_time_ms = response_time_ms
            else:
                # Media móvil simple
                stats.avg_response_time_ms = (stats.avg_response_time_ms + response_time_ms) / 2

    # Callbacks
    async def _notify_eviction_callbacks(self, key: str, value: Any):
        """Notifica callbacks de eviction."""
        for callback in self.eviction_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(key, value)
                else:
                    callback(key, value)
            except Exception as e:
                logger.error(f"Error en callback de eviction: {e}")

    async def _notify_miss_callbacks(self, namespace: str, key: str):
        """Notifica callbacks de miss."""
        for callback in self.miss_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(namespace, key)
                else:
                    callback(namespace, key)
            except Exception as e:
                logger.error(f"Error en callback de miss: {e}")

    # Tareas de mantenimiento
    async def _start_maintenance_tasks(self):
        """Inicia tareas de mantenimiento."""
        self.maintenance_tasks = [
            asyncio.create_task(self._cleanup_expired_entries()),
            asyncio.create_task(self._optimize_cache()),
            asyncio.create_task(self._update_statistics()),
            asyncio.create_task(self._persist_critical_data())
        ]

    async def _cleanup_expired_entries(self):
        """Limpia entradas expiradas."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                
                cleaned_count = 0
                
                # Limpiar memoria
                with self.memory_lock:
                    expired_keys = []
                    for key, entry in self.memory_cache.items():
                        if entry.is_expired:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        entry = self.memory_cache[key]
                        del self.memory_cache[key]
                        
                        # Actualizar estadísticas
                        self.stats[CacheType.MEMORY].total_size_bytes -= entry.size_bytes
                        self.stats[CacheType.MEMORY].entry_count -= 1
                        cleaned_count += 1
                
                # Limpiar archivos expirados
                if self.file_cache_enabled:
                    cache_files = list(self.cache_dir.glob("*.cache*"))
                    for cache_file in cache_files:
                        try:
                            # Verificar edad del archivo
                            file_age = time.time() - cache_file.stat().st_mtime
                            if file_age > self.default_ttl_seconds:
                                cache_file.unlink()
                                cleaned_count += 1
                        except:
                            pass
                
                if cleaned_count > 0:
                    logger.info(f"🧹 {cleaned_count} entradas expiradas limpiadas")
                
            except Exception as e:
                logger.error(f"Error en limpieza de entradas expiradas: {e}")
                await asyncio.sleep(600)

    async def _optimize_cache(self):
        """Optimiza el cache periódicamente."""
        while self.is_running:
            try:
                await asyncio.sleep(1800)  # Cada 30 minutos
                
                # Reordenar cache de memoria por frecuencia de acceso
                with self.memory_lock:
                    # Convertir a lista ordenada por access_count
                    items = sorted(
                        self.memory_cache.items(),
                        key=lambda x: x[1].access_count,
                        reverse=True
                    )
                    
                    # Recrear OrderedDict con el nuevo orden
                    self.memory_cache.clear()
                    for key, entry in items:
                        self.memory_cache[key] = entry
                
                logger.info("🔧 Cache optimizado por frecuencia de acceso")
                
            except Exception as e:
                logger.error(f"Error optimizando cache: {e}")
                await asyncio.sleep(3600)

    async def _update_statistics(self):
        """Actualiza estadísticas del cache."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Cada minuto
                
                # Actualizar hit rates
                for stats in self.stats.values():
                    stats.update_hit_rate()
                
                # Log de estadísticas
                memory_stats = self.stats[CacheType.MEMORY]
                logger.debug(
                    f"📊 Cache Stats - Memory: {memory_stats.entry_count} entries, "
                    f"{memory_stats.hit_rate:.1f}% hit rate, "
                    f"{memory_stats.total_size_bytes / (1024*1024):.1f}MB"
                )
                
            except Exception as e:
                logger.error(f"Error actualizando estadísticas: {e}")
                await asyncio.sleep(120)

    async def _persist_critical_data(self):
        """Persiste datos críticos del cache."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Cada hora
                
                # Identificar entradas críticas (más accedidas)
                critical_entries = []
                with self.memory_lock:
                    for key, entry in self.memory_cache.items():
                        if entry.access_count > 10:  # Accedido más de 10 veces
                            critical_entries.append((key, entry))
                
                # Guardar en archivos
                for key, entry in critical_entries:
                    if not await self._file_exists(key):
                        await self._set_to_file(key, entry.value, entry.ttl_seconds, entry.tags)
                
                if critical_entries:
                    logger.info(f"💾 {len(critical_entries)} entradas críticas persistidas")
                
            except Exception as e:
                logger.error(f"Error persistiendo datos críticos: {e}")
                await asyncio.sleep(1800)

    async def _file_exists(self, key: str) -> bool:
        """Verifica si existe archivo de cache para una clave."""
        file_key = hashlib.md5(key.encode()).hexdigest()
        cache_file = self.cache_dir / f"{file_key}.cache"
        cache_file_gz = self.cache_dir / f"{file_key}.cache.gz"
        return cache_file.exists() or cache_file_gz.exists()

    # API pública de gestión
    def register_eviction_callback(self, callback: Callable):
        """Registra callback para eventos de eviction."""
        self.eviction_callbacks.append(callback)

    def register_miss_callback(self, callback: Callable):
        """Registra callback para eventos de miss."""
        self.miss_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        return {
            cache_type.value: {
                "hits": stats.hits,
                "misses": stats.misses,
                "sets": stats.sets,
                "deletes": stats.deletes,
                "evictions": stats.evictions,
                "total_size_bytes": stats.total_size_bytes,
                "entry_count": stats.entry_count,
                "hit_rate": stats.hit_rate,
                "avg_response_time_ms": stats.avg_response_time_ms
            }
            for cache_type, stats in self.stats.items()
        }

    def get_memory_usage(self) -> Dict[str, Any]:
        """Obtiene uso de memoria del cache."""
        memory_stats = self.stats[CacheType.MEMORY]
        return {
            "current_entries": memory_stats.entry_count,
            "max_entries": self.max_memory_entries,
            "current_size_mb": memory_stats.total_size_bytes / (1024 * 1024),
            "max_size_mb": self.max_memory_size_mb,
            "utilization_percent": (memory_stats.entry_count / self.max_memory_entries) * 100
        }

    async def get_hit_rate(self) -> float:
        """Obtiene tasa de aciertos global."""
        total_hits = sum(stats.hits for stats in self.stats.values())
        total_misses = sum(stats.misses for stats in self.stats.values())
        total_requests = total_hits + total_misses
        
        return (total_hits / total_requests * 100) if total_requests > 0 else 0.0

    async def warm_up(self, data: Dict[str, Any], namespace: str = "warmup"):
        """Precarga datos críticos en el cache."""
        try:
            warmed_count = 0
            
            for key, value in data.items():
                success = await self.set(key, value, namespace=namespace)
                if success:
                    warmed_count += 1
            
            logger.info(f"🔥 Cache warm-up completado: {warmed_count} entradas cargadas")
            
        except Exception as e:
            logger.error(f"Error en cache warm-up: {e}")

    def is_healthy(self) -> bool:
        """Verifica si el cache está funcionando correctamente."""
        try:
            # Verificar que el cache de memoria responde
            test_key = "__health_check__"
            test_value = "healthy"
            
            with self.memory_lock:
                # Test básico de escritura/lectura
                entry = CacheEntry(key=test_key, value=test_value, ttl_seconds=1)
                self.memory_cache[test_key] = entry
                
                # Verificar lectura
                retrieved = self.memory_cache.get(test_key)
                success = retrieved is not None and retrieved.value == test_value
                
                # Limpiar
                if test_key in self.memory_cache:
                    del self.memory_cache[test_key]
                
                return success and self.is_running
                
        except Exception:
            return False

    async def shutdown(self):
        """Apaga el gestor de cache."""
        logger.info("Apagando gestor de cache...")
        
        self.is_running = False
        
        # Cancelar tareas de mantenimiento
        for task in self.maintenance_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Persistir datos importantes antes del shutdown
        try:
            await self._persist_critical_data()
        except:
            pass
        
        # Cerrar conexión Redis
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        logger.info("✅ Gestor de cache apagado")