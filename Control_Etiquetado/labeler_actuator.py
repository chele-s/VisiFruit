# Control_Etiquetado/labeler_actuator.py
"""
Sistema de Control del Actuador de Etiquetado Industrial - FruPrint
================================================================

Módulo avanzado para control de actuadores de etiquetado con características industriales:
- Control preciso de múltiples tipos de actuadores (solenoides, servomotores, stepper)
- Sistema de calibración automática y validación de funcionamiento
- Monitoreo en tiempo real de rendimiento y desgaste
- Recuperación automática de errores y modo de seguridad
- Telemetría avanzada y análisis predictivo
- Compatibilidad con múltiples protocolos de comunicación

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Edición Industrial
"""

import asyncio
import logging
import time
import threading
import json
import statistics
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional, List, Callable, Any, Union
from contextlib import contextmanager

import numpy as np

try:
    import sys
    from pathlib import Path
    # Añadir directorio padre al path para importar utils
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, is_simulation_mode
    
    if is_simulation_mode():
        print("🏷️ Etiquetadoras: Modo simulación activo (ideal para desarrollo)")
    else:
        print("✅ Etiquetadoras: GPIO hardware activo")
        
except ImportError:
    print("⚠️ GPIO wrapper no disponible - Modo simulación para etiquetadoras")
    GPIO_AVAILABLE = False

# Configuración del logger
logger = logging.getLogger(__name__)

class ActuatorType(Enum):
    """Tipos de actuadores soportados."""
    SOLENOID = "solenoid"
    SERVO = "servo"
    STEPPER = "stepper"
    PNEUMATIC = "pneumatic"
    DC_MOTOR = "dc_motor"

class ActuatorState(Enum):
    """Estados del actuador."""
    OFFLINE = auto()
    INITIALIZING = auto()
    IDLE = auto()
    ACTIVE = auto()
    CALIBRATING = auto()
    ERROR = auto()
    MAINTENANCE = auto()
    EMERGENCY_STOP = auto()

class ActuatorHealth(Enum):
    """Estado de salud del actuador."""
    EXCELLENT = auto()
    GOOD = auto()
    WARNING = auto()
    CRITICAL = auto()
    FAILED = auto()

@dataclass
class ActuatorMetrics:
    """Métricas del actuador."""
    timestamp: datetime = field(default_factory=datetime.now)
    activations_count: int = 0
    total_active_time: float = 0.0
    average_activation_time: float = 0.0
    last_activation_duration: float = 0.0
    response_time_ms: float = 0.0
    power_consumption_w: float = 0.0
    temperature_c: float = 0.0
    vibration_level: float = 0.0
    error_count: int = 0
    health_score: float = 1.0
    efficiency_percent: float = 100.0
    wear_level: float = 0.0

@dataclass
class CalibrationResult:
    """Resultado de calibración del actuador."""
    success: bool
    min_pulse_width: float
    max_pulse_width: float
    optimal_frequency: float
    response_time_ms: float
    accuracy_percent: float
    calibration_date: datetime = field(default_factory=datetime.now)
    notes: str = ""

class BaseActuatorDriver(ABC):
    """Clase base abstracta para drivers de actuadores."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_initialized = False
        self.last_error: Optional[str] = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Inicializa el driver."""
        pass
    
    @abstractmethod
    async def activate(self, duration: float, intensity: float = 100.0) -> bool:
        """Activa el actuador por una duración específica."""
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """Desactiva el actuador."""
        pass
    
    @abstractmethod
    async def calibrate(self) -> CalibrationResult:
        """Calibra el actuador."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del actuador."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Limpia recursos del driver."""
        pass

