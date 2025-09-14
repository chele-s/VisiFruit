#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 DEMO SISTEMA COMPLETO - VisiFruit v3.0 RT-DETR
===============================================

Demo interactiva que integra:
- Motor DC banda transportadora (L298N/Relays)
- Driver DRV8825 stepper (real o simulado)
- Sensor digital (MH Flying Fish)
- Control completo por consola

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Enero 2025
Versión: 3.0 - RT-DETR Edition
"""

import asyncio
import inspect
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import os
import subprocess

# Agregar directorio padre para importaciones
sys.path.append(str(Path(__file__).parent.parent))

# Importaciones del sistema VisiFruit
from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, GPIO_MODE, GPIOState, get_gpio_info, is_simulation_mode

try:
    from Control_Etiquetado.sensor_interface import SensorInterface
    from Control_Etiquetado.labeler_actuator import LabelerActuator
    SENSOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Módulos de sensores no disponibles: {e}")
    SENSOR_AVAILABLE = False

try:
    # Intentar controlador Pi5 primero
    from Control_Etiquetado.relay_motor_controller_pi5 import create_relay_motor_driver_pi5
    USE_PI5_DRIVER = True
    BELT_AVAILABLE = True
except ImportError:
    try:
        # Fallback a controlador original
        from Control_Etiquetado.relay_motor_controller import create_relay_motor_driver
        USE_PI5_DRIVER = False
        BELT_AVAILABLE = True
    except ImportError:
        # Fallback final: usar GPIO wrapper directamente
        BELT_AVAILABLE = GPIO_AVAILABLE
        USE_PI5_DRIVER = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class SimpleBeltController:
    """Controlador simple de banda usando GPIO wrapper directamente."""
    
    def __init__(self, relay1_pin=22, relay2_pin=23, enable_pin=27):
        self.relay1_pin = relay1_pin  # Adelante
        self.relay2_pin = relay2_pin  # Atrás  
        self.enable_pin = enable_pin  # Enable (opcional)
        self.initialized = False
        self.current_state = "stopped"
        
        logger.info(f"🎢 SimpleBeltController - Pines: R1={relay1_pin}, R2={relay2_pin}, EN={enable_pin}")
    
    async def initialize(self):
        """Inicializa el controlador."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.relay1_pin, GPIO.OUT)
            GPIO.setup(self.relay2_pin, GPIO.OUT)
            if self.enable_pin:
                GPIO.setup(self.enable_pin, GPIO.OUT)
                GPIO.output(self.enable_pin, GPIO.HIGH)  # Habilitar driver
            
            # Estado inicial: parado
            GPIO.output(self.relay1_pin, GPIO.LOW)
            GPIO.output(self.relay2_pin, GPIO.LOW)
            
            self.initialized = True
            self.current_state = "stopped"
            logger.info("✅ SimpleBeltController inicializado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando SimpleBeltController: {e}")
            return False
    
    async def move_forward(self, duration_seconds=None):
        """Mueve la banda hacia adelante."""
        if not self.initialized:
            return False
            
        try:
            GPIO.output(self.relay2_pin, GPIO.LOW)   # Asegurar que atrás esté apagado
            GPIO.output(self.relay1_pin, GPIO.HIGH)  # Activar adelante
            self.current_state = "forward"
            logger.info("🟢 Banda: ADELANTE")
            
            if duration_seconds:
                await asyncio.sleep(duration_seconds)
                await self.stop()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error moviendo adelante: {e}")
            return False
    
    async def move_backward(self, duration_seconds=None):
        """Mueve la banda hacia atrás."""
        if not self.initialized:
            return False
            
        try:
            GPIO.output(self.relay1_pin, GPIO.LOW)   # Asegurar que adelante esté apagado
            GPIO.output(self.relay2_pin, GPIO.HIGH)  # Activar atrás
            self.current_state = "backward"
            logger.info("🔴 Banda: ATRÁS")
            
            if duration_seconds:
                await asyncio.sleep(duration_seconds)
                await self.stop()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error moviendo atrás: {e}")
            return False
    
    async def stop(self):
        """Detiene la banda."""
        if not self.initialized:
            return False
            
        try:
            GPIO.output(self.relay1_pin, GPIO.LOW)
            GPIO.output(self.relay2_pin, GPIO.LOW)
            self.current_state = "stopped"
            logger.info("⚫ Banda: PARADA")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo banda: {e}")
            return False
    
    def get_status(self):
        """Obtiene el estado actual."""
        return {
            "initialized": self.initialized,
            "state": self.current_state,
            "gpio_mode": GPIO_MODE.value,
            "simulation": is_simulation_mode()
        }
    
    async def cleanup(self):
        """Limpia recursos."""
        try:
            if self.initialized:
                await self.stop()
                GPIO.cleanup([self.relay1_pin, self.relay2_pin, self.enable_pin])
            logger.info("🧹 SimpleBeltController limpiado")
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")

