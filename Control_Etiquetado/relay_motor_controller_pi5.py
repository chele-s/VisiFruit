# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# relay_motor_controller_pi5.py - Driver para Motor DC con Relays - Raspberry Pi 5
#
# Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez  
# Fecha: Julio 2025
# Versión: 2.0 - Pi5 Compatible
# Descripción:
#   Driver especializado para control de motor DC usando 2 relays de 12V
#   Compatible con Raspberry Pi 5 usando lgpio.
#   Soporta control bidireccional (adelante/atrás) y parada.
# -----------------------------------------------------------------------------

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    import lgpio
    LGPIO_AVAILABLE = True
except ImportError:
    LGPIO_AVAILABLE = False

# Importar clase base si está disponible
try:
    from .conveyor_belt_controller import BeltDriver, BeltConfiguration
    BASE_AVAILABLE = True
except ImportError:
    # Clase base mínima para funcionamiento independiente
    from abc import ABC, abstractmethod
    
    @dataclass
    class BeltConfiguration:
        relay1_pin_bcm: Optional[int] = None
        relay2_pin_bcm: Optional[int] = None
        enable_pin_bcm: Optional[int] = None
        active_state_on: str = "LOW"  # Los relays generalmente se activan con LOW
        safety_timeout_s: float = 10.0
        recovery_attempts: int = 3
        
    class BeltDriver(ABC):
        def __init__(self, config: BeltConfiguration):
            self.config = config
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            self._initialized = False
    
    BASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class RelayDirection:
    """Direcciones del motor con relays."""
    FORWARD = "forward"
    BACKWARD = "backward" 
    STOP = "stop"
    BRAKE = "brake"

