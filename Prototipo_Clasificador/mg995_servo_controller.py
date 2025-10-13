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

# Usar controlador optimizado para Raspberry Pi 5 (RPi5ServoController) EXCLUSIVAMENTE
try:
    from Prototipo_Clasificador.rpi5_servo_controller import (
        RPi5ServoController,
        RPi5MultiServoController,
        ServoConfig as RPi5ServoConfig,
        ServoDirection as RPi5ServoDirection,
        ServoProfile as RPi5ServoProfile,
        ServoCalibration as RPi5ServoCalibration,
    )
    RPI5_AVAILABLE = True
    print("✅ Controlador de servos usando RPi5ServoController (Hardware PWM nativo)")
except ImportError as e:
    print(f"⚠️ RPi5ServoController no disponible: {e}")
    print("   El sistema requiere este controlador para funcionar.")
    RPI5_AVAILABLE = False

# Wrapper GPIO para modo simulación si falla RPi5
if not RPI5_AVAILABLE:
    try:
        from utils.gpio_wrapper import GPIO, is_simulation_mode
        print("   Usando GPIO wrapper en modo simulación")
    except ImportError:
        from unittest.mock import Mock
        GPIO = Mock()
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
    min_pulse_us: int = 1000     # Pulso mínimo en microsegundos (MG995 típico)
    max_pulse_us: int = 2000     # Pulso máximo en microsegundos (MG995 típico)
    default_angle: float = 90.0  # Ángulo por defecto (posición neutra)
    activation_angle: float = 0.0  # Ángulo de activación (clasificación)
    activation_duration_s: float = 2.0  # Duración total de activación
    hold_duration_s: float = 1.5  # Tiempo manteniendo posición rígida
    return_smoothly: bool = True  # Retornar suavemente a posición default
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
    
    # Pines con hardware PWM en Raspberry Pi 5 (solo 12 y 13)
    HARDWARE_PWM_PINS = {12, 13}
    
    def __init__(self, config: Dict):
        """
        Inicializa el controlador de servos.
        
        Args:
            config: Diccionario con configuración de servos
        """
        self.config = config
        self.servos: Dict[FruitCategory, ServoConfig] = {}
        self.current_angles: Dict[FruitCategory, float] = {}
        
        # Control de hardware - RPi5ServoController EXCLUSIVAMENTE
        self.rpi5_controllers: Dict[FruitCategory, RPi5ServoController] = {}
        
        # Modo de operación
        self.use_rpi5 = RPI5_AVAILABLE
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
        self.min_activation_interval_s = 0.5  # Intervalo mínimo entre activaciones
        self.max_continuous_activations = 10  # Máximo de activaciones continuas
        
        # Control de activaciones simultáneas
        self._active_servos: set = set()  # Servos actualmente en movimiento
        self._servo_locks: Dict[FruitCategory, asyncio.Lock] = {}
        
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
                    # Resolver activation_angle absoluto a partir de modo relativo si existe
                    activation_mode = str(servo_cfg.get("activation_mode", "absolute")).lower()
                    default_angle_val = float(servo_cfg.get("default_angle", 90.0))
                    if activation_mode == "relative":
                        offset = float(servo_cfg.get("activation_offset_deg", 0.0))
                        resolved_activation = default_angle_val + offset
                    else:
                        resolved_activation = float(servo_cfg.get("activation_angle", 0.0))

                    servo_config = ServoConfig(
                        pin_bcm=servo_cfg["pin_bcm"],
                        name=servo_cfg.get("name", f"Servo_{category_name}"),
                        category=category,
                        min_pulse_us=servo_cfg.get("min_pulse_us", 500),
                        max_pulse_us=servo_cfg.get("max_pulse_us", 2500),
                        default_angle=default_angle_val,
                        activation_angle=resolved_activation,
                        activation_duration_s=servo_cfg.get("activation_duration_s", 2.0),
                        hold_duration_s=servo_cfg.get("hold_duration_s", 1.5),
                        return_smoothly=servo_cfg.get("return_smoothly", True),
                        invert=servo_cfg.get("invert", False)
                    )
                    self.servos[category] = servo_config
                    self.current_angles[category] = servo_config.default_angle
                    self._servo_locks[category] = asyncio.Lock()
                    
                    # Log configuración con detalles
                    angle_diff = servo_config.activation_angle - servo_config.default_angle
                    logger.info(f"   ✅ Servo {category.value}: Pin BCM {servo_config.pin_bcm}")
                    logger.info(f"      📐 Default: {servo_config.default_angle}° → Activación: {servo_config.activation_angle}° (Δ {angle_diff:+.0f}°)")
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ Error configurando servo {category_name}: {e}")
            
            if not self.servos:
                logger.error("❌ No se configuraron servos válidos")
                return False
            
            # Inicializar hardware con RPi5ServoController EXCLUSIVAMENTE
            if self.use_rpi5 and RPI5_AVAILABLE:
                logger.info("🚀 Inicializando servos con RPi5ServoController (Hardware PWM nativo)...")
                
                # Verificar pines con hardware PWM
                hardware_pins = [s.pin_bcm for s in self.servos.values() if s.pin_bcm in self.HARDWARE_PWM_PINS]
                if hardware_pins:
                    logger.info(f"   🎯 Pines con hardware PWM detectados: {hardware_pins}")
                else:
                    logger.warning(f"   ⚠️ Los pines configurados no tienen hardware PWM. Recomendado: GPIO 12, 13")
                
                # Crear controladores RPi5 para cada servo
                for category, servo in self.servos.items():
                    try:
                        # Construir calibración y config para RPi5
                        cal = RPi5ServoCalibration(
                            min_pulse_ms=max(0.5, min(2.5, servo.min_pulse_us / 1000.0)),
                            max_pulse_ms=max(0.5, min(2.5, servo.max_pulse_us / 1000.0)),
                            min_angle=0.0,
                            max_angle=180.0,
                            center_pulse_ms=1.5,
                            center_angle=90.0,
                        )
                        rpi5_cfg = RPi5ServoConfig(
                            pin_bcm=servo.pin_bcm,
                            name=servo.name,
                            calibration=cal,
                            default_angle=servo.default_angle,
                            activation_angle=servo.activation_angle,
                            direction=RPi5ServoDirection.REVERSE if servo.invert else RPi5ServoDirection.FORWARD,
                            movement_speed=0.7,  # Velocidad más lenta para movimientos más suaves
                            smooth_movement=True,
                            smooth_steps=30,  # Más pasos para movimiento ultra-suave
                            min_safe_angle=0.0,
                            max_safe_angle=180.0,
                            hold_torque=True,
                            initial_delay_ms=200,
                            profile=RPi5ServoProfile.MG995_STANDARD,
                        )
                        controller = RPi5ServoController(rpi5_cfg, auto_init=True)
                        if controller.initialized:
                            self.rpi5_controllers[category] = controller
                            pwm_type = "Hardware" if servo.pin_bcm in self.HARDWARE_PWM_PINS else "Software"
                            logger.info(f"   ✅ {category.value}: RPi5ServoController inicializado (Pin {servo.pin_bcm}, {pwm_type} PWM)")
                        else:
                            logger.error(f"   ❌ {category.value}: no se pudo inicializar RPi5ServoController")
                            return False
                    except Exception as e:
                        logger.error(f"   ❌ {category.value}: error creando RPi5ServoController: {e}")
                        return False
            else:
                logger.warning("🎭 Modo simulación - RPi5ServoController no disponible")
                logger.warning("   Instala: sudo apt install python3-gpiozero python3-lgpio")
                self.initialized = True
                return True
            
            # Marcar inicializado
            self.initialized = True
            
            # Mover servos a posición inicial
            logger.info("📍 Moviendo servos a posición inicial...")
            await self.home_all_servos(silent=True)
            
            if self.use_rpi5:
                logger.info(f"✅ Controlador de servos inicializado con RPi5ServoController ({len(self.servos)} servos)")
                logger.info("   🎯 PWM nativo Raspberry Pi 5 activo (lgpio tx_pwm, sin jitter)")
            else:
                logger.info(f"✅ Controlador de servos en modo simulación ({len(self.servos)} servos)")
            
            # Test rápido de movimiento
            if self.config.get("test_on_init", False):
                await self._test_servos()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servos: {e}", exc_info=True)
            return False
    
    async def _set_servo_angle_rpi5(self, category: FruitCategory, angle: float, hold: bool = False):
        """
        Establece el ángulo del servo usando RPi5ServoController.
        
        Args:
            category: Categoría del servo
            angle: Ángulo objetivo (0-180°)
            hold: Si True, mantiene el PWM activo (RPi5 siempre mantiene activo)
        """
        controller = self.rpi5_controllers.get(category)
        if controller:
            # RPi5 controller maneja suavizado internamente
            await controller.set_angle_async(angle, smooth=True)
        else:
            logger.warning(f"⚠️ No se encontró controlador RPi5 para {category.value}")
    
    async def set_servo_angle(self, category: FruitCategory, angle: float, hold: bool = False) -> bool:
        """
        Establece el ángulo de un servo específico.
        
        Args:
            category: Categoría de fruta (servo)
            angle: Ángulo en grados (0-180°)
            hold: Si True, mantiene PWM activo para posición rígida
        
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
            
            # Modo simulación
            if not self.use_rpi5:
                logger.info(f"🎭 SIMULACIÓN: Servo {category.value} → {angle}° {'(HOLD)' if hold else ''}")
                self.current_angles[category] = angle
                return True
            
            # Mover servo usando RPi5ServoController
            await self._set_servo_angle_rpi5(category, angle, hold)
            
            self.current_angles[category] = angle
            logger.debug(f"✅ Servo {category.value} movido a {angle}° {'(HOLD)' if hold else ''}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error moviendo servo {category.value}: {e}")
            return False
    
    async def activate_servo(self, category: FruitCategory, duration: Optional[float] = None) -> bool:
        """
        Activa un servo con sistema de hold rígido y retorno suave.
        
        Secuencia:
        1. Verificar que el servo no esté activo
        2. Mover rápidamente a posición de activación
        3. Mantener posición rígida (hold) durante tiempo configurado
        4. Retornar suavemente a posición default
        5. Desactivar PWM para evitar oscilaciones
        
        Args:
            category: Categoría de fruta
            duration: Duración total (None = usar configuración)
        
        Returns:
            True si fue exitoso
        """
        try:
            servo = self.servos.get(category)
            if not servo:
                logger.error(f"❌ Servo {category.value} no encontrado")
                return False
            
            # Prevenir activaciones simultáneas del mismo servo
            lock = self._servo_locks.get(category)
            if lock and lock.locked():
                logger.warning(f"⚠️ Servo {category.value} ya está activo, ignorando")
                return False
            
            # Validar intervalo mínimo
            last_time = self.last_activation.get(category, 0)
            if (time.time() - last_time) < self.min_activation_interval_s:
                logger.warning(f"⚠️ Activación de {category.value} demasiado rápida, ignorando")
                return False
            
            # Adquirir lock para esta activación
            async with self._servo_locks[category]:
                self._active_servos.add(category)
                
                try:
                    # Configuración de timing
                    hold_time = servo.hold_duration_s
                    total_time = duration if duration is not None else servo.activation_duration_s
                    
                    logger.info(f"🎯 Activando servo {category.value}")
                    logger.info(f"   📐 {servo.default_angle}° → {servo.activation_angle}° (Δ {servo.activation_angle - servo.default_angle:+.0f}°)")
                    logger.info(f"   ⏱️ Hold: {hold_time:.1f}s | Total: {total_time:.1f}s")
                    
                    # FASE 1: Mover a posición de activación con suavizado integrado
                    if not self.use_rpi5:
                        logger.info(f"🎭 SIMULACIÓN: Moviendo a {servo.activation_angle}°")
                        await asyncio.sleep(0.3)  # Simular tiempo de movimiento
                    else:
                        # Usar el suavizado integrado del RPi5ServoController
                        controller = self.rpi5_controllers.get(category)
                        if controller:
                            await controller.set_angle_async(servo.activation_angle, smooth=True)
                    
                    # FASE 2: Mantener posición RÍGIDA durante hold_duration
                    logger.info(f"   🔒 Manteniendo posición rígida por {hold_time:.1f}s...")
                    await asyncio.sleep(hold_time)
                    
                    # FASE 3: Retorno suave usando el suavizado integrado del RPi5ServoController
                    logger.info(f"   🔄 Retornando suavemente a {servo.default_angle}°...")
                    if not self.use_rpi5:
                        await asyncio.sleep(0.3)
                    else:
                        # Retorno con suavizado integrado (sin pasos manuales que causan jitter)
                        controller = self.rpi5_controllers.get(category)
                        if controller:
                            await controller.set_angle_async(servo.default_angle, smooth=True)
                    
                    # Actualizar estadísticas
                    self.activation_count[category] += 1
                    self.total_activations += 1
                    self.last_activation[category] = time.time()
                    
                    logger.info(f"   ✅ Servo {category.value} completado exitosamente")
                    return True
                    
                finally:
                    self._active_servos.discard(category)
            
        except Exception as e:
            logger.error(f"❌ Error activando servo {category.value}: {e}", exc_info=True)
            self._active_servos.discard(category)
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
    
    async def home_all_servos(self, silent: bool = False) -> bool:
        """
        Mueve todos los servos a su posición inicial (default_angle).
        
        Args:
            silent: Si True, no imprime mensajes de log (útil para inicialización)
        
        Returns:
            True si fue exitoso
        """
        try:
            if not silent:
                logger.info("🏠 Regresando todos los servos a posición inicial...")
            
            for category, servo in self.servos.items():
                # Mover sin hold para que se desactive PWM después
                await self.set_servo_angle(category, servo.default_angle, hold=False)
                
                # Pequeña pausa entre servos
                await asyncio.sleep(0.2)
                
                # Asegurar que PWM está apagado (opcional con RPi5)
                if self.use_rpi5:
                    controller = self.rpi5_controllers.get(category)
                    if controller:
                        try:
                            controller.stop_hold()
                        except Exception:
                            pass
            
            if not silent:
                logger.info("✅ Todos los servos en posición inicial")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en home_all_servos: {e}")
            return False
    
    async def emergency_stop(self) -> bool:
        """Parada de emergencia - detiene todos los servos."""
        try:
            logger.warning("🚨 Parada de emergencia de servos")
            
            if self.use_rpi5:
                # Detener todos los controladores RPi5
                for category, controller in self.rpi5_controllers.items():
                    try:
                        controller.stop_hold()
                    except Exception:
                        pass
            
            return True
        except Exception as e:
            logger.error(f"❌ Error en parada de emergencia: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual del controlador."""
        return {
            "initialized": self.initialized,
            "use_rpi5": self.use_rpi5,
            "simulation_mode": not self.use_rpi5,
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
            logger.info("🏠 Regresando todos los servos a posición inicial...")
            await self.home_all_servos()
            await asyncio.sleep(0.5)
            
            # Limpiar controladores RPi5
            if self.use_rpi5 and self.rpi5_controllers:
                for category, controller in self.rpi5_controllers.items():
                    try:
                        controller.cleanup()
                    except Exception as e:
                        logger.warning(f"Error limpiando controlador {category.value}: {e}")
                logger.info("✅ Controladores RPi5 limpiados")
            
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