class DemoSistemaCompleto:
    """Demo completa del sistema VisiFruit con todos los componentes."""
    
    def __init__(self):
        self.running = True
        self.demo_active = True
        
        # Componentes del sistema
        self.belt_driver = None
        self.laser_stepper = None
        self.sensor_interface = None
        
        # Estado del sistema
        self.belt_running = False
        self.stepper_enabled = True
        self.laser_monitoring = False
        self.simulation_mode = False
        
        # Configuración por defecto
        self.config = self._load_default_config()

        # Loop de asyncio para programar tareas desde callbacks de hilos GPIO
        self._loop = None
        
        # Estadísticas
        self.stats = {
            'laser_triggers': 0,
            'stepper_activations': 0,
            'belt_starts': 0,
            'start_time': time.time(),
            'stepper_total_active_time_s': 0.0,
            'last_trigger_time': None,
            'last_stepper_activation_time': None
        }
        
        # Control de activación láser
        self.last_laser_activation = 0.0
        self.min_laser_interval = 0.15  # segundos
        self.sensor_to_labeler_delay_s = 0.0
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Carga configuración por defecto."""
        config_path = Path("Config_Etiquetadora.json")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("✅ Configuración cargada desde Config_Etiquetadora.json")
                return config
            except Exception as e:
                logger.warning(f"⚠️ Error cargando configuración: {e}")
        
        # Configuración por defecto
        return {
            "sensor_settings": {
                "trigger_sensor": {
                    "type": "mh_flying_fish",
                    "name": "MH_FlyingFish",
                    "pin_bcm": 4,
                    "trigger_level": "falling",
                    "trigger_on_state": "LOW",
                    "debounce_time_ms": 50,
                    "debounce_s": 0.050,
                    "pull_up_down": "PUD_UP",
                    "response_time_ms": 10,
                    "enable_diagnostics": True
                }
            },
            "laser_stepper_settings": {
                "enabled": True,
                "type": "stepper",
                "name": "LabelApplicatorStepper",
                "step_pin_bcm": 19,
                "dir_pin_bcm": 26,
                "enable_pin_bcm": 21,
                "enable_active_low": True,
                "base_speed_sps": 1500,
                "step_pulse_us": 4,
                "activation_on_laser": {
                    "enabled": True,
                    "activation_duration_seconds": 0.6,
                    "intensity_percent": 80.0,
                    "min_interval_seconds": 0.15
                },
                "sensor_to_labeler_distance_m": 0.05 # Nuevo parámetro
            },
            "conveyor_belt_settings": {
                "relay1_pin": 22,  # Adelante (BCM 22 → físico 15)
                "relay2_pin": 23,  # Atrás   (BCM 23 → físico 16)
                "enable_pin": 27,   # Enable  (BCM 27 → físico 13)
                "belt_speed_mps": 0.15 # Nuevo parámetro
            }
        }
    
    async def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema."""
        print("\n" + "="*70)
        print("🚀 DEMO SISTEMA COMPLETO - VisiFruit v3.0 RT-DETR")
        print("="*70)
        print("🔧 Inicializando componentes del sistema...")
        # Guardar referencia al event loop activo para usarla en callbacks de otros hilos
        try:
            self._loop = asyncio.get_running_loop()
        except Exception:
            self._loop = None

        success = True
        
        # 1. Inicializar banda transportadora
        if BELT_AVAILABLE:
            success &= await self._initialize_belt()
        else:
            print("⚠️ Controlador de banda no disponible - Modo simulación")
            self.simulation_mode = True
        
        # 2. Inicializar stepper DRV8825
        success &= await self._initialize_stepper()
        
        # 3. Inicializar sensor (MH Flying Fish)
        if SENSOR_AVAILABLE:
            success &= await self._initialize_sensor()
        else:
            print("⚠️ Sensor interface no disponible - Modo simulación")
            self.simulation_mode = True
        
        if success:
            print("✅ Sistema inicializado correctamente")
            await self._show_system_status()
        else:
            print("❌ Error en inicialización del sistema")
        
        return success
    
    async def _initialize_belt(self) -> bool:
        """Inicializa el controlador de banda."""
        try:
            belt_config = self.config.get("conveyor_belt_settings", {})
            relay1_pin = belt_config.get("relay1_pin", 22)
            relay2_pin = belt_config.get("relay2_pin", 23)
            enable_pin = belt_config.get("enable_pin", 27)
            
            # Intentar drivers específicos primero
            if USE_PI5_DRIVER and BELT_AVAILABLE:
                try:
                    self.belt_driver = create_relay_motor_driver_pi5(
                        relay1_pin=relay1_pin,
                        relay2_pin=relay2_pin,
                        enable_pin=enable_pin
                    )
                    if await self.belt_driver.initialize():
                        print("✅ Banda: Usando driver Pi5 (lgpio)")
                        return True
                except Exception as e:
                    print(f"⚠️ Driver Pi5 falló: {e}")
                    self.belt_driver = None
            
            if self.belt_driver is None and BELT_AVAILABLE:
                try:
                    self.belt_driver = create_relay_motor_driver(
                        relay1_pin=relay1_pin,
                        relay2_pin=relay2_pin,
                        enable_pin=enable_pin
                    )
                    if await self.belt_driver.initialize():
                        print("⚠️ Banda: Usando driver legacy (RPi.GPIO)")
                        return True
                except Exception as e:
                    print(f"⚠️ Driver legacy falló: {e}")
                    self.belt_driver = None
            
            # Fallback final: GPIO wrapper directo
            if self.belt_driver is None and GPIO_AVAILABLE:
                self.belt_driver = SimpleBeltController(relay1_pin, relay2_pin, enable_pin)
                if await self.belt_driver.initialize():
                    print(f"🔧 Banda: Usando GPIO wrapper ({GPIO_MODE.value})")
                    return True
            
            print("❌ No se pudo inicializar controlador de banda")
            return False
                
        except Exception as e:
            print(f"❌ Error inicializando banda: {e}")
            return False
    
    async def _initialize_stepper(self) -> bool:
        """Inicializa el stepper DRV8825."""
        try:
            stepper_config = self.config.get("laser_stepper_settings", {})
            stepper_config["type"] = "stepper"
            
            self.laser_stepper = LabelerActuator(stepper_config)
            
            if await self.laser_stepper.initialize():
                print("✅ Stepper DRV8825 inicializado")
                try:
                    distance_m = float(self.config.get("laser_stepper_settings", {}).get("sensor_to_labeler_distance_m", 0.0))
                    belt_speed_mps = float(self.config.get("conveyor_belt_settings", {}).get("belt_speed_mps", 0.15))
                    if distance_m > 0 and belt_speed_mps > 0:
                        self.sensor_to_labeler_delay_s = max(0.0, distance_m / belt_speed_mps)
                        print(f"⏱️ Delay sensor→etiquetadora: {self.sensor_to_labeler_delay_s:.3f}s (dist={distance_m:.3f}m, v_banda={belt_speed_mps:.3f}m/s)")
                except Exception:
                    pass
                return True
            else:
                print("⚠️ Stepper DRV8825 en modo simulación")
                return True  # Continuar en modo simulación
                
        except Exception as e:
            print(f"⚠️ Stepper en modo simulación: {e}")
            return True  # Continuar en modo simulación
    
    async def _initialize_sensor(self) -> bool:
        """Inicializa el sensor digital (MH Flying Fish)."""
        try:
            sensor_config = self.config.get("sensor_settings", {})
            self.sensor_interface = SensorInterface(
                trigger_callback=self._laser_trigger_callback
            )
            
            if self.sensor_interface.initialize(sensor_config):
                # Activar monitoreo automáticamente
                try:
                    self.sensor_interface.enable_trigger_monitoring()
                    self.laser_monitoring = True
                    print("✅ Sensor MH Flying Fish inicializado y monitoreo ACTIVO")
                except Exception as e:
                    print(f"⚠️ Sensor inicializado, pero no se pudo habilitar el monitoreo: {e}")
                return True
            else:
                print("⚠️ Sensor en modo simulación")
                return True
                
        except Exception as e:
            print(f"⚠️ Sensor en modo simulación: {e}")
            return True
    
    def _laser_trigger_callback(self):
        """Callback cuando se detecta el sensor (disparo)."""
        try:
            current_time = time.time()
            
            # Control de debounce
            if (current_time - self.last_laser_activation) < self.min_laser_interval:
                return
            
            self.last_laser_activation = current_time
            self.stats['laser_triggers'] += 1
            self.stats['last_trigger_time'] = current_time
            
            print(f"\n🔴 SENSOR DETECTADO #{self.stats['laser_triggers']} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Activar stepper si está habilitado
            if self.stepper_enabled and self.laser_stepper:
                activation_config = self.config.get("laser_stepper_settings", {}).get("activation_on_laser", {})
                duration = activation_config.get("activation_duration_seconds", 0.6)
                intensity = activation_config.get("intensity_percent", 80.0)
                
                # Programar activación asíncrona después del tiempo de viaje
                delay_before = max(0.0, float(self.sensor_to_labeler_delay_s))
                try:
                    if self._loop is not None and self._loop.is_running():
                        # Ejecutar de forma thread‑safe desde el hilo del GPIO
                        self._loop.call_soon_threadsafe(
                            lambda: asyncio.create_task(
                                self._activate_stepper_after_delay(duration, intensity, delay_before)
                            )
                        )
                    else:
                        # Si estamos en el mismo hilo del loop
                        loop = asyncio.get_running_loop()
                        loop.create_task(self._activate_stepper_after_delay(duration, intensity, delay_before))
                except Exception:
                    # Último recurso: crear un hilo dedicado con su propio loop
                    import threading
                    threading.Thread(
                        target=lambda: asyncio.run(
                            self._activate_stepper_after_delay(duration, intensity, delay_before)
                        ),
                        daemon=True
                    ).start()
                
        except Exception as e:
            logger.error(f"Error en callback de sensor: {e}")

    async def _activate_stepper_async(self, duration: float, intensity: float):
        """Activa el stepper de forma asíncrona."""
        try:
            if self.laser_stepper:
                success = await self.laser_stepper.activate_for_duration(duration, intensity)
                if success:
                    self.stats['stepper_activations'] += 1
                    self.stats['stepper_total_active_time_s'] = self.stats.get('stepper_total_active_time_s', 0.0) + float(duration)
                    self.stats['last_stepper_activation_time'] = time.time()
                    print(f"  ✅ Stepper activado: {duration:.2f}s @ {intensity:.0f}%")
                else:
                    print(f"  ❌ Error activando stepper")
            else:
                # Simulación
                print(f"  🎭 SIMULACIÓN: Stepper activado {duration:.2f}s @ {intensity:.0f}%")
                await asyncio.sleep(duration)
                self.stats['stepper_activations'] += 1
                self.stats['stepper_total_active_time_s'] = self.stats.get('stepper_total_active_time_s', 0.0) + float(duration)
                self.stats['last_stepper_activation_time'] = time.time()
                print(f"  ✅ Stepper simulado completado")
                
        except Exception as e:
            print(f"  ❌ Error activando stepper: {e}")

    async def _activate_stepper_after_delay(self, duration: float, intensity: float, delay_s: float):
        """Espera delay_s y luego activa el stepper."""
        try:
            if delay_s > 0:
                await asyncio.sleep(delay_s)
        except Exception:
            pass
        await self._activate_stepper_async(duration, intensity)
    
    async def _show_system_status(self):
        """Muestra el estado actual del sistema."""
        print("\n📊 ESTADO DEL SISTEMA")
        print("-" * 50)
        
        # Información del GPIO wrapper
        gpio_info = get_gpio_info()
        print(f"🔌 GPIO: {gpio_info['mode']} ({'simulado' if is_simulation_mode() else 'hardware'})")
        
        # Estado de componentes
        print(f"🎢 Banda transportadora: {'✅ Activa' if self.belt_running else '⏹️ Parada'}")
        if self.belt_driver and hasattr(self.belt_driver, 'get_status'):
            try:
                status_result = self.belt_driver.get_status()
                belt_info = await status_result if inspect.isawaitable(status_result) else status_result
                if isinstance(belt_info, dict):
                    print(f"   Estado: {'Funcionando' if belt_info.get('running') else 'Parada'}")
            except Exception:
                pass
        
        print(f"🔧 Stepper DRV8825: {'✅ Habilitado' if self.stepper_enabled else '❌ Deshabilitado'}")
        print(f"📡 Monitoreo sensor: {'✅ Activo' if self.laser_monitoring else '⏹️ Inactivo'}")
        print(f"🎭 Modo simulación: {'✅ Activo' if self.simulation_mode else '❌ Hardware real'}")
        if self.sensor_to_labeler_delay_s > 0:
            print(f"⏱️ Delay sensor→etiquetadora: {self.sensor_to_labeler_delay_s:.3f}s")
    
    async def run_interactive_demo(self):
        """Ejecuta la demo interactiva."""
        print("\n" + "="*50)
        print("🎮 DEMO INTERACTIVA - SISTEMA COMPLETO")
        print("="*50)
        
        while self.demo_active:
            await self._show_menu()
            
            try:
                command = input("\n🎯 Comando: ").strip().upper()
                await self._process_command(command)
                
            except KeyboardInterrupt:
                print("\n⚠️ Ctrl+C detectado - Saliendo...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _show_menu(self):
        """Muestra el menú de opciones."""
        print("\n" + "="*60)
        print("🎛️ COMANDOS DISPONIBLES")
        print("="*60)
        
        # Control de banda
        print("🎢 BANDA TRANSPORTADORA:")
        print("  [B1] - Iniciar banda ADELANTE")
        print("  [B2] - Iniciar banda ATRÁS")
        print("  [B0] - PARAR banda")
        
        # Control de stepper
        print("\n🔧 STEPPER DRV8825:")
        print("  [S1] - Activar stepper manualmente")
        print("  [S0] - Toggle habilitación sensor→stepper")
        print("  [SS] - Configurar stepper")
        
        # Control de sensor
        print("\n📡 SENSOR (MH Flying Fish):")
        print("  [L1] - Iniciar monitoreo sensor")
        print("  [L0] - Parar monitoreo sensor")
        print("  [LT] - Simular trigger sensor")
        print("  [LD] - Diagnóstico sensor (lecturas en tiempo real)")
        
        # Sistema
        print("\n🔧 SISTEMA:")
        print("  [I] - Mostrar información")
        print("  [D] - Demo automática")
        print("  [R] - Resetear estadísticas")
        print("  [Q] - Salir")
        
        await self._show_system_status()
    
    async def _process_command(self, command: str):
        """Procesa los comandos del usuario."""
        
        # Control de banda
        if command == "B1":
            await self._belt_forward()
        elif command == "B2":
            await self._belt_backward()
        elif command == "B0":
            await self._belt_stop()
            
        # Control de stepper
        elif command == "S1":
            await self._manual_stepper()
        elif command == "S0":
            await self._toggle_stepper()
        elif command == "SS":
            await self._configure_stepper()
            
        # Control de sensor
        elif command == "L1":
            await self._start_laser_monitoring()
        elif command == "L0":
            await self._stop_laser_monitoring()
        elif command == "LT":
            await self._simulate_laser_trigger()
        elif command == "LD":
            await self._sensor_diagnostics()
            
        # Sistema
        elif command == "I":
            await self._show_detailed_info()
        elif command == "D":
            await self._run_auto_demo()
        elif command == "R":
            await self._reset_stats()
        elif command == "Q":
            print("👋 Saliendo del sistema...")
            self.demo_active = False
        else:
            print("❓ Comando no reconocido")
    
    # === CONTROL DE BANDA ===
    
    async def _belt_forward(self):
        """Inicia banda hacia adelante."""
        print("⏩ Iniciando banda ADELANTE...")
        try:
            if self.belt_driver:
                success = await self.belt_driver.start_belt()
                if success:
                    self.belt_running = True
                    self.stats['belt_starts'] += 1
                    print("✅ Banda funcionando hacia ADELANTE")
                else:
                    print("❌ Error iniciando banda")
            else:
                print("🎭 SIMULACIÓN: Banda iniciada hacia ADELANTE")
                self.belt_running = True
                self.stats['belt_starts'] += 1
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _belt_backward(self):
        """Inicia banda hacia atrás."""
        print("⏪ Iniciando banda ATRÁS...")
        try:
            if self.belt_driver:
                success = await self.belt_driver.reverse_direction()
                if success:
                    self.belt_running = True
                    self.stats['belt_starts'] += 1
                    print("✅ Banda funcionando hacia ATRÁS")
                else:
                    print("❌ Error cambiando dirección")
            else:
                print("🎭 SIMULACIÓN: Banda iniciada hacia ATRÁS")
                self.belt_running = True
                self.stats['belt_starts'] += 1
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _belt_stop(self):
        """Para la banda."""
        print("⏹️ Parando banda...")
        try:
            if self.belt_driver:
                success = await self.belt_driver.stop_belt()
                if success:
                    self.belt_running = False
                    print("✅ Banda PARADA")
                else:
                    print("❌ Error parando banda")
            else:
                print("🎭 SIMULACIÓN: Banda PARADA")
                self.belt_running = False
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # === CONTROL DE STEPPER ===
    
    async def _manual_stepper(self):
        """Activación manual del stepper."""
        try:
            duration = float(input("⏱️ Duración (segundos) [0.6]: ") or "0.6")
            intensity = float(input("⚡ Intensidad (%) [80]: ") or "80")
            
            print(f"🔧 Activando stepper manualmente: {duration:.2f}s @ {intensity:.0f}%")
            await self._activate_stepper_async(duration, intensity)
            
        except ValueError:
            print("❌ Valores inválidos")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _toggle_stepper(self):
        """Toggle habilitación del stepper."""
        self.stepper_enabled = not self.stepper_enabled
        status = "HABILITADO" if self.stepper_enabled else "DESHABILITADO"
        print(f"🔧 Activación sensor→stepper: {status}")
    
    async def _configure_stepper(self):
        """Configuración del stepper."""
        print("\n🔧 CONFIGURACIÓN STEPPER")
        print("-" * 30)
        
        try:
            config = self.config.get("laser_stepper_settings", {}).get("activation_on_laser", {})
            
            print(f"Duración actual: {config.get('activation_duration_seconds', 0.6)}s")
            new_duration = input("Nueva duración (Enter para mantener): ")
            if new_duration:
                config['activation_duration_seconds'] = float(new_duration)
            
            print(f"Intensidad actual: {config.get('intensity_percent', 80)}%")
            new_intensity = input("Nueva intensidad (Enter para mantener): ")
            if new_intensity:
                config['intensity_percent'] = float(new_intensity)
            
            print(f"Intervalo mínimo actual: {config.get('min_interval_seconds', 0.15)}s")
            new_interval = input("Nuevo intervalo (Enter para mantener): ")
            if new_interval:
                config['min_interval_seconds'] = float(new_interval)
                self.min_laser_interval = float(new_interval)
            
            print("✅ Configuración actualizada")
            
        except ValueError:
            print("❌ Valores inválidos")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # === CONTROL DE SENSOR ===
    
    async def _start_laser_monitoring(self):
        """Inicia monitoreo del sensor."""
        print("📡 Iniciando monitoreo del sensor...")
        try:
            if self.sensor_interface:
                self.sensor_interface.enable_trigger_monitoring()
                self.laser_monitoring = True
                print("✅ Monitoreo del sensor ACTIVO")
                print("💡 Active el sensor para disparar el stepper")
            else:
                print("🎭 SIMULACIÓN: Monitoreo del sensor activo")
                self.laser_monitoring = True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _stop_laser_monitoring(self):
        """Para monitoreo del sensor."""
        print("📡 Parando monitoreo del sensor...")
        try:
            if self.sensor_interface:
                self.sensor_interface.disable_trigger_monitoring()
                self.laser_monitoring = False
                print("✅ Monitoreo del sensor PARADO")
            else:
                print("🎭 SIMULACIÓN: Monitoreo del sensor parado")
                self.laser_monitoring = False
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _simulate_laser_trigger(self):
        """Simula un trigger del sensor."""
        print("🔴 SIMULANDO trigger del sensor...")
        self._laser_trigger_callback()
    
    async def _sensor_diagnostics(self):
        """Diagnóstico en tiempo real del sensor MH Flying Fish."""
        print("\n🔍 DIAGNÓSTICO SENSOR MH FLYING FISH")
        print("="*50)
        
        # Obtener configuración del sensor
        sensor_config = self.config.get("sensor_settings", {}).get("trigger_sensor", {})
        pin = sensor_config.get("pin_bcm", 4)
        
        print(f"📍 Pin configurado: BCM {pin}")
        print(f"🔧 Tipo: {sensor_config.get('type', 'N/A')}")
        print(f"⚡ Trigger en: {sensor_config.get('trigger_on_state', 'LOW')}")
        print(f"🕰️ Debounce: {sensor_config.get('debounce_time_ms', 50)}ms")
        print(f"📌 Pull: {sensor_config.get('pull_up_down', 'PUD_UP')}")
        
        if not GPIO_AVAILABLE:
            print("⚠️ GPIO no disponible - modo simulación")
            return
            
        print(f"\n🔄 Iniciando monitoreo en tiempo real del pin BCM {pin}")
        print("   📊 Lecturas: 0=LOW (~0.10V), 1=HIGH (~2.70V)")
        print("   🎯 Esperando trigger cuando cambie de HIGH→LOW")
        print("   ⌨️ Presiona Enter para salir del diagnóstico...\n")
        
        try:
            # Configurar pin si no está configurado
            if not hasattr(self, '_diagnostic_pin_setup') or self._diagnostic_pin_setup != pin:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self._diagnostic_pin_setup = pin
                await asyncio.sleep(0.1)  # Estabilización
                
            # Variables de monitoreo
            last_state = None
            trigger_count = 0
            high_count = 0
            low_count = 0
            
            # Crear tarea para leer input del usuario
            import sys
            from concurrent.futures import ThreadPoolExecutor
            
            def get_input():
                return input()
            
            with ThreadPoolExecutor() as executor:
                input_task = asyncio.get_event_loop().run_in_executor(executor, get_input)
                
                start_time = time.time()
                last_print_time = 0
                
                while not input_task.done():
                    current_time = time.time()
                    current_state = GPIO.input(pin)
                    
                    # Contar estados
                    if current_state == GPIO.HIGH:
                        high_count += 1
                    else:
                        low_count += 1
                    
                    # Detectar cambio de estado (trigger)
                    if last_state is not None and last_state != current_state:
                        if last_state == GPIO.HIGH and current_state == GPIO.LOW:
                            trigger_count += 1
                            print(f"🔴 TRIGGER #{trigger_count} detectado! HIGH→LOW a las {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                    
                    # Imprimir estado cada segundo
                    if current_time - last_print_time >= 1.0:
                        elapsed = current_time - start_time
                        total_reads = high_count + low_count
                        high_percent = (high_count / total_reads * 100) if total_reads > 0 else 0
                        low_percent = (low_count / total_reads * 100) if total_reads > 0 else 0
                        
                        state_symbol = "🟢 HIGH" if current_state == GPIO.HIGH else "🔴 LOW"
                        print(f"⏱️ {elapsed:04.1f}s | Estado: {state_symbol} | "
                              f"HIGH: {high_percent:05.1f}% | LOW: {low_percent:04.1f}% | "
                              f"Triggers: {trigger_count}")
                        
                        last_print_time = current_time
                    
                    last_state = current_state
                    await asyncio.sleep(0.01)  # 10ms polling
                
                # Cancelar la tarea de input
                input_task.cancel()
                
                print(f"\n✅ Diagnóstico completado:")
                print(f"   🎯 Triggers detectados: {trigger_count}")
                print(f"   📊 Estados HIGH: {high_percent:.1f}%")
                print(f"   📊 Estados LOW: {low_percent:.1f}%")
                
                if trigger_count == 0:
                    print(f"\n💡 SUGERENCIAS:")
                    print(f"   - Verifica que el sensor esté conectado al pin BCM {pin}")
                    print(f"   - Activa manualmente el sensor (bloquea el haz de luz)")
                    print(f"   - Verifica la alimentación (3.3V conectado correctamente)")
                    print(f"   - Si los valores se mantienen siempre en HIGH o LOW, revisa el cableado")
                
        except KeyboardInterrupt:
            print("\n⚠️ Diagnóstico interrumpido por usuario")
        except Exception as e:
            print(f"\n❌ Error en diagnóstico: {e}")
            logger.error(f"Error en diagnóstico de sensor: {e}")
        
        print("🔄 Regresando al menú principal...")
    
    # === SISTEMA ===
    
    async def _show_detailed_info(self):
        """Muestra información detallada del sistema."""
        print("\n📊 INFORMACIÓN DETALLADA DEL SISTEMA")
        print("="*60)
        
        # Información de componentes
        if self.belt_driver:
            try:
                belt_status = await self.belt_driver.get_status()
                print(f"🎢 BANDA TRANSPORTADORA:")
                print(f"   Estado: {'Funcionando' if belt_status.get('running') else 'Parada'}")
                print(f"   Dirección: {belt_status.get('direction', 'N/A')}")
                print(f"   Tipo: {belt_status.get('control_type', 'N/A')}")
            except:
                print(f"🎢 BANDA: Error obteniendo estado")
        
        if self.laser_stepper:
            try:
                stepper_status = self.laser_stepper.get_status()
                print(f"🔧 STEPPER DRV8825:")
                print(f"   Estado: {stepper_status.get('state', 'N/A')}")
                print(f"   Tipo: {stepper_status.get('type', 'N/A')}")
                print(f"   Activaciones: {stepper_status.get('metrics', {}).get('activations_count', 0)}")
            except:
                print(f"🔧 STEPPER: Error obteniendo estado")
        
        if self.sensor_interface:
            try:
                sensor_status = self.sensor_interface.get_status()
                print(f"📡 SENSOR:")
                print(f"   Inicializado: {sensor_status.get('is_initialized', False)}")
                print(f"   Monitoreo: {sensor_status.get('trigger_enabled', False)}")
            except:
                print(f"📡 SENSOR: Error obteniendo estado")
        
        # Estadísticas detalladas
        uptime = time.time() - self.stats['start_time']
        print(f"\n📈 ESTADÍSTICAS DETALLADAS:")
        print(f"   ⏱️ Tiempo activo: {uptime:.1f}s ({uptime/60:.1f}min)")
        print(f"   🔴 Triggers sensor: {self.stats['laser_triggers']}")
        print(f"   🔧 Activaciones stepper: {self.stats['stepper_activations']}")
        print(f"   ⏱️ Tiempo stepper acumulado: {self.stats.get('stepper_total_active_time_s', 0.0):.1f}s")
        if self.stats.get('last_trigger_time'):
            print(f"   🕘 Último trigger: {datetime.fromtimestamp(self.stats['last_trigger_time']).strftime('%H:%M:%S')}")
        if self.stats.get('last_stepper_activation_time'):
            print(f"   🕘 Última activación stepper: {datetime.fromtimestamp(self.stats['last_stepper_activation_time']).strftime('%H:%M:%S')}")
        print(f"   🎢 Inicios banda: {self.stats['belt_starts']}")
        
        if self.stats['laser_triggers'] > 0:
            rate = self.stats['laser_triggers'] / (uptime / 60)
            print(f"   📊 Tasa triggers: {rate:.1f}/min")
    
    async def _run_auto_demo(self):
        """Ejecuta demo automática."""
        print("\n🤖 INICIANDO DEMO AUTOMÁTICA")
        print("="*50)
        
        demo_steps = [
            ("Iniciando banda transportadora...", self._belt_forward, 2),
            ("Habilitando monitoreo del sensor...", self._start_laser_monitoring, 1),
            ("Simulando triggers del sensor...", self._demo_laser_sequence, 8),
            ("Activación manual stepper...", self._demo_manual_stepper, 3),
            ("Parando monitoreo del sensor...", self._stop_laser_monitoring, 1),
            ("Parando banda...", self._belt_stop, 1),
        ]
        
        for description, action, duration in demo_steps:
            print(f"\n🔄 {description}")
            try:
                await action()
                print(f"   ⏱️ Esperando {duration}s...")
                await asyncio.sleep(duration)
            except Exception as e:
                print(f"   ❌ Error: {e}")
                break
        
        print("\n✅ Demo automática completada")
        await self._show_system_status()
    
    async def _demo_laser_sequence(self):
        """Secuencia de demo del sensor."""
        print("   🔴 Simulando 3 triggers del sensor con intervalos...")
        for i in range(3):
            await asyncio.sleep(2)
            print(f"   🔴 Trigger {i+1}/3")
            self._laser_trigger_callback()
            await asyncio.sleep(1)
    
    async def _demo_manual_stepper(self):
        """Demo manual del stepper."""
        print("   🔧 Activación manual del stepper...")
        await self._activate_stepper_async(0.8, 90.0)
    
    async def _reset_stats(self):
        """Resetea las estadísticas."""
        self.stats = {
            'laser_triggers': 0,
            'stepper_activations': 0,
            'belt_starts': 0,
            'start_time': time.time(),
            'stepper_total_active_time_s': 0.0,
            'last_trigger_time': None,
            'last_stepper_activation_time': None
        }
        print("✅ Estadísticas reseteadas")
    
    async def cleanup(self):
        """Limpia recursos del sistema."""
        print("\n🧹 Limpiando recursos del sistema...")
        
        try:
            # Parar banda
            if self.belt_driver:
                await self.belt_driver.stop_belt()
                await self.belt_driver.cleanup()
            
            # Limpiar stepper
            if self.laser_stepper:
                await self.laser_stepper.cleanup()
            
            # Limpiar sensor
            if self.sensor_interface:
                self.sensor_interface.shutdown()
            
            print("✅ Limpieza completada")
            
        except Exception as e:
            print(f"⚠️ Error en limpieza: {e}")

async def main():
    """Función principal de la demo."""
    demo = DemoSistemaCompleto()
    
    # Configurar manejo de señales
    def signal_handler(signum, frame):
        print(f"\n🛑 Señal {signum} recibida - Terminando demo...")
        demo.demo_active = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Mostrar información inicial
        print("🚀 VisiFruit v3.0 RT-DETR - Demo Sistema Completo")
        print("🔧 Motor DC + DRV8825 Stepper + Sensor MH Flying Fish")
        print("\n⚠️  IMPORTANTE: Verifica las conexiones antes de continuar")
        
        input("\n📋 Presiona Enter para inicializar el sistema...")
        # Preflight: cerrar procesos que usan GPIO y pueden bloquear pines
        try:
            # Matar instancias de main_etiquetadora.py si están corriendo en este usuario
            out = subprocess.run(["pgrep", "-af", "main_etiquetadora.py"], capture_output=True, text=True)
            if out.returncode == 0 and out.stdout.strip():
                for line in out.stdout.strip().splitlines():
                    try:
                        pid = int(line.strip().split()[0])
                        # Evitar matarnos a nosotros mismos
                        if pid != os.getpid():
                            os.kill(pid, signal.SIGTERM)
                    except Exception:
                        pass
                # Pequeña espera y kill -9 si persisten
                time.sleep(0.3)
                out2 = subprocess.run(["pgrep", "-af", "main_etiquetadora.py"], capture_output=True, text=True)
                if out2.returncode == 0 and out2.stdout.strip():
                    for line in out2.stdout.strip().splitlines():
                        try:
                            pid = int(line.strip().split()[0])
                            if pid != os.getpid():
                                os.kill(pid, signal.SIGKILL)
                        except Exception:
                            pass
        except Exception:
            # Si falla preflight, continuamos; el wrapper gestionará reintentos
            pass
        
        # Inicializar sistema
        if not await demo.initialize():
            print("❌ No se pudo inicializar el sistema completo")
            return
        
        # Ejecutar demo interactiva
        await demo.run_interactive_demo()
    
    except Exception as e:
        print(f"💥 Error fatal en demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await demo.cleanup()
        print("\n👋 Demo terminada. ¡Gracias por probar VisiFruit v3.0!")

if __name__ == "__main__":
    print("\n🚀 Iniciando Demo Sistema Completo...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrumpida por usuario")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()
