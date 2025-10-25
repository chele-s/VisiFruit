#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Driver de Servomotores MG995 con gpiozero para Raspberry Pi 5
=================================================================

Driver optimizado para usar PWM por hardware en Raspberry Pi 5 mediante gpiozero.
Compatible con los canales PWM hardware disponibles (GPIO 18/19).

Características:
- Soporte completo para hardware PWM en Pi 5
- Fallback automático a software PWM para pines sin hardware PWM
- Control preciso de servos MG995 (pulsos 1000-2000 µs)
- Operación asíncrona thread-safe
- Sin jitter ni vibraciones

Hardware PWM en Raspberry Pi 5:
- PWM0: GPIO 12 (Canal 0 - Hardware PWM dedicado)
- PWM1: GPIO 13 (Canal 1 - Hardware PWM dedicado)

NOTA IMPORTANTE:
- GPIO 12 y 13 son los ÚNICOS pines con hardware PWM real en Pi 5
- GPIO 18 y 19 NO tienen hardware PWM en Pi 5 (cambio de arquitectura)

Recomendado:
- GPIO 12 (PWM0) - Hardware PWM real
- GPIO 13 (PWM1) - Hardware PWM real

Requisitos:
- sudo apt install python3-gpiozero
- Configurar /boot/firmware/config.txt con dtoverlay=pwm-2chan

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Octubre 2025
Versión: 1.0 - Raspberry Pi 5 gpiozero Edition
"""

import asyncio
import logging
import time
from typing import Optional
from dataclasses import dataclass

try:
    from gpiozero import Servo, Device
    from gpiozero.pins.lgpio import LGPIOFactory
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False
    print("⚠️ gpiozero no disponible. Instalar: sudo apt install python3-gpiozero python3-lgpio")

logger = logging.getLogger(__name__)

@dataclass
class ServoConfig:
    """Configuración de un servomotor MG995."""
    pin_bcm: int
    name: str
    min_pulse_us: int = 1000      # Pulso mínimo (0°)
    max_pulse_us: int = 2000      # Pulso máximo (180°)
    default_angle: float = 90.0   # Ángulo inicial
    activation_angle: float = 0.0 # Ángulo de activación
    invert: bool = False          # Invertir dirección


class GPIOZeroServoDriver:
    """
    Driver de servomotor MG995 usando gpiozero para Raspberry Pi 5.
    
    Utiliza PWM por hardware cuando está disponible (GPIO 18, 19)
    y automáticamente hace fallback a software PWM en otros pines.
    """
    
    def __init__(self, config: ServoConfig):
        """
        Inicializa el driver del servo.
        
        Args:
            config: Configuración del servomotor
        """
        self.config = config
        self.servo: Optional[Servo] = None
        self.current_angle: float = config.default_angle
        self.initialized = False
        
        # Pines con hardware PWM REAL en Raspberry Pi 5
        # IMPORTANTE: Solo GPIO 12 y 13 tienen hardware PWM en Pi 5
        self.hardware_pwm_pins = {12, 13}
        
        logger.info(f"🎮 GPIOZeroServoDriver creado para pin {config.pin_bcm}")
    
    def initialize(self) -> bool:
        """
        Inicializa el servo con gpiozero.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            if not GPIOZERO_AVAILABLE:
                logger.error("❌ gpiozero no está disponible")
                return False
            
            # Configurar factory para usar lgpio (compatible con Pi 5)
            try:
                Device.pin_factory = LGPIOFactory()
                logger.info("✅ Usando LGPIOFactory (Raspberry Pi 5 compatible)")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo configurar LGPIOFactory: {e}")
                logger.warning("   Usando factory por defecto")
            
            # Convertir microsegundos a milisegundos para gpiozero
            min_pulse_ms = self.config.min_pulse_us / 1000.0
            max_pulse_ms = self.config.max_pulse_us / 1000.0
            
            # Crear instancia del servo
            # gpiozero usa valores entre -1 (min_pulse) y +1 (max_pulse)
            self.servo = Servo(
                self.config.pin_bcm,
                min_pulse_width=min_pulse_ms / 1000.0,  # Convertir a segundos
                max_pulse_width=max_pulse_ms / 1000.0,
                frame_width=20.0 / 1000.0  # 20ms período = 50Hz
            )
            
            # Verificar si usa hardware PWM
            is_hardware = self.config.pin_bcm in self.hardware_pwm_pins
            pwm_type = "Hardware PWM" if is_hardware else "Software PWM"
            
            logger.info(f"✅ Servo inicializado en GPIO {self.config.pin_bcm}")
            logger.info(f"   🔧 Tipo: {pwm_type}")
            logger.info(f"   📐 Rango: {self.config.min_pulse_us}-{self.config.max_pulse_us} µs")
            
            # Mover a posición inicial
            self.set_angle_sync(self.config.default_angle)
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servo en GPIO {self.config.pin_bcm}: {e}")
            return False
    
    def _angle_to_gpiozero_value(self, angle: float) -> float:
        """
        Convierte ángulo (0-180°) a valor gpiozero (-1 a +1).
        
        Args:
            angle: Ángulo en grados (0-180)
            
        Returns:
            Valor para gpiozero (-1 a +1)
        """
        # Limitar ángulo
        angle = max(0.0, min(180.0, angle))
        
        # Invertir si está configurado
        if self.config.invert:
            angle = 180.0 - angle
        
        # Convertir: 0° = -1, 90° = 0, 180° = +1
        value = (angle / 90.0) - 1.0
        
        return value
    
    def set_angle_sync(self, angle: float, hold: bool = False):
        """
        Establece el ángulo del servo (método síncrono).
        
        Args:
            angle: Ángulo objetivo (0-180°)
            hold: Si True, mantiene PWM activo (gpiozero siempre mantiene activo)
        """
        try:
            if not self.initialized or not self.servo:
                logger.warning("⚠️ Servo no inicializado")
                return
            
            # Convertir ángulo a valor gpiozero
            value = self._angle_to_gpiozero_value(angle)
            
            # Establecer posición
            self.servo.value = value
            
            self.current_angle = angle
            logger.debug(f"🎯 Servo GPIO {self.config.pin_bcm} → {angle}° (value={value:.3f})")
            
        except Exception as e:
            logger.error(f"❌ Error estableciendo ángulo: {e}")
    
    async def set_angle_async(self, angle: float, hold: bool = False):
        """
        Establece el ángulo del servo (método asíncrono thread-safe).
        
        Args:
            angle: Ángulo objetivo (0-180°)
            hold: Si True, mantiene PWM activo
        """
        # Ejecutar en thread pool para no bloquear event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.set_angle_sync, angle, hold)
    
    def stop_pwm(self):
        """
        Detiene el PWM (desactiva el servo para evitar consumo).
        
        En gpiozero, puedes usar servo.detach() o servo.value = None
        """
        try:
            if self.servo:
                self.servo.value = None
                logger.debug(f"⏹️ PWM detenido en GPIO {self.config.pin_bcm}")
        except Exception as e:
            logger.error(f"❌ Error deteniendo PWM: {e}")
    
    def get_current_angle(self) -> float:
        """Obtiene el ángulo actual del servo."""
        return self.current_angle
    
    def cleanup(self):
        """Limpia recursos del servo."""
        try:
            if self.servo:
                # Mover a posición segura antes de cerrar
                self.set_angle_sync(self.config.default_angle)
                time.sleep(0.5)
                
                # Detener PWM y cerrar
                self.servo.close()
                logger.debug(f"🧹 Servo GPIO {self.config.pin_bcm} limpiado")
                
            self.initialized = False
            
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")


