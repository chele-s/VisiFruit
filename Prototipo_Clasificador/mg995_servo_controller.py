#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Controlador de Servomotores MG995 para Clasificación - VisiFruit Prototipo
=============================================================================

Sistema de control de servomotores Tower Pro MG995 para clasificación automática
de frutas basado en detección por IA.

Características:
- Control de 3 servomotores MG995 (uno por categoría: manzanas, peras, limones)
- Soporte PWM con pigpio y RPi.GPIO
- Calibración automática de posiciones
- Sistema de seguridad y timeout
- Modo simulación para desarrollo

Especificaciones MG995:
- Voltaje: 4.8-7.2V
- Torque: 9.4-11 kg·cm
- Velocidad: 0.2s/60° (4.8V) - 0.16s/60° (6V)
- Ángulo: 0-180°
- Pulso: 1ms (0°) - 2ms (180°)
- Frecuencia: 50Hz (período 20ms)

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 1.0 - Prototipo Edition
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass

try:
    # Usaremos el wrapper centralizado que ya funciona con lgpio en tu Pi 5
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, is_simulation_mode
    print("✅ Controlador de servos usando GPIO Wrapper centralizado.")
except ImportError:
    print("❌ Error crítico: No se encontró el GPIO Wrapper centralizado.")
    # Forzar simulación si el wrapper no se encuentra
    from unittest.mock import Mock
    GPIO = Mock()
    GPIO_AVAILABLE = False
    def is_simulation_mode(): return True

logger = logging.getLogger(__name__)

class ServoPosition(Enum):
    """Posiciones predefinidas del servo."""
    CLOSED = 0       # Posición cerrada (bloqueado)
    OPEN = 90        # Posición abierta (liberado)
    MIDDLE = 45      # Posición media (para calibración)
    
class FruitCategory(Enum):
    """Categorías de frutas para clasificación."""
    APPLE = "apple"      # Manzanas
    PEAR = "pear"        # Peras
    LEMON = "lemon"      # Limones
    UNKNOWN = "unknown"  # Desconocido

@dataclass
class ServoConfig:
    """Configuración de un servomotor."""
    pin_bcm: int
    name: str
    category: FruitCategory
    min_pulse_us: int = 500      # Pulso mínimo en microsegundos
    max_pulse_us: int = 2500     # Pulso máximo en microsegundos
    default_angle: float = 0.0   # Ángulo por defecto
    activation_angle: float = 90.0  # Ángulo de activación
    activation_duration_s: float = 1.0  # Duración de activación
    invert: bool = False         # Invertir dirección

