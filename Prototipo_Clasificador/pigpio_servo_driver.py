#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Driver Dedicado de Servos MG995 usando Pigpio - VisiFruit Prototipo
======================================================================

Driver especializado para control ultra-preciso de servomotores MG995
usando EXCLUSIVAMENTE pigpio daemon.

IMPORTANTE: Este driver NO debe mezclarse con lgpio. Usa SOLO pigpio.

Características:
- Control PWM hardware-timed por pigpio daemon (sin jitter)
- Pulsos precisos de 1000-2000μs a 50Hz
- Sin conflictos con lgpio (usa pigpio independiente)
- Soporte para 3 servos MG995 simultáneos

Especificaciones MG995:
- Voltaje: 4.8-7.2V
- Pulso: 1000μs (0°) - 2000μs (180°) 
- Frecuencia: 50Hz (período 20ms)
- Rango: 0-180° típico

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Enero 2025
Versión: 1.0 - Pigpio Exclusive Edition
"""

import logging
import time
import asyncio
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Importar pigpio
try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    logger.warning("⚠️ pigpio no disponible. Instalar con: sudo apt install python3-pigpio")

@dataclass
class ServoConfig:
    """Configuración de un servo MG995."""
    pin_bcm: int
    name: str
    min_pulse_us: int = 1000  # Pulso mínimo (0°)
    max_pulse_us: int = 2000  # Pulso máximo (180°)
    default_angle: float = 90.0
    activation_angle: float = 0.0
    invert: bool = False

class PigpioServoDriver:
    """
    Driver dedicado para servos MG995 usando SOLO pigpio.
    
    NO mezclar con lgpio - este driver usa pigpio daemon exclusivamente.
    """
    
    # Constantes
    PWM_FREQUENCY_HZ = 50  # 50Hz estándar para servos
    
    def __init__(self, servo_config: ServoConfig):
        """
        Inicializa el driver para un servo.
        
        Args:
            servo_config: Configuración del servo
        """
        self.config = servo_config
        self.pi: Optional[pigpio.pi] = None
        self.is_initialized = False
        self.current_angle: float = servo_config.default_angle
        
        logger.info(f"🎯 PigpioServoDriver creado para {servo_config.name} (Pin {servo_config.pin_bcm})")
    
    def initialize(self) -> bool:
        """
        Inicializa la conexión con el daemon pigpio.
        
        Returns:
            True si fue exitoso
        """
        try:
            if not PIGPIO_AVAILABLE:
                logger.error("❌ pigpio no disponible")
                return False
            
            # Conectar al daemon pigpio
            self.pi = pigpio.pi()
            
            if not self.pi.connected:
                logger.error(f"❌ No se pudo conectar al daemon pigpio")
                logger.error("   Ejecuta: sudo pigpiod")
                return False
            
            # Configurar pin como salida
            self.pi.set_mode(self.config.pin_bcm, pigpio.OUTPUT)
            
            # Establecer frecuencia PWM a 50Hz
            self.pi.set_PWM_frequency(self.config.pin_bcm, self.PWM_FREQUENCY_HZ)
            
            # Mover a posición inicial
            self._set_pulse_width(self._angle_to_pulse_width(self.config.default_angle))
            
            self.is_initialized = True
            logger.info(f"✅ Servo {self.config.name} inicializado con pigpio (daemon conectado)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servo con pigpio: {e}")
            return False
    
    def _angle_to_pulse_width(self, angle: float) -> int:
        """
        Convierte ángulo (0-180°) a ancho de pulso (μs).
        
        Args:
            angle: Ángulo en grados
            
        Returns:
            Ancho de pulso en microsegundos
        """
        # Normalizar ángulo
        angle = max(0.0, min(180.0, angle))
        
        # Invertir si está configurado
        if self.config.invert:
            angle = 180.0 - angle
        
        # Mapear linealmente: 0° → min_pulse_us, 180° → max_pulse_us
        pulse_range = self.config.max_pulse_us - self.config.min_pulse_us
        pulse_us = int(self.config.min_pulse_us + (angle / 180.0) * pulse_range)
        
        return pulse_us
    
    def _set_pulse_width(self, pulse_width_us: int):
        """
        Establece el ancho de pulso PWM directamente.
        
        Args:
            pulse_width_us: Ancho de pulso en microsegundos
        """
        if not self.is_initialized or not self.pi:
            return
        
        # Limitar al rango válido
        pulse_width_us = max(self.config.min_pulse_us, 
                            min(self.config.max_pulse_us, pulse_width_us))
        
        # Establecer servo pulse width (pigpio usa microsegundos directamente)
        self.pi.set_servo_pulsewidth(self.config.pin_bcm, pulse_width_us)
    
    def set_angle(self, angle: float, hold: bool = True):
        """
        Mueve el servo a un ángulo específico.
        
        Args:
            angle: Ángulo objetivo (0-180°)
            hold: Si True, mantiene PWM activo; si False, lo desactiva tras 300ms
        """
        try:
            if not self.is_initialized:
                logger.warning("⚠️ Servo no inicializado")
                return False
            
            pulse_width = self._angle_to_pulse_width(angle)
            self._set_pulse_width(pulse_width)
            
            self.current_angle = angle
            
            logger.debug(f"Servo {self.config.name}: {angle:.1f}° (pulso: {pulse_width}μs) {'[HOLD]' if hold else ''}")
            
            # Si no es hold, desactivar PWM después de que el servo llegue
            if not hold:
                time.sleep(0.3)  # Dar tiempo al servo para llegar
                self.stop_pwm()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error moviendo servo: {e}")
            return False
    
    async def set_angle_async(self, angle: float, hold: bool = True):
        """Versión asíncrona de set_angle."""
        return await asyncio.to_thread(self.set_angle, angle, hold)
    
    def stop_pwm(self):
        """Detiene la señal PWM (libera el servo)."""
        if self.is_initialized and self.pi:
            self.pi.set_servo_pulsewidth(self.config.pin_bcm, 0)
    
    def cleanup(self):
        """Limpia recursos del driver."""
        try:
            if self.pi:
                # Detener PWM
                self.stop_pwm()
                
                # Cerrar conexión
                self.pi.stop()
                
            self.is_initialized = False
            logger.info(f"✅ Servo {self.config.name} limpiado")
            
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")
    
    def get_status(self) -> Dict:
        """Obtiene el estado del servo."""
        return {
            "name": self.config.name,
            "pin_bcm": self.config.pin_bcm,
            "initialized": self.is_initialized,
            "connected": self.pi.connected if self.pi else False,
            "current_angle": self.current_angle,
            "default_angle": self.config.default_angle,
            "activation_angle": self.config.activation_angle
        }

# ==================== FUNCIONES DE UTILIDAD ====================

def check_pigpio_daemon() -> bool:
    """
    Verifica si el daemon pigpio está corriendo.
    
    Returns:
        True si está corriendo
    """
    if not PIGPIO_AVAILABLE:
        return False
    
    try:
        pi = pigpio.pi()
        connected = pi.connected
        pi.stop()
        return connected
    except:
        return False

async def test_servo():
    """Función de prueba del driver."""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Probando PigpioServoDriver...")
    
    # Verificar daemon
    if not check_pigpio_daemon():
        print("❌ Daemon pigpio no está corriendo")
        print("   Ejecuta: sudo pigpiod")
        return
    
    print("✅ Daemon pigpio conectado\n")
    
    # Configuración de prueba
    config = ServoConfig(
        pin_bcm=18,
        name="Servo_Test",
        min_pulse_us=1000,
        max_pulse_us=2000,
        default_angle=90.0,
        activation_angle=45.0
    )
    
    driver = PigpioServoDriver(config)
    
    try:
        if driver.initialize():
            print("✅ Driver inicializado\n")
            
            # Probar movimientos
            print("📐 Probando ángulos...")
            for angle in [0, 45, 90, 135, 180, 90]:
                print(f"   → {angle}°")
                await driver.set_angle_async(angle, hold=True)
                await asyncio.sleep(1.0)
            
            print("\n✅ Prueba completada")
        else:
            print("❌ Error inicializando driver")
            
    except KeyboardInterrupt:
        print("\n⚡ Interrumpido")
    finally:
        driver.cleanup()

if __name__ == "__main__":
    asyncio.run(test_servo())

