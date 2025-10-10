# ultra_api.py
"""
API Ultra-Avanzada FruPrint v4.0
================================

Sistema de API REST y WebSocket ultra-avanzado para el sistema
industrial de etiquetado de frutas.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import asyncio
import logging
import uvicorn
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core_modules.system_types import (
    SystemState, FruitCategory, LabelerGroup,
    LABELERS_PER_GROUP
)

logger = logging.getLogger(__name__)

# ==================== MODELOS PYDANTIC ====================

class SpeedData(BaseModel):
    """Modelo para datos de velocidad de banda."""
    speed: float

class CategoryRequest(BaseModel):
    """Modelo para solicitudes de categoría."""
    category: str
    delay: Optional[float] = 0.0

class StepperRequest(BaseModel):
    """Modelo para solicitudes del stepper."""
    duration: Optional[float] = 0.5
    intensity: Optional[float] = 80.0
    enabled: Optional[bool] = None

# ==================== CREADOR DE API ====================

class UltraAPIFactory:
    """Factory para crear la aplicación FastAPI ultra-avanzada."""
    
    def __init__(self, system_instance):
        """
        Inicializa el factory de API.
        
        Args:
            system_instance: Instancia del sistema principal de etiquetado
        """
        self.system = system_instance
        self.websocket_connections: List[WebSocket] = []
    
    def create_app(self) -> FastAPI:
        """Crea y configura la aplicación FastAPI."""
        app = FastAPI(
            title="FruPrint ULTRA Industrial API v4.0",
            description="API Ultra-Avanzada del Sistema de 6 Etiquetadoras con IA",
            version=self.system.version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Middleware CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Registrar rutas
        self._register_basic_routes(app)
        self._register_control_routes(app)
        self._register_motor_routes(app)
        self._register_belt_routes(app)
        self._register_diverter_routes(app)
        self._register_metrics_routes(app)
        self._register_websocket_routes(app)
        
        return app
    
    def _register_basic_routes(self, app: FastAPI):
        """Registra rutas básicas de salud y estado."""
        
        @app.get("/health")
        async def ultra_health_check():
            """Verificación de salud del sistema."""
            motor_status = {}
            if self.system.motor_controller:
                motor_status = self.system.motor_controller.get_status()
            
            return {
                "status": "ultra_healthy",
                "system_state": self.system._system_state.value,
                "uptime_seconds": self.system.metrics_manager.metrics.uptime_seconds,
                "version": self.system.version,
                "active_group": self.system.active_group_id,
                "motor_status": motor_status
            }
        
        @app.get("/status")
        async def get_ultra_status():
            """Obtiene el estado completo del sistema."""
            labelers_status = {}
            if hasattr(self.system, 'labeler_manager') and self.system.labeler_manager:
                labelers_status = self.system.labeler_manager.get_status_all()
            
            motor_status = {}
            if self.system.motor_controller:
                motor_status = self.system.motor_controller.get_status()
            
            # Estado de la banda transportadora
            belt_status = {
                "available": False,
                "running": False,
                "direction": "stopped",
                "speed": 0.0,
                "enabled": True,
            }
            
            if self.system.belt_controller:
                try:
                    belt_driver_status = await self.system.belt_controller.get_status()
                    if isinstance(belt_driver_status, dict):
                        # Mapear del formato del driver al formato esperado por el frontend
                        belt_status["available"] = True
                        belt_status["running"] = belt_driver_status.get("running", belt_driver_status.get("is_running", False))
                        belt_status["enabled"] = belt_driver_status.get("enabled", True)
                        
                        # Determinar dirección
                        if belt_status["running"]:
                            direction = belt_driver_status.get("direction", "forward")
                            belt_status["direction"] = direction if direction != "stopped" else "forward"
                        else:
                            belt_status["direction"] = "stopped"
                        
                        # Velocidad (convertir de porcentaje a m/s si es necesario)
                        speed_value = belt_driver_status.get("speed", belt_driver_status.get("speed_percent", 0.0))
                        belt_status["speed"] = speed_value
                except Exception as e:
                    logger.error(f"Error obteniendo estado de banda: {e}")
            
            # Estado del stepper (labeler laser DRV8825)
            stepper_status = {
                "available": self.system.laser_stepper is not None,
                "enabled": True,
                "isActive": False,
                "currentPower": 0,
                "activationCount": 0,
                "lastActivation": None,
                "sensorTriggers": 0,
                "manualActivations": 0,
            }
            
            if self.system.laser_stepper:
                try:
                    labeler_state = self.system.laser_stepper.get_status()
                    if isinstance(labeler_state, dict):
                        driver_info = labeler_state.get('driver', {})
                        stepper_status["isActive"] = driver_info.get('is_active', False)
                        stepper_status["activationCount"] = labeler_state.get('activation_count', 0)
                        
                        # Última activación
                        history = labeler_state.get('activation_history', [])
                        if history:
                            stepper_status["lastActivation"] = history[-1]
                except Exception as e:
                    logger.debug(f"Error obteniendo estado del stepper: {e}")
            
            # Estado del sistema de clasificación
            stats = {
                "uptime_s": self.system.metrics_manager.metrics.uptime_seconds,
                "detections_total": self.system.metrics_manager.metrics.total_fruits_detected,
                "labeled_total": self.system.metrics_manager.metrics.total_labels_applied,
                "classified_total": sum(
                    metrics.classified_count 
                    for metrics in self.system.metrics_manager.category_metrics.values()
                ),
            }
            
            return {
                "system": {
                    "id": self.system.system_id,
                    "name": self.system.system_name,
                    "state": self.system._system_state.value,
                    "uptime": self.system.metrics_manager.metrics.uptime_seconds,
                    "version": self.system.version
                },
                "belt": belt_status,
                "stepper": stepper_status,
                "stats": stats,
                "metrics": asdict(self.system.metrics_manager.metrics),
                "labelers": labelers_status,
                "motor": motor_status,
                "categories": {
                    cat.fruit_name: asdict(metrics) 
                    for cat, metrics in self.system.metrics_manager.category_metrics.items()
                }
            }
    
    def _register_control_routes(self, app: FastAPI):
        """Registra rutas de control de producción."""
        
        @app.post("/control/start")
        async def start_ultra_production():
            """Inicia la producción."""
            if self.system._system_state == SystemState.IDLE:
                await self.system.start_production()
                labelers_count = len(getattr(self.system.labeler_manager, 'labelers', {}))
                return {
                    "message": "Producción ultra iniciada", 
                    "labelers_active": labelers_count
                }
            else:
                raise HTTPException(
                    400, 
                    f"No se puede iniciar desde estado: {self.system._system_state.value}"
                )
        
        @app.post("/control/stop")
        async def stop_ultra_production():
            """Detiene la producción."""
            await self.system.stop_production()
            return {"message": "Producción ultra detenida"}
        
        @app.post("/control/emergency_stop")
        async def ultra_emergency_stop():
            """Parada de emergencia del sistema."""
            await self.system.emergency_stop()
            return {"message": "PARADA DE EMERGENCIA ULTRA"}
    
    def _register_motor_routes(self, app: FastAPI):
        """Registra rutas de control del motor lineal."""
        
        @app.post("/motor/activate_group")
        async def activate_labeler_group(category: str):
            """Activa un grupo de etiquetadoras para una categoría."""
            try:
                fruit_category = FruitCategory[category.upper()]
                
                if not self.system.motor_controller:
                    raise HTTPException(404, "Motor controller no disponible")
                
                success = await self.system.motor_controller.activate_labeler_group(fruit_category)
                
                group_info = None
                for group in LabelerGroup:
                    if group.category == fruit_category.fruit_name:
                        group_info = group
                        break
                
                return {
                    "success": success,
                    "category": category,
                    "active_group": self.system.motor_controller.current_active_group,
                    "labeler_ids": group_info.labeler_ids if group_info else [],
                    "message": f"Grupo {fruit_category.emoji} activado - {LABELERS_PER_GROUP} etiquetadoras operativas"
                }
            except KeyError:
                raise HTTPException(
                    400, 
                    f"Categoría no válida: {category}. Disponibles: apple, pear, lemon"
                )
            except Exception as e:
                raise HTTPException(500, f"Error activando grupo: {e}")
        
        @app.get("/motor/status")
        async def get_motor_status():
            """Obtiene el estado del motor."""
            if not self.system.motor_controller:
                raise HTTPException(404, "Motor controller no disponible")
            return self.system.motor_controller.get_status()
        
        @app.post("/laser_stepper/toggle")
        async def toggle_laser_stepper(request: StepperRequest):
            """Habilita/deshabilita el stepper láser."""
            if self.system.laser_stepper_settings is None:
                self.system.laser_stepper_settings = {}
            
            if request.enabled is not None:
                self.system.laser_stepper_settings.setdefault("activation_on_laser", {})
                self.system.laser_stepper_settings["activation_on_laser"]["enabled"] = request.enabled
                return {"success": True, "enabled": request.enabled}
            
            return {"success": False, "message": "enabled parameter required"}
        
        @app.post("/laser_stepper/test")
        async def test_laser_stepper(request: StepperRequest):
            """Prueba el stepper láser."""
            if not self.system.laser_stepper:
                raise HTTPException(404, "Stepper no inicializado")
            
            duration = request.duration or 0.5
            intensity = request.intensity or 80.0
            ok = await self.system.laser_stepper.activate_for_duration(duration, intensity)
            return {"success": ok, "duration": duration, "intensity": intensity}
    
    def _register_belt_routes(self, app: FastAPI):
        """Registra rutas de control de banda transportadora."""
        
        @app.post("/belt/start_forward")
        async def start_belt_forward():
            """Inicia la banda hacia adelante."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            success = await self.system.belt_controller.start_belt()
            if success:
                return {
                    "success": True,
                    "message": "Banda iniciada hacia adelante",
                    "direction": "forward",
                    "timestamp": datetime.now().isoformat()
                }
            raise HTTPException(500, "Error iniciando banda")
        
        @app.post("/belt/start_backward")
        async def start_belt_backward():
            """Inicia la banda hacia atrás."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            success = await self.system.belt_controller.reverse_direction()
            if success:
                return {
                    "success": True,
                    "message": "Banda iniciada hacia atrás",
                    "direction": "backward",
                    "timestamp": datetime.now().isoformat()
                }
            raise HTTPException(500, "Error iniciando banda")
        
        @app.post("/belt/stop")
        async def stop_belt():
            """Detiene la banda."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            success = await self.system.belt_controller.stop_belt()
            if success:
                return {
                    "success": True,
                    "message": "Banda detenida",
                    "direction": "stopped",
                    "timestamp": datetime.now().isoformat()
                }
            raise HTTPException(500, "Error deteniendo banda")
        
        @app.post("/belt/set_speed")
        async def set_belt_speed(speed_data: SpeedData):
            """Establece la velocidad de la banda."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            speed = speed_data.speed
            if not (0.1 <= speed <= 2.0):
                raise HTTPException(400, "Velocidad debe estar entre 0.1 y 2.0 m/s")
            
            speed_percent = (speed / 2.0) * 100
            success = await self.system.belt_controller.set_speed(speed_percent)
            
            if success:
                return {
                    "success": True,
                    "message": f"Velocidad establecida a {speed} m/s",
                    "speed_ms": speed,
                    "speed_percent": speed_percent,
                    "timestamp": datetime.now().isoformat()
                }
            raise HTTPException(500, "Error estableciendo velocidad")
        
        @app.get("/belt/status")
        async def get_belt_status():
            """Obtiene el estado de la banda."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            status = await self.system.belt_controller.get_status()
            return {
                **status,
                "timestamp": datetime.now().isoformat(),
                "system_connected": True
            }
        
        @app.post("/belt/emergency_stop")
        async def emergency_stop_belt():
            """Parada de emergencia de la banda."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            try:
                # Detener inmediatamente
                success = await self.system.belt_controller.stop_belt()
                
                # Si el controlador tiene método específico de emergencia, usarlo
                if hasattr(self.system.belt_controller, 'emergency_brake'):
                    await self.system.belt_controller.emergency_brake()
                
                return {
                    "success": True,
                    "message": "PARADA DE EMERGENCIA EJECUTADA",
                    "direction": "emergency_stopped",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(500, f"Error en parada de emergencia: {e}")
        
        @app.post("/belt/toggle_enable")
        async def toggle_belt_enable():
            """Habilita o deshabilita el sistema de banda."""
            if not self.system.belt_controller:
                raise HTTPException(404, "Controlador de banda no disponible")
            
            try:
                # Obtener estado actual
                current_status = await self.system.belt_controller.get_status()
                is_enabled = current_status.get('enabled', True)
                
                # Alternar estado
                new_state = not is_enabled
                
                # Si se deshabilita, detener banda
                if not new_state:
                    await self.system.belt_controller.stop_belt()
                
                return {
                    "success": True,
                    "enabled": new_state,
                    "message": f"Sistema {'habilitado' if new_state else 'deshabilitado'}",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(500, f"Error al alternar estado: {e}")
    
    def _register_diverter_routes(self, app: FastAPI):
        """Registra rutas del sistema de desviadores."""
        
        @app.get("/diverters/status")
        async def get_diverters_status():
            """Obtiene el estado del sistema de desviadores."""
            if not self.system.diverter_controller:
                raise HTTPException(404, "Sistema de desviadores no disponible")
            return self.system.diverter_controller.get_status()
        
        @app.post("/diverters/classify")
        async def manual_classify_fruit(request: CategoryRequest):
            """Clasifica manualmente una fruta."""
            if not self.system.diverter_controller:
                raise HTTPException(404, "Sistema de desviadores no disponible")
            
            try:
                # Importar enum del diverter controller
                from Control_Etiquetado.fruit_diverter_controller import FruitCategory as DiverterFruitCategory
                fruit_category = DiverterFruitCategory[request.category.upper()]
                success = await self.system.diverter_controller.classify_fruit(
                    fruit_category, 
                    request.delay
                )
                
                return {
                    "success": success,
                    "category": request.category,
                    "delay": request.delay,
                    "message": f"Clasificación {'exitosa' if success else 'fallida'} para {fruit_category.emoji}"
                }
            except KeyError:
                raise HTTPException(
                    400, 
                    f"Categoría no válida: {request.category}. Disponibles: apple, pear, lemon"
                )
    
    def _register_metrics_routes(self, app: FastAPI):
        """Registra rutas de métricas y predicciones."""
        
        @app.get("/metrics/categories")
        async def get_category_metrics():
            """Obtiene métricas detalladas por categoría."""
            return {
                cat.fruit_name: {
                    "emoji": cat.emoji,
                    "labeler_id": cat.labeler_id,
                    "metrics": asdict(metrics)
                } 
                for cat, metrics in self.system.metrics_manager.category_metrics.items()
            }
        
        @app.get("/metrics/predictions")
        async def get_predictions():
            """Obtiene predicciones del sistema."""
            if not hasattr(self.system, 'prediction_engine') or not self.system.prediction_engine:
                return {"error": "Motor de predicción no disponible"}
            
            next_category = None
            if hasattr(self.system, 'pattern_analyzer') and self.system.pattern_analyzer:
                predicted = self.system.pattern_analyzer.predict_next_category()
                next_category = predicted.fruit_name if predicted else "unknown"
            
            return {
                "predicted_throughput_1h": self.system.prediction_engine.predict_throughput(60),
                "next_category": next_category,
                "patterns": list(self.system.pattern_analyzer.pattern_history)[-10:] if self.system.pattern_analyzer else []
            }
    
    def _register_websocket_routes(self, app: FastAPI):
        """Registra rutas de WebSocket."""
        
        @app.websocket("/ws/ultra_dashboard")
        async def ultra_websocket_endpoint(websocket: WebSocket):
            """WebSocket para dashboard ultra en tiempo real."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    labelers_status = {}
                    if hasattr(self.system, 'labeler_manager') and self.system.labeler_manager:
                        labelers_status = self.system.labeler_manager.get_status_all()
                    
                    motor_position = 0.0
                    if self.system.motor_controller:
                        motor_position = getattr(self.system.motor_controller, 'current_position', 0.0)
                    
                    ultra_data = {
                        "timestamp": datetime.now().isoformat(),
                        "system_state": self.system._system_state.value,
                        "metrics": asdict(self.system.metrics_manager.metrics),
                        "active_labeler": self.system.active_group_id,
                        "motor_position": motor_position,
                        "categories": {
                            cat.fruit_name: asdict(metrics) 
                            for cat, metrics in self.system.metrics_manager.category_metrics.items()
                        },
                        "labelers_status": labelers_status
                    }
                    
                    await websocket.send_json(ultra_data)
                    await asyncio.sleep(1)
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def broadcast_to_websockets(self, data: Dict[str, Any]):
        """Envía datos a todas las conexiones WebSocket activas."""
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        
        for ws in disconnected:
            try:
                self.websocket_connections.remove(ws)
            except ValueError:
                pass
    
    async def broadcast_detection_event(self, category: str, count: int, confidence: float = 0.95):
        """Envía evento de detección a todos los clientes conectados."""
        event_data = {
            "type": "detection_event",
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "count": count,
            "confidence": confidence,
            "emoji": FruitCategory[category.upper()].emoji if category.upper() in FruitCategory.__members__ else "🍎"
        }
        await self.broadcast_to_websockets(event_data)

# ==================== SERVIDOR API ====================

async def start_api_server(app: FastAPI, host: str = "0.0.0.0", port: int = 8000):
    """Inicia el servidor API."""
    logger.info(f"🚀 Iniciando servidor API en {host}:{port}")
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    
    try:
        started_event = getattr(server, 'started', None)
        if started_event is not None:
            await started_event.wait()
        else:
            await asyncio.sleep(0.5)
        logger.info(f"✅ Servidor API escuchando en http://{host}:{port}")
    except Exception:
        pass
    
    return server_task

__all__ = ['UltraAPIFactory', 'start_api_server']