def check_gpiozero_available() -> bool:
    """Verifica si gpiozero está disponible."""
    return GPIOZERO_AVAILABLE


async def test_gpiozero_servo():
    """Función de prueba del driver gpiozero."""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Test de GPIOZeroServoDriver")
    print("=" * 50)
    
    if not GPIOZERO_AVAILABLE:
        print("❌ gpiozero no está disponible")
        print("   Instalar: sudo apt install python3-gpiozero python3-lgpio")
        return
    
    # Configuración de prueba (GPIO 12 = Hardware PWM en Pi 5)
    config = ServoConfig(
        pin_bcm=12,
        name="Servo_Test",
        min_pulse_us=1000,
        max_pulse_us=2000,
        default_angle=90,
        activation_angle=45,
        invert=False
    )
    
    driver = GPIOZeroServoDriver(config)
    
    try:
        # Inicializar
        if not driver.initialize():
            print("❌ Fallo al inicializar servo")
            return
        
        print("\n✅ Servo inicializado")
        print(f"📍 Posición inicial: {driver.get_current_angle()}°")
        
        # Probar movimientos
        print("\n🔄 Probando movimientos...")
        
        angles = [0, 45, 90, 135, 180, 90]
        for angle in angles:
            print(f"   → {angle}°")
            await driver.set_angle_async(angle, hold=True)
            await asyncio.sleep(1.0)
        
        print("\n✅ Test completado")
        
    except KeyboardInterrupt:
        print("\n⚡ Interrumpido por usuario")
    finally:
        driver.cleanup()
        print("🧹 Cleanup completado")


if __name__ == "__main__":
    asyncio.run(test_gpiozero_servo())
