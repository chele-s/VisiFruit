# fruprint_system/core/controller.py
import asyncio
from typing import Dict, Any

from fruprint_system.core.logging_config import get_logger
from fruprint_system.core.exceptions import *
from fruprint_system.core.state_machine import SystemStateMachine # Importamos la máquina de estados

from fruprint_system.config.schemas import MainConfig
from fruprint_system.hardware.motors.linear_motor_controller import UltraLinearMotorController
from fruprint_system.hardware.labelers.labeler_actuator import LabelerActuator
from fruprint_system.hardware.motors.conveyor_belt_controller import ConveyorBeltController
from fruprint_system.hardware.sensors.sensor_interface import SensorInterface
from utils.camera_controller import CameraController
from fruprint_system.ai.fruit_detector import FruitDetector
from fruprint_system.api.api_server import APIServer
from fruprint_system.core.types import LabelerGroup

from utils.gpio_wrapper import get_gpio_info

logger = get_logger(__name__)

TOTAL_LABELERS = 6

class SystemController:
    """
    Controlador principal del sistema FruPrint. El estado es gestionado
    por la SystemStateMachine.
    """
    def __init__(self, config_path: str):
        try:
            self.config = MainConfig.from_json(config_path)
        except Exception as e:
            raise ConfigError(f"Error al cargar la configuración: {e}") from e
            
        # La máquina de estados se encargará del estado.
        # El estado actual se consultará a través de `self.state`.
        self.state_machine = SystemStateMachine(self)
        
        self._processing_queue = asyncio.queue.Queue(maxsize=100)
        self._main_loop_task: asyncio.Task | None = None
        
        self.motor_controller: UltraLinearMotorController | None = None
        self.labelers: Dict[int, LabelerActuator] = {}
        self.belt_controller: ConveyorBeltController | None = None
        self.trigger_sensor: SensorInterface | None = None
        self.camera: CameraController | None = None
        self.ai_detector: FruitDetector | None = None
        self.api_server: APIServer | None = None
        
    async def initialize_system(self):
        """Dispara la transición para inicializar el sistema."""
        if self.state != 'offline':
            logger.warning("El sistema ya está inicializado o en proceso.", current_state=self.state)
            return False
        
        await self.initialize() # Dispara el trigger de la máquina de estados
        return self.state == 'idle'

    async def on_enter_initializing(self, event):
        """Callback que se ejecuta al entrar en el estado 'initializing'."""
        logger.info("=== Iniciando secuencia de inicialización ===")
        try:
            gpio_info = get_gpio_info()
            logger.info("GPIO Wrapper Status", **gpio_info)
            
            await self._initialize_components()
            await self._initialize_services()
            self._main_loop_task = asyncio.create_task(self._processing_loop())
            
            await self.initialization_complete() # Transición al estado 'idle'
        except Exception as e:
            logger.critical("Fallo crítico durante la inicialización.", error=str(e), exc_info=True)
            await self.encounter_error(error=e)

    async def _initialize_components(self):
        # ... (los métodos _initialize_* permanecen igual pero pueden lanzar excepciones)
        logger.info("--- Inicializando componentes ---")
        await self._initialize_ai_detector()
        await self._initialize_camera()
        await self._initialize_sensor()
        await self._initialize_belt_controller()
        await self._initialize_motor_controller()
        await self._initialize_labelers()
        logger.info("--- Componentes inicializados ---")

    async def _initialize_services(self):
        logger.info("--- Inicializando servicios ---")
        await self._initialize_api_server()
        logger.info("--- Servicios inicializados ---")

    async def on_enter_running(self, event):
        """Callback que se ejecuta al entrar en el estado 'running'."""
        if self.belt_controller:
            await self.belt_controller.start_belt()
        logger.info("Producción activa.")

    async def on_enter_stopping(self, event):
        """Callback que se ejecuta al entrar en el estado 'stopping'."""
        if self.belt_controller:
            await self.belt_controller.stop_belt()
        logger.info("Producción detenida.")
        await self.production_stopped() # Transición a 'idle'

    async def on_enter_emergency_stop(self, event):
        """Callback para la parada de emergencia."""
        logger.critical("ESTADO DE PARADA DE EMERGENCIA ACTIVADO")
        if self.belt_controller: await self.belt_controller.emergency_brake()
        if self.motor_controller: await self.motor_controller.emergency_stop()
        if self.labelers: await asyncio.gather(*(l.emergency_stop() for l in self.labelers.values()))
        # Detener más componentes si es necesario

    async def shutdown_system(self):
        """Dispara la transición para apagar el sistema."""
        await self.shutdown()

    async def on_enter_offline(self, event):
        """Callback que se ejecuta al entrar en el estado 'offline'."""
        logger.info("Iniciando secuencia de apagado de componentes...")
        if self._main_loop_task:
            self._main_loop_task.cancel()
            await asyncio.sleep(0.1)

        if self.api_server: await self.api_server.stop()
        if self.labelers: await asyncio.gather(*(l.cleanup() for l in self.labelers.values()))
        if self.motor_controller: await self.motor_controller.cleanup()
        if self.belt_controller: await self.belt_controller.cleanup()
        if self.trigger_sensor: self.trigger_sensor.cleanup()
        if self.camera: await self.camera.shutdown()
        if self.ai_detector: await self.ai_detector.shutdown()
        logger.info("Apagado de componentes completado.")
        
    async def _processing_loop(self):
        while self.state not in ['offline', 'error', 'emergency_stop']:
            try:
                if self.state == 'running':
                    frame = await asyncio.wait_for(self._processing_queue.get(), timeout=1.0)
                    if self.ai_detector:
                        detections = await self.ai_detector.detect(frame)
                        if detections:
                            logger.info("Detección completada", num_detections=len(detections))
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
                
    # El resto de los métodos (_initialize_*, _handle_sensor_trigger, etc.) permanecen sin cambios
    async def _initialize_api_server(self):
        api_config = self.config.api_settings
        self.api_server = APIServer(self, host=api_config.host, port=api_config.port)
        await self.api_server.start()
    async def _initialize_ai_detector(self):
        ai_config = self.config.ai_model_settings.dict()
        self.ai_detector = FruitDetector(ai_config)
        if not await self.ai_detector.initialize(): raise AIError("Fallo al inicializar IA.")
    async def _initialize_camera(self):
        camera_config = self.config.camera_settings.dict()
        self.camera = CameraController(camera_config)
        if not await self.camera.initialize(): raise CameraError("Fallo al inicializar cámara.")
    async def _initialize_sensor(self):
        sensor_config = self.config.sensor_settings.dict()
        self.trigger_sensor = SensorInterface(sensor_config, self._handle_sensor_trigger)
        if not self.trigger_sensor.initialize(): raise SensorError("Fallo al inicializar sensor.")
    async def _initialize_belt_controller(self):
        belt_config = self.config.conveyor_belt_settings.dict()
        self.belt_controller = ConveyorBeltController(belt_config)
        if not await self.belt_controller.initialize(): raise HardwareException("Fallo al inicializar cinta.")
    async def _initialize_motor_controller(self):
        motor_config = self.config.motor_controller_settings.dict()
        self.motor_controller = UltraLinearMotorController(motor_config)
        if not await self.motor_controller.initialize(): raise MotorError("Fallo al inicializar motor lineal.")
    async def _initialize_labelers(self):
        base_config = self.config.labeler_settings.dict()
        groups_config = [{"name": "Apple", "ids": LabelerGroup.GROUP_APPLE.labeler_ids}, {"name": "Pear", "ids": LabelerGroup.GROUP_PEAR.labeler_ids}, {"name": "Lemon", "ids": LabelerGroup.GROUP_LEMON.labeler_ids}]
        tasks = [self._create_labeler(g, id, base_config) for g in groups_config for id in g["ids"]]
        if not all(await asyncio.gather(*tasks)): raise LabelerError("Fallo al inicializar etiquetadoras.")
    async def _create_labeler(self, group, labeler_id, base_config):
        pin = base_config.get("pin", 20) + labeler_id
        config = {"name": f"Labeler-{group['name']}-{labeler_id}", "pin": pin}
        labeler = LabelerActuator(config)
        self.labelers[labeler_id] = labeler
        return await labeler.initialize()
    async def _handle_sensor_trigger(self):
        if self.state != 'running': return
        if not self.camera: return
        frame = await self.camera.capture_frame()
        if frame is not None:
            try: self._processing_queue.put_nowait(frame)
            except asyncio.QueueFull: logger.warning("Cola de procesamiento llena.")
        else: logger.error("No se pudo capturar imagen.")

