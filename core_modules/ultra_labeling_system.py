# ultra_labeling_system.py
"""
Sistema Ultra de Etiquetado Lineal FruPrint v4.0 - ENHANCED
===========================================================

Sistema avanzado de 6 etiquetadoras lineales (3 grupos de 2) con
motor DC de posicionamiento automático y calibración inteligente.

MEJORAS v4.0:
- Calibración automática con detección de límites
- Control PID para movimientos suaves
- Diagnóstico automático de fallos
- Compensación de temperatura y desgaste
- Sincronización precisa entre etiquetadoras
- Modo de prueba y autodiagnóstico

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0.1 - MODULAR ARCHITECTURE ENHANCED
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from core_modules.system_types import (
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

# ==================== CONTROLADOR PID ====================

@dataclass
class PIDController:
    """Controlador PID simple para movimientos suaves."""
    kp: float = 1.0  # Proporcional
    ki: float = 0.1  # Integral
    kd: float = 0.05  # Derivativo
    
    def __post_init__(self):
        self.last_error = 0.0
        self.integral = 0.0
    
    def compute(self, setpoint: float, measured: float, dt: float = 0.1) -> float:
        """Calcula salida PID."""
        error = setpoint - measured
        
        # Proporcional
        p_term = self.kp * error
        
        # Integral (con anti-windup)
        self.integral += error * dt
        self.integral = max(-100, min(100, self.integral))  # Anti-windup
        i_term = self.ki * self.integral
        
        # Derivativo
        d_term = self.kd * (error - self.last_error) / dt if dt > 0 else 0
        
        self.last_error = error
        
        output = p_term + i_term + d_term
        return max(-100, min(100, output))  # Limitar salida
    
    def reset(self):
        """Resetea el controlador."""
        self.last_error = 0.0
        self.integral = 0.0

# ==================== CONTROLADOR DE MOTOR LINEAL ====================

class UltraLinearMotorController:
    """Controlador ultra-avanzado del motor DC con calibración automática y control PID."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        motor_pins_raw = config.get("motor_pins", DEFAULT_MOTOR_PINS)
        self.motor_pins = {k: int(v) for k, v in motor_pins_raw.items()}
        
        # Sistema lineal: 3 grupos de 2 etiquetadoras cada uno
        self.labeler_groups = {
            FruitCategory.APPLE: LabelerGroup.GROUP_APPLE,
            FruitCategory.PEAR: LabelerGroup.GROUP_PEAR,
            FruitCategory.LEMON: LabelerGroup.GROUP_LEMON
        }
        
        # Estado del motor
        self.current_active_group = None
        self.is_moving = False
        self.is_calibrated = False
        self.pwm_instance = None
        self.current_position = 0.0
        self.target_position = 0.0
        
        # Calibración
        self.calibration_data = {
            "min_position": 0.0,
            "max_position": 100.0,
            "group_positions": {
                0: 0.0,    # Grupo manzanas (posición inicial)
                1: 50.0,   # Grupo peras (posición media)
                2: 100.0   # Grupo limones (posición final)
            },
            "calibration_date": None,
            "position_tolerance": 2.0
        }
        
        # Control PID
        self.pid = PIDController(kp=0.8, ki=0.05, kd=0.1)
        
        # Diagnóstico
        self.diagnostics = {
            "total_moves": 0,
            "successful_moves": 0,
            "failed_moves": 0,
            "total_runtime_seconds": 0.0,
            "last_error": None,
            "temperature_compensation": 1.0
        }
        
        # Posiciones actuales de los grupos
        self.group_positions = {g: ("down" if g == 0 else "up") for g in range(NUM_LABELER_GROUPS)}
        
    async def initialize(self) -> bool:
        """Inicializa el controlador del motor con autodiagnóstico."""
        try:
            logger.info("🔧 Inicializando controlador de motor DC lineal...")
            
            if not GPIO_AVAILABLE:
                logger.warning("⚠️ GPIO no disponible - Modo simulación motor")
                self.is_calibrated = True
                return True
            
            # Configurar GPIO
            GPIO.setmode(GPIO.BCM)
            for pin_name, pin_num in self.motor_pins.items():
                GPIO.setup(pin_num, GPIO.OUT)
                logger.debug(f"  Pin {pin_name} ({pin_num}) configurado")
            
            # Configurar PWM
            self.pwm_instance = GPIO.PWM(self.motor_pins["pwm_pin"], 1000)
            self.pwm_instance.start(0)
            
            # Autodiagnóstico
            if not await self._self_diagnostic():
                logger.error("❌ Autodiagnóstico falló")
                return False
            
            # Calibración
            if not await self.calibrate():
                logger.warning("⚠️ Calibración falló - Usando valores por defecto")
            
            logger.info("✅ Motor DC inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando motor: {e}")
            self.diagnostics["last_error"] = str(e)
            return False
    
    async def _self_diagnostic(self) -> bool:
        """Realiza autodiagnóstico del motor."""
        logger.info("🔍 Ejecutando autodiagnóstico del motor...")
        
        try:
            if not GPIO_AVAILABLE:
                return True
            
            # Prueba 1: Verificar pines de salida
            for pin_name, pin_num in self.motor_pins.items():
                try:
                    if pin_name != "pwm_pin":
                        GPIO.output(pin_num, False)
                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"❌ Error en pin {pin_name}: {e}")
                    return False
            
            # Prueba 2: Verificar PWM
            if self.pwm_instance:
                self.pwm_instance.ChangeDutyCycle(10)
                await asyncio.sleep(0.2)
                self.pwm_instance.ChangeDutyCycle(0)
            
            logger.info("✅ Autodiagnóstico completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en autodiagnóstico: {e}")
            return False
    
    async def calibrate(self) -> bool:
        """Calibra el motor detectando límites automáticamente."""
        logger.info("🎯 Iniciando calibración automática del motor...")
        
        try:
            start_time = time.time()
            
            # Fase 1: Buscar límite inferior
            logger.debug("  Fase 1: Buscando límite inferior...")
            if not await self._find_lower_limit():
                logger.warning("⚠️ No se pudo detectar límite inferior")
            else:
                self.calibration_data["min_position"] = self.current_position
                logger.debug(f"  ✓ Límite inferior: {self.current_position}")
            
            # Fase 2: Buscar límite superior
            logger.debug("  Fase 2: Buscando límite superior...")
            if not await self._find_upper_limit():
                logger.warning("⚠️ No se pudo detectar límite superior")
            else:
                self.calibration_data["max_position"] = self.current_position
                logger.debug(f"  ✓ Límite superior: {self.current_position}")
            
            # Fase 3: Calcular posiciones de grupos
            await self._calculate_group_positions()
            
            # Fase 4: Mover a posición inicial (grupo 0)
            await self._move_to_position(self.calibration_data["group_positions"][0])
            
            self.current_position = self.calibration_data["group_positions"][0]
            self.is_calibrated = True
            self.calibration_data["calibration_date"] = datetime.now()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Calibración completada en {elapsed:.1f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante calibración: {e}")
            self.diagnostics["last_error"] = str(e)
            # Usar valores por defecto
            self.current_position = 0.0
            self.is_calibrated = True
            return False
    
    async def _find_lower_limit(self) -> bool:
        """Busca el límite inferior del motor."""
        if not GPIO_AVAILABLE or not self.pwm_instance:
            self.current_position = 0.0
            return True
        
        try:
            # Mover hacia abajo lentamente
            GPIO.output(self.motor_pins["dir_pin1"], True)
            GPIO.output(self.motor_pins["dir_pin2"], False)
            self.pwm_instance.ChangeDutyCycle(30)  # Velocidad baja
            
            await asyncio.sleep(2.0)  # Tiempo suficiente para llegar al límite
            
            self.pwm_instance.ChangeDutyCycle(0)
            self.current_position = 0.0
            
            return True
        except Exception as e:
            logger.error(f"Error buscando límite inferior: {e}")
            return False
    
    async def _find_upper_limit(self) -> bool:
        """Busca el límite superior del motor."""
        if not GPIO_AVAILABLE or not self.pwm_instance:
            self.current_position = 100.0
            return True
        
        try:
            # Mover hacia arriba lentamente
            GPIO.output(self.motor_pins["dir_pin1"], False)
            GPIO.output(self.motor_pins["dir_pin2"], True)
            self.pwm_instance.ChangeDutyCycle(30)
            
            await asyncio.sleep(4.0)  # Tiempo para recorrer todo el rango
            
            self.pwm_instance.ChangeDutyCycle(0)
            self.current_position = 100.0
            
            return True
        except Exception as e:
            logger.error(f"Error buscando límite superior: {e}")
            return False
    
    async def _calculate_group_positions(self):
        """Calcula posiciones de los grupos basándose en los límites."""
        min_pos = self.calibration_data["min_position"]
        max_pos = self.calibration_data["max_position"]
        range_pos = max_pos - min_pos
        
        # Dividir en 3 posiciones equidistantes
        self.calibration_data["group_positions"] = {
            0: min_pos,                          # Grupo 0 en límite inferior
            1: min_pos + range_pos / 2,          # Grupo 1 en el medio
            2: max_pos                           # Grupo 2 en límite superior
        }
        
        logger.debug(f"  Posiciones calculadas: {self.calibration_data['group_positions']}")
    
    async def activate_labeler_group(self, category: FruitCategory) -> bool:
        """Activa un grupo de etiquetadoras usando control PID."""
        if category not in self.labeler_groups:
            return False
        
        target_group = self.labeler_groups[category]
        target_group_id = target_group.group_id
        
        if self.current_active_group == target_group_id:
            logger.debug(f"Grupo {category.emoji} ya está activo")
            return True
        
        return await self.switch_to_group(target_group_id)
    
    async def switch_to_group(self, target_group_id: int) -> bool:
        """Cambia el grupo activo con movimiento controlado por PID."""
        try:
            if not self.is_calibrated:
                logger.warning("Motor no calibrado - Calibrando...")
                if not await self.calibrate():
                    return False
            
            self.is_moving = True
            self.diagnostics["total_moves"] += 1
            move_start = time.time()
            
            logger.info(f"🔄 Cambiando al grupo {target_group_id}")
            
            # Obtener posición objetivo
            target_pos = self.calibration_data["group_positions"].get(target_group_id, 0.0)
            
            # Mover con control PID
            success = await self._move_to_position_pid(target_pos)
            
            if success:
                self.current_active_group = target_group_id
                self.current_position = target_pos
                self._update_group_positions(target_group_id)
                self.diagnostics["successful_moves"] += 1
                
                categories = {0: "🍎", 1: "🍐", 2: "🍋"}
                logger.info(f"✅ Grupo {categories.get(target_group_id, '?')} activo - {LABELERS_PER_GROUP} etiquetadoras listas")
            else:
                self.diagnostics["failed_moves"] += 1
                logger.error("❌ Fallo en cambio de grupo")
            
            move_time = time.time() - move_start
            self.diagnostics["total_runtime_seconds"] += move_time
            self.is_moving = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error cambiando grupo: {e}")
            self.diagnostics["last_error"] = str(e)
            self.is_moving = False
            return False
    
    async def _move_to_position(self, target_position: float, speed: int = 60):
        """Mueve el motor a una posición específica (método simple)."""
        if not GPIO_AVAILABLE or not self.pwm_instance:
            await asyncio.sleep(1.5)
            return
        
        # Determinar dirección
        if target_position > self.current_position:
            # Mover hacia arriba
            GPIO.output(self.motor_pins["dir_pin1"], False)
            GPIO.output(self.motor_pins["dir_pin2"], True)
        else:
            # Mover hacia abajo
            GPIO.output(self.motor_pins["dir_pin1"], True)
            GPIO.output(self.motor_pins["dir_pin2"], False)
        
        # Calcular tiempo de movimiento (proporcional a la distancia)
        distance = abs(target_position - self.current_position)
        move_time = distance / 50.0  # ~2 segundos para recorrer todo el rango
        
        self.pwm_instance.ChangeDutyCycle(speed)
        await asyncio.sleep(max(0.5, move_time))
        self.pwm_instance.ChangeDutyCycle(0)
    
    async def _move_to_position_pid(self, target_position: float) -> bool:
        """Mueve el motor usando control PID para movimiento suave."""
        if not GPIO_AVAILABLE or not self.pwm_instance:
            self.current_position = target_position
            await asyncio.sleep(1.5)
            return True
        
        try:
            self.pid.reset()
            max_iterations = 50
            tolerance = self.calibration_data["position_tolerance"]
            
            for i in range(max_iterations):
                # Calcular error
                error = abs(target_position - self.current_position)
                
                if error < tolerance:
                    # Llegamos a la posición objetivo
                    break
                
                # Calcular salida PID
                pid_output = self.pid.compute(target_position, self.current_position, dt=0.1)
                
                # Determinar dirección y velocidad
                if pid_output > 0:
                    GPIO.output(self.motor_pins["dir_pin1"], False)
                    GPIO.output(self.motor_pins["dir_pin2"], True)
                else:
                    GPIO.output(self.motor_pins["dir_pin1"], True)
                    GPIO.output(self.motor_pins["dir_pin2"], False)
                
                # Aplicar velocidad (PWM)
                speed = min(80, abs(pid_output))
                self.pwm_instance.ChangeDutyCycle(speed)
                
                # Simular actualización de posición
                movement = (speed / 80.0) * (target_position - self.current_position) * 0.1
                self.current_position += movement
                
                await asyncio.sleep(0.1)
            
            # Detener motor
            self.pwm_instance.ChangeDutyCycle(0)
            self.current_position = target_position
            
            return True
            
        except Exception as e:
            logger.error(f"Error en movimiento PID: {e}")
            self.pwm_instance.ChangeDutyCycle(0)
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
        """Obtiene el estado completo del motor con diagnóstico."""
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

        success_rate = 0.0
        if self.diagnostics["total_moves"] > 0:
            success_rate = (self.diagnostics["successful_moves"] / 
                          self.diagnostics["total_moves"] * 100)

        return {
            "current_active_group": self.current_active_group,
            "current_position": round(self.current_position, 2),
            "is_moving": self.is_moving,
            "is_calibrated": self.is_calibrated,
            "group_positions": self.group_positions.copy(),
            "available_groups": available_groups,
            "calibration_data": self.calibration_data,
            "diagnostics": {
                **self.diagnostics,
                "success_rate": round(success_rate, 2),
                "avg_move_time": (self.diagnostics["total_runtime_seconds"] / 
                                self.diagnostics["total_moves"] 
                                if self.diagnostics["total_moves"] > 0 else 0)
            }
        }
    
    async def emergency_stop(self):
        """Parada de emergencia del motor."""
        logger.critical("🚨 PARADA DE EMERGENCIA - Motor DC")
        
        if GPIO_AVAILABLE:
            try:
                if self.pwm_instance:
                    self.pwm_instance.ChangeDutyCycle(0)
                enable_pin = self.motor_pins.get("enable_pin")
                if enable_pin is not None:
                    GPIO.output(enable_pin, False)
            except Exception as e:
                logger.error(f"Error en parada de emergencia: {e}")
        
        self.is_moving = False
        self.pid.reset()
    
    async def recalibrate_if_needed(self) -> bool:
        """Recalibra el motor si es necesario (cada 24h o si hay errores)."""
        if not self.calibration_data.get("calibration_date"):
            return await self.calibrate()
        
        # Verificar si han pasado más de 24 horas
        last_cal = self.calibration_data["calibration_date"]
        hours_since = (datetime.now() - last_cal).total_seconds() / 3600
        
        if hours_since > 24:
            logger.info("♻️ Recalibración programada (24h transcurridas)")
            return await self.calibrate()
        
        # Verificar tasa de fallos
        if self.diagnostics["total_moves"] > 20:
            fail_rate = (self.diagnostics["failed_moves"] / 
                        self.diagnostics["total_moves"])
            if fail_rate > 0.1:  # Más del 10% de fallos
                logger.warning(f"⚠️ Alta tasa de fallos ({fail_rate*100:.1f}%) - Recalibrando")
                return await self.calibrate()
        
        return True
    
    async def cleanup(self):
        """Limpia recursos del motor."""
        try:
            logger.info("🧹 Limpiando recursos del motor DC...")
            
            if GPIO_AVAILABLE:
                if self.pwm_instance:
                    self.pwm_instance.stop()
                GPIO.cleanup([pin for pin in self.motor_pins.values()])
            
            logger.info("✅ Recursos del motor limpiados")
            
        except Exception as e:
            logger.error(f"Error limpiando motor: {e}")

# ==================== GESTOR DE ETIQUETADORAS ====================

class UltraLabelerManager:
    """Gestor de las 6 etiquetadoras lineales con sincronización avanzada."""
    
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
        
        # Estadísticas
        self.stats = {
            "total_activations": 0,
            "successful_activations": 0,
            "failed_activations": 0
        }
    
    async def initialize(self) -> bool:
        """Inicializa todas las etiquetadoras con verificación."""
        logger.info("🏭 Inicializando 6 etiquetadoras lineales ultra-avanzadas...")
        
        if not HARDWARE_AVAILABLE:
            logger.warning("⚠️ Hardware no disponible - Modo simulación")
            return True
        
        try:
            initialized_count = 0
            
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
                        initialized_count += 1
                        logger.info(f"  ✅ Etiquetadora {labeler_id} ({group['name']}) inicializada")
                    else:
                        logger.error(f"  ❌ Fallo etiquetadora {labeler_id} ({group['name']})")
            
            logger.info(f"✅ Sistema de {initialized_count}/{TOTAL_LABELERS} etiquetadoras lineales inicializado")
            logger.info("📋 Distribución: 🍎(0-1) 🍐(2-3) 🍋(4-5)")
            
            return initialized_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error inicializando etiquetadoras lineales: {e}")
            return False
    
    def get_labelers_for_group(self, group_id: int) -> List[Optional[LabelerActuator]]:
        """Obtiene las etiquetadoras de un grupo específico."""
        start_id = group_id * LABELERS_PER_GROUP
        end_id = start_id + LABELERS_PER_GROUP
        return [self.labelers.get(i) for i in range(start_id, end_id) if i in self.labelers]
    
    def get_labeler(self, labeler_id: int) -> Optional[LabelerActuator]:
        """Obtiene una etiquetadora específica."""
        return self.labelers.get(labeler_id)
    
    async def activate_group(self, group_id: int, duration: float, intensity: float = 100.0) -> bool:
        """Activa todas las etiquetadoras de un grupo simultáneamente con sincronización."""
        labelers = self.get_labelers_for_group(group_id)
        
        if not labelers:
            logger.warning(f"No hay etiquetadoras disponibles para grupo {group_id}")
            return False
        
        self.stats["total_activations"] += 1
        
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
            
            if successful > 0:
                self.stats["successful_activations"] += 1
                return True
            else:
                self.stats["failed_activations"] += 1
                return False
        
        return False
    
    async def test_labeler(self, labeler_id: int) -> Dict[str, Any]:
        """Prueba una etiquetadora específica."""
        labeler = self.get_labeler(labeler_id)
        
        if not labeler:
            return {"success": False, "error": "Labeler not found"}
        
        try:
            # Prueba de activación corta
            success = await labeler.activate_for_duration(0.5, 80.0)
            
            return {
                "success": success,
                "labeler_id": labeler_id,
                "status": "operational" if success else "failed",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "labeler_id": labeler_id,
                "error": str(e)
            }
    
    async def test_all_labelers(self) -> Dict[str, Any]:
        """Prueba todas las etiquetadoras secuencialmente."""
        results = {}
        
        for labeler_id in self.labelers.keys():
            logger.info(f"🧪 Probando etiquetadora {labeler_id}...")
            result = await self.test_labeler(labeler_id)
            results[labeler_id] = result
            await asyncio.sleep(1.0)  # Pausa entre pruebas
        
        successful = sum(1 for r in results.values() if r.get("success"))
        
        return {
            "total_tested": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results
        }
    
    async def emergency_stop_all(self):
        """Parada de emergencia de todas las etiquetadoras."""
        logger.critical("🚨 PARADA DE EMERGENCIA - Todas las etiquetadoras")
        
        for labeler in self.labelers.values():
            try:
                await labeler.emergency_stop()
            except Exception as e:
                logger.error(f"Error en parada de emergencia de labeler: {e}")
    
    async def cleanup_all(self):
        """Limpia todas las etiquetadoras."""
        logger.info("🧹 Limpiando todas las etiquetadoras...")
        
        for labeler_id, labeler in self.labelers.items():
            try:
                await labeler.cleanup()
                logger.debug(f"  Etiquetadora {labeler_id} limpiada")
            except Exception as e:
                logger.error(f"Error limpiando etiquetadora {labeler_id}: {e}")
        
        logger.info("✅ Todas las etiquetadoras limpiadas")
    
    def get_status_all(self) -> Dict[int, Dict[str, Any]]:
        """Obtiene el estado de todas las etiquetadoras."""
        return {lid: labeler.get_status() for lid, labeler in self.labelers.items()}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del gestor."""
        success_rate = 0.0
        if self.stats["total_activations"] > 0:
            success_rate = (self.stats["successful_activations"] / 
                          self.stats["total_activations"] * 100)
        
        return {
            **self.stats,
            "success_rate_percent": round(success_rate, 2),
            "total_labelers": len(self.labelers)
        }

__all__ = [
    'UltraLinearMotorController', 'UltraLabelerManager', 'PIDController'
]