# fruprint_system/api/api_server.py
import asyncio
from typing import Any, Optional, List
from pydantic import BaseModel, Field

import uvicorn
from fastapi import FastAPI, HTTPException

from fruprint_system.core import controller as system_controller
from fruprint_system.core.logging_config import get_logger

logger = get_logger(__name__)

# --- Pydantic Models for API Documentation ---

class ProductionStartRequest(BaseModel):
    """Cuerpo de la solicitud para iniciar la producción."""
    speed: float = Field(1.0, gt=0, le=2.0, description="Velocidad relativa de la cinta (0.1 a 2.0)")
    category_filter: Optional[List[str]] = Field(None, description="Lista opcional de categorías de fruta a procesar.")

class BeltSpeedRequest(BaseModel):
    """Cuerpo de la solicitud para establecer la velocidad de la cinta."""
    speed_percent: float = Field(100.0, ge=0, le=100, description="Velocidad de la cinta como porcentaje (0-100).")

class StatusResponse(BaseModel):
    """Respuesta del endpoint de estado."""
    current_state: str
    
class ActionResponse(BaseModel):
    """Respuesta genérica para acciones de control."""
    message: str
    
class BeltStatusResponse(BaseModel):
    """Respuesta detallada del estado de la cinta."""
    is_running: bool
    direction: str
    is_initialized: bool
    is_enabled: bool
    control_type: str
    simulation_mode: bool

class APIServer:
    def __init__(self, controller: "system_controller.SystemController", host: str, port: int):
        self.controller = controller
        self.host = host
        self.port = port
        self.app = self._create_fastapi_app()
        self.server_task: asyncio.Task | None = None

    def _create_fastapi_app(self) -> FastAPI:
        app = FastAPI(
            title="FruPrint System API (State Machine)",
            description="API para controlar y monitorear el sistema de etiquetado.",
            version="4.1"
        )
        # ... (CORS middleware)

        @app.get("/status", response_model=StatusResponse)
        async def get_status():
            """Obtiene el estado actual de la máquina de estados del sistema."""
            return {"current_state": self.controller.state}

        @app.post("/control/start", response_model=ActionResponse)
        async def start_production(request: ProductionStartRequest):
            """
            Inicia la producción del sistema.
            
            - **speed**: Velocidad relativa de la cinta (0.1 a 2.0).
            - **category_filter**: Lista de categorías a procesar (ej: ["apple", "pear"]).
            """
            if self.controller.state != 'idle':
                raise HTTPException(status_code=409, detail=f"No se puede iniciar desde el estado actual: {self.controller.state}")
            
            await self.controller.state_machine.trigger('start_production')
            return {"message": f"Comando 'start_production' enviado. Transicionando a 'running'."}

        @app.post("/control/stop", response_model=ActionResponse)
        async def stop_production():
            """Detiene la producción y devuelve el sistema al estado 'idle'."""
            if self.controller.state != 'running':
                raise HTTPException(status_code=409, detail=f"No se puede detener desde el estado actual: {self.controller.state}")
            await self.controller.state_machine.trigger('stop_production')
            return {"message": "Comando 'stop_production' enviado. Transicionando a 'stopping'."}
            
        @app.post("/control/emergency_stop", response_model=ActionResponse)
        async def emergency_stop():
            """Activa la parada de emergencia del sistema."""
            logger.critical("Comando de PARADA DE EMERGENCIA recibido desde la API.")
            await self.controller.state_machine.trigger('emergency_stop')
            return {"message": "Comando de emergencia enviado."}
            
        @app.post("/control/reset", response_model=ActionResponse)
        async def reset_from_error():
            """Resetea el sistema desde un estado de error o emergencia."""
            if self.controller.state not in ['error', 'emergency_stop']:
                 raise HTTPException(status_code=409, detail=f"No hay error que resetear. Estado actual: {self.controller.state}")
            await self.controller.state_machine.trigger('reset_error')
            return {"message": "Comando de reseteo enviado. Transicionando a 'idle'."}

        # --- Endpoints de Control de Cinta ---

        @app.get("/belt/status", response_model=BeltStatusResponse)
        async def get_belt_status():
            """Obtiene el estado detallado de la cinta transportadora."""
            if not self.controller.belt_controller:
                raise HTTPException(status_code=503, detail="El controlador de la cinta no está disponible.")
            return self.controller.belt_controller.get_status()

        @app.post("/belt/start_forward", response_model=ActionResponse)
        async def belt_start_forward():
            """Inicia la cinta hacia adelante."""
            if not self.controller.belt_controller:
                raise HTTPException(status_code=503, detail="El controlador de la cinta no está disponible.")
            await self.controller.belt_controller.start_belt()
            return {"message": "Cinta iniciada hacia adelante."}

        @app.post("/belt/start_backward", response_model=ActionResponse)
        async def belt_start_backward():
            """Inicia la cinta hacia atrás."""
            if not self.controller.belt_controller:
                raise HTTPException(status_code=503, detail="El controlador de la cinta no está disponible.")
            await self.controller.belt_controller.reverse_direction()
            return {"message": "Cinta iniciada hacia atrás."}
            
        @app.post("/belt/stop", response_model=ActionResponse)
        async def belt_stop():
            """Detiene la cinta."""
            if not self.controller.belt_controller:
                raise HTTPException(status_code=503, detail="El controlador de la cinta no está disponible.")
            await self.controller.belt_controller.stop_belt()
            return {"message": "Cinta detenida."}

        @app.post("/belt/set_speed", response_model=ActionResponse)
        async def belt_set_speed(request: BeltSpeedRequest):
            """Establece la velocidad de la cinta (puede ser simulado)."""
            if not self.controller.belt_controller:
                raise HTTPException(status_code=503, detail="El controlador de la cinta no está disponible.")
            await self.controller.belt_controller.set_speed(request.speed_percent)
            return {"message": f"Velocidad de la cinta establecida al {request.speed_percent}%."}

        return app

    async def start(self):
        if self.server_task and not self.server_task.done():
            return
        logger.info(f"Iniciando servidor API en http://{self.host}:{self.port}")
        config = uvicorn.Config(app=self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(server.serve())
        await asyncio.sleep(1)

    async def stop(self):
        if self.server_task and not self.server_task.done():
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            logger.info("Servidor API detenido.")
