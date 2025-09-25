# fruprint_system/hardware/motors/conveyor_belt_controller.py
import asyncio
import logging
from typing import Dict, Any, Optional

from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE
from fruprint_system.core.exceptions import ConfigError, HardwareException

logger = logging.getLogger(__name__)

class ConveyorBeltController:
    """
    Controlador robusto para la cinta transportadora usando un módulo de 2 relays.
    Incorpora lógica de dirección, habilitación y un estado detallado.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # --- Configuración de Pines ---
        self.pin_forward = self.config.get('pin_forward_relay')
        self.pin_backward = self.config.get('pin_backward_relay')
        self.pin_enable = self.config.get('pin_enable') # Opcional
        
        if not self.pin_forward or not self.pin_backward:
            raise ConfigError("Pines 'pin_forward_relay' y 'pin_backward_relay' son requeridos.")
            
        # --- Lógica de Activación de Relays ---
        # Típicamente, los módulos de relay se activan con un estado BAJO.
        self.is_active_low = self.config.get('is_active_low', True)
        self.STATE_ON = GPIO.LOW if self.is_active_low else GPIO.HIGH
        self.STATE_OFF = GPIO.HIGH if self.is_active_low else GPIO.LOW
        
        # --- Estado del Controlador ---
        self.is_initialized = False
        self.is_running = False
        self.is_enabled = False # Refleja el estado del pin 'enable'
        self.current_direction = "stopped"
        
    async def initialize(self) -> bool:
        """Configura los pines GPIO y establece el estado inicial."""
        logger.info("Inicializando controlador de cinta (tipo: relay)...")
        if not GPIO_AVAILABLE:
            logger.warning("GPIO no disponible. Controlador de cinta operará en modo simulación.")
            self.is_initialized = True
            return True

        try:
            # Configurar pines de dirección
            await asyncio.to_thread(GPIO.setup, self.pin_forward, GPIO.OUT, initial=self.STATE_OFF)
            await asyncio.to_thread(GPIO.setup, self.pin_backward, GPIO.OUT, initial=self.STATE_OFF)
            
            # Configurar pin de habilitación si existe
            if self.pin_enable is not None:
                await asyncio.to_thread(GPIO.setup, self.pin_enable, GPIO.OUT, initial=GPIO.LOW)
                self.is_enabled = False # El driver está deshabilitado al inicio
            else:
                self.is_enabled = True # Siempre habilitado si no hay pin de control

            self.is_initialized = True
            logger.info("✅ Controlador de cinta inicializado.")
            return True
        except Exception as e:
            raise HardwareException(f"Fallo al configurar pines GPIO para la cinta: {e}") from e

    async def _set_direction(self, forward: bool, backward: bool):
        """Función interna segura para activar los relays."""
        if not self.is_initialized: return
        
        # Estado seguro: apagar ambos antes de cambiar
        await asyncio.to_thread(GPIO.output, self.pin_forward, self.STATE_OFF)
        await asyncio.to_thread(GPIO.output, self.pin_backward, self.STATE_OFF)
        await asyncio.sleep(0.05) # Pequeña pausa de seguridad
        
        if forward:
            await asyncio.to_thread(GPIO.output, self.pin_forward, self.STATE_ON)
        elif backward:
            await asyncio.to_thread(GPIO.output, self.pin_backward, self.STATE_ON)

    async def start_belt(self) -> bool:
        """Inicia la cinta en dirección hacia adelante."""
        if not self.is_initialized: return False
        
        logger.info("Iniciando cinta hacia adelante...")
        await self._enable_driver()
        if GPIO_AVAILABLE:
            await self._set_direction(forward=True, backward=False)
            
        self.is_running = True
        self.current_direction = "forward"
        return True
        
    async def reverse_direction(self) -> bool:
        """Inicia la cinta en dirección hacia atrás."""
        if not self.is_initialized: return False
        
        logger.info("Iniciando cinta hacia atrás...")
        await self._enable_driver()
        if GPIO_AVAILABLE:
            await self._set_direction(forward=False, backward=True)
            
        self.is_running = True
        self.current_direction = "backward"
        return True

    async def stop_belt(self) -> bool:
        """Detiene la cinta (corte suave)."""
        if not self.is_initialized: return False

        logger.info("Deteniendo cinta transportadora...")
        if GPIO_AVAILABLE:
            await self._set_direction(forward=False, backward=False)
        
        self.is_running = False
        self.current_direction = "stopped"
        # Opcional: Deshabilitar el driver para ahorrar energía
        # await self._disable_driver()
        return True

    async def emergency_brake(self):
        """Parada de emergencia (corte brusco y deshabilitación)."""
        logger.warning("🛑 Parada de emergencia para la cinta transportadora.")
        await self.stop_belt()
        await self._disable_driver()

    async def set_speed(self, speed_percent: float) -> bool:
        """Establece la velocidad (simulado para relays)."""
        logger.info(f"🎭 SIMULACIÓN: Velocidad de la cinta establecida a {speed_percent:.0f}%. "
                    f"El control por relay no soporta velocidad variable.")
        return True

    async def _enable_driver(self):
        if self.pin_enable and GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.pin_enable, GPIO.HIGH)
            self.is_enabled = True
            await asyncio.sleep(0.01) # Tiempo para que el driver se estabilice

    async def _disable_driver(self):
        if self.pin_enable and GPIO_AVAILABLE:
            await asyncio.to_thread(GPIO.output, self.pin_enable, GPIO.LOW)
            self.is_enabled = False
    
    async def cleanup(self):
        logger.info("Limpiando recursos de la cinta transportadora.")
        if self.is_initialized and GPIO_AVAILABLE:
            await self.stop_belt()
            # La limpieza general de GPIO se hará en el SystemController

    def get_status(self) -> Dict[str, Any]:
        """Retorna un estado detallado del controlador de la cinta."""
        return {
            "is_running": self.is_running,
            "direction": self.current_direction,
            "is_initialized": self.is_initialized,
            "is_enabled": self.is_enabled,
            "control_type": "relay",
            "simulation_mode": not GPIO_AVAILABLE
        }
