# fruprint_system/core/controller.py
import asyncio
import time
from typing import Dict, Any, List

from fruprint_system.core.logging_config import get_logger
from fruprint_system.core.exceptions import *
from fruprint_system.core.state_machine import SystemStateMachine
from fruprint_system.config.schemas import MainConfig
from fruprint_system.hardware.motors.linear_motor_controller import UltraLinearMotorController
from fruprint_system.hardware.labelers.labeler_actuator import LabelerActuator
from fruprint_system.hardware.motors.conveyor_belt_controller import ConveyorBeltController
from fruprint_system.hardware.sensors.sensor_interface import SensorInterface
from utils.camera_controller import CameraController
from fruprint_system.ai.fruit_detector import FruitDetector
from fruprint_system.api.api_server import APIServer
from fruprint_system.core.types import LabelerGroup
from fruprint_system.metrics.prometheus_metrics import MetricsCollector
from fruprint_system.core.persistent_queue import PersistentQueue

from utils.gpio_wrapper import get_gpio_info

logger = get_logger(__name__)

class SystemController:
    def __init__(self, config_path: str):
        # ... (inicialización existente)
        self.pending_activations: List[asyncio.TimerHandle] = []

    # ... (métodos existentes como __aenter__, __aexit__, initialize_system, etc.)

    async def on_enter_offline(self, event):
        # ... (lógica de apagado existente)
        # Cancelar cualquier activación de etiquetado pendiente
        for handle in self.pending_activations:
            handle.cancel()
        self.pending_activations.clear()
        logger.info("Activaciones de etiquetado pendientes canceladas.")

    async def _processing_loop(self):
        while self.state not in ['offline', 'error', 'emergency_stop']:
            try:
                if self.state == 'running':
                    frame = await asyncio.wait_for(self._processing_queue.get(), timeout=1.0)
                    if self.ai_detector:
                        detections = await self.ai_detector.detect(frame)
                        if detections:
                            logger.info("Detección completada", num_detections=len(detections))
                            # Programar acciones de etiquetado basadas en las detecciones
                            await self._schedule_labeling_actions(detections)
                    self._processing_queue.task_done()
                else:
                    await asyncio.sleep(0.1)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error en bucle de procesamiento", error=str(e), exc_info=True)
                await self.encounter_error(error=e)

    async def _schedule_labeling_actions(self, detections: List[Dict]):
        """
        Calcula el delay y programa la activación de los etiquetadores para cada detección.
        """
        belt_speed_mps = self.config.conveyor_belt_settings.belt_speed_mps
        if belt_speed_mps <= 0:
            logger.warning("La velocidad de la cinta es 0 o negativa. No se puede programar el etiquetado.")
            return

        for detection in detections:
            # TODO: Implementar una lógica más sofisticada para mapear 'class_name' a un grupo/etiquetador
            # Por ahora, activaremos el grupo 0 (Manzanas) como ejemplo
            target_group = LabelerGroup.GROUP_APPLE 
            
            # Usar la distancia configurada para ese grupo de etiquetadores
            distance_m = self.config.motor_controller_settings.distance_camera_to_labeler_m

            # Fórmula de sincronización
            travel_time_s = distance_m / belt_speed_mps
            processing_delay_s = self.config.sync_settings.processing_delay_ms / 1000.0
            safety_margin_s = self.config.sync_settings.safety_margin_ms / 1000.0
            total_delay_s = travel_time_s + processing_delay_s + safety_margin_s

            logger.info(f"Programando activación para '{detection['class_name']}' en {total_delay_s:.2f} segundos.")
            
            # Programar la activación usando asyncio.call_later
            loop = asyncio.get_running_loop()
            handle = loop.call_later(
                total_delay_s,
                lambda group=target_group: asyncio.create_task(self._execute_labeling(group))
            )
            self.pending_activations.append(handle)

    async def _execute_labeling(self, group: LabelerGroup):
        """
        Activa el grupo de etiquetadores correcto. Esta es la función que se llama después del delay.
        """
        if self.state != 'running':
            logger.warning(f"Se omitió el etiquetado para el grupo {group.name} porque el sistema ya no está en estado 'running'.")
            return

        logger.info(f"¡TIEMPO CUMPLIDO! Activando etiquetadores para el grupo: {group.name}")
        
        # 1. Mover el motor lineal al grupo correcto
        if self.motor_controller:
            # Esta es una simplificación. En un sistema real, necesitarías gestionar
            # el cambio de grupo de forma más inteligente si las detecciones son muy seguidas.
            await self.motor_controller.activate_labeler_group_by_id(group.group_id)

        # 2. Activar los solenoides de ese grupo
        duration = self.config.labeler_settings.activation_duration_s
        tasks = []
        for labeler_id in group.labeler_ids:
            if labeler_id in self.labelers:
                tasks.append(self.labelers[labeler_id].activate_for_duration(duration))
        
        await asyncio.gather(*tasks)
        logger.info(f"Activación completada para el grupo {group.name}.")

    # ... (resto de los métodos de la clase)
