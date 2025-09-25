# fruprint_system/hardware/labelers/labeler_actuator.py
import asyncio
import logging
import time
from typing import Dict, Any

from tenacity import retry, stop_after_attempt, wait_exponential

from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE
from fruprint_system.core.exceptions import LabelerError, ConfigError

logger = logging.getLogger(__name__)

# --- Clases Base y Drivers ---

class BaseActuatorDriver:
    """Clase base para diferentes tipos de actuadores."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pin = int(config["pin"])
        self.is_initialized = False
        self._is_active = False

    async def initialize(self) -> bool:
        raise NotImplementedError

    async def activate(self, duration: float, intensity: float) -> bool:
        raise NotImplementedError

    async def deactivate(self) -> bool:
        raise NotImplementedError

    async def cleanup(self):
        pass

class SolenoidDriver(BaseActuatorDriver):
    """Driver para un solenoide simple."""
    async def initialize(self) -> bool:
        if not GPIO_AVAILABLE:
            self.is_initialized = True
            return True
        try:
            await asyncio.to_thread(GPIO.setup, self.pin, GPIO.OUT)
            await asyncio.to_thread(GPIO.output, self.pin, False)
            self.is_initialized = True
            return True
        except Exception as e:
            raise LabelerError(f"Fallo al inicializar solenoide en pin {self.pin}") from e

    async def activate(self, duration: float, intensity: float) -> bool:
        self._is_active = True
        if GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.pin, True)
        
        await asyncio.sleep(duration)
        await self.deactivate()
        return True

    async def deactivate(self) -> bool:
        if GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.pin, False)
        self._is_active = False
        return True

class StepperDriver(BaseActuatorDriver):
    """Driver para un motor paso a paso (como DRV8825)."""
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.dir_pin = int(config["dir_pin"])
        self.step_pin = int(config["step_pin"]) # El 'pin' base se considera el step_pin
        self.pin = self.step_pin 
        self.enable_pin = config.get("enable_pin")
        self.step_pulse_us = config.get("step_pulse_us", 4)

    async def initialize(self) -> bool:
        if not GPIO_AVAILABLE:
            self.is_initialized = True
            return True
        try:
            await asyncio.to_thread(GPIO.setup, self.step_pin, GPIO.OUT)
            await asyncio.to_thread(GPIO.setup, self.dir_pin, GPIO.OUT)
            if self.enable_pin:
                await asyncio.to_thread(GPIO.setup, self.enable_pin, GPIO.OUT)
                await asyncio.to_thread(GPIO.output, self.enable_pin, True) # Deshabilitar
            self.is_initialized = True
            return True
        except Exception as e:
            raise LabelerError(f"Fallo al inicializar stepper en pines STEP={self.step_pin}, DIR={self.dir_pin}") from e

    async def activate(self, duration: float, intensity: float) -> bool:
        self._is_active = True
        if self.enable_pin and GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.enable_pin, False) # Habilitar

        # Lógica para generar pulsos
        speed_sps = max(100.0, 3000.0 * (intensity / 100.0))
        await self._run_steps(duration, speed_sps)

        await self.deactivate()
        return True

    async def _run_steps(self, duration: float, speed_sps: float):
        """Genera pulsos de paso en un hilo para no bloquear."""
        if not GPIO_AVAILABLE:
            await asyncio.sleep(duration)
            return

        step_interval_s = 1.0 / speed_sps
        half_pulse_s = max(self.step_pulse_us / 1_000_000.0, 1e-6)
        end_time = time.time() + duration
        
        def _loop():
            while time.time() < end_time:
                GPIO.output(self.step_pin, True)
                time.sleep(half_pulse_s)
                GPIO.output(self.step_pin, False)
                time.sleep(step_interval_s - half_pulse_s)
        
        await asyncio.to_thread(_loop)

    async def deactivate(self) -> bool:
        if self.enable_pin and GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.enable_pin, True) # Deshabilitar
        self._is_active = False
        return True


# --- Clase Principal del Actuador ---

class LabelerActuator:
    """
    Controlador para un actuador de etiquetadora individual.
    Selecciona el driver correcto (solenoid, stepper) basado en la configuración.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", f"Labeler-Pin{config.get('pin')}")
        self.actuator_type = config.get("type", "solenoid")
        
        self.driver = self._create_driver()

    def _create_driver(self) -> BaseActuatorDriver:
        if self.actuator_type == "stepper":
            return StepperDriver(self.config)
        elif self.actuator_type == "solenoid":
            return SolenoidDriver(self.config)
        else:
            raise ConfigError(f"Tipo de actuador no soportado: {self.actuator_type}")

    async def initialize(self) -> bool:
        logger.info(f"Inicializando actuador '{self.name}' (tipo: {self.actuator_type})...")
        try:
            success = await self.driver.initialize()
            if success:
                logger.info(f"✅ Actuador '{self.name}' inicializado.")
            return success
        except LabelerError as e:
            logger.error(f"❌ Fallo al inicializar '{self.name}': {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True  # Vuelve a lanzar la excepción si todos los reintentos fallan
    )
    async def activate_for_duration(self, duration: float, intensity: float = 100.0) -> bool:
        if not self.driver.is_initialized or self.driver._is_active:
            return False
        
        logger.debug(f"Activando '{self.name}' por {duration:.2f}s.")
        try:
            return await self.driver.activate(duration, intensity)
        except Exception as e:
            logger.error(f"Error durante activación de '{self.name}': {e}")
            raise  # Re-lanzamos para que Tenacity lo capture y reintente

    async def emergency_stop(self):
        logger.warning(f"🛑 Parada de emergencia para actuador '{self.name}'")
        await self.driver.deactivate()

    async def cleanup(self):
        if self.driver and self.driver.is_initialized:
            logger.info(f"Limpiando recursos para '{self.name}'.")
            await self.emergency_stop()
            await self.driver.cleanup()
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.actuator_type,
            "is_initialized": self.driver.is_initialized,
            "is_active": self.driver._is_active,
        }
