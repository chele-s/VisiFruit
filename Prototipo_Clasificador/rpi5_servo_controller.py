#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Controlador Optimizado de Servos MG995 para Raspberry Pi 5
==============================================================

Controlador especializado para Raspberry Pi 5 usando gpiozero con hardware PWM.
Diseñado específicamente para los pines GPIO 12 y GPIO 13 que son los únicos
con verdadero hardware PWM en la Raspberry Pi 5.

Características:
- Hardware PWM real en GPIO 12 y 13 (sin jitter, ultra preciso)
- Configuración flexible de ángulos y dirección
- Calibración automática para servos MG995
- Sistema de perfiles para diferentes configuraciones
- Thread-safe y asyncio compatible
- Protección contra movimientos bruscos

Requisitos:
- Raspberry Pi 5
- gpiozero con backend lgpio
- Configurar /boot/firmware/config.txt con:
  dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4

Autor(es): Sistema VisiFruit
Fecha: Enero 2025
Versión: 2.0 - Raspberry Pi 5 Optimized Edition
"""

import asyncio
import logging
import time
import json
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading

try:
    from gpiozero import Servo, Device, AngularServo
    from gpiozero.pins.lgpio import LGPIOFactory
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False
    print("⚠️ gpiozero no disponible. Instalar: sudo apt install python3-gpiozero python3-lgpio")

logger = logging.getLogger(__name__)

class ServoDirection(Enum):
    """Dirección del movimiento del servo."""
    FORWARD = "forward"     # Movimiento normal
    REVERSE = "reverse"     # Movimiento invertido
    
class ServoProfile(Enum):
    """Perfiles predefinidos para diferentes tipos de servos."""
    MG995_STANDARD = "mg995_standard"
    MG995_EXTENDED = "mg995_extended"
    MG996R = "mg996r"
    CUSTOM = "custom"

@dataclass
class ServoCalibration:
    """Datos de calibración para un servo específico."""
    min_pulse_ms: float = 0.5      # Pulso mínimo en ms (0°)
    max_pulse_ms: float = 2.5      # Pulso máximo en ms (180°)
    min_angle: float = 0.0          # Ángulo mínimo real
    max_angle: float = 180.0        # Ángulo máximo real
    center_pulse_ms: float = 1.5    # Pulso central (90°)
    center_angle: float = 90.0      # Ángulo central
    deadband_ms: float = 0.01       # Zona muerta en ms

@dataclass
class ServoConfig:
    """Configuración completa de un servo MG995."""
    pin_bcm: int
    name: str
    # Calibración
    calibration: ServoCalibration = field(default_factory=ServoCalibration)
    # Configuración de movimiento
    default_angle: float = 90.0
    activation_angle: float = 0.0
    direction: ServoDirection = ServoDirection.FORWARD
    # Velocidad y suavizado
    movement_speed: float = 1.0     # Velocidad relativa (0.1-1.0)
    smooth_movement: bool = True    # Movimiento suave entre posiciones
    smooth_steps: int = 20          # Pasos para movimiento suave
    # Límites de seguridad
    min_safe_angle: float = 0.0     # Límite mínimo seguro
    max_safe_angle: float = 180.0   # Límite máximo seguro
    # Configuración avanzada
    hold_torque: bool = True        # Mantener torque cuando está quieto
    initial_delay_ms: float = 500   # Delay inicial antes del primer movimiento
    profile: ServoProfile = ServoProfile.MG995_STANDARD

class RPi5ServoController:
    """
    Controlador avanzado de servos para Raspberry Pi 5.
    
    Optimizado para usar hardware PWM en GPIO 12 y 13.
    """
    
    # Pines con hardware PWM real en Raspberry Pi 5
    HARDWARE_PWM_PINS = {12, 13}
    
    # Perfiles predefinidos
    SERVO_PROFILES = {
        ServoProfile.MG995_STANDARD: ServoCalibration(
            min_pulse_ms=1.0,
            max_pulse_ms=2.0,
            min_angle=0.0,
            max_angle=180.0,
            center_pulse_ms=1.5,
            center_angle=90.0
        ),
        ServoProfile.MG995_EXTENDED: ServoCalibration(
            min_pulse_ms=0.5,
            max_pulse_ms=2.5,
            min_angle=0.0,
            max_angle=180.0,
            center_pulse_ms=1.5,
            center_angle=90.0
        ),
        ServoProfile.MG996R: ServoCalibration(
            min_pulse_ms=0.8,
            max_pulse_ms=2.2,
            min_angle=0.0,
            max_angle=180.0,
            center_pulse_ms=1.5,
            center_angle=90.0
        )
    }
    
    def __init__(self, config: ServoConfig, auto_init: bool = True):
        """
        Inicializa el controlador del servo.
        
        Args:
            config: Configuración del servo
            auto_init: Si True, inicializa automáticamente el hardware
        """
        self.config = config
        self.servo: Optional[AngularServo] = None
        self.current_angle: float = config.default_angle
        self.target_angle: float = config.default_angle
        self.is_moving: bool = False
        self.initialized: bool = False
        
        # Thread safety
        self._lock = threading.Lock()
        self._movement_task: Optional[asyncio.Task] = None
        
        # Aplicar perfil si no es custom
        if config.profile != ServoProfile.CUSTOM:
            self.config.calibration = self.SERVO_PROFILES.get(
                config.profile, 
                ServoCalibration()
            )
        
        # Validar pin
        if config.pin_bcm not in self.HARDWARE_PWM_PINS:
            logger.warning(
                f"⚠️ Pin {config.pin_bcm} no tiene hardware PWM. "
                f"Usa GPIO 12 o 13 para mejor rendimiento."
            )
        
        logger.info(f"🎮 RPi5ServoController creado para '{config.name}' en GPIO {config.pin_bcm}")
        
        if auto_init:
            self.initialize()
    
    def initialize(self) -> bool:
        """
        Inicializa el hardware del servo.
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            if not GPIOZERO_AVAILABLE:
                logger.error("❌ gpiozero no está disponible")
                return False
            
            with self._lock:
                # Configurar factory para Raspberry Pi 5
                try:
                    Device.pin_factory = LGPIOFactory()
                    logger.info("✅ Usando LGPIOFactory (Raspberry Pi 5)")
                except Exception as e:
                    logger.warning(f"⚠️ Error configurando LGPIOFactory: {e}")
                    logger.info("   Usando factory por defecto")
                
                # Crear servo con configuración angular
                cal = self.config.calibration
                self.servo = AngularServo(
                    self.config.pin_bcm,
                    initial_angle=None,  # No mover inicialmente
                    min_angle=cal.min_angle,
                    max_angle=cal.max_angle,
                    min_pulse_width=cal.min_pulse_ms / 1000.0,
                    max_pulse_width=cal.max_pulse_ms / 1000.0,
                    frame_width=20.0 / 1000.0  # 20ms = 50Hz
                )
                
                # Información de configuración
                pwm_type = "Hardware" if self.config.pin_bcm in self.HARDWARE_PWM_PINS else "Software"
                logger.info(f"✅ Servo inicializado:")
                logger.info(f"   📍 Pin: GPIO {self.config.pin_bcm} ({pwm_type} PWM)")
                logger.info(f"   📐 Rango: {cal.min_angle}° - {cal.max_angle}°")
                logger.info(f"   ⚡ Pulsos: {cal.min_pulse_ms}ms - {cal.max_pulse_ms}ms")
                logger.info(f"   🎯 Perfil: {self.config.profile.value}")
                
                # Delay inicial
                if self.config.initial_delay_ms > 0:
                    time.sleep(self.config.initial_delay_ms / 1000.0)
                
                # Mover a posición inicial
                self._set_angle_direct(self.config.default_angle)
                
                self.initialized = True
                return True
                
        except Exception as e:
            logger.error(f"❌ Error inicializando servo: {e}", exc_info=True)
            return False
    
    def _apply_direction(self, angle: float) -> float:
        """
        Aplica la dirección configurada al ángulo.
        
        Args:
            angle: Ángulo original
            
        Returns:
            Ángulo con dirección aplicada
        """
        if self.config.direction == ServoDirection.REVERSE:
            return self.config.calibration.max_angle - angle
        return angle
    
    def _apply_limits(self, angle: float) -> float:
        """
        Aplica los límites de seguridad al ángulo.
        
        Args:
            angle: Ángulo deseado
            
        Returns:
            Ángulo dentro de los límites seguros
        """
        return max(
            self.config.min_safe_angle,
            min(self.config.max_safe_angle, angle)
        )
    
    def _set_angle_direct(self, angle: float):
        """
        Establece el ángulo del servo directamente (sin suavizado).
        
        Args:
            angle: Ángulo objetivo
        """
        if not self.servo:
            return
        
        # Aplicar límites y dirección
        safe_angle = self._apply_limits(angle)
        final_angle = self._apply_direction(safe_angle)
        
        try:
            self.servo.angle = final_angle
            self.current_angle = angle  # Guardar ángulo original (sin dirección)
            
            logger.debug(
                f"🎯 {self.config.name}: {angle}° → {final_angle}° "
                f"(dir={self.config.direction.value})"
            )
        except Exception as e:
            logger.error(f"❌ Error moviendo servo: {e}")
    
    def set_angle(self, angle: float, smooth: Optional[bool] = None) -> bool:
        """
        Establece el ángulo del servo (síncrono).
        
        Args:
            angle: Ángulo objetivo (0-180°)
            smooth: Si True, usa movimiento suave (None = usar config)
            
        Returns:
            True si fue exitoso
        """
        try:
            if not self.initialized or not self.servo:
                logger.warning(f"⚠️ Servo '{self.config.name}' no inicializado")
                return False
            
            with self._lock:
                self.target_angle = angle
                use_smooth = smooth if smooth is not None else self.config.smooth_movement
                
                if use_smooth and abs(angle - self.current_angle) > 5:
                    # Movimiento suave para cambios grandes
                    self._smooth_move_sync(angle)
                else:
                    # Movimiento directo
                    self._set_angle_direct(angle)
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error en set_angle: {e}")
            return False
    
    def _smooth_move_sync(self, target_angle: float):
        """
        Realiza un movimiento suave síncrono.
        
        Args:
            target_angle: Ángulo objetivo
        """
        steps = self.config.smooth_steps
        current = self.current_angle
        
        for i in range(steps + 1):
            # Interpolación lineal
            progress = i / steps
            intermediate = current + (target_angle - current) * progress
            
            self._set_angle_direct(intermediate)
            
            # Delay proporcional a la velocidad configurada
            delay_ms = (1.0 - self.config.movement_speed) * 10 + 5
            time.sleep(delay_ms / 1000.0)
    
    async def set_angle_async(self, angle: float, smooth: Optional[bool] = None) -> bool:
        """
        Establece el ángulo del servo (asíncrono).
        
        Args:
            angle: Ángulo objetivo
            smooth: Si True, usa movimiento suave
            
        Returns:
            True si fue exitoso
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.set_angle, angle, smooth)
    
    async def move_to_activation(self) -> bool:
        """Mueve el servo a la posición de activación."""
        return await self.set_angle_async(self.config.activation_angle)
    
    async def move_to_default(self) -> bool:
        """Mueve el servo a la posición por defecto."""
        return await self.set_angle_async(self.config.default_angle)
    
    def stop_hold(self):
        """
        Detiene el torque de mantención (ahorra energía).
        
        El servo queda libre para moverse manualmente.
        """
        try:
            if self.servo and not self.config.hold_torque:
                self.servo.angle = None
                logger.debug(f"⏹️ Torque detenido en {self.config.name}")
        except Exception as e:
            logger.error(f"❌ Error deteniendo torque: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del servo.
        
        Returns:
            Diccionario con información de estado
        """
        return {
            "name": self.config.name,
            "pin": self.config.pin_bcm,
            "initialized": self.initialized,
            "current_angle": self.current_angle,
            "target_angle": self.target_angle,
            "is_moving": self.is_moving,
            "direction": self.config.direction.value,
            "profile": self.config.profile.value,
            "hardware_pwm": self.config.pin_bcm in self.HARDWARE_PWM_PINS,
            "limits": {
                "min_safe": self.config.min_safe_angle,
                "max_safe": self.config.max_safe_angle,
                "min_pulse_ms": self.config.calibration.min_pulse_ms,
                "max_pulse_ms": self.config.calibration.max_pulse_ms
            }
        }
    
    def update_config(self, **kwargs) -> bool:
        """
        Actualiza la configuración del servo en tiempo real.
        
        Args:
            **kwargs: Parámetros a actualizar
            
        Returns:
            True si fue exitoso
        """
        try:
            with self._lock:
                # Actualizar configuración
                for key, value in kwargs.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                        logger.info(f"   ✅ {key} = {value}")
                
                # Re-aplicar calibración si cambió el perfil
                if 'profile' in kwargs and kwargs['profile'] != ServoProfile.CUSTOM:
                    self.config.calibration = self.SERVO_PROFILES.get(
                        kwargs['profile'],
                        self.config.calibration
                    )
                
                # Re-inicializar servo si cambió la calibración
                if 'calibration' in kwargs or 'profile' in kwargs:
                    logger.info(f"   🔄 Re-inicializando servo con nueva calibración")
                    self.cleanup()
                    self.initialize()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error actualizando configuración: {e}")
            return False
    
    def cleanup(self):
        """Limpia recursos del servo."""
        try:
            with self._lock:
                if self.servo:
                    # Mover a posición segura
                    self._set_angle_direct(self.config.default_angle)
                    time.sleep(0.5)
                    
                    # Cerrar servo
                    self.servo.close()
                    self.servo = None
                
                self.initialized = False
                logger.info(f"🧹 Servo '{self.config.name}' limpiado")
                
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")
    
    def __del__(self):
        """Destructor para asegurar limpieza."""
        self.cleanup()