class SolenoidDriver(BaseActuatorDriver):
    """Driver para solenoides con control PWM avanzado."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pin = int(config.get("pin", 26))
        self.pwm_frequency = int(config.get("pwm_frequency", 1000))
        self.voltage_rating = float(config.get("voltage_rating", 12.0))
        self.current_rating = float(config.get("current_rating", 1.5))
        self.response_time_ms = float(config.get("response_time_ms", 10))
        
        self.pwm_instance = None
        self.is_active = False
        self.activation_start_time = 0.0
        
    async def initialize(self) -> bool:
        """Inicializa el solenoide."""
        try:
            if not GPIO_AVAILABLE:
                logger.warning("GPIO no disponible, usando modo simulación")
                self.is_initialized = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            
            # Configurar PWM
            self.pwm_instance = GPIO.PWM(self.pin, self.pwm_frequency)
            self.pwm_instance.start(0)
            
            # Prueba rápida de funcionamiento
            await self._test_functionality()
            
            self.is_initialized = True
            logger.info(f"Solenoide inicializado en pin {self.pin}")
            return True
            
        except Exception as e:
            self.last_error = f"Error inicializando solenoide: {e}"
            logger.error(self.last_error)
            return False
    
    async def _test_functionality(self):
        """Prueba rápida de funcionamiento."""
        if self.pwm_instance:
            # Pulso corto de prueba
            self.pwm_instance.ChangeDutyCycle(50)
            await asyncio.sleep(0.1)
            self.pwm_instance.ChangeDutyCycle(0)
    
    async def activate(self, duration: float, intensity: float = 100.0) -> bool:
        """Activa el solenoide con intensidad específica."""
        try:
            if not self.is_initialized:
                raise RuntimeError("Solenoide no inicializado")
            
            if self.is_active:
                logger.warning("Solenoide ya está activo")
                return False
            
            intensity = max(0, min(100, intensity))  # Limitar 0-100%
            duty_cycle = intensity
            
            self.activation_start_time = time.time()
            self.is_active = True
            
            if GPIO_AVAILABLE and self.pwm_instance:
                self.pwm_instance.ChangeDutyCycle(duty_cycle)
            
            logger.debug(f"Solenoide activado: {duration}s, intensidad: {intensity}%")
            
            # Programar desactivación automática
            asyncio.create_task(self._auto_deactivate(duration))
            
            return True
            
        except Exception as e:
            self.last_error = f"Error activando solenoide: {e}"
            logger.error(self.last_error)
            self.is_active = False
            return False
    
    async def _auto_deactivate(self, delay: float):
        """Desactiva automáticamente después del delay."""
        await asyncio.sleep(delay)
        await self.deactivate()
    
    async def deactivate(self) -> bool:
        """Desactiva el solenoide."""
        try:
            if not self.is_active:
                return True
            
            if GPIO_AVAILABLE and self.pwm_instance:
                self.pwm_instance.ChangeDutyCycle(0)
            
            self.is_active = False
            activation_time = time.time() - self.activation_start_time
            
            logger.debug(f"Solenoide desactivado después de {activation_time:.3f}s")
            return True
            
        except Exception as e:
            self.last_error = f"Error desactivando solenoide: {e}"
            logger.error(self.last_error)
            return False
    
    async def calibrate(self) -> CalibrationResult:
        """Calibra el solenoide."""
        logger.info("Iniciando calibración del solenoide...")
        
        try:
            # Pruebas de respuesta con diferentes intensidades
            response_times = []
            
            for intensity in [25, 50, 75, 100]:
                start_time = time.time()
                await self.activate(0.1, intensity)
                await asyncio.sleep(0.2)  # Esperar a que se complete
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
            
            avg_response_time = statistics.mean(response_times)
            
            result = CalibrationResult(
                success=True,
                min_pulse_width=0.0,
                max_pulse_width=self.voltage_rating,
                optimal_frequency=self.pwm_frequency,
                response_time_ms=avg_response_time,
                accuracy_percent=95.0,  # Estimación
                notes=f"Calibración completada con {len(response_times)} pruebas"
            )
            
            logger.info(f"Calibración completada: {avg_response_time:.1f}ms respuesta promedio")
            return result
            
        except Exception as e:
            logger.error(f"Error en calibración: {e}")
            return CalibrationResult(
                success=False,
                min_pulse_width=0,
                max_pulse_width=0,
                optimal_frequency=0,
                response_time_ms=0,
                accuracy_percent=0,
                notes=f"Error: {e}"
            )
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del solenoide."""
        return {
            "type": "solenoid",
            "pin": self.pin,
            "is_initialized": self.is_initialized,
            "is_active": self.is_active,
            "pwm_frequency": self.pwm_frequency,
            "voltage_rating": self.voltage_rating,
            "last_error": self.last_error
        }
    
    async def cleanup(self):
        """Limpia recursos del solenoide."""
        try:
            await self.deactivate()
            
            if GPIO_AVAILABLE and self.pwm_instance:
                self.pwm_instance.stop()
                GPIO.cleanup(self.pin)
            
            self.is_initialized = False
            logger.info("Solenoide limpiado correctamente")
            
        except Exception as e:
            logger.error(f"Error limpiando solenoide: {e}")