class RelayMotorDriverPi5(BeltDriver):
    """
    Driver especializado para motor DC con 2 relays de 12V - Raspberry Pi 5.
    
    Esquema de control:
    - Relay 1: Control dirección adelante
    - Relay 2: Control dirección atrás
    - Ambos OFF: Motor parado
    - Solo Relay 1 ON: Motor adelante
    - Solo Relay 2 ON: Motor atrás
    - Ambos ON: PROHIBIDO (cortocircuito)
    """
    
    def __init__(self, config: BeltConfiguration):
        super().__init__(config)
        self.current_direction = RelayDirection.STOP
        self.motor_running = False
        self.safety_timer = None
        self._direction_change_delay = 0.5  # Delay entre cambios de dirección
        self._last_direction_change = 0
        self._gpio_handle = None
        
    async def initialize(self) -> bool:
        """Inicializar control con relays usando lgpio."""
        try:
            if not LGPIO_AVAILABLE:
                self.logger.warning("lgpio no disponible - Modo simulación activado")
                self._initialized = True
                return True
                
            # Validar configuración
            if self.config.relay1_pin_bcm is None:
                raise ValueError("relay1_pin_bcm no especificado para control con relays")
            if self.config.relay2_pin_bcm is None:
                raise ValueError("relay2_pin_bcm no especificado para control con relays")
                
            # Abrir chip GPIO
            self._gpio_handle = lgpio.gpiochip_open(0)
            if self._gpio_handle < 0:
                raise RuntimeError(f"No se pudo abrir el chip GPIO: {self._gpio_handle}")
            
            # Configurar Relay 1 (Adelante) - especificar nivel inicial inactivo
            inactive_level = 1 if self.config.active_state_on == "LOW" else 0
            result = lgpio.gpio_claim_output(self._gpio_handle, self.config.relay1_pin_bcm, inactive_level)
            if result < 0:
                raise RuntimeError(f"Error configurando relay 1 GPIO {self.config.relay1_pin_bcm}: {result}")
            
            # Configurar Relay 2 (Atrás) - especificar nivel inicial inactivo
            result = lgpio.gpio_claim_output(self._gpio_handle, self.config.relay2_pin_bcm, inactive_level)
            if result < 0:
                raise RuntimeError(f"Error configurando relay 2 GPIO {self.config.relay2_pin_bcm}: {result}")
            
            # Configurar pin de habilitación si existe
            if self.config.enable_pin_bcm is not None:
                result = lgpio.gpio_claim_output(self._gpio_handle, self.config.enable_pin_bcm, 0)
                if result < 0:
                    raise RuntimeError(f"Error configurando enable GPIO {self.config.enable_pin_bcm}: {result}")
                # Deshabilitar inicialmente
                lgpio.gpio_write(self._gpio_handle, self.config.enable_pin_bcm, 0)
            
            # Establecer estado inicial (relays desactivados)
            inactive_level = 1 if self.config.active_state_on == "LOW" else 0
            lgpio.gpio_write(self._gpio_handle, self.config.relay1_pin_bcm, inactive_level)
            lgpio.gpio_write(self._gpio_handle, self.config.relay2_pin_bcm, inactive_level)
                
            self.current_direction = RelayDirection.STOP
            self.motor_running = False
            self._initialized = True
            
            self.logger.info(f"Driver de Relays Pi5 inicializado:")
            self.logger.info(f"  - Relay 1 (Adelante): GPIO {self.config.relay1_pin_bcm}")
            self.logger.info(f"  - Relay 2 (Atrás): GPIO {self.config.relay2_pin_bcm}")
            if self.config.enable_pin_bcm:
                self.logger.info(f"  - Enable: GPIO {self.config.enable_pin_bcm}")
            self.logger.info(f"  - Estado activo: {self.config.active_state_on}")
            self.logger.info(f"  - GPIO handle: {self._gpio_handle}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando driver de relays Pi5: {e}")
            if self._gpio_handle is not None and self._gpio_handle >= 0:
                try:
                    lgpio.gpiochip_close(self._gpio_handle)
                except:
                    pass
                self._gpio_handle = None
            return False
    
    async def _set_relay_direction(self, direction: str) -> bool:
        """
        Establecer dirección del motor controlando los relays.
        
        IMPORTANTE: Nunca activar ambos relays simultáneamente para evitar cortocircuito.
        """
        try:
            if not self._initialized:
                raise RuntimeError("Driver de relays no inicializado")
            
            # Verificar tiempo mínimo entre cambios de dirección
            current_time = time.time()
            if current_time - self._last_direction_change < self._direction_change_delay:
                await asyncio.sleep(self._direction_change_delay)
            
            # Primero, desactivar ambos relays (estado seguro)
            await self._deactivate_all_relays()
            await asyncio.sleep(0.1)  # Pausa de seguridad
            
            if not LGPIO_AVAILABLE:
                # Modo simulación
                self.current_direction = direction
                self.logger.info(f"[SIMULACIÓN] Dirección establecida: {direction}")
                return True
            
            # Calcular niveles de activación
            active_level = 0 if self.config.active_state_on == "LOW" else 1
            inactive_level = 1 if self.config.active_state_on == "LOW" else 0
            
            # Habilitar sistema si hay pin enable
            if self.config.enable_pin_bcm is not None:
                lgpio.gpio_write(self._gpio_handle, self.config.enable_pin_bcm, 1)
            
            # Configurar relays según dirección
            if direction == RelayDirection.FORWARD:
                lgpio.gpio_write(self._gpio_handle, self.config.relay1_pin_bcm, active_level)    # Relay 1 ON
                lgpio.gpio_write(self._gpio_handle, self.config.relay2_pin_bcm, inactive_level)  # Relay 2 OFF
                self.motor_running = True
                
            elif direction == RelayDirection.BACKWARD:
                lgpio.gpio_write(self._gpio_handle, self.config.relay1_pin_bcm, inactive_level)  # Relay 1 OFF
                lgpio.gpio_write(self._gpio_handle, self.config.relay2_pin_bcm, active_level)    # Relay 2 ON
                self.motor_running = True
                
            elif direction == RelayDirection.STOP:
                lgpio.gpio_write(self._gpio_handle, self.config.relay1_pin_bcm, inactive_level)  # Relay 1 OFF
                lgpio.gpio_write(self._gpio_handle, self.config.relay2_pin_bcm, inactive_level)  # Relay 2 OFF
                self.motor_running = False
                
            elif direction == RelayDirection.BRAKE:
                # Para frenado, primero parar y luego aplicar frenado dinámico si es posible
                lgpio.gpio_write(self._gpio_handle, self.config.relay1_pin_bcm, inactive_level)  # Relay 1 OFF
                lgpio.gpio_write(self._gpio_handle, self.config.relay2_pin_bcm, inactive_level)  # Relay 2 OFF
                self.motor_running = False
                
            else:
                raise ValueError(f"Dirección no válida: {direction}")
            
            self.current_direction = direction
            self._last_direction_change = time.time()
            
            self.logger.debug(f"Relays configurados para: {direction}")
            self.logger.debug(f"  - Relay 1: {'ON' if direction == RelayDirection.FORWARD else 'OFF'}")
            self.logger.debug(f"  - Relay 2: {'ON' if direction == RelayDirection.BACKWARD else 'OFF'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error estableciendo dirección con relays: {e}")
            # En caso de error, ir a estado seguro
            await self._emergency_stop_relays()
            return False
    
    async def _deactivate_all_relays(self):
        """Desactivar todos los relays (estado seguro)."""
        if not LGPIO_AVAILABLE or self._gpio_handle is None:
            return
            
        try:
            inactive_level = 1 if self.config.active_state_on == "LOW" else 0
            lgpio.gpio_write(self._gpio_handle, self.config.relay1_pin_bcm, inactive_level)
            lgpio.gpio_write(self._gpio_handle, self.config.relay2_pin_bcm, inactive_level)
            
            # Deshabilitar sistema si hay pin enable
            if self.config.enable_pin_bcm is not None:
                lgpio.gpio_write(self._gpio_handle, self.config.enable_pin_bcm, 0)
                
        except Exception as e:
            self.logger.error(f"Error desactivando relays: {e}")
    
    async def _emergency_stop_relays(self):
        """Parada de emergencia inmediata."""
        try:
            await self._deactivate_all_relays()
            self.motor_running = False
            self.current_direction = RelayDirection.STOP
            self.logger.warning("Parada de emergencia de relays ejecutada")
        except Exception as e:
            self.logger.error(f"Error en parada de emergencia de relays: {e}")
    
    async def start_belt(self, speed_percent: float = None) -> bool:
        """Iniciar motor hacia adelante."""
        try:
            if not self._initialized:
                raise RuntimeError("Driver de relays no inicializado")
            
            # Los relays no soportan control de velocidad variable
            if speed_percent is not None and speed_percent != 100:
                self.logger.warning("Control de velocidad no disponible con relays - usando velocidad completa")
            
            success = await self._set_relay_direction(RelayDirection.FORWARD)
            
            if success:
                # Configurar timeout de seguridad
                if self.safety_timer:
                    self.safety_timer.cancel()
                
                if self.config.safety_timeout_s > 0:
                    self.safety_timer = asyncio.create_task(self._safety_timeout())
                
                self.logger.info("Motor iniciado hacia adelante con relays Pi5")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error iniciando motor con relays Pi5: {e}")
            return False
    
    async def stop_belt(self) -> bool:
        """Detener motor."""
        try:
            if self.safety_timer:
                self.safety_timer.cancel()
                self.safety_timer = None
            
            success = await self._set_relay_direction(RelayDirection.STOP)
            
            if success:
                self.logger.info("Motor detenido con relays Pi5")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deteniendo motor con relays Pi5: {e}")
            return False
    
    async def reverse_direction(self) -> bool:
        """Cambiar a dirección reversa."""
        try:
            if not self._initialized:
                raise RuntimeError("Driver de relays no inicializado")
            
            success = await self._set_relay_direction(RelayDirection.BACKWARD)
            
            if success:
                # Configurar timeout de seguridad
                if self.safety_timer:
                    self.safety_timer.cancel()
                
                if self.config.safety_timeout_s > 0:
                    self.safety_timer = asyncio.create_task(self._safety_timeout())
                
                self.logger.info("Motor cambiado a dirección reversa con relays Pi5")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error cambiando a reversa con relays Pi5: {e}")
            return False
    
    async def emergency_brake(self) -> bool:
        """Frenado de emergencia."""
        try:
            if self.safety_timer:
                self.safety_timer.cancel()
                self.safety_timer = None
            
            # Con relays, el frenado es simplemente parar el motor
            success = await self._set_relay_direction(RelayDirection.BRAKE)
            
            if success:
                self.logger.warning("Frenado de emergencia con relays Pi5 ejecutado")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error en frenado de emergencia con relays Pi5: {e}")
            return False
    
    async def _safety_timeout(self):
        """Timeout de seguridad para auto-parada."""
        try:
            await asyncio.sleep(self.config.safety_timeout_s)
            self.logger.warning(f"Timeout de seguridad alcanzado ({self.config.safety_timeout_s}s) - deteniendo motor")
            await self.stop_belt()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error en timeout de seguridad: {e}")
    
    async def set_speed(self, speed_percent: float) -> bool:
        """Control de velocidad (no aplicable para relays)."""
        self.logger.warning("Control de velocidad no disponible con relays - motor funciona a velocidad completa")
        return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del driver de relays Pi5."""
        try:
            if not self._initialized:
                return {"initialized": False, "running": False}
            
            return {
                "initialized": True,
                "running": self.motor_running,
                "direction": self.current_direction,
                "speed_percent": 100.0 if self.motor_running else 0.0,
                "control_type": "relay_motor_pi5",
                "safety_timeout_active": self.safety_timer is not None and not self.safety_timer.done(),
                "gpio_handle": self._gpio_handle,
                "pins": {
                    "relay1_forward": self.config.relay1_pin_bcm,
                    "relay2_backward": self.config.relay2_pin_bcm,
                    "enable": self.config.enable_pin_bcm
                },
                "relay_states": self._get_relay_states()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de relays Pi5: {e}")
            return {"error": str(e)}
    
    def _get_relay_states(self) -> Dict[str, str]:
        """Obtener estado actual de los relays."""
        if not LGPIO_AVAILABLE or not self._initialized or self._gpio_handle is None:
            return {"relay1": "unknown", "relay2": "unknown"}
        
        try:
            active_level = 0 if self.config.active_state_on == "LOW" else 1
            
            relay1_state = lgpio.gpio_read(self._gpio_handle, self.config.relay1_pin_bcm)
            relay2_state = lgpio.gpio_read(self._gpio_handle, self.config.relay2_pin_bcm)
            
            return {
                "relay1": "ON" if relay1_state == active_level else "OFF",
                "relay2": "ON" if relay2_state == active_level else "OFF"
            }
        except Exception as e:
            self.logger.error(f"Error leyendo estado de relays: {e}")
            return {"relay1": "error", "relay2": "error"}
    
    async def cleanup(self) -> None:
        """Limpiar recursos del driver de relays Pi5."""
        try:
            # Cancelar timer de seguridad
            if self.safety_timer:
                self.safety_timer.cancel()
                self.safety_timer = None
            
            # Detener motor
            await self.stop_belt()
            
            # Limpiar GPIO
            if LGPIO_AVAILABLE and self._initialized and self._gpio_handle is not None:
                try:
                    await self._deactivate_all_relays()
                    lgpio.gpiochip_close(self._gpio_handle)
                except Exception as e:
                    self.logger.error(f"Error cerrando GPIO: {e}")
                self._gpio_handle = None
            
            self._initialized = False
            self.motor_running = False
            self.logger.info("Limpieza de relays Pi5 completada")
            
        except Exception as e:
            self.logger.error(f"Error durante limpieza de relays Pi5: {e}")

# Función de compatibilidad para integración fácil
def create_relay_motor_driver_pi5(relay1_pin: int, relay2_pin: int, enable_pin: int = None) -> RelayMotorDriverPi5:
    """
    Crear driver de relays Pi5 con configuración simple.
    
    Args:
        relay1_pin: Pin BCM para relay 1 (adelante)
        relay2_pin: Pin BCM para relay 2 (atrás)
        enable_pin: Pin BCM para habilitación (opcional)
    """
    config = BeltConfiguration(
        relay1_pin_bcm=relay1_pin,
        relay2_pin_bcm=relay2_pin,
        enable_pin_bcm=enable_pin,
        active_state_on="LOW",  # Típico para módulos de relays
        safety_timeout_s=10.0
    )
    
    return RelayMotorDriverPi5(config)

# --- Ejemplo de uso ---
if __name__ == "__main__":
    async def test_relay_driver_pi5():
        """Prueba básica del driver de relays Pi5."""
        logging.basicConfig(level=logging.INFO)
        
        # Crear driver con configuración simple
        driver = create_relay_motor_driver_pi5(
            relay1_pin=18,  # GPIO 18 para relay adelante
            relay2_pin=19,  # GPIO 19 para relay atrás
            enable_pin=26   # GPIO 26 para habilitación
        )
        
        try:
            # Inicializar
            if await driver.initialize():
                print("✓ Driver de relays Pi5 inicializado")
                
                # Probar adelante
                print("\n--- Prueba: Motor adelante ---")
                await driver.start_belt()
                await asyncio.sleep(2)
                
                # Parar
                print("\n--- Prueba: Parar motor ---")
                await driver.stop_belt()
                await asyncio.sleep(1)
                
                # Probar atrás
                print("\n--- Prueba: Motor atrás ---")
                await driver.reverse_direction()
                await asyncio.sleep(2)
                
                # Frenado de emergencia
                print("\n--- Prueba: Frenado emergencia ---")
                await driver.emergency_brake()
                
                # Mostrar estado final
                status = await driver.get_status()
                print(f"\n--- Estado final ---")
                print(f"Estado: {status}")
                
            else:
                print("✗ Error inicializando driver")
                
        except Exception as e:
            print(f"Error en prueba: {e}")
        finally:
            await driver.cleanup()
    
    # Ejecutar prueba
    asyncio.run(test_relay_driver_pi5())