class MG995ServoController:
    """
    Controlador avanzado para servomotores MG995.
    
    Maneja hasta 3 servomotores para clasificación de frutas por categoría.
    Cada servo controla una compuerta/desviador para una categoría específica.
    """
    
    # Constantes PWM
    PWM_FREQUENCY_HZ = 50  # 50Hz para servos estándar
    PWM_PERIOD_MS = 20     # Período de 20ms
    
    def __init__(self, config: Dict):
        """
        Inicializa el controlador de servos.
        
        Args:
            config: Diccionario con configuración de servos
        """
        self.config = config
        self.servos: Dict[FruitCategory, ServoConfig] = {}
        self.current_angles: Dict[FruitCategory, float] = {}
        
        # Control de hardware
        self.pi = None  # Instancia de pigpio
        self.pwm_objects: Dict[int, any] = {}  # Objetos PWM de RPi.GPIO
        self.use_pigpio = False
        self.initialized = False
        
        # Estado y estadísticas
        self.activation_count: Dict[FruitCategory, int] = {
            FruitCategory.APPLE: 0,
            FruitCategory.PEAR: 0,
            FruitCategory.LEMON: 0
        }
        self.last_activation: Dict[FruitCategory, float] = {}
        self.total_activations = 0
        
        # Seguridad
        self.min_activation_interval_s = 0.1  # Intervalo mínimo entre activaciones
        self.max_continuous_activations = 10  # Máximo de activaciones continuas
        
        logger.info("🤖 MG995ServoController creado")
    
    async def initialize(self) -> bool:
        """
        Inicializa el controlador y los servos.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info("🔧 Inicializando controlador de servos MG995...")
            
            # Cargar configuración de servos
            servo_configs = self.config.get("servo_settings", {})
            
            if not servo_configs:
                logger.error("❌ No hay configuración de servos")
                return False
            
            # Configurar cada servo
            for category_name, servo_cfg in servo_configs.items():
                try:
                    category = FruitCategory(category_name)
                    servo_config = ServoConfig(
                        pin_bcm=servo_cfg["pin_bcm"],
                        name=servo_cfg.get("name", f"Servo_{category_name}"),
                        category=category,
                        min_pulse_us=servo_cfg.get("min_pulse_us", 500),
                        max_pulse_us=servo_cfg.get("max_pulse_us", 2500),
                        default_angle=servo_cfg.get("default_angle", 0.0),
                        activation_angle=servo_cfg.get("activation_angle", 90.0),
                        activation_duration_s=servo_cfg.get("activation_duration_s", 1.0),
                        invert=servo_cfg.get("invert", False)
                    )
                    self.servos[category] = servo_config
                    self.current_angles[category] = servo_config.default_angle
                    logger.info(f"   ✅ Servo {category.value}: Pin BCM {servo_config.pin_bcm}")
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ Error configurando servo {category_name}: {e}")
            
            if not self.servos:
                logger.error("❌ No se configuraron servos válidos")
                return False
            
            # Inicializar hardware
            if not GPIO_WRAPPER_AVAILABLE or is_simulation_mode():
                logger.info("🎭 Modo simulación - Sin hardware GPIO")
                self.initialized = True
                return True
            
            # Intentar pigpio primero (mejor precisión PWM)
            if PIGPIO_AVAILABLE and self.config.get("use_pigpio", True):
                try:
                    import pigpio
                    self.pi = pigpio.pi()
                    if self.pi.connected:
                        self.use_pigpio = True
                        logger.info("✅ Usando pigpio para control PWM de alta precisión")
                        
                        # Configurar pines con pigpio
                        for category, servo in self.servos.items():
                            self.pi.set_mode(servo.pin_bcm, pigpio.OUTPUT)
                            self.pi.set_PWM_frequency(servo.pin_bcm, self.PWM_FREQUENCY_HZ)
                            # Posición inicial
                            await self._set_servo_angle_pigpio(servo, servo.default_angle)
                    else:
                        logger.warning("⚠️ pigpio no conectado, usando RPi.GPIO")
                        self.use_pigpio = False
                except Exception as e:
                    logger.warning(f"⚠️ Error con pigpio: {e}, usando RPi.GPIO")
                    self.use_pigpio = False
            
            # Fallback a RPi.GPIO
            if not self.use_pigpio:
                GPIO.setmode(GPIO.BCM)
                for category, servo in self.servos.items():
                    GPIO.setup(servo.pin_bcm, GPIO.OUT)
                    pwm = GPIO.PWM(servo.pin_bcm, self.PWM_FREQUENCY_HZ)
                    pwm.start(0)
                    self.pwm_objects[servo.pin_bcm] = pwm
                    # Posición inicial
                    await self._set_servo_angle_gpio(servo, servo.default_angle)
                logger.info("✅ Usando RPi.GPIO para control PWM")
            
            self.initialized = True
            logger.info(f"✅ Controlador de servos inicializado ({len(self.servos)} servos)")
            
            # Test rápido de movimiento
            if self.config.get("test_on_init", False):
                await self._test_servos()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servos: {e}", exc_info=True)
            return False
    
    async def _set_servo_angle_pigpio(self, servo: ServoConfig, angle: float):
        """Establece el ángulo del servo usando pigpio."""
        if not self.pi or not self.pi.connected:
            return
        
        # Limitar ángulo
        angle = max(0.0, min(180.0, angle))
        if servo.invert:
            angle = 180.0 - angle
        
        # Convertir ángulo a pulso en microsegundos
        pulse_width = servo.min_pulse_us + (angle / 180.0) * (servo.max_pulse_us - servo.min_pulse_us)
        pulse_width = int(pulse_width)
        
        # Enviar comando
        self.pi.set_servo_pulsewidth(servo.pin_bcm, pulse_width)
        await asyncio.sleep(0.02)  # Pequeño delay para estabilidad
    
    async def _set_servo_angle_gpio(self, servo: ServoConfig, angle: float):
        """Establece el ángulo del servo usando RPi.GPIO."""
        pwm = self.pwm_objects.get(servo.pin_bcm)
        if not pwm:
            return
        
        # Limitar ángulo
        angle = max(0.0, min(180.0, angle))
        if servo.invert:
            angle = 180.0 - angle
        
        # Convertir ángulo a duty cycle (0-180° → 2.5-12.5% para pulsos 0.5-2.5ms en 20ms)
        duty_cycle = 2.5 + (angle / 180.0) * 10.0
        pwm.ChangeDutyCycle(duty_cycle)
        await asyncio.sleep(0.02)
    
    async def set_servo_angle(self, category: FruitCategory, angle: float) -> bool:
        """
        Establece el ángulo de un servo específico.
        
        Args:
            category: Categoría de fruta (servo)
            angle: Ángulo en grados (0-180)
        
        Returns:
            True si fue exitoso
        """
        try:
            if not self.initialized:
                logger.warning("⚠️ Controlador no inicializado")
                return False
            
            servo = self.servos.get(category)
            if not servo:
                logger.error(f"❌ Servo para categoría {category.value} no encontrado")
                return False
            
            if is_simulation_mode():
                logger.info(f"🎭 SIMULACIÓN: Servo {category.value} → {angle}°")
                self.current_angles[category] = angle
                return True
            
            # Mover servo
            if self.use_pigpio:
                await self._set_servo_angle_pigpio(servo, angle)
            else:
                await self._set_servo_angle_gpio(servo, angle)
            
            self.current_angles[category] = angle
            logger.debug(f"✅ Servo {category.value} movido a {angle}°")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error moviendo servo {category.value}: {e}")
            return False
    
    async def activate_servo(self, category: FruitCategory, duration: Optional[float] = None) -> bool:
        """
        Activa un servo (mueve a posición de activación y luego regresa).
        
        Args:
            category: Categoría de fruta
            duration: Duración de la activación en segundos (None = usar configuración)
        
        Returns:
            True si fue exitoso
        """
        try:
            servo = self.servos.get(category)
            if not servo:
                return False
            
            # Validar intervalo mínimo
            last_time = self.last_activation.get(category, 0)
            if (time.time() - last_time) < self.min_activation_interval_s:
                logger.warning(f"⚠️ Activación de {category.value} demasiado rápida, ignorando")
                return False
            
            # Usar duración configurada o por defecto
            activation_time = duration if duration is not None else servo.activation_duration_s
            
            logger.info(f"🎯 Activando servo {category.value} por {activation_time:.2f}s")
            
            # Mover a posición de activación
            success = await self.set_servo_angle(category, servo.activation_angle)
            if not success:
                return False
            
            # Esperar duración
            await asyncio.sleep(activation_time)
            
            # Regresar a posición por defecto
            success = await self.set_servo_angle(category, servo.default_angle)
            
            # Actualizar estadísticas
            self.activation_count[category] += 1
            self.total_activations += 1
            self.last_activation[category] = time.time()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error activando servo {category.value}: {e}")
            return False
    
    async def activate_for_fruit(self, fruit_class: str) -> bool:
        """
        Activa el servo correspondiente a una clase de fruta detectada.
        
        Args:
            fruit_class: Nombre de la clase detectada ("apple", "pear", "lemon")
        
        Returns:
            True si fue exitoso
        """
        try:
            # Mapear clase a categoría
            category_map = {
                "apple": FruitCategory.APPLE,
                "manzana": FruitCategory.APPLE,
                "pear": FruitCategory.PEAR,
                "pera": FruitCategory.PEAR,
                "lemon": FruitCategory.LEMON,
                "limon": FruitCategory.LEMON,
                "limón": FruitCategory.LEMON,
            }
            
            category = category_map.get(fruit_class.lower())
            if not category:
                logger.warning(f"⚠️ Clase de fruta desconocida: {fruit_class}")
                return False
            
            return await self.activate_servo(category)
            
        except Exception as e:
            logger.error(f"❌ Error activando para fruta {fruit_class}: {e}")
            return False
    
    async def _test_servos(self):
        """Prueba rápida de todos los servos."""
        logger.info("🧪 Ejecutando prueba de servos...")
        for category in self.servos.keys():
            logger.info(f"   Probando servo {category.value}...")
            await self.activate_servo(category, 0.5)
            await asyncio.sleep(0.3)
        logger.info("✅ Prueba de servos completada")
    
    async def home_all_servos(self) -> bool:
        """Mueve todos los servos a su posición inicial."""
        try:
            logger.info("🏠 Regresando todos los servos a posición inicial...")
            for category, servo in self.servos.items():
                await self.set_servo_angle(category, servo.default_angle)
                await asyncio.sleep(0.1)
            logger.info("✅ Todos los servos en posición inicial")
            return True
        except Exception as e:
            logger.error(f"❌ Error en home_all_servos: {e}")
            return False
    
    async def emergency_stop(self) -> bool:
        """Parada de emergencia - detiene todos los servos."""
        try:
            logger.warning("🚨 Parada de emergencia de servos")
            
            if self.use_pigpio and self.pi:
                for servo in self.servos.values():
                    self.pi.set_servo_pulsewidth(servo.pin_bcm, 0)  # Desactivar señal PWM
            else:
                for pin, pwm in self.pwm_objects.items():
                    pwm.ChangeDutyCycle(0)  # Desactivar señal PWM
            
            return True
        except Exception as e:
            logger.error(f"❌ Error en parada de emergencia: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual del controlador."""
        return {
            "initialized": self.initialized,
            "use_pigpio": self.use_pigpio,
            "simulation_mode": is_simulation_mode(),
            "servo_count": len(self.servos),
            "servos": {
                category.value: {
                    "pin_bcm": servo.pin_bcm,
                    "current_angle": self.current_angles.get(category, 0),
                    "activations": self.activation_count.get(category, 0),
                    "last_activation": self.last_activation.get(category, 0)
                }
                for category, servo in self.servos.items()
            },
            "total_activations": self.total_activations,
            "timestamp": time.time()
        }
    
    async def cleanup(self):
        """Limpia recursos del controlador."""
        try:
            logger.info("🧹 Limpiando controlador de servos...")
            
            # Regresar servos a posición inicial
            await self.home_all_servos()
            await asyncio.sleep(0.5)
            
            # Limpiar hardware
            if self.use_pigpio and self.pi:
                for servo in self.servos.values():
                    self.pi.set_servo_pulsewidth(servo.pin_bcm, 0)
                self.pi.stop()
                logger.info("✅ pigpio detenido")
            
            if self.pwm_objects:
                for pin, pwm in self.pwm_objects.items():
                    try:
                        pwm.stop()
                    except Exception:
                        pass
                logger.info("✅ PWM objects limpiados")
            
            if GPIO_WRAPPER_AVAILABLE:
                GPIO.cleanup()
            
            self.initialized = False
            logger.info("✅ Controlador de servos limpiado")
            
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")

