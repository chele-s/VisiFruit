# fruit_diverter_controller.py
"""
Controlador de Desviadores de Frutas con Servomotores SG995
===========================================================

Sistema de clasificación automática que utiliza servomotores SG995 para
desviar frutas etiquetadas hacia cajas específicas según su categoría.

Flujo de clasificación:
- Manzanas → Desviador 1 activo → Caja manzanas
- Peras → Desviador 2 activo → Caja peras  
- Limones → Sin desviador → Caja final (straight through)

Autor: Elias Bautista, Gabriel Calderón, Cristian Hernandez
Fecha: Julio 2025
Versión: 1.0
"""

import asyncio
import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from pathlib import Path

# GPIO para control de servomotores
try:
    import sys
    from pathlib import Path
    # Añadir directorio padre al path para importar utils
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, is_simulation_mode
    import pigpio
    PIGPIO_AVAILABLE = True
    
    if is_simulation_mode():
        print("🔧 Desviadores: Modo simulación activo (ideal para desarrollo)")
    else:
        print("✅ Desviadores: GPIO hardware activo")
        
except ImportError:
    print("⚠️ GPIO/Pigpio no disponible - Modo simulación para desviadores")
    GPIO_AVAILABLE = False
    PIGPIO_AVAILABLE = False

logger = logging.getLogger("FruitDiverterController")

class DiverterPosition(Enum):
    """Posiciones del desviador."""
    STRAIGHT = "straight"    # Posición recta (sin desviar)
    DIVERTED = "diverted"   # Posición desviada (desviar fruta)

class FruitCategory(Enum):
    """Categorías de frutas para clasificación."""
    APPLE = ("apple", 0, "🍎")
    PEAR = ("pear", 1, "🍐") 
    LEMON = ("lemon", 2, "🍋")
    UNKNOWN = ("unknown", 99, "❓")
    
    def __init__(self, name: str, diverter_id: int, emoji: str):
        self.fruit_name = name
        self.diverter_id = diverter_id  # ID del desviador (-1 para sin desviador)
        self.emoji = emoji

@dataclass
class DiverterMetrics:
    """Métricas de un desviador."""
    diverter_id: int
    category: FruitCategory
    activations_count: int = 0
    total_runtime_seconds: float = 0.0
    success_rate: float = 100.0
    last_activation: Optional[datetime] = None
    maintenance_score: float = 100.0
    position_errors: int = 0

