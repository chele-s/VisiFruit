# ultra_labeling_system.py
"""
Sistema Ultra de Etiquetado Lineal FruPrint v4.0
================================================

Sistema avanzado de 6 etiquetadoras lineales (3 grupos de 2) con
motor DC de posicionamiento automático.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from system_types import (
    FruitCategory, LabelerGroup, LABELERS_PER_GROUP,
    NUM_LABELER_GROUPS, DEFAULT_MOTOR_PINS
)

try:
    from Control_Etiquetado.labeler_actuator import LabelerActuator
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False

logger = logging.getLogger(__name__)

# ==================== CONTROLADOR DE MOTOR LINEAL ====================

class UltraLinearMotorController:
    """Controlador ultra-avanzado del motor DC para sistema lineal de 2 etiquetadoras por grupo."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        motor_pins_raw = config.get("motor_pins", DEFAULT_MOTOR_PINS)
        # Asegurar que todos los pines sean enteros
        self.motor_pins = {k: int(v) for k, v in motor_pins_raw.items()}
        
        # Sistema lineal: 3 grupos de 2 etiquetadoras cada uno
        self.labeler_groups = {
            FruitCategory.APPLE: LabelerGroup.GROUP_APPLE,
            FruitCategory.PEAR: LabelerGroup.GROUP_PEAR,
            FruitCategory.LEMON: LabelerGroup.GROUP_LEMON
        }
        
        self.current_active_group = None  # Grupo actualmente activo (bajado)
        self.is_moving = False
        self.is_calibrated = False
        self.pwm_instance = None
        self.current_position = 0.0
        
        # Posiciones iniciales de los grupos
        self.group_positions = {g: ("down" if g == 0 else "up") for g in range(NUM_LABELER_GROUPS)}
        
    async def initialize(self) -> bool:
        """Inicializa el controlador del motor."""
        try:
            if not GPIO_AVAILABLE:
                logger.warning("GPIO no disponible - Modo simulación motor")
                self.is_calibrated = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            for pin in self.motor_pins.values():
                GPIO.setup(pin, GPIO.OUT)
            
            self.pwm_instance = GPIO.PWM(self.motor_pins["pwm_pin"], 1000)
            self.pwm_instance.start(0)
            
            await self.calibrate()
            logger.info("✅ Motor DC inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando motor: {e}")
            return False
    
    async def calibrate(self) -> bool:
        """Calibra el motor encontrando posiciones de referencia."""
        try:
            logger.info("🔧 Calibrando motor DC...")
            await asyncio.sleep(2.0)
            self.current_position = 0.0
            self.is_calibrated = True
            logger.info("✅ Motor calibrado correctamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error calibrando motor: {e}")
            return False
    
    async def activate_labeler_group(self, category: FruitCategory) -> bool:
        """Activa un grupo de etiquetadoras (baja el grupo target, sube los otros)."""
        if category not in self.labeler_groups:
            return False
        
        target_group = self.labeler_groups[category]
        target_group_id = target_group.group_id
        
        # Si el grupo ya está activo, no hacer nada
        if self.current_active_group == target_group_id:
            logger.debug(f"Grupo {category.emoji} ya está activo")
            return True
        
        return await self.switch_to_group(target_group_id)
    
    async def switch_to_group(self, target_group_id: int) -> bool:
        """Cambia el grupo activo (sube el actual, baja el nuevo)."""
        try:
            if not self.is_calibrated:
                return False
            
            self.is_moving = True
            logger.info(f"🔄 Cambiando grupo activo: Grupo {target_group_id}")
            
            # 1. Subir grupo actual (si hay uno)
            if self.current_active_group is not None:
                await self._lift_group(self.current_active_group)
            
            # 2. Bajar nuevo grupo
            await self._lower_group(target_group_id)
            
            # 3. Actualizar estado
            self.current_active_group = target_group_id
            self._update_group_positions(target_group_id)
            
            self.is_moving = False
            
            categories = {0: "🍎", 1: "🍐", 2: "🍋"}
            logger.info(f"✅ Grupo {categories.get(target_group_id, '?')} activo - {LABELERS_PER_GROUP} etiquetadoras listas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cambiando grupo: {e}")
            self.is_moving = False
            return False
    
    async def _lift_group(self, group_id: int):
        """Sube un grupo de etiquetadoras."""
        logger.debug(f"⬆️ Subiendo grupo {group_id}")
        
        if GPIO_AVAILABLE and self.pwm_instance:
            GPIO.output(self.motor_pins["dir_pin1"], True)
            GPIO.output(self.motor_pins["dir_pin2"], False)
            self.pwm_instance.ChangeDutyCycle(60)
            await asyncio.sleep(1.5)
            self.pwm_instance.ChangeDutyCycle(0)
        else:
            await asyncio.sleep(1.5)
    
    async def _lower_group(self, group_id: int):
        """Baja un grupo de etiquetadoras."""
        logger.debug(f"⬇️ Bajando grupo {group_id}")
        
        if GPIO_AVAILABLE and self.pwm_instance:
            GPIO.output(self.motor_pins["dir_pin1"], False)
            GPIO.output(self.motor_pins["dir_pin2"], True)
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
        if GPIO_AVAILABLE:
            try:
                if self.pwm_instance:
                    self.pwm_instance.ChangeDutyCycle(0)
                enable_pin = self.motor_pins.get("enable_pin")
                if enable_pin is not None:
                    GPIO.output(enable_pin, False)
            except Exception:
                pass
        self.is_moving = False
    
    async def cleanup(self):
        """Limpia recursos del motor."""
        try:
            if GPIO_AVAILABLE:
                if self.pwm_instance:
                    self.pwm_instance.stop()
                GPIO.cleanup([pin for pin in self.motor_pins.values()])
        except Exception as e:
            logger.error(f"Error limpiando motor: {e}")