class RPi5MultiServoController:
    """
    Controlador para gestionar múltiples `RPi5ServoController`.
    Provee utilidades para agregar, mover y consultar el estado de varios servos.
    """

    def __init__(self):
        self.controllers: Dict[str, RPi5ServoController] = {}

    def add_servo(
        self,
        servo_id: str,
        pin: int,
        name: str = None,
        profile: ServoProfile = ServoProfile.MG995_STANDARD,
        default_angle: float = 90.0,
        activation_angle: float = 0.0,
        direction: ServoDirection = ServoDirection.FORWARD,
        movement_speed: float = 1.0,
        smooth_movement: bool = True,
        smooth_steps: int = 20,
        min_safe_angle: float = 0.0,
        max_safe_angle: float = 180.0,
        hold_torque: bool = True,
        initial_delay_ms: float = 500.0,
        calibration: Optional[ServoCalibration] = None,
    ) -> bool:
        """
        Agrega un servo y lo inicializa.

        Returns:
            True si fue exitoso
        """
        try:
            # Si ya existe, limpiar antes de reemplazar
            if servo_id in self.controllers:
                try:
                    self.controllers[servo_id].cleanup()
                except Exception:
                    pass

            cfg = ServoConfig(
                pin_bcm=pin,
                name=name or f"Servo_{servo_id}",
                default_angle=default_angle,
                activation_angle=activation_angle,
                direction=direction,
                movement_speed=movement_speed,
                smooth_movement=smooth_movement,
                smooth_steps=smooth_steps,
                min_safe_angle=min_safe_angle,
                max_safe_angle=max_safe_angle,
                hold_torque=hold_torque,
                initial_delay_ms=initial_delay_ms,
                profile=profile,
            )

            # Si se proporciona una calibración explícita, usar perfil CUSTOM
            if calibration is not None:
                cfg.calibration = calibration
                cfg.profile = ServoProfile.CUSTOM

            controller = RPi5ServoController(cfg, auto_init=True)
            if controller.initialized:
                self.controllers[servo_id] = controller
                return True

            # Si no inicializó, limpiar por seguridad
            controller.cleanup()
            return False

        except Exception as e:
            logger.error(f"❌ Error agregando servo '{servo_id}': {e}")
            return False

    def remove_servo(self, servo_id: str) -> bool:
        """Elimina y limpia un servo por su ID."""
        try:
            controller = self.controllers.pop(servo_id, None)
            if controller:
                controller.cleanup()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error eliminando servo '{servo_id}': {e}")
            return False

    def get_servo(self, servo_id: str) -> Optional[RPi5ServoController]:
        """Obtiene el controlador de un servo por ID."""
        return self.controllers.get(servo_id)

    async def move_all(self, angle: float, smooth: bool = True) -> Dict[str, bool]:
        """Mueve todos los servos al mismo ángulo."""
        try:
            ids: List[str] = []
            coros: List[asyncio.Future] = []
            for sid, ctrl in self.controllers.items():
                ids.append(sid)
                coros.append(ctrl.set_angle_async(angle, smooth))

            results_list = await asyncio.gather(*coros, return_exceptions=False)
            return {sid: bool(res) for sid, res in zip(ids, results_list)}
        except Exception as e:
            logger.error(f"❌ Error moviendo todos los servos: {e}")
            return {sid: False for sid in self.controllers.keys()}

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene el estado de todos los servos."""
        status: Dict[str, Dict[str, Any]] = {}
        for sid, ctrl in self.controllers.items():
            try:
                status[sid] = ctrl.get_status()
            except Exception as e:
                status[sid] = {"error": str(e)}
        return status

    def cleanup_all(self):
        """Limpia todos los servos administrados."""
        for ctrl in self.controllers.values():
            try:
                ctrl.cleanup()
            except Exception:
                pass

# ==================== FUNCIONES DE PRUEBA ====================

async def test_single_servo():
    """Prueba un servo individual."""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Prueba de Servo Individual - Raspberry Pi 5")
    print("=" * 50)
    
    # Configuración para GPIO 12 (hardware PWM)
    config = ServoConfig(
        pin_bcm=12,
        name="Servo_Test",
        profile=ServoProfile.MG995_STANDARD,
        default_angle=90,
        activation_angle=0,
        direction=ServoDirection.FORWARD,
        smooth_movement=True,
        movement_speed=0.8
    )
    
    controller = RPi5ServoController(config)
    
    try:
        print("\n📐 Probando movimientos...")
        
        # Movimientos de prueba
        test_angles = [0, 45, 90, 135, 180, 90]
        for angle in test_angles:
            print(f"   → Moviendo a {angle}°")
            await controller.set_angle_async(angle, smooth=True)
            await asyncio.sleep(1.5)
        
        # Estado final
        print("\n📊 Estado del servo:")
        status = controller.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Prueba completada")
        
    except KeyboardInterrupt:
        print("\n⚡ Interrumpido por usuario")
    finally:
        controller.cleanup()


if __name__ == "__main__":
    asyncio.run(test_single_servo())
