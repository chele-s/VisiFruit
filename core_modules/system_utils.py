# system_utils.py
"""
Utilidades del Sistema FruPrint v4.0
====================================

Módulo de utilidades generales: logging avanzado, cache inteligente,
helpers y funciones auxiliares.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import sys
import time
import pickle
import hashlib
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Callable

# ==================== SISTEMA DE LOGGING AVANZADO ====================

def setup_ultra_logging(config: Dict[str, Any]):
    """Configura sistema de logging ultra-avanzado con múltiples niveles."""
    log_level = config.get("system_settings", {}).get("log_level", "INFO")
    
    # Crear directorio de logs con subcarpetas
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    (log_dir / "categories").mkdir(exist_ok=True)
    (log_dir / "performance").mkdir(exist_ok=True)
    (log_dir / "errors").mkdir(exist_ok=True)
    
    # Formateador ultra-detallado
    formatter = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [PID:%(process)d] [%(name)25s] [%(levelname)8s] "
            "[%(funcName)20s:%(lineno)4d] [%(thread)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Multiple handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Handler general
    main_log = log_dir / f"fruprint_ultra_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(main_log, encoding='utf-8')
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    
    # Handler para errores
    error_log = log_dir / "errors" / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    handlers.append(error_handler)
    
    # Handler para performance
    perf_log = log_dir / "performance" / f"performance_{datetime.now().strftime('%Y%m%d')}.log"
    perf_handler = logging.FileHandler(perf_log, encoding='utf-8')
    perf_handler.addFilter(lambda record: 'PERF' in record.getMessage())
    perf_handler.setFormatter(formatter)
    handlers.append(perf_handler)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    
    logging.info("✅ Sistema de logging ultra-avanzado configurado")

# ==================== CACHE INTELIGENTE ====================

def intelligent_cache(ttl_seconds: int = 300, max_size: int = 1000):
    """Decorador para cache inteligente con TTL y límite de tamaño."""
    def decorator(func):
        cache = {}
        access_times = {}

        def _make_key(args, kwargs):
            try:
                key_source = pickle.dumps((args, kwargs))
            except Exception:
                try:
                    key_source = repr((args, kwargs)).encode("utf-8", errors="ignore")
                except Exception:
                    key_source = f"{id(args)}-{id(kwargs)}-{time.time()}".encode("utf-8")
            return hashlib.md5(key_source).hexdigest()

        def _evict_and_cleanup(now):
            expired_keys = [k for k, t in access_times.items() if now - t > ttl_seconds]
            for k in expired_keys:
                cache.pop(k, None)
                access_times.pop(k, None)
            if len(cache) >= max_size and access_times:
                oldest_key = min(access_times.keys(), key=lambda k: access_times[k])
                cache.pop(oldest_key, None)
                access_times.pop(oldest_key, None)

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_time = time.time()
                key = _make_key(args, kwargs)
                _evict_and_cleanup(current_time)
                if key in cache:
                    access_times[key] = current_time
                    return cache[key]
                result = await func(*args, **kwargs)
                cache[key] = result
                access_times[key] = current_time
                return result

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_time = time.time()
                key = _make_key(args, kwargs)
                _evict_and_cleanup(current_time)
                if key in cache:
                    access_times[key] = current_time
                    return cache[key]
                result = func(*args, **kwargs)
                cache[key] = result
                access_times[key] = current_time
                return result

            return sync_wrapper
    return decorator

# ==================== MEDIDOR DE PERFORMANCE ====================

def measure_performance(func: Callable):
    """Decorador para medir el rendimiento de funciones."""
    logger = logging.getLogger(func.__module__)
    
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                logger.debug(f"🚀 PERF: {func.__name__} ejecutado en {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"❌ PERF: {func.__name__} falló en {elapsed_ms:.2f}ms - {e}")
                raise
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                logger.debug(f"🚀 PERF: {func.__name__} ejecutado en {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"❌ PERF: {func.__name__} falló en {elapsed_ms:.2f}ms - {e}")
                raise
        return sync_wrapper

# ==================== HELPERS ====================

def format_bytes(bytes_value: int) -> str:
    """Formatea bytes a unidades legibles."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_duration(seconds: float) -> str:
    """Formatea duración en segundos a formato legible."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """División segura que evita división por cero."""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default

def calculate_percentage(part: float, total: float, decimals: int = 2) -> float:
    """Calcula porcentaje de forma segura."""
    if total == 0:
        return 0.0
    percentage = (part / total) * 100
    return round(percentage, decimals)

# ==================== VALIDADORES ====================

def validate_config_keys(config: Dict[str, Any], required_keys: list) -> tuple[bool, list]:
    """Valida que un diccionario de configuración tenga las claves requeridas."""
    missing_keys = [key for key in required_keys if key not in config]
    is_valid = len(missing_keys) == 0
    return is_valid, missing_keys

def validate_pin_number(pin: int, min_pin: int = 0, max_pin: int = 27) -> bool:
    """Valida un número de pin GPIO."""
    return isinstance(pin, int) and min_pin <= pin <= max_pin

# ==================== RATE LIMITER ====================

class RateLimiter:
    """Limitador de tasa para prevenir sobrecarga."""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Args:
            max_calls: Máximo número de llamadas permitidas
            time_window: Ventana de tiempo en segundos
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_proceed(self) -> bool:
        """Verifica si se puede proceder con una nueva llamada."""
        now = time.time()
        
        # Limpiar llamadas antiguas
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        # Verificar límite
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def reset(self):
        """Resetea el limitador."""
        self.calls.clear()

# ==================== RETRY MECHANISM ====================

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorador para reintentar operaciones fallidas."""
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                current_delay = delay
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_attempts:
                            raise
                        logging.warning(
                            f"⚠️ {func.__name__} falló (intento {attempt}/{max_attempts}): {e}. "
                            f"Reintentando en {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                current_delay = delay
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_attempts:
                            raise
                        logging.warning(
                            f"⚠️ {func.__name__} falló (intento {attempt}/{max_attempts}): {e}. "
                            f"Reintentando en {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
            return sync_wrapper
    return decorator

__all__ = [
    'setup_ultra_logging', 'intelligent_cache', 'measure_performance',
    'format_bytes', 'format_duration', 'safe_divide', 'calculate_percentage',
    'validate_config_keys', 'validate_pin_number', 'RateLimiter', 'retry_on_failure'
]