# ==================== GESTOR DE ETIQUETADORAS ====================

class UltraLabelerManager:
    """Gestor de las 6 etiquetadoras lineales."""
    
    def __init__(self, base_config: Dict[str, Any]):
        self.base_config = base_config
        self.labelers: Dict[int, LabelerActuator] = {}
        
        # Configuración de grupos
        self.groups_config = [
            {"category": FruitCategory.APPLE, "name": "Apple", "emoji": "🍎", 
             "ids": LabelerGroup.GROUP_APPLE.labeler_ids},
            {"category": FruitCategory.PEAR, "name": "Pear", "emoji": "🍐", 
             "ids": LabelerGroup.GROUP_PEAR.labeler_ids},
            {"category": FruitCategory.LEMON, "name": "Lemon", "emoji": "🍋", 
             "ids": LabelerGroup.GROUP_LEMON.labeler_ids}
        ]
    
    async def initialize(self) -> bool:
        """Inicializa todas las etiquetadoras."""
        logger.info("🏭 Inicializando 6 etiquetadoras lineales ultra-avanzadas...")
        
        if not HARDWARE_AVAILABLE:
            logger.warning("⚠️ Hardware no disponible - Modo simulación")
            return True
        
        try:
            for group in self.groups_config:
                logger.info(f"Inicializando grupo {group['emoji']} {group['name']}...")
                
                for labeler_id in group["ids"]:
                    labeler_config = self.base_config.copy()
                    labeler_config.update({
                        "name": f"LinearLabeler-{group['name']}-{labeler_id}",
                        "labeler_id": labeler_id,
                        "category": group["category"].fruit_name,
                        "group_id": group["category"].labeler_group_id,
                        "pin": int(self.base_config.get("pin", 26)) + labeler_id,
                        "type": "solenoid"
                    })
                    
                    labeler = LabelerActuator(labeler_config)
                    
                    if await labeler.initialize():
                        self.labelers[labeler_id] = labeler
                        logger.info(f"  ✅ Etiquetadora {labeler_id} ({group['name']}) inicializada")
                    else:
                        logger.error(f"  ❌ Fallo etiquetadora {labeler_id} ({group['name']})")
            
            logger.info(f"✅ Sistema de {len(self.labelers)} etiquetadoras lineales inicializado")
            logger.info("📋 Distribución: 🍎(0-1) 🍐(2-3) 🍋(4-5)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando etiquetadoras lineales: {e}")
            return False
    
    def get_labelers_for_group(self, group_id: int) -> list:
        """Obtiene las etiquetadoras de un grupo específico."""
        start_id = group_id * LABELERS_PER_GROUP
        end_id = start_id + LABELERS_PER_GROUP
        return [self.labelers.get(i) for i in range(start_id, end_id) if i in self.labelers]
    
    def get_labeler(self, labeler_id: int) -> Optional[LabelerActuator]:
        """Obtiene una etiquetadora específica."""
        return self.labelers.get(labeler_id)
    
    async def activate_group(self, group_id: int, duration: float, intensity: float = 100.0) -> bool:
        """Activa todas las etiquetadoras de un grupo simultáneamente."""
        labelers = self.get_labelers_for_group(group_id)
        
        if not labelers:
            logger.warning(f"No hay etiquetadoras disponibles para grupo {group_id}")
            return False
        
        # Activar todas en paralelo con timeout
        timeout_seconds = max(1.0, min(duration + 2.0, 30.0))
        tasks = []
        
        for labeler in labelers:
            if labeler:
                coro = labeler.activate_for_duration(duration, intensity)
                task = asyncio.create_task(asyncio.wait_for(coro, timeout=timeout_seconds))
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)
            return successful > 0
        
        return False
    
    async def emergency_stop_all(self):
        """Parada de emergencia de todas las etiquetadoras."""
        for labeler in self.labelers.values():
            try:
                await labeler.emergency_stop()
            except Exception:
                pass
    
    async def cleanup_all(self):
        """Limpia todas las etiquetadoras."""
        for labeler in self.labelers.values():
            try:
                await labeler.cleanup()
            except Exception:
                pass
    
    def get_status_all(self) -> Dict[int, Dict[str, Any]]:
        """Obtiene el estado de todas las etiquetadoras."""
        return {lid: labeler.get_status() for lid, labeler in self.labelers.items()}

__all__ = [
    'UltraLinearMotorController', 'UltraLabelerManager'
]