# ==================== FUNCIONES DE UTILIDAD ====================

async def test_mg995_servos():
    """Función de prueba del controlador de servos."""
    logging.basicConfig(level=logging.INFO)
    
    # Configuración de prueba
    config = {
        "servo_settings": {
            "apple": {
                "pin_bcm": 5,
                "name": "Servo_Manzanas",
                "default_angle": 0,
                "activation_angle": 90,
                "activation_duration_s": 1.0
            },
            "pear": {
                "pin_bcm": 6,
                "name": "Servo_Peras",
                "default_angle": 0,
                "activation_angle": 90,
                "activation_duration_s": 1.0
            },
            "lemon": {
                "pin_bcm": 7,
                "name": "Servo_Limones",
                "default_angle": 0,
                "activation_angle": 90,
                "activation_duration_s": 1.0
            }
        },
        "use_pigpio": True,
        "test_on_init": True
    }
    
    controller = MG995ServoController(config)
    
    try:
        if await controller.initialize():
            print("✅ Controlador inicializado\n")
            
            # Probar cada servo
            for category in [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]:
                print(f"🧪 Probando {category.value}...")
                await controller.activate_servo(category, 1.0)
                await asyncio.sleep(1.0)
            
            # Estado final
            print("\n📊 Estado final:")
            status = controller.get_status()
            for cat, info in status["servos"].items():
                print(f"   {cat}: {info['activations']} activaciones")
        
    except KeyboardInterrupt:
        print("\n⚡ Interrumpido por usuario")
    finally:
        await controller.cleanup()

if __name__ == "__main__":
    asyncio.run(test_mg995_servos())
