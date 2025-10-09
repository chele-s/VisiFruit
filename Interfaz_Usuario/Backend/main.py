"""
Sistema de Backend Ultra-Avanzado para FruPrint v3.0
===================================================

Backend complejo con múltiples APIs, WebSockets en tiempo real,
sistema de métricas avanzadas, alertas, reportes y dashboard 3D.

Características Ultra-Avanzadas:
- API REST completa con 50+ endpoints
- WebSockets en tiempo real para dashboard 3D
- Sistema de métricas y analytics avanzado
- Gestión de alertas con diferentes niveles
- Sistema de reportes y estadísticas
- Base de datos PostgreSQL/SQLite híbrida
- Cache Redis multinivel
- Sistema de autenticación JWT
- APIs especializadas por módulo
- Middleware personalizado para logging
- Sistema de configuración dinámico
- Exportación de datos en múltiples formatos

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 3.0.0-ULTRA-BACKEND
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import os
import redis
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import psutil
# Import GPU utils opcional
try:
    import GPUtil  # type: ignore[reportMissingImports]
    GPUUTIL_AVAILABLE = True
except Exception:
    GPUtil = None  # type: ignore
    GPUUTIL_AVAILABLE = False

# Importar módulos del sistema principal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos especializados del backend
from backend_modules.metrics_manager import UltraMetricsManager
from backend_modules.alert_system import UltraAlertSystem
from backend_modules.websocket_manager import UltraWebSocketManager
from backend_modules.database_manager import UltraDatabaseManager
from backend_modules.report_generator import UltraReportGenerator
from backend_modules.config_manager import UltraConfigManager
from backend_modules.auth_manager import UltraAuthManager
from backend_modules.cache_manager import UltraCacheManager
from backend_modules.api_modules import (
    ProductionAPI, SystemAPI, MetricsAPI, AlertsAPI, 
    ConfigAPI, ReportsAPI, AnalyticsAPI, MaintenanceAPI
)

# Función auxiliar para logging seguro en Windows
def safe_log(logger_instance, level, message, *args, **kwargs):
    """Función auxiliar para logging seguro que maneja caracteres Unicode en Windows."""
    try:
        # Reemplazar emojis problemáticos con texto descriptivo
        safe_message = message
        emoji_replacements = {
            "✅": "[OK]",
            "🚀": "[START]", 
            "📊": "[METRICS]",
            "⚠️": "[WARNING]",
            "❌": "[ERROR]",
            "🔧": "[CONFIG]",
            "🌍": "[ENV]",
            "💾": "[DB]",
            "🔒": "[AUTH]",
            "Ôä╣´©Å": "[REDIS]",
            "Ô£à": "[SUCCESS]",
            "­ƒùâ´©Å": "[SQLITE]",
            "­ƒîì": "[ENV]",
            "­ƒôä": "[CONFIG]",
            "ÔÜá´©Å": "[WARNING]",
            "­ƒÆ¥": "[BACKUP]"
        }
        
        for emoji, replacement in emoji_replacements.items():
            safe_message = safe_message.replace(emoji, replacement)
        
        getattr(logger_instance, level)(safe_message, *args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: log sin caracteres especiales
        try:
            fallback_message = message.encode('utf-8', errors='ignore').decode('utf-8')
            getattr(logger_instance, level)(fallback_message, *args, **kwargs)
        except Exception:
            # Último fallback: solo texto ASCII
            fallback_message = message.encode('ascii', errors='ignore').decode('ascii')
            getattr(logger_instance, level)(fallback_message, *args, **kwargs)

# Configurar logging (crear directorio si no existe)
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend_ultra.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("UltraBackend")

# Variables globales
SYSTEM_INSTANCE = None
BACKEND_MANAGERS = {}

class UltraBackendSystem:
    """Sistema Backend Ultra-Avanzado para FruPrint v3.0"""
    
    def __init__(self):
        self.app = None
        self.start_time = time.time()
        self.version = "3.0.0-ULTRA-BACKEND"
        self.system_id = str(uuid.uuid4())[:8]
        
        # Gestores ultra-especializados
        self.metrics_manager = UltraMetricsManager()
        self.alert_system = UltraAlertSystem()
        self.websocket_manager = UltraWebSocketManager()
        self.db_manager = UltraDatabaseManager()
        self.report_generator = UltraReportGenerator()
        self.config_manager = UltraConfigManager()
        self.auth_manager = UltraAuthManager()
        self.cache_manager = UltraCacheManager()
        
        # APIs especializadas
        self.production_api = ProductionAPI()
        self.system_api = SystemAPI()
        self.metrics_api = MetricsAPI()
        self.alerts_api = AlertsAPI()
        self.config_api = ConfigAPI()
        self.reports_api = ReportsAPI()
        self.analytics_api = AnalyticsAPI()
        self.maintenance_api = MaintenanceAPI()
        
        # Estado del sistema
        self.is_running = False
        self.connected_clients = set()
        self.background_tasks = []
        
        # Métricas en tiempo real
        self.realtime_metrics = {
            "system": {},
            "production": {},
            "labelers": {},
            "motor": {},
            "ia": {},
            "alerts": [],
            "performance": {}
        }

    async def initialize(self):
        """Inicializa todos los componentes del backend."""
        try:
            logger.info("=== Inicializando Backend Ultra-Avanzado ===")
            
            # Crear directorios necesarios
            Path("logs").mkdir(exist_ok=True)
            Path("data/reports").mkdir(parents=True, exist_ok=True)
            Path("data/exports").mkdir(parents=True, exist_ok=True)
            Path("static").mkdir(exist_ok=True)
            
            # Inicializar gestores
            await self.metrics_manager.initialize(self)
            await self.alert_system.initialize()
            await self.websocket_manager.initialize()
            await self.db_manager.initialize()
            await self.report_generator.initialize()
            await self.config_manager.initialize()
            await self.auth_manager.initialize()
            # Permitir desactivar Redis vía env sin ruido en logs
            os.environ.setdefault("VISIFRUIT_REDIS_ENABLED", os.environ.get("VISIFRUIT_REDIS_ENABLED", "0"))
            await self.cache_manager.initialize()
            
            # Inicializar APIs especializadas
            await self.production_api.initialize(self)
            await self.system_api.initialize(self)
            await self.metrics_api.initialize(self)
            await self.alerts_api.initialize(self)
            await self.config_api.initialize(self)
            await self.reports_api.initialize(self)
            await self.analytics_api.initialize(self)
            await self.maintenance_api.initialize(self)
            
            # Crear aplicación FastAPI
            self.app = self._create_ultra_app()
            
            # Iniciar tareas en background
            await self._start_background_tasks()
            
            self.is_running = True
            safe_log(logger, "info", "✅ Backend Ultra-Avanzado inicializado exitosamente")
            return True
            
        except Exception as e:
            safe_log(logger, "error", f"❌ Error inicializando backend: {e}")
            return False

    def _create_ultra_app(self) -> FastAPI:
        """Crea la aplicación FastAPI ultra-avanzada."""
        app = FastAPI(
            title="FruPrint Ultra Backend API v3.0",
            description="Backend Ultra-Avanzado con 50+ endpoints, WebSockets, métricas en tiempo real y dashboard 3D",
            version=self.version,
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            openapi_url="/api/openapi.json"
        )
        
        # Middleware avanzado
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        app.add_middleware(GZipMiddleware, minimum_size=1000)
        app.add_middleware(UltraLoggingMiddleware)
        app.add_middleware(UltraPerformanceMiddleware)
        app.add_middleware(UltraSecurityMiddleware)
        
        # Archivos estáticos
        app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # Rutas principales del sistema
        self._register_main_routes(app)
        
        # APIs especializadas
        app.include_router(self.production_api.router, prefix="/api/production", tags=["Production"])
        app.include_router(self.system_api.router, prefix="/api/system", tags=["System"])
        app.include_router(self.metrics_api.router, prefix="/api/metrics", tags=["Metrics"])
        app.include_router(self.alerts_api.router, prefix="/api/alerts", tags=["Alerts"])
        app.include_router(self.config_api.router, prefix="/api/config", tags=["Configuration"])
        app.include_router(self.reports_api.router, prefix="/api/reports", tags=["Reports"])
        app.include_router(self.analytics_api.router, prefix="/api/analytics", tags=["Analytics"])
        app.include_router(self.maintenance_api.router, prefix="/api/maintenance", tags=["Maintenance"])
        
        return app

    def _register_main_routes(self, app: FastAPI):
        """Registra las rutas principales del sistema."""
        
        @app.get("/")
        async def root():
            """Endpoint raíz con información del sistema."""
            return {
                "system": "FruPrint Ultra Backend",
                "version": self.version,
                "status": "running" if self.is_running else "stopped",
                "uptime_seconds": time.time() - self.start_time,
                "endpoints_count": len(app.routes),
                "connected_clients": len(self.connected_clients),
                "documentation": "/api/docs"
            }
        
        @app.get("/health")
        async def health_check():
            """Check de salud completo del sistema."""
            return await self._get_health_status()
        
        @app.get("/api/status/ultra")
        async def ultra_status():
            """Estado ultra-detallado del sistema."""
            return await self._get_ultra_status()
        
        @app.websocket("/ws/realtime")
        async def realtime_websocket(websocket: WebSocket):
            """WebSocket principal para datos en tiempo real."""
            await self.websocket_manager.handle_connection(websocket, "realtime")
        
        @app.websocket("/ws/dashboard")
        async def dashboard_websocket(websocket: WebSocket):
            """WebSocket para dashboard 3D."""
            await self.websocket_manager.handle_connection(websocket, "dashboard")
        
        @app.websocket("/ws/alerts")
        async def alerts_websocket(websocket: WebSocket):
            """WebSocket para alertas en tiempo real."""
            await self.websocket_manager.handle_connection(websocket, "alerts")
        
        @app.get("/api/system/performance")
        async def system_performance():
            """Métricas de rendimiento del sistema."""
            return await self._get_performance_metrics()
        
        @app.post("/api/system/simulate")
        async def simulate_production():
            """Simula producción para testing."""
            return await self._simulate_production_data()

    async def _get_health_status(self) -> Dict[str, Any]:
        """Obtiene el estado de salud completo del sistema."""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Estado de los gestores
            managers_status = {
                "metrics_manager": self.metrics_manager.is_healthy(),
                "alert_system": self.alert_system.is_healthy(),
                "websocket_manager": self.websocket_manager.is_healthy(),
                "db_manager": self.db_manager.is_healthy(),
                "cache_manager": self.cache_manager.is_healthy()
            }
            
            overall_health = all(managers_status.values())
            
            return {
                "status": "healthy" if overall_health else "degraded",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "system_metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "available_memory_gb": memory.available / (1024**3)
                },
                "managers": managers_status,
                "connected_clients": len(self.connected_clients),
                "background_tasks": len(self.background_tasks)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado de salud: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _get_ultra_status(self) -> Dict[str, Any]:
        """Obtiene estado ultra-detallado del sistema CON DATOS REALES DEL BACKEND PRINCIPAL."""
        try:
            current_time = time.time()
            
            # Intentar conectar al sistema principal (puerto 8000)
            main_system_status = {}
            main_connected = False
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8000/status', timeout=aiohttp.ClientTimeout(total=2)) as resp:
                        if resp.status == 200:
                            main_system_status = await resp.json()
                            main_connected = True
                            safe_log(logger, logging.DEBUG, "✅ Conectado al sistema principal en puerto 8000")
            except Exception as e:
                safe_log(logger, logging.DEBUG, f"Sistema principal no disponible: {e}")
            
            # Estado de la banda CON DATOS REALES O FALLBACK
            belt_status = {
                "available": False,
                "running": False,
                "isRunning": False,
                "direction": "stopped",
                "speed": 0.0,
                "currentSpeed": 0.0,
                "targetSpeed": 0.0,
                "enabled": True,
                "controlType": "relay",
                "hasSpeedControl": False,
                "motorTemperature": 35.0,
                "lastAction": "stopped",
                "actionTime": datetime.now().isoformat(),
                "totalRuntime": current_time - self.start_time,
                "timestamp": current_time
            }
            
            if main_system_status and "belt" in main_system_status:
                belt_status.update(main_system_status["belt"])
                
                # Persistir histórico
                if not hasattr(self, '_belt_history'):
                    self._belt_history = []
                self._belt_history.append({
                    "timestamp": current_time,
                    "running": belt_status.get("running", False),
                    "direction": belt_status.get("direction", "stopped")
                })
                if len(self._belt_history) > 1000:
                    self._belt_history = self._belt_history[-1000:]
            
            # Estado del stepper CON DATOS REALES O FALLBACK
            stepper_status = {
                "available": False,
                "enabled": True,
                "isActive": False,
                "currentPower": 0,
                "activationCount": 0,
                "lastActivation": None,
                "sensorTriggers": 0,
                "manualActivations": 0,
                "driverTemperature": 45.0,
                "currentStepRate": 0,
                "timestamp": current_time
            }
            
            if main_system_status and "stepper" in main_system_status:
                stepper_status.update(main_system_status["stepper"])
                
                # Persistir histórico
                if not hasattr(self, '_stepper_history'):
                    self._stepper_history = []
                self._stepper_history.append({
                    "timestamp": current_time,
                    "isActive": stepper_status.get("isActive", False),
                    "sensorTriggers": stepper_status.get("sensorTriggers", 0),
                    "manualActivations": stepper_status.get("manualActivations", 0)
                })
                if len(self._stepper_history) > 1000:
                    self._stepper_history = self._stepper_history[-1000:]
            
            # Estado de los desviadores (clasificación) CON DATOS REALES O FALLBACK
            diverters_status = {
                "available": False,
                "enabled": True,
                "initialized": False,
                "diverters_count": 0,
                "active_diverters": [],
                "diverters": {},
                "timestamp": current_time
            }
            
            if main_system_status and "diverters" in main_system_status:
                diverters_status.update(main_system_status["diverters"])
                
                # Persistir histórico
                if not hasattr(self, '_diverters_history'):
                    self._diverters_history = []
                self._diverters_history.append({
                    "timestamp": current_time,
                    "initialized": diverters_status.get("initialized", False),
                    "active_count": len(diverters_status.get("active_diverters", []))
                })
                if len(self._diverters_history) > 1000:
                    self._diverters_history = self._diverters_history[-1000:]
            
            # Estadísticas generales
            stats = main_system_status.get("stats", {}) if main_connected else {
                "uptime_s": current_time - self.start_time,
                "detections_total": 0,
                "labeled_total": 0,
                "classified_total": 0
            }
            
            # Datos históricos calculados
            belt_uptime = 0.0
            stepper_rate = 0.0
            diverters_usage = 0.0
            
            if hasattr(self, '_belt_history') and len(self._belt_history) > 0:
                belt_uptime = (sum(1 for h in self._belt_history if h.get("running")) / len(self._belt_history)) * 100
            if hasattr(self, '_stepper_history') and len(self._stepper_history) > 0:
                stepper_rate = (sum(1 for h in self._stepper_history if h.get("isActive")) / len(self._stepper_history)) * 100
            if hasattr(self, '_diverters_history') and len(self._diverters_history) > 0:
                diverters_usage = (sum(1 for h in self._diverters_history if h.get("active_count", 0) > 0) / len(self._diverters_history)) * 100
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_id": self.system_id,
                "version": self.version,
                "system": {
                    "state": main_system_status.get("system_state", "offline") if main_connected else "offline",
                    "running": main_system_status.get("system_running", False) if main_connected else False,
                    "uptime": current_time - self.start_time,
                    "start_time": datetime.fromtimestamp(self.start_time).isoformat()
                },
                "belt": belt_status,
                "stepper": stepper_status,
                "diverters": diverters_status,
                "stats": stats,
                "historical": {
                    "belt_uptime_percent": belt_uptime,
                    "stepper_activation_rate": stepper_rate,
                    "diverters_usage_rate": diverters_usage,
                    "data_points": {
                        "belt": len(self._belt_history) if hasattr(self, '_belt_history') else 0,
                        "stepper": len(self._stepper_history) if hasattr(self, '_stepper_history') else 0,
                        "diverters": len(self._diverters_history) if hasattr(self, '_diverters_history') else 0
                    }
                },
                "main_system_connected": main_connected,
                "alerts_active": await self.alert_system.get_active_count(),
                "metrics_collected": await self.metrics_manager.get_total_count()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado ultra: {e}")
            traceback.print_exc()
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "belt": {"available": False, "running": False},
                "stepper": {"available": False, "isActive": False}
            }

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento del sistema."""
        try:
            # Métricas del sistema
            cpu_times = psutil.cpu_times()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Métricas de GPU si están disponibles
            gpu_metrics = []
            if GPUUTIL_AVAILABLE and GPUtil is not None:
                try:
                    gpus = GPUtil.getGPUs()
                    for gpu in gpus:
                        gpu_metrics.append({
                            "id": gpu.id,
                            "name": gpu.name,
                            "load": gpu.load * 100,
                            "memory_used": gpu.memoryUsed,
                            "memory_total": gpu.memoryTotal,
                            "temperature": gpu.temperature
                        })
                except Exception:
                    gpu_metrics = []
            
            # Métricas de red
            net_io = psutil.net_io_counters()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                    "load_average": load_avg,
                    "times": cpu_times._asdict()
                },
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage('/')._asdict(),
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "gpu": gpu_metrics,
                "processes": len(psutil.pids()),
                "boot_time": psutil.boot_time()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de rendimiento: {e}")
            return {"error": str(e)}

    async def _simulate_production_data(self) -> Dict[str, Any]:
        """Simula datos de producción para testing."""
        try:
            # Simular detección de frutas
            categories = ["apple", "pear", "lemon"]
            simulated_detections = []
            
            for _ in range(np.random.randint(1, 8)):
                detection = {
                    "id": str(uuid.uuid4())[:8],
                    "category": np.random.choice(categories),
                    "confidence": np.random.uniform(0.8, 0.99),
                    "bbox": [
                        np.random.randint(0, 200),
                        np.random.randint(0, 200), 
                        np.random.randint(50, 150),
                        np.random.randint(50, 150)
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                simulated_detections.append(detection)
            
            # Simular métricas de etiquetado
            labeling_metrics = {
                "group_activated": np.random.randint(0, 3),
                "labelers_used": np.random.randint(1, 4),
                "duration_seconds": np.random.uniform(1.5, 3.0),
                "success": np.random.choice([True, True, True, False]),  # 75% success
                "items_labeled": len(simulated_detections)
            }
            
            # Actualizar métricas en tiempo real
            await self._update_realtime_metrics(simulated_detections, labeling_metrics)
            
            # Enviar a WebSockets
            await self.websocket_manager.broadcast_to_channel(
                "realtime",
                {
                    "type": "simulation",
                    "detections": simulated_detections,
                    "labeling": labeling_metrics,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "status": "success",
                "detections": simulated_detections,
                "labeling": labeling_metrics,
                "message": f"Simulados {len(simulated_detections)} detecciones"
            }
            
        except Exception as e:
            logger.error(f"Error simulando datos: {e}")
            return {"status": "error", "error": str(e)}

    async def _update_realtime_metrics(self, detections: List[Dict], labeling: Dict):
        """Actualiza métricas en tiempo real."""
        try:
            # Actualizar contadores por categoría
            if "categories" not in self.realtime_metrics:
                self.realtime_metrics["categories"] = {"apple": 0, "pear": 0, "lemon": 0}
            
            for detection in detections:
                category = detection["category"]
                if category in self.realtime_metrics["categories"]:
                    self.realtime_metrics["categories"][category] += 1
            
            # Actualizar métricas de producción
            self.realtime_metrics["production"] = {
                "last_detection_count": len(detections),
                "last_labeling_success": labeling["success"],
                "total_processed": self.realtime_metrics["production"].get("total_processed", 0) + len(detections),
                "efficiency": np.random.uniform(85, 95),
                "timestamp": datetime.now().isoformat()
            }
            
            # Guardar en base de datos
            await self.db_manager.save_production_data(detections, labeling)
            
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")

    async def _start_background_tasks(self):
        """Inicia tareas en background."""
        tasks = [
            asyncio.create_task(self._metrics_collector_task()),
            asyncio.create_task(self._alert_processor_task()),
            asyncio.create_task(self._websocket_broadcaster_task()),
            asyncio.create_task(self._cache_cleaner_task()),
            asyncio.create_task(self._system_monitor_task())
        ]
        
        self.background_tasks.extend(tasks)
        safe_log(logger, "info", f"✅ Iniciadas {len(tasks)} tareas en background")

    async def _metrics_collector_task(self):
        """Tarea para recolectar métricas periódicamente."""
        while self.is_running:
            try:
                # Recolectar métricas del sistema
                metrics = await self._get_performance_metrics()
                await self.metrics_manager.save_metrics(metrics)
                
                # Recolectar métricas de la aplicación
                app_metrics = {
                    "connected_clients": len(self.connected_clients),
                    "background_tasks": len(self.background_tasks),
                    "cache_hit_rate": await self.cache_manager.get_hit_rate(),
                    "db_connections": self.db_manager.get_connection_count()  # No es async
                }
                
                await self.metrics_manager.save_app_metrics(app_metrics)
                
                await asyncio.sleep(5)  # Cada 5 segundos
                
            except Exception as e:
                logger.error(f"Error en collector de métricas: {e}")
                await asyncio.sleep(10)

    async def _alert_processor_task(self):
        """Tarea para procesar alertas."""
        while self.is_running:
            try:
                # Verificar condiciones de alerta
                metrics = await self.metrics_manager.get_latest_metrics()
                
                if metrics:
                    # CPU alto
                    if metrics.get("cpu", {}).get("percent", 0) > 80:
                        await self.alert_system.create_alert(
                            "system", "high_cpu", 
                            f"CPU al {metrics['cpu']['percent']:.1f}%",
                            {"cpu_percent": metrics["cpu"]["percent"]}
                        )
                    
                    # Memoria alta
                    if metrics.get("memory", {}).get("percent", 0) > 85:
                        await self.alert_system.create_alert(
                            "system", "high_memory",
                            f"Memoria al {metrics['memory']['percent']:.1f}%",
                            {"memory_percent": metrics["memory"]["percent"]}
                        )
                
                await asyncio.sleep(10)  # Cada 10 segundos
                
            except Exception as e:
                logger.error(f"Error en procesador de alertas: {e}")
                await asyncio.sleep(15)

    async def _websocket_broadcaster_task(self):
        """Tarea para enviar datos a WebSockets."""
        while self.is_running:
            try:
                # Preparar datos para broadcast
                broadcast_data = {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": self.realtime_metrics,
                    "system_status": await self._get_health_status(),
                    "alerts": await self.alert_system.get_recent_alerts(10)
                }
                
                # Enviar a todos los canales
                await self.websocket_manager.broadcast_to_all(broadcast_data)
                
                await asyncio.sleep(1)  # Cada segundo
                
            except Exception as e:
                logger.error(f"Error en broadcaster WebSocket: {e}")
                await asyncio.sleep(2)

    async def _cache_cleaner_task(self):
        """Tarea para limpiar cache periódicamente."""
        while self.is_running:
            try:
                # Ejecutar mantenimiento básico del cache
                # El UltraCacheManager ya tiene sus propias tareas de limpieza internas
                # Solo necesitamos hacer un mantenimiento ligero aquí
                await asyncio.sleep(300)  # Cada 5 minutos
                
            except Exception as e:
                logger.error(f"Error en limpiador de cache: {e}")
                await asyncio.sleep(600)

    async def _system_monitor_task(self):
        """Tarea para monitorear el sistema."""
        while self.is_running:
            try:
                # Verificar salud de componentes
                if not self.db_manager.is_healthy():
                    await self.alert_system.create_alert(
                        "database", "connection_error",
                        "Base de datos no disponible"
                    )
                
                if not self.cache_manager.is_healthy():
                    await self.alert_system.create_alert(
                        "cache", "connection_error", 
                        "Cache no disponible"
                    )
                
                await asyncio.sleep(30)  # Cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error en monitor del sistema: {e}")
                await asyncio.sleep(60)

    async def shutdown(self):
        """Apaga el sistema backend."""
        logger.info("Apagando Backend Ultra-Avanzado...")
        
        self.is_running = False
        
        # Cancelar tareas
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Apagar gestores
        await self.websocket_manager.shutdown()
        await self.db_manager.shutdown()
        await self.cache_manager.shutdown()
        
        safe_log(logger, "info", "✅ Backend apagado correctamente")


# Middleware personalizado
class UltraLoggingMiddleware:
    """Middleware para logging avanzado."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    process_time = time.time() - start_time
                    logger.info(
                        f"Request: {scope['method']} {scope['path']} - "
                        f"Status: {message['status']} - "
                        f"Time: {process_time:.3f}s"
                    )
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class UltraPerformanceMiddleware:
    """Middleware para métricas de rendimiento."""
    
    def __init__(self, app):
        self.app = app
        self.request_times = deque(maxlen=1000)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    process_time = time.time() - start_time
                    self.request_times.append(process_time)
                    
                    # Agregar header con tiempo de respuesta
                    headers = list(message.get("headers", []))
                    headers.append([b"x-process-time", f"{process_time:.3f}".encode()])
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class UltraSecurityMiddleware:
    """Middleware para seguridad avanzada."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Agregar headers de seguridad
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.extend([
                        [b"x-content-type-options", b"nosniff"],
                        [b"x-frame-options", b"DENY"],
                        [b"x-xss-protection", b"1; mode=block"],
                        [b"strict-transport-security", b"max-age=31536000; includeSubDomains"]
                    ])
                    message["headers"] = headers
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


async def startup_backend():
    """Inicia el sistema backend."""
    global SYSTEM_INSTANCE
    
    try:
        SYSTEM_INSTANCE = UltraBackendSystem()
        success = await SYSTEM_INSTANCE.initialize()
        
        if not success:
            logger.error("❌ Fallo al inicializar backend")
            return None
        
        return SYSTEM_INSTANCE.app
        
    except Exception as e:
        logger.error(f"❌ Error crítico iniciando backend: {e}")
        return None


async def shutdown_backend():
    """Apaga el sistema backend."""
    global SYSTEM_INSTANCE
    
    if SYSTEM_INSTANCE:
        await SYSTEM_INSTANCE.shutdown()


if __name__ == "__main__":
    async def main():
        """Punto de entrada principal."""
        
        # Configurar señales
        def signal_handler(signum, frame):
            logger.info("Señal de apagado recibida")
            asyncio.create_task(shutdown_backend())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicializar backend
        app = await startup_backend()
        
        # Iniciar sistema de etiquetado en segundo plano junto al backend
        labeling_process = None
        try:
            from pathlib import Path
            repo_root = Path(__file__).resolve().parents[2]
            labeling_script = repo_root / "main_etiquetadora.py"
            if labeling_script.exists():
                try:
                    safe_log(logger, "info", "🎯 Lanzando sistema de etiquetado: main_etiquetadora.py")
                    labeling_process = await asyncio.create_subprocess_exec(
                        sys.executable,
                        "-u",
                        str(labeling_script),
                        cwd=str(repo_root)
                    )
                    safe_log(logger, "info", "🏷️  Sistema de etiquetado lanzado en segundo plano")
                except Exception as e:
                    safe_log(logger, "error", f"❌ No se pudo iniciar main_etiquetadora.py: {e}")
            else:
                safe_log(logger, "warning", f"⚠️ No se encontró {labeling_script}. Omitiendo inicio de etiquetadora")
        except Exception as e:
            safe_log(logger, "error", f"❌ Error preparando inicio de etiquetadora: {e}")
        
        if app:
            # Configurar servidor (puerto 8001 para evitar conflicto con sistema principal)
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=8001,
                log_level="info",
                reload=False
            )
            
            server = uvicorn.Server(config)
            
            safe_log(logger, "info", "🚀 Iniciando servidor Backend Ultra-Avanzado en http://0.0.0.0:8001")
            safe_log(logger, "info", "📊 Dashboard disponible en http://0.0.0.0:8001/api/docs")
            
            try:
                await server.serve()
            except KeyboardInterrupt:
                logger.info("Interrupción recibida")
            finally:
                # Intentar apagar sistema de etiquetado si está activo
                try:
                    if labeling_process and labeling_process.returncode is None:
                        safe_log(logger, "info", "🛑 Deteniendo sistema de etiquetado...")
                        labeling_process.terminate()
                        try:
                            await asyncio.wait_for(labeling_process.wait(), timeout=10)
                        except asyncio.TimeoutError:
                            safe_log(logger, "warning", "Forzando cierre del sistema de etiquetado")
                            labeling_process.kill()
                            await labeling_process.wait()
                except Exception as e:
                    safe_log(logger, "error", f"Error deteniendo etiquetadora: {e}")
                await shutdown_backend()
        else:
            logger.error("❌ No se pudo inicializar el backend")
            sys.exit(1)
    
    asyncio.run(main())