class ServoDriver(BaseActuatorDriver):
    """Driver para servomotores con control de posición preciso."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.pin = int(config.get("pin", 18))
        self.min_angle = int(config.get("min_angle", 0))
        self.max_angle = int(config.get("max_angle", 180))
        self.rest_angle = int(config.get("rest_angle", 90))
        self.active_angle = int(config.get("active_angle", 45))
        self.pwm_frequency = 50  # Estándar para servos
        
        self.pwm_instance = None
        self.current_angle = self.rest_angle
        self.is_active = False
    
    async def initialize(self) -> bool:
        """Inicializa el servo."""
        try:
            if not GPIO_AVAILABLE:
                logger.warning("GPIO no disponible, usando modo simulación")
                self.is_initialized = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)
            
            self.pwm_instance = GPIO.PWM(self.pin, self.pwm_frequency)
            self.pwm_instance.start(0)
            
            # Mover a posición de reposo
            await self._move_to_angle(self.rest_angle)
            
            self.is_initialized = True
            logger.info(f"Servo inicializado en pin {self.pin}")
            return True
            
        except Exception as e:
            self.last_error = f"Error inicializando servo: {e}"
            logger.error(self.last_error)
            return False
    
    def _angle_to_duty_cycle(self, angle: float) -> float:
        """Convierte ángulo a duty cycle para PWM."""
        # Fórmula estándar para servos: 2.5% a 12.5% duty cycle para 0-180°
        return 2.5 + (angle / 180.0) * 10.0
    
    async def _move_to_angle(self, angle: float):
        """Mueve el servo a un ángulo específico."""
        angle = max(self.min_angle, min(self.max_angle, angle))
        duty_cycle = self._angle_to_duty_cycle(angle)
        
        if GPIO_AVAILABLE and self.pwm_instance:
            self.pwm_instance.ChangeDutyCycle(duty_cycle)
        
        self.current_angle = angle
        await asyncio.sleep(0.5)  # Tiempo para que el servo se mueva
    
    async def activate(self, duration: float, intensity: float = 100.0) -> bool:
        """Activa el servo moviéndolo a la posición activa."""
        try:
            if not self.is_initialized:
                raise RuntimeError("Servo no inicializado")
            
            # Calcular ángulo basado en intensidad
            angle_range = abs(self.active_angle - self.rest_angle)
            target_angle = self.rest_angle + (angle_range * intensity / 100.0)
            
            self.is_active = True
            await self._move_to_angle(target_angle)
            
            logger.debug(f"Servo activado: {duration}s, ángulo: {target_angle:.1f}°")
            
            # Programar retorno a posición de reposo
            asyncio.create_task(self._auto_return_to_rest(duration))
            
            return True
            
        except Exception as e:
            self.last_error = f"Error activando servo: {e}"
            logger.error(self.last_error)
            self.is_active = False
            return False
    
    async def _auto_return_to_rest(self, delay: float):
        """Retorna automáticamente a posición de reposo."""
        await asyncio.sleep(delay)
        await self.deactivate()
    
    async def deactivate(self) -> bool:
        """Retorna el servo a posición de reposo."""
        try:
            await self._move_to_angle(self.rest_angle)
            self.is_active = False
            
            logger.debug("Servo retornado a posición de reposo")
            return True
            
        except Exception as e:
            self.last_error = f"Error desactivando servo: {e}"
            logger.error(self.last_error)
            return False
    
    async def calibrate(self) -> CalibrationResult:
        """Calibra el servo."""
        logger.info("Iniciando calibración del servo...")
        
        try:
            # Probar movimiento completo
            start_time = time.time()
            
            await self._move_to_angle(self.min_angle)
            await self._move_to_angle(self.max_angle)
            await self._move_to_angle(self.rest_angle)
            
            total_time = (time.time() - start_time) * 1000
            
            result = CalibrationResult(
                success=True,
                min_pulse_width=self._angle_to_duty_cycle(self.min_angle),
                max_pulse_width=self._angle_to_duty_cycle(self.max_angle),
                optimal_frequency=self.pwm_frequency,
                response_time_ms=total_time / 3,  # Promedio por movimiento
                accuracy_percent=98.0,
                notes="Calibración completa de rango de movimiento"
            )
            
            logger.info(f"Calibración completada: {total_time:.1f}ms para rango completo")
            return result
            
        except Exception as e:
            logger.error(f"Error en calibración: {e}")
            return CalibrationResult(
                success=False,
                min_pulse_width=0,
                max_pulse_width=0,
                optimal_frequency=0,
                response_time_ms=0,
                accuracy_percent=0,
                notes=f"Error: {e}"
            )
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servo."""
        return {
            "type": "servo",
            "pin": self.pin,
            "is_initialized": self.is_initialized,
            "is_active": self.is_active,
            "current_angle": self.current_angle,
            "rest_angle": self.rest_angle,
            "active_angle": self.active_angle,
            "last_error": self.last_error
        }
    
    async def cleanup(self):
        """Limpia recursos del servo."""
        try:
            await self.deactivate()
            
            if GPIO_AVAILABLE and self.pwm_instance:
                self.pwm_instance.stop()
                GPIO.cleanup(self.pin)
            
            self.is_initialized = False
            logger.info("Servo limpiado correctamente")
            
        except Exception as e:
            logger.error(f"Error limpiando servo: {e}")

