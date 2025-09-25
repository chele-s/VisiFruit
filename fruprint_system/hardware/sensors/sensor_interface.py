# fruprint_system/hardware/sensors/sensor_interface.py
import asyncio
import logging
from typing import Callable, Coroutine

from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE

logger = logging.getLogger(__name__)

class SensorInterface:
    """
    Interfaz para sensores de disparo, optimizada para usar interrupciones.
    Gestiona la detección de objetos en la cinta transportadora.
    """
    def __init__(self, config: dict, trigger_callback: Callable[[], Coroutine]):
        """
        Inicializa el sensor.
        
        Args:
            config: Diccionario de configuración con 'trigger_pin'.
            trigger_callback: Una función (async) a la que llamar cuando el sensor se activa.
        """
        self.trigger_pin = config['trigger_pin']
        self.callback = trigger_callback
        self.is_initialized = False
        self._loop = None

    def initialize(self) -> bool:
        """Configura el pin del sensor y la detección de eventos (interrupción)."""
        logger.info(f"Inicializando sensor de disparo en pin {self.trigger_pin}...")
        if not GPIO_AVAILABLE:
            logger.warning("GPIO no disponible. Sensor de disparo en modo simulación.")
            self.is_initialized = True
            return True

        try:
            self._loop = asyncio.get_running_loop()
            GPIO.setmode(GPIO.BCM)
            # Configurar el pin como entrada con una resistencia pull-down
            GPIO.setup(self.trigger_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            # Añadir detección de eventos (interrupción) en el flanco de subida (cuando se detecta algo)
            # El bouncetime ayuda a evitar múltiples detecciones por ruido eléctrico.
            GPIO.add_event_detect(
                self.trigger_pin, 
                GPIO.RISING, 
                callback=self._internal_callback_handler, 
                bouncetime=200 # ms
            )
            self.is_initialized = True
            logger.info(f"✅ Sensor de disparo listo y escuchando eventos en pin {self.trigger_pin}.")
            return True
        except Exception as e:
            logger.error(f"❌ Fallo al inicializar el sensor de disparo: {e}")
            return False

    def _internal_callback_handler(self, channel):
        """
        Manejador interno que se ejecuta en el hilo de la interrupción de GPIO.
        Su única función es programar la ejecución del callback real en el 
        event loop de asyncio de forma segura.
        """
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(asyncio.create_task, self.callback())

    async def simulate_trigger(self):
        """Permite simular un disparo del sensor para pruebas."""
        if not GPIO_AVAILABLE:
            logger.info("Simulando disparo de sensor...")
            await self.callback()
        else:
            logger.warning("La simulación de disparo solo está disponible en modo sin GPIO.")

    def cleanup(self):
        """Limpia los recursos del sensor."""
        logger.info(f"Limpiando recursos del sensor en pin {self.trigger_pin}.")
        if self.is_initialized and GPIO_AVAILABLE:
            try:
                GPIO.remove_event_detect(self.trigger_pin)
            except Exception as e:
                logger.error(f"Error al remover el detector de eventos del sensor: {e}")
