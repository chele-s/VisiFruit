# fruprint_system/hardware/motors/conveyor_belt_controller.py
import asyncio
import logging
from typing import Dict, Any

from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE
from fruprint_system.core.exceptions import ConfigError, HardwareException

logger = logging.getLogger(__name__)

# --- Clases de Drivers ---

class BaseBeltDriver:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_initialized = False

    async def initialize(self) -> bool: raise NotImplementedError
    async def start(self, forward: bool = True) -> bool: raise NotImplementedError
    async def stop(self) -> bool: raise NotImplementedError
    async def cleanup(self): pass

class RelayBeltDriver(BaseBeltDriver):
    """Controlador para cinta transportadora usando un módulo de 2 relays."""
    async def initialize(self) -> bool:
        self.pin_forward = self.config.get('pin_forward_relay')
        self.pin_backward = self.config.get('pin_backward_relay')
        if not self.pin_forward or not self.pin_backward:
            raise ConfigError("Pines 'pin_forward_relay' y 'pin_backward_relay' son requeridos para el driver de relay.")
        
        self.is_active_low = self.config.get('is_active_low', True)
        self.STATE_ON = GPIO.LOW if self.is_active_low else GPIO.HIGH
        self.STATE_OFF = GPIO.HIGH if self.is_active_low else GPIO.LOW
        
        if GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.setup, self.pin_forward, GPIO.OUT, initial=self.STATE_OFF)
            await asyncio.to_thread(GPIO.setup, self.pin_backward, GPIO.OUT, initial=self.STATE_OFF)
        
        self.is_initialized = True
        return True

    async def start(self, forward: bool = True) -> bool:
        await self.stop()
        await asyncio.sleep(0.1) # Pausa de seguridad
        
        target_pin = self.pin_forward if forward else self.pin_backward
        if GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, target_pin, self.STATE_ON)
        return True

    async def stop(self) -> bool:
        if GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.pin_forward, self.STATE_OFF)
            await asyncio.to_thread(GPIO.output, self.pin_backward, self.STATE_OFF)
        return True

# (Aquí se podrían añadir otros drivers como L298NBeltDriver o PWMBeltDriver en el futuro)

# --- Clase Principal del Controlador ---

class ConveyorBeltController:
    """
    Controlador para la cinta transportadora.
    Selecciona el driver adecuado (relay, L298N, etc.) basado en la configuración.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.control_type = self.config.get("control_type", "relay")
        self.driver = self._create_driver()
        
        self.is_running = False
        self.current_direction = "stopped"

    def _create_driver(self) -> BaseBeltDriver:
        if self.control_type == "relay":
            return RelayBeltDriver(self.config)
        # Añadir 'elif' para otros tipos de drivers aquí
        else:
            raise ConfigError(f"Tipo de control de cinta no soportado: {self.control_type}")

    async def initialize(self) -> bool:
        logger.info(f"Inicializando controlador de cinta (tipo: {self.control_type})...")
        try:
            success = await self.driver.initialize()
            if success:
                logger.info("✅ Controlador de cinta inicializado.")
            return success
        except (ConfigError, HardwareException) as e:
            logger.error(f"❌ Fallo al inicializar driver de cinta: {e}")
            return False

    async def start_belt(self, forward: bool = True) -> bool:
        if not self.driver.is_initialized: return False
        
        self.current_direction = "forward" if forward else "backward"
        logger.info(f"Iniciando cinta en dirección: {self.current_direction}")
        success = await self.driver.start(forward)
        if success:
            self.is_running = True
        return success

    async def stop_belt(self) -> bool:
        if not self.driver.is_initialized: return False

        logger.info("Deteniendo cinta transportadora.")
        success = await self.driver.stop()
        if success:
            self.is_running = False
            self.current_direction = "stopped"
        return success

    async def emergency_brake(self):
        logger.warning("🛑 Parada de emergencia para la cinta transportadora.")
        await self.stop_belt()

    async def cleanup(self):
        logger.info("Limpiando recursos de la cinta transportadora.")
        if self.driver and self.driver.is_initialized:
            await self.driver.cleanup()

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "direction": self.current_direction,
            "is_initialized": self.driver.is_initialized if self.driver else False,
            "control_type": self.control_type
        }