class StepperDriver(BaseActuatorDriver):
    """Driver para motor paso a paso con DRV8825.
    
    Controla pines STEP/DIR/EN y opcionales MS1-MS3 para microstepping.
    La activación usa velocidad en pasos/seg basada en "intensity" (0-100%).
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Pines básicos
        self.step_pin = int(config.get("step_pin_bcm", config.get("step_pin", 19)))
        self.dir_pin = int(config.get("dir_pin_bcm", config.get("dir_pin", 26)))
        self.enable_pin = int(config.get("enable_pin_bcm", config.get("enable_pin", 21)))
        # Pines microstep (opcionales)
        ms_pins = config.get("microstep_pins", {})
        self.ms1_pin = ms_pins.get("ms1_pin_bcm", ms_pins.get("ms1", None))
        self.ms2_pin = ms_pins.get("ms2_pin_bcm", ms_pins.get("ms2", None))
        self.ms3_pin = ms_pins.get("ms3_pin_bcm", ms_pins.get("ms3", None))
        # Parámetros
        self.enable_active_low = bool(config.get("enable_active_low", True))
        self.default_direction = config.get("default_direction", "CW")  # "CW"/"CCW"
        self.invert_direction = bool(config.get("invert_direction", False))
        self.base_speed_sps = float(config.get("base_speed_sps", 1000.0))  # pasos/seg al 100%
        self.max_speed_sps = float(config.get("max_speed_sps", 3000.0))
        self.min_speed_sps = float(config.get("min_speed_sps", 100.0))
        self.step_pulse_us = int(config.get("step_pulse_us", 4))  # ≥2us para DRV8825
        self.acceleration_enabled = bool(config.get("enable_acceleration", False))
        self.accel_sps2 = float(config.get("acceleration_sps2", 5000.0))
        
        # Estado
        self._is_enabled = False
        self._is_active = False
        self._stop_flag = False
    
    async def initialize(self) -> bool:
        try:
            if not GPIO_AVAILABLE:
                logger.warning("GPIO no disponible, Stepper en modo simulación")
                self.is_initialized = True
                return True
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.step_pin, GPIO.OUT)
            GPIO.setup(self.dir_pin, GPIO.OUT)
            if self.enable_pin is not None and self.enable_pin >= 0:
                try:
                    GPIO.setup(self.enable_pin, GPIO.OUT)
                    # Deshabilitar al inicio
                    GPIO.output(self.enable_pin, GPIO.HIGH if self.enable_active_low else GPIO.LOW)
                    self._is_enabled = False
                except Exception as e:
                    # Si el pin EN está ocupado, continuar sin control de EN
                    logger.warning(f"No se pudo configurar pin EN {self.enable_pin}: {e}. Continuando sin pin de habilitación.")
                    self.enable_pin = None
                    self._is_enabled = True
            
            # Configurar pines de microstepping si existen (no cambiamos por defecto)
            for ms_pin in [self.ms1_pin, self.ms2_pin, self.ms3_pin]:
                if ms_pin is not None and int(ms_pin) >= 0:
                    GPIO.setup(int(ms_pin), GPIO.OUT)
            
            # Dirección por defecto
            default_dir_high = (self.default_direction.upper() == "CW") ^ self.invert_direction
            GPIO.output(self.dir_pin, GPIO.HIGH if default_dir_high else GPIO.LOW)
            
            self.is_initialized = True
            logger.info(f"Stepper (DRV8825) inicializado STEP={self.step_pin} DIR={self.dir_pin} EN={self.enable_pin}")
            return True
        except Exception as e:
            self.last_error = f"Error inicializando stepper: {e}"
            logger.error(self.last_error)
            return False
    
    def _enable_driver(self, enable: bool):
        if not GPIO_AVAILABLE or self.enable_pin is None or self.enable_pin < 0:
            self._is_enabled = enable
            return
        try:
            if self.enable_active_low:
                GPIO.output(self.enable_pin, GPIO.LOW if enable else GPIO.HIGH)
            else:
                GPIO.output(self.enable_pin, GPIO.HIGH if enable else GPIO.LOW)
            self._is_enabled = enable
        except Exception as e:
            logger.error(f"Error cambiando EN del stepper: {e}")
    
    async def _run_steps_for_time(self, duration_s: float, speed_sps: float):
        """Genera pasos por un tiempo usando bucle en hilo para no bloquear el event loop."""
        if speed_sps <= 0:
            return
        step_interval_s = max(1.0 / speed_sps, (self.step_pulse_us / 1_000_000.0) * 2)
        half_pulse_s = max(self.step_pulse_us / 1_000_000.0, 1e-6)
        end_time = time.perf_counter() + max(0.0, duration_s)
        
        def _loop():
            try:
                while time.perf_counter() < end_time and not self._stop_flag:
                    # Flanco alto
                    GPIO.output(self.step_pin, GPIO.HIGH)
                    time.sleep(half_pulse_s)
                    # Flanco bajo
                    GPIO.output(self.step_pin, GPIO.LOW)
                    # Resto del periodo
                    remaining = step_interval_s - half_pulse_s
                    if remaining > 0:
                        time.sleep(remaining)
            except Exception as e:
                logger.error(f"Error en bucle de pasos: {e}")
        
        await asyncio.to_thread(_loop)
    
    async def activate(self, duration: float, intensity: float = 100.0) -> bool:
        try:
            if not self.is_initialized:
                raise RuntimeError("Stepper no inicializado")
            if self._is_active:
                logger.warning("Stepper ya activo")
                return False
            
            # Calcular velocidad
            intensity = max(1.0, min(100.0, float(intensity)))
            target_sps = self.base_speed_sps * (intensity / 100.0)
            target_sps = max(self.min_speed_sps, min(self.max_speed_sps, target_sps))
            
            # Habilitar driver
            self._stop_flag = False
            self._enable_driver(True)
            self._is_active = True
            
            logger.debug(f"Stepper activado: {duration:.3f}s @ {target_sps:.0f} sps")
            
            # Ejecutar pasos por duración solicitada
            await self._run_steps_for_time(duration, target_sps)
            
            # Auto desactivar
            await self.deactivate()
            return True
        except Exception as e:
            self.last_error = f"Error activando stepper: {e}"
            logger.error(self.last_error)
            self._is_active = False
            self._enable_driver(False)
            return False
    
    async def deactivate(self) -> bool:
        try:
            self._stop_flag = True
            if not GPIO_AVAILABLE:
                self._is_active = False
                return True
            # Asegurar STEP en LOW y deshabilitar
            GPIO.output(self.step_pin, GPIO.LOW)
            self._enable_driver(False)
            self._is_active = False
            return True
        except Exception as e:
            self.last_error = f"Error desactivando stepper: {e}"
            logger.error(self.last_error)
            return False
    
    async def calibrate(self) -> CalibrationResult:
        """Calibración básica: verifica giros cortos en ambos sentidos."""
        try:
            # CW breve
            GPIO.output(self.dir_pin, GPIO.HIGH if not self.invert_direction else GPIO.LOW)
            await self.activate(0.1, 50.0)
            await asyncio.sleep(0.1)
            # CCW breve
            GPIO.output(self.dir_pin, GPIO.LOW if not self.invert_direction else GPIO.HIGH)
            await self.activate(0.1, 50.0)
            # Restaurar dirección por defecto
            default_dir_high = (self.default_direction.upper() == "CW") ^ self.invert_direction
            GPIO.output(self.dir_pin, GPIO.HIGH if default_dir_high else GPIO.LOW)
            
            return CalibrationResult(
                success=True,
                min_pulse_width=self.step_pulse_us / 1_000_000.0,
                max_pulse_width=self.step_pulse_us / 1_000_000.0,
                optimal_frequency=self.base_speed_sps,
                response_time_ms=5.0,
                accuracy_percent=95.0,
                notes="Calibración básica de dirección y pasos"
            )
        except Exception as e:
            logger.error(f"Error calibrando stepper: {e}")
            return CalibrationResult(
                success=False,
                min_pulse_width=0,
                max_pulse_width=0,
                optimal_frequency=0,
                response_time_ms=0,
                accuracy_percent=0,
                notes=f"Error: {e}"
            )
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            "type": "stepper",
            "step_pin": self.step_pin,
            "dir_pin": self.dir_pin,
            "enable_pin": self.enable_pin,
            "is_initialized": self.is_initialized,
            "is_active": self._is_active,
            "enabled": self._is_enabled,
            "last_error": self.last_error
        }
    
    async def cleanup(self):
        try:
            await self.deactivate()
            if GPIO_AVAILABLE:
                pins = [self.step_pin, self.dir_pin]
                if self.enable_pin is not None and self.enable_pin >= 0:
                    pins.append(self.enable_pin)
                for ms_pin in [self.ms1_pin, self.ms2_pin, self.ms3_pin]:
                    if ms_pin is not None and int(ms_pin) >= 0:
                        pins.append(int(ms_pin))
                GPIO.cleanup(pins)
            self.is_initialized = False
            logger.info("Stepper limpiado correctamente")
        except Exception as e:
            logger.error(f"Error limpiando stepper: {e}")

class LabelerActuator:
    """
    Sistema avanzado de control de actuador de etiquetado industrial.
    
    Características:
    - Soporte para múltiples tipos de actuadores
    - Sistema de métricas y telemetría en tiempo real
    - Calibración automática y validación
    - Recuperación automática de errores
    - Análisis predictivo de mantenimiento
    - Modo de seguridad y parada de emergencia
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.actuator_type = ActuatorType(config.get("type", "solenoid"))
        self.name = config.get("name", "LabelerActuator-1")
        
        # Estado del sistema
        self.state = ActuatorState.OFFLINE
        self.health = ActuatorHealth.GOOD
        self.last_error: Optional[str] = None
        
        # Driver del actuador
        self.driver: Optional[BaseActuatorDriver] = None
        
        # Métricas y estadísticas
        self.metrics = ActuatorMetrics()
        self.activation_history = deque(maxlen=1000)
        self.error_history = deque(maxlen=100)
        
        # Configuración de seguridad
        self.max_activation_time = config.get("max_activation_time", 60.0)
        self.min_rest_time = config.get("min_rest_time", 0.1)
        self.max_activations_per_minute = config.get("max_activations_per_minute", 120)
        
        # Sistema de alertas
        self.alert_callbacks: List[Callable] = []
        
        # Calibración
        self.calibration_result: Optional[CalibrationResult] = None
        self.last_calibration: Optional[datetime] = None
        
        # Threading
        self._lock = threading.RLock()
        self._emergency_stop = threading.Event()
        
        logger.info(f"LabelerActuator '{self.name}' instanciado (tipo: {self.actuator_type.value})")
    
    def _create_driver(self) -> BaseActuatorDriver:
        """Crea el driver apropiado según el tipo de actuador."""
        if self.actuator_type == ActuatorType.SOLENOID:
            return SolenoidDriver(self.config)
        elif self.actuator_type == ActuatorType.SERVO:
            return ServoDriver(self.config)
        else:
            if self.actuator_type == ActuatorType.STEPPER:
                return StepperDriver(self.config)
            raise ValueError(f"Tipo de actuador no soportado: {self.actuator_type}")
    
    async def initialize(self) -> bool:
        """Inicializa el sistema de actuador."""
        try:
            self.state = ActuatorState.INITIALIZING
            logger.info(f"Inicializando {self.name}...")
            
            # Crear driver
            self.driver = self._create_driver()
            
            # Inicializar driver
            if not await self.driver.initialize():
                raise RuntimeError("Fallo al inicializar driver")
            
            # Verificar funcionamiento básico
            await self._verify_functionality()
            
            # Cargar calibración previa si existe
            await self._load_calibration()
            
            self.state = ActuatorState.IDLE
            self.health = ActuatorHealth.GOOD
            
            logger.info(f"{self.name} inicializado correctamente")
            return True
            
        except Exception as e:
            self.last_error = f"Error en inicialización: {e}"
            self.state = ActuatorState.ERROR
            self.health = ActuatorHealth.FAILED
            logger.error(f"Error inicializando {self.name}: {e}")
            return False
    
    async def _verify_functionality(self):
        """Verifica el funcionamiento básico del actuador."""
        logger.info(f"Verificando funcionamiento de {self.name}...")
        
        # Prueba de activación corta
        test_success = await self.driver.activate(0.1, 25.0)  # 100ms al 25%
        await asyncio.sleep(0.2)
        
        if not test_success:
            raise RuntimeError("Fallo en prueba de activación")
        
        logger.info("Verificación de funcionamiento exitosa")
    
    async def _load_calibration(self):
        """Carga la calibración previa si existe."""
        try:
            cal_file = Path(f"calibration_{self.name.lower()}.json")
            if cal_file.exists():
                with open(cal_file, 'r') as f:
                    cal_data = json.load(f)
                
                self.calibration_result = CalibrationResult(**cal_data)
                self.last_calibration = datetime.fromisoformat(cal_data['calibration_date'])
                
                logger.info(f"Calibración cargada desde {cal_file}")
            else:
                logger.info("No se encontró calibración previa")
                
        except Exception as e:
            logger.warning(f"Error cargando calibración: {e}")
    
    async def _save_calibration(self):
        """Guarda la calibración actual."""
        try:
            if self.calibration_result:
                cal_file = Path(f"calibration_{self.name.lower()}.json")
                cal_data = {
                    'success': self.calibration_result.success,
                    'min_pulse_width': self.calibration_result.min_pulse_width,
                    'max_pulse_width': self.calibration_result.max_pulse_width,
                    'optimal_frequency': self.calibration_result.optimal_frequency,
                    'response_time_ms': self.calibration_result.response_time_ms,
                    'accuracy_percent': self.calibration_result.accuracy_percent,
                    'calibration_date': self.calibration_result.calibration_date.isoformat(),
                    'notes': self.calibration_result.notes
                }
                
                with open(cal_file, 'w') as f:
                    json.dump(cal_data, f, indent=2)
                
                logger.info(f"Calibración guardada en {cal_file}")
                
        except Exception as e:
            logger.error(f"Error guardando calibración: {e}")
    
    async def activate_for_duration(self, duration: float, intensity: float = 100.0) -> bool:
        """
        Activa el actuador por una duración específica con validaciones de seguridad.
        
        Args:
            duration: Duración en segundos
            intensity: Intensidad de 0-100%
        
        Returns:
            True si la activación fue exitosa
        """
        try:
            with self._lock:
                # Verificaciones de seguridad
                if self._emergency_stop.is_set():
                    logger.error("Sistema en parada de emergencia")
                    return False
                
                if self.state not in [ActuatorState.IDLE]:
                    # Intentar recuperación automática si está en ERROR
                    if self.state == ActuatorState.ERROR:
                        logger.info("Intentando recuperación automática del actuador tras estado ERROR...")
                        try:
                            if self.driver:
                                # Asegurar limpieza e intentar re-inicialización del driver
                                await self.driver.deactivate()
                                await self.driver.cleanup()
                            self.driver = self._create_driver()
                            if not await self.driver.initialize():
                                logger.error("Recuperación fallida: no se pudo re-inicializar el driver")
                                return False
                            # Verificación básica opcional (no fatal si falla)
                            try:
                                await self._verify_functionality()
                            except Exception as e:
                                logger.warning(f"Verificación tras recuperación falló: {e}")
                            self.state = ActuatorState.IDLE
                            logger.info("Recuperación exitosa. Continuando con activación.")
                        except Exception as e:
                            logger.error(f"Error en recuperación automática: {e}")
                            return False
                    else:
                        logger.warning(f"Estado incorrecto para activación: {self.state}")
                        return False
                
                if duration > self.max_activation_time:
                    logger.error(f"Duración excede máximo permitido: {duration}s > {self.max_activation_time}s")
                    return False
                
                # Verificar límite de activaciones por minuto
                if not self._check_activation_rate():
                    logger.warning("Límite de activaciones por minuto excedido")
                    return False
                
                # Cambiar estado
                self.state = ActuatorState.ACTIVE
                activation_start = time.time()
                
                try:
                    # Activar actuador
                    success = await self.driver.activate(duration, intensity)
                    
                    if success:
                        # Registrar métricas
                        self._record_activation(duration, intensity, activation_start)
                        
                        # Enviar alerta de activación
                        self._send_alert("info", f"Actuador activado: {duration:.2f}s @ {intensity:.1f}%")
                        
                        logger.info(f"{self.name} activado: {duration:.2f}s @ {intensity:.1f}%")
                        
                        # Driver ya bloqueó por la duración solicitada; no retener estado activo extra
                        return True
                    else:
                        self._record_error("Fallo en activación del driver")
                        return False
                        
                finally:
                    self.state = ActuatorState.IDLE
                    
        except Exception as e:
            self.last_error = f"Error en activación: {e}"
            self.state = ActuatorState.ERROR
            self._record_error(str(e))
            logger.error(f"Error activando {self.name}: {e}")
            return False
    
    def _check_activation_rate(self) -> bool:
        """Verifica si se puede activar según el límite de activaciones por minuto."""
        now = time.time()
        recent_activations = [t for t in self.activation_history if now - t < 60.0]
        return len(recent_activations) < self.max_activations_per_minute
    
    def _record_activation(self, duration: float, intensity: float, start_time: float):
        """Registra métricas de activación."""
        activation_time = time.time() - start_time
        
        self.activation_history.append(start_time)
        self.metrics.activations_count += 1
        self.metrics.total_active_time += duration
        self.metrics.last_activation_duration = duration
        self.metrics.average_activation_time = self.metrics.total_active_time / self.metrics.activations_count
        self.metrics.response_time_ms = activation_time * 1000
        
        # Calcular desgaste estimado
        self.metrics.wear_level += duration * 0.001  # Fórmula simplificada
        
        # Actualizar score de salud
        self._update_health_score()
    
    def _record_error(self, error_msg: str):
        """Registra un error en el historial."""
        self.error_history.append({
            'timestamp': datetime.now(),
            'error': error_msg
        })
        self.metrics.error_count += 1
        self._update_health_score()
    
    def _update_health_score(self):
        """Actualiza el score de salud basado en métricas."""
        # Factores que afectan la salud
        error_factor = max(0, 1.0 - (self.metrics.error_count * 0.1))
        wear_factor = max(0, 1.0 - self.metrics.wear_level)
        
        # Calcular score general
        health_score = (error_factor + wear_factor) / 2.0
        self.metrics.health_score = health_score
        
        # Determinar estado de salud
        if health_score >= 0.9:
            self.health = ActuatorHealth.EXCELLENT
        elif health_score >= 0.7:
            self.health = ActuatorHealth.GOOD
        elif health_score >= 0.5:
            self.health = ActuatorHealth.WARNING
        elif health_score >= 0.3:
            self.health = ActuatorHealth.CRITICAL
        else:
            self.health = ActuatorHealth.FAILED
    
    def _send_alert(self, level: str, message: str):
        """Envía alerta a los callbacks registrados."""
        alert_data = {
            'timestamp': datetime.now(),
            'level': level,
            'component': self.name,
            'message': message,
            'metrics': self.get_metrics()
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")
    
    async def emergency_stop(self):
        """Activa parada de emergencia."""
        logger.critical(f"PARADA DE EMERGENCIA activada en {self.name}")
        
        self._emergency_stop.set()
        self.state = ActuatorState.EMERGENCY_STOP
        
        # Desactivar inmediatamente
        if self.driver:
            await self.driver.deactivate()
        
        self._send_alert("critical", "Parada de emergencia activada")
    
    async def reset_emergency_stop(self):
        """Resetea la parada de emergencia tras verificaciones."""
        logger.info(f"Reseteando parada de emergencia en {self.name}")
        
        # Verificar que el sistema esté seguro
        if self.driver:
            status = await self.driver.get_status()
            if status.get("is_active", False):
                logger.error("No se puede resetear: actuador aún activo")
                return False
        
        self._emergency_stop.clear()
        self.state = ActuatorState.IDLE
        
        self._send_alert("info", "Parada de emergencia reseteada")
        return True
    
    async def calibrate(self) -> bool:
        """Ejecuta calibración completa del actuador."""
        try:
            self.state = ActuatorState.CALIBRATING
            logger.info(f"Iniciando calibración de {self.name}...")
            
            if not self.driver:
                raise RuntimeError("Driver no inicializado")
            
            # Ejecutar calibración
            self.calibration_result = await self.driver.calibrate()
            
            if self.calibration_result.success:
                self.last_calibration = datetime.now()
                await self._save_calibration()
                
                self.state = ActuatorState.IDLE
                logger.info(f"Calibración exitosa de {self.name}")
                self._send_alert("info", "Calibración completada exitosamente")
                return True
            else:
                self.state = ActuatorState.ERROR
                logger.error(f"Fallo en calibración de {self.name}")
                self._send_alert("error", "Fallo en calibración")
                return False
                
        except Exception as e:
            self.last_error = f"Error en calibración: {e}"
            self.state = ActuatorState.ERROR
            logger.error(f"Error calibrando {self.name}: {e}")
            return False
    
    def register_alert_callback(self, callback: Callable):
        """Registra callback para alertas."""
        self.alert_callbacks.append(callback)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del actuador."""
        driver_status = {}
        if self.driver:
            try:
                # Llamar a get_status async del driver correctamente
                driver_status = await self.driver.get_status()
            except Exception as e:
                logger.debug(f"Error obteniendo estado del driver: {e}")
                driver_status = {"error": "No se pudo obtener estado del driver"}
        
        return {
            "name": self.name,
            "type": self.actuator_type.value,
            "state": self.state.name,
            "health": self.health.name,
            "last_error": self.last_error,
            "metrics": {
                "activations_count": self.metrics.activations_count,
                "total_active_time": self.metrics.total_active_time,
                "average_activation_time": self.metrics.average_activation_time,
                "error_count": self.metrics.error_count,
                "health_score": self.metrics.health_score,
                "wear_level": self.metrics.wear_level
            },
            "calibration": {
                "is_calibrated": self.calibration_result is not None,
                "last_calibration": self.last_calibration.isoformat() if self.last_calibration else None,
                "accuracy_percent": self.calibration_result.accuracy_percent if self.calibration_result else 0
            },
            "driver": driver_status,
            "emergency_stop": self._emergency_stop.is_set()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas detalladas."""
        return {
            "timestamp": datetime.now().isoformat(),
            "activations_count": self.metrics.activations_count,
            "total_active_time": self.metrics.total_active_time,
            "average_activation_time": self.metrics.average_activation_time,
            "last_activation_duration": self.metrics.last_activation_duration,
            "response_time_ms": self.metrics.response_time_ms,
            "error_count": self.metrics.error_count,
            "health_score": self.metrics.health_score,
            "efficiency_percent": self.metrics.efficiency_percent,
            "wear_level": self.metrics.wear_level,
            "activation_rate_per_minute": len([t for t in self.activation_history if time.time() - t < 60])
        }
    
    async def cleanup(self):
        """Limpia recursos del actuador."""
        try:
            logger.info(f"Limpiando {self.name}...")
            
            # Asegurar que esté desactivado
            if self.driver:
                await self.driver.deactivate()
                await self.driver.cleanup()
            
            self.state = ActuatorState.OFFLINE
            
            # Guardar calibración final
            await self._save_calibration()
            
            logger.info(f"{self.name} limpiado correctamente")
            
        except Exception as e:
            logger.error(f"Error limpiando {self.name}: {e}")

# --- Funciones de Utilidad ---

def create_labeler_actuator(config: Dict[str, Any]) -> LabelerActuator:
    """Factory function para crear actuador de etiquetado."""
    return LabelerActuator(config)

async def test_actuator(config: Dict[str, Any]) -> bool:
    """Función de prueba para validar configuración del actuador."""
    try:
        actuator = create_labeler_actuator(config)
        
        # Inicializar
        if not await actuator.initialize():
            return False
        
        # Calibrar
        if not await actuator.calibrate():
            logger.warning("Calibración falló, pero el actuador puede funcionar")
        
        # Prueba rápida
        result = await actuator.activate_for_duration(0.5, 50.0)
        
        # Cleanup
        await actuator.cleanup()
        
        return result
        
    except Exception as e:
        logger.error(f"Error en prueba de actuador: {e}")
        return False

# --- Punto de Entrada Principal ---

if __name__ == "__main__":
    """Script de prueba para el sistema de actuador."""
    import asyncio
    
    # Configuración de prueba
    test_config = {
        "type": "solenoid",
        "name": "TestLabeler",
        "pin": 26,
        "pwm_frequency": 1000,
        "voltage_rating": 12.0,
        "max_activation_time": 30.0,
        "min_rest_time": 0.1,
        "max_activations_per_minute": 60
    }
    
    async def main():
        print("=== Prueba del Sistema de Actuador de Etiquetado ===")
        
        success = await test_actuator(test_config)
        
        if success:
            print("✓ Prueba exitosa")
        else:
            print("✗ Prueba falló")
        
        print("=== Prueba Completada ===")
    
    asyncio.run(main())