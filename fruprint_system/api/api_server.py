# fruprint_system/api/api_server.py
import asyncio
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

from fruprint_system.core import controller as system_controller
from fruprint_system.core.logging_config import get_logger

logger = get_logger(__name__)

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

        @app.get("/status")
        async def get_status():
            return {"current_state": self.controller.state}

        @app.post("/control/start")
        async def start_production():
            if self.controller.state != 'idle':
                raise HTTPException(status_code=409, detail=f"No se puede iniciar desde el estado actual: {self.controller.state}")
            await self.controller.start_production()
            return {"message": f"Comando 'start_production' enviado. Transicionando a 'starting'."}

        @app.post("/control/stop")
        async def stop_production():
            if self.controller.state != 'running':
                raise HTTPException(status_code=409, detail=f"No se puede detener desde el estado actual: {self.controller.state}")
            await self.controller.stop_production()
            return {"message": "Comando 'stop_production' enviado. Transicionando a 'stopping'."}
            
        @app.post("/control/emergency_stop")
        async def emergency_stop():
            logger.critical("Comando de PARADA DE EMERGENCIA recibido desde la API.")
            await self.controller.emergency()
            return {"message": "Comando de emergencia enviado."}
            
        @app.post("/control/reset")
        async def reset_from_error():
            if self.controller.state not in ['error', 'emergency_stop']:
                 raise HTTPException(status_code=409, detail=f"No hay error que resetear. Estado actual: {self.controller.state}")
            await self.controller.reset_error()
            return {"message": "Comando de reseteo enviado. Transicionando a 'idle'."}

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
