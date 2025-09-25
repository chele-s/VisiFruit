# fruprint_system/hardware/sensors/sensor_interface.py
import asyncio
import logging
from typing import Dict, Any, Callable, Optional

from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE
from fruprint_system.core.exceptions import SensorError

logger = logging.getLogger(__name__)

class SensorInterface:
    """
    Interfaz unificada para el manejo de los sensores del sistema,
    principalmente el sensor de disparo (trigger) de la cámara.
    """
    def __init__(self, config: Dict[str, Any], trigger_callback: Optional[Callable] = None):
        self.config = config
        self.trigger_callback = trigger_callback
        self.is_initialized = False
        
        self.pin = self.config.get("pin")
        if self.pin is None:
            raise SensorError("El 'pin' no está definido en la configuración del sensor.")
            
        # Determinar el borde de activación (rising/falling)
        trigger_on_low = self.config.get("trigger_on_state", "LOW").upper() == "LOW"
        self.trigger_edge = GPIO.FALLING if trigger_on_low else GPIO.RISING
        
        # Configuración de debounce
        self.debounce_ms = self.config.get("debounce_time_ms", 50)
        
        # Configuración de pull-up/down
        pud_str = self.config.get("pull_up_down", "PUD_OFF").upper()
        self.pull_up_down = getattr(GPIO, pud_str, GPIO.PUD_OFF)

    def initialize(self) -> bool:
        """Configura el pin GPIO para el sensor de disparo."""
        logger.info(f"Inicializando sensor de disparo en pin {self.pin}...")
        if not GPIO_AVAILABLE:
            logger.warning("GPIO no disponible. Sensor operará en modo simulación.")
            self.is_initialized = True
            return True

        try:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=self.pull_up_down)
            
            # Registrar el callback del evento si se proporcionó
            if self.trigger_callback:
                GPIO.add_event_detect(
                    self.pin, 
                    self.trigger_edge, 
                    callback=self.trigger_callback, 
                    bouncetime=self.debounce_ms
                )
            self.is_initialized = True
            logger.info("✅ Sensor de disparo inicializado y monitoreando.")
            return True
        except Exception as e:
            raise SensorError(f"Fallo al configurar el pin del sensor {self.pin}: {e}") from e

    def get_current_state(self) -> bool:
        """Lee el estado digital actual del pin del sensor."""
        if not self.is_initialized: return False
        if not GPIO_AVAILABLE: return False # Simula estado inactivo
        
        return GPIO.input(self.pin) == (GPIO.LOW if self.trigger_edge == GPIO.FALLING else GPIO.HIGH)

    def cleanup(self):
        """Libera los recursos GPIO utilizados por el sensor."""
        logger.info(f"Limpiando recursos para el sensor en pin {self.pin}.")
        if self.is_initialized and GPIO_AVAILABLE and self.trigger_callback:
            try:
                GPIO.remove_event_detect(self.pin)
            except Exception as e:
                logger.warning(f"No se pudo remover el detector de eventos para el pin {self.pin}: {e}")
