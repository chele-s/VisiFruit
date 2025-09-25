# fruprint_system/hardware/motors/linear_motor_controller.py
import asyncio
import logging
from typing import Dict, Any

from fruprint_system.core.types import FruitCategory, LabelerGroup
from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE

# Constantes
LABELERS_PER_GROUP = 2
NUM_LABELER_GROUPS = 3

logger = logging.getLogger(__name__)

class UltraLinearMotorController:
    """Controlador avanzado del motor DC para sistema lineal de etiquetadoras."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        motor_pins_raw = config.get("motor_pins", {
            "pwm_pin": 12, "dir_pin1": 20, "dir_pin2": 21, "enable_pin": 16
        })
        self.motor_pins = {k: int(v) for k, v in motor_pins_raw.items()}
        
        self.labeler_groups = {
            FruitCategory.APPLE: LabelerGroup.GROUP_APPLE,
            FruitCategory.PEAR: LabelerGroup.GROUP_PEAR,
            FruitCategory.LEMON: LabelerGroup.GROUP_LEMON,
        }
        
        self.current_active_group: int | None = None
        self.is_moving = False
        self.is_calibrated = False
        self.pwm_instance = None
        self.group_positions = {g: ("down" if g == 0 else "up") for g in range(NUM_LABELER_GROUPS)}
        self.current_position = 0.0 # Posición para simulación

    async def initialize(self) -> bool:
        """Inicializa el controlador del motor."""
        try:
            if not GPIO_AVAILABLE:
                logger.warning("GPIO no disponible - Modo simulación para motor DC")
                self.is_calibrated = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            for pin in self.motor_pins.values():
                GPIO.setup(pin, GPIO.OUT)
            
            self.pwm_instance = GPIO.PWM(self.motor_pins["pwm_pin"], 1000)
            self.pwm_instance.start(0)
            
            await self.calibrate()
            logger.info("Motor DC inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error inicializando motor: {e}")
            return False

    async def calibrate(self) -> bool:
        """Calibra el motor encontrando posiciones de referencia."""
        logger.info("Calibrando motor DC...")
        await asyncio.sleep(2.0)  # Simulación de calibración
        self.current_position = 0.0
        self.is_calibrated = True
        logger.info("Motor calibrado correctamente")
        return True

    async def activate_labeler_group(self, category: FruitCategory) -> bool:
        """Activa un grupo de etiquetadoras (baja el grupo target, sube los otros)."""
        if category not in self.labeler_groups:
            return False
        
        target_group = self.labeler_groups[category]
        target_group_id = target_group.group_id
        
        if self.current_active_group == target_group_id:
            logger.info(f"Grupo {category.emoji} ya está activo")
            return True
        
        return await self.switch_to_group(target_group_id)

    async def switch_to_group(self, target_group_id: int) -> bool:
        """Cambia el grupo activo (sube el actual, baja el nuevo)."""
        if not self.is_calibrated:
            logger.warning("Intento de cambiar de grupo sin calibrar el motor.")
            return False

        self.is_moving = True
        logger.info(f"🔄 Cambiando grupo activo: Grupo {target_group_id}")
        
        try:
            if self.current_active_group is not None:
                await self._lift_group(self.current_active_group)
            
            await self._lower_group(target_group_id)
            
            self.current_active_group = target_group_id
            self._update_group_positions(target_group_id)
            
            categories = {0: "🍎", 1: "🍐", 2: "🍋"}
            logger.info(f"✅ Grupo {categories.get(target_group_id, '?')} activo - {LABELERS_PER_GROUP} etiquetadoras listas")
            return True
        except Exception as e:
            logger.error(f"Error cambiando grupo: {e}")
            return False
        finally:
            self.is_moving = False

    async def _lift_group(self, group_id: int):
        """Sube un grupo de etiquetadoras."""
        logger.info(f"⬆️ Subiendo grupo {group_id}")
        if GPIO_AVAILABLE and self.pwm_instance:
            await asyncio.to_thread(GPIO.output, self.motor_pins["dir_pin1"], True)
            await asyncio.to_thread(GPIO.output, self.motor_pins["dir_pin2"], False)
            self.pwm_instance.ChangeDutyCycle(60)
            await asyncio.sleep(1.5)
            self.pwm_instance.ChangeDutyCycle(0)
        else:
            await asyncio.sleep(1.5)

    async def _lower_group(self, group_id: int):
        """Baja un grupo de etiquetadoras."""
        logger.info(f"⬇️ Bajando grupo {group_id}")
        if GPIO_AVAILABLE and self.pwm_instance:
            await asyncio.to_thread(GPIO.output, self.motor_pins["dir_pin1"], False)
            await asyncio.to_thread(GPIO.output, self.motor_pins["dir_pin2"], True)
            self.pwm_instance.ChangeDutyCycle(60)
            await asyncio.sleep(1.5)
            self.pwm_instance.ChangeDutyCycle(0)
        else:
            await asyncio.sleep(1.5)

    def _update_group_positions(self, active_group_id: int):
        """Actualiza las posiciones de todos los grupos."""
        for group_id in range(NUM_LABELER_GROUPS):
            self.group_positions[group_id] = "down" if group_id == active_group_id else "up"

    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del motor y grupos de etiquetadoras."""
        emojis = {
            FruitCategory.APPLE.fruit_name: FruitCategory.APPLE.emoji,
            FruitCategory.PEAR.fruit_name: FruitCategory.PEAR.emoji,
            FruitCategory.LEMON.fruit_name: FruitCategory.LEMON.emoji,
        }
        available_groups = {
            group.group_id: {
                "category": group.category,
                "emoji": emojis.get(group.category, "❓"),
                "labelers": group.labeler_ids,
            }
            for group in LabelerGroup
        }
        return {
            "current_active_group": self.current_active_group,
            "is_moving": self.is_moving,
            "is_calibrated": self.is_calibrated,
            "group_positions": self.group_positions.copy(),
            "available_groups": available_groups,
        }

    async def emergency_stop(self):
        """Parada de emergencia del motor."""
        logger.warning("🛑 Parada de emergencia del motor activada")
        if GPIO_AVAILABLE and self.pwm_instance:
            self.pwm_instance.ChangeDutyCycle(0)
            enable_pin = self.motor_pins.get("enable_pin")
            if enable_pin is not None:
                await asyncio.to_thread(GPIO.output, enable_pin, False)
        self.is_moving = False

    async def cleanup(self):
        """Limpia recursos del motor."""
        logger.info("Limpiando recursos del motor DC...")
        try:
            if GPIO_AVAILABLE and self.pwm_instance:
                self.pwm_instance.stop()
                # No llamamos a GPIO.cleanup() aquí, se hará globalmente.
        except Exception as e:
            logger.error(f"Error limpiando motor: {e}")