class ServoMotorSG995:
    """
    Controlador para servomotor SG995.
    
    Características SG995:
    - Torque: 8.5 kg-cm
    - Velocidad: 0.2 seg/60°
    - Ángulo: 180°
    - Frecuencia PWM: 50Hz
    - Ancho pulso: 1-2ms (1ms=0°, 1.5ms=90°, 2ms=180°)
    """
    
    def __init__(self, pin: int, name: str, config: Dict[str, Any]):
        self.pin = pin
        self.name = name
        self.config = config
        
        # Configuración SG995
        self.frequency = 50  # Hz
        self.min_pulse_width = 1.0  # ms para 0°
        self.max_pulse_width = 2.0  # ms para 180°
        self.center_pulse_width = 1.5  # ms para 90°
        
        # Posiciones configurables
        self.straight_angle = config.get("straight_angle", 0)    # Ángulo para posición recta
        self.diverted_angle = config.get("diverted_angle", 90)   # Ángulo para desviar
        
        # Estado
        self.current_position = DiverterPosition.STRAIGHT
        self.current_angle = self.straight_angle
        self.is_initialized = False
        self.pwm_instance = None
        self.last_movement_time = 0
        
        # Thread safety
        self._lock = threading.Lock()
        
    async def initialize(self) -> bool:
        """Inicializa el servomotor."""
        try:
            if not GPIO_AVAILABLE:
                logger.warning(f"GPIO no disponible - Servo {self.name} en modo simulación")
                self.is_initialized = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            
            # Configurar PWM
            self.pwm_instance = GPIO.PWM(self.pin, self.frequency)
            self.pwm_instance.start(0)
            
            # Mover a posición inicial (recta)
            await self.move_to_position(DiverterPosition.STRAIGHT)
            
            self.is_initialized = True
            logger.info(f"Servo {self.name} (Pin {self.pin}) inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando servo {self.name}: {e}")
            return False
    
    def _angle_to_duty_cycle(self, angle: float) -> float:
        """Convierte ángulo a duty cycle para PWM."""
        # Limitar ángulo
        angle = max(0, min(180, angle))
        
        # Calcular ancho de pulso en ms
        pulse_width = self.min_pulse_width + (angle / 180.0) * (self.max_pulse_width - self.min_pulse_width)
        
        # Convertir a duty cycle (período = 20ms a 50Hz)
        duty_cycle = (pulse_width / 20.0) * 100
        return duty_cycle
    
    async def move_to_angle(self, target_angle: float) -> bool:
        """Mueve el servo a un ángulo específico."""
        try:
            with self._lock:
                if not self.is_initialized:
                    return False
                
                # Limitar ángulo
                target_angle = max(0, min(180, target_angle))
                
                if GPIO_AVAILABLE and self.pwm_instance:
                    # Movimiento real
                    duty_cycle = self._angle_to_duty_cycle(target_angle)
                    self.pwm_instance.ChangeDutyCycle(duty_cycle)
                    
                    # Calcular tiempo de movimiento (aprox 0.2s por 60°)
                    angle_diff = abs(target_angle - self.current_angle)
                    movement_time = (angle_diff / 60.0) * 0.2
                    
                    # Esperar movimiento
                    await asyncio.sleep(movement_time + 0.1)  # +100ms margen
                    
                    # Apagar PWM para evitar ruido
                    self.pwm_instance.ChangeDutyCycle(0)
                else:
                    # Simulación
                    await asyncio.sleep(0.3)
                
                self.current_angle = target_angle
                self.last_movement_time = time.time()
                
                logger.debug(f"Servo {self.name} movido a {target_angle}°")
                return True
                
        except Exception as e:
            logger.error(f"Error moviendo servo {self.name} a {target_angle}°: {e}")
            return False
    
    async def move_to_position(self, position: DiverterPosition) -> bool:
        """Mueve el servo a una posición predefinida."""
        target_angle = self.straight_angle if position == DiverterPosition.STRAIGHT else self.diverted_angle
        
        success = await self.move_to_angle(target_angle)
        if success:
            self.current_position = position
            logger.info(f"Servo {self.name} en posición {position.value} ({target_angle}°)")
        
        return success
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servo."""
        return {
            "name": self.name,
            "pin": self.pin,
            "initialized": self.is_initialized,
            "current_position": self.current_position.value,
            "current_angle": self.current_angle,
            "last_movement": self.last_movement_time,
            "config": {
                "straight_angle": self.straight_angle,
                "diverted_angle": self.diverted_angle
            }
        }
    
    async def cleanup(self):
        """Limpia recursos del servo."""
        try:
            with self._lock:
                if GPIO_AVAILABLE and self.pwm_instance:
                    self.pwm_instance.stop()
                    GPIO.cleanup(self.pin)
                
                self.is_initialized = False
                logger.info(f"Servo {self.name} limpiado correctamente")
                
        except Exception as e:
            logger.error(f"Error limpiando servo {self.name}: {e}")

class FruitDiverterController:
    """
    Controlador principal del sistema de desviadores de frutas.
    
    Gestiona múltiples servomotores SG995 para clasificar frutas:
    - Desviador 0: Manzanas → Caja manzanas
    - Desviador 1: Peras → Caja peras
    - Sin desviador: Limones → Caja final
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.diverters: Dict[int, ServoMotorSG995] = {}
        self.diverter_metrics: Dict[int, DiverterMetrics] = {}
        
        # Configuración de timing
        self.activation_duration = config.get("activation_duration_seconds", 2.0)
        self.return_delay = config.get("return_delay_seconds", 0.5)
        
        # Estado del sistema
        self.is_initialized = False
        self.active_diverters = set()
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("Controlador de desviadores inicializado")
    
    async def initialize(self) -> bool:
        """Inicializa todos los desviadores."""
        try:
            logger.info("Inicializando sistema de desviadores...")
            
            diverters_config = self.config.get("diverters", {})
            
            # Configuración por defecto para 2 desviadores
            default_diverters = {
                0: {  # Desviador para manzanas
                    "pin": 18,
                    "name": "Diverter-Apple",
                    "category": "apple",
                    "straight_angle": 0,
                    "diverted_angle": 90,
                    "description": "Desviador para manzanas hacia caja específica"
                },
                1: {  # Desviador para peras
                    "pin": 19,
                    "name": "Diverter-Pear", 
                    "category": "pear",
                    "straight_angle": 0,
                    "diverted_angle": 90,
                    "description": "Desviador para peras hacia caja específica"
                }
                # Limones no tienen desviador - van directo a caja final
            }
            
            # Usar configuración personalizada si está disponible, sino usar por defecto
            diverters_to_create = diverters_config if diverters_config else default_diverters
            
            # Inicializar cada desviador
            for diverter_id, diverter_config in diverters_to_create.items():
                servo = ServoMotorSG995(
                    pin=diverter_config["pin"],
                    name=diverter_config["name"],
                    config=diverter_config
                )
                
                if await servo.initialize():
                    self.diverters[int(diverter_id)] = servo
                    
                    # Inicializar métricas
                    try:
                        category = FruitCategory[diverter_config["category"].upper()]
                    except KeyError:
                        category = FruitCategory.UNKNOWN
                    
                    self.diverter_metrics[int(diverter_id)] = DiverterMetrics(
                        diverter_id=int(diverter_id),
                        category=category
                    )
                    
                    logger.info(f"✅ Desviador {diverter_id} ({diverter_config['name']}) inicializado")
                else:
                    logger.error(f"❌ Fallo inicializando desviador {diverter_id}")
            
            self.is_initialized = len(self.diverters) > 0
            
            if self.is_initialized:
                logger.info(f"🚀 Sistema de desviadores inicializado: {len(self.diverters)} desviadores operativos")
                logger.info("📋 Configuración:")
                logger.info("   🍎 Manzanas → Desviador 0 → Caja manzanas")
                logger.info("   🍐 Peras → Desviador 1 → Caja peras")
                logger.info("   🍋 Limones → Sin desviador → Caja final")
            else:
                logger.warning("⚠️ Sin desviadores operativos - Modo pass-through")
            
            return self.is_initialized
            
        except Exception as e:
            logger.error(f"Error inicializando desviadores: {e}")
            return False
    
    async def classify_fruit(self, category: FruitCategory, delay_seconds: float = 0.0) -> bool:
        """
        Clasifica una fruta activando el desviador correspondiente.
        
        Args:
            category: Categoría de la fruta detectada
            delay_seconds: Tiempo de espera antes de activar (para sincronización con banda)
        """
        try:
            if not self.is_initialized:
                logger.warning("Sistema de desviadores no inicializado")
                return False
            
            # Esperar delay si es necesario
            if delay_seconds > 0:
                logger.info(f"⏱️ Esperando {delay_seconds:.1f}s para clasificar {category.emoji}")
                await asyncio.sleep(delay_seconds)
            
            # Determinar acción según categoría
            if category == FruitCategory.APPLE:
                return await self._activate_diverter(0, "manzanas")
            elif category == FruitCategory.PEAR:
                return await self._activate_diverter(1, "peras")
            elif category == FruitCategory.LEMON:
                # Limones van directo - no activar desviador
                logger.info("🍋 Limón: pass-through a caja final")
                return True
            else:
                logger.warning(f"❓ Categoría desconocida: {category.fruit_name} - pass-through")
                return True
                
        except Exception as e:
            logger.error(f"Error clasificando fruta {category.emoji}: {e}")
            return False
    
    async def _activate_diverter(self, diverter_id: int, fruit_name: str) -> bool:
        """Activa un desviador específico."""
        try:
            if diverter_id not in self.diverters:
                logger.error(f"Desviador {diverter_id} no existe")
                return False
            
            with self._lock:
                if diverter_id in self.active_diverters:
                    logger.warning(f"Desviador {diverter_id} ya está activo")
                    return False
                
                self.active_diverters.add(diverter_id)
            
            diverter = self.diverters[diverter_id]
            metrics = self.diverter_metrics[diverter_id]
            
            start_time = time.time()
            
            logger.info(f"🔄 Activando desviador {diverter_id} para {fruit_name}")
            
            # 1. Mover a posición desviada
            success = await diverter.move_to_position(DiverterPosition.DIVERTED)
            if not success:
                with self._lock:
                    self.active_diverters.discard(diverter_id)
                return False
            
            # 2. Mantener posición durante tiempo de activación
            await asyncio.sleep(self.activation_duration)
            
            # 3. Regresar a posición recta
            success = await diverter.move_to_position(DiverterPosition.STRAIGHT)
            
            # 4. Actualizar métricas
            runtime = time.time() - start_time
            metrics.activations_count += 1
            metrics.total_runtime_seconds += runtime
            metrics.last_activation = datetime.now()
            
            if not success:
                metrics.position_errors += 1
                metrics.success_rate = max(0, metrics.success_rate - 1)
            
            with self._lock:
                self.active_diverters.discard(diverter_id)
            
            logger.info(f"✅ Desviador {diverter_id} completado - {fruit_name} clasificadas")
            return success
            
        except Exception as e:
            logger.error(f"Error activando desviador {diverter_id}: {e}")
            with self._lock:
                self.active_diverters.discard(diverter_id)
            return False
    
    async def emergency_stop(self):
        """Parada de emergencia - mueve todos los desviadores a posición recta."""
        logger.critical("🚨 PARADA DE EMERGENCIA - Desviadores a posición segura")
        
        tasks = []
        for diverter in self.diverters.values():
            task = asyncio.create_task(diverter.move_to_position(DiverterPosition.STRAIGHT))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        with self._lock:
            self.active_diverters.clear()
        
        logger.info("🛡️ Todos los desviadores en posición segura")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema de desviadores."""
        return {
            "initialized": self.is_initialized,
            "total_diverters": len(self.diverters),
            "active_diverters": list(self.active_diverters),
            "diverters": {
                diverter_id: diverter.get_status()
                for diverter_id, diverter in self.diverters.items()
            },
            "metrics": {
                diverter_id: {
                    "category": metrics.category.fruit_name,
                    "emoji": metrics.category.emoji,
                    "activations": metrics.activations_count,
                    "runtime_seconds": metrics.total_runtime_seconds,
                    "success_rate": metrics.success_rate,
                    "last_activation": metrics.last_activation.isoformat() if metrics.last_activation else None,
                    "position_errors": metrics.position_errors
                }
                for diverter_id, metrics in self.diverter_metrics.items()
            },
            "configuration": {
                "activation_duration": self.activation_duration,
                "return_delay": self.return_delay
            }
        }
    
    async def calibrate_all(self) -> bool:
        """Calibra todos los desviadores moviendo a posiciones extremas."""
        logger.info("🔧 Iniciando calibración de desviadores...")
        
        try:
            for diverter_id, diverter in self.diverters.items():
                logger.info(f"Calibrando desviador {diverter_id}...")
                
                # Mover a posición recta
                await diverter.move_to_position(DiverterPosition.STRAIGHT)
                await asyncio.sleep(1)
                
                # Mover a posición desviada
                await diverter.move_to_position(DiverterPosition.DIVERTED)
                await asyncio.sleep(1)
                
                # Regresar a posición recta
                await diverter.move_to_position(DiverterPosition.STRAIGHT)
                
                logger.info(f"✅ Desviador {diverter_id} calibrado")
            
            logger.info("🎉 Calibración de desviadores completada")
            return True
            
        except Exception as e:
            logger.error(f"Error en calibración de desviadores: {e}")
            return False
    
    async def cleanup(self):
        """Limpia todos los recursos de los desviadores."""
        logger.info("Limpiando sistema de desviadores...")
        
        try:
            # Parar cualquier activación en curso
            await self.emergency_stop()
            
            # Limpiar cada desviador
            for diverter in self.diverters.values():
                await diverter.cleanup()
            
            self.diverters.clear()
            self.diverter_metrics.clear()
            self.is_initialized = False
            
            logger.info("🧹 Sistema de desviadores limpiado correctamente")
            
        except Exception as e:
            logger.error(f"Error limpiando desviadores: {e}")
