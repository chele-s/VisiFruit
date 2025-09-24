#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 DEMO SISTEMA COMPLETO CON SERVIDOR WEB - VisiFruit v3.0 RT-DETR
=================================================================

Versión web del demo con servidor FastAPI para compatibilidad con el frontend.
Basado en demo_sistema_completo.py pero con endpoints HTTP.

Endpoints compatibles con main_etiquetadora.py:
- /belt/* - Control de banda transportadora
- /laser_stepper/* - Control de stepper DRV8825
- /health - Estado del sistema
- /status - Información detallada

Puerto por defecto: 8002 (para no conflictuar con main_etiquetadora.py:8000)

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Enero 2025
Versión: 3.0 - RT-DETR Web Edition
"""

import asyncio
import json
import logging
import signal
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import os

# Importaciones web
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    WEB_AVAILABLE = True
except ImportError:
    print("❌ FastAPI no disponible. Instalar con: pip install fastapi uvicorn")
    WEB_AVAILABLE = False
    sys.exit(1)

# Agregar directorio padre para importaciones
sys.path.append(str(Path(__file__).parent.parent))

# Importaciones del demo original
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
        self.current_direction = "stopped"
        
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
            self.current_direction = "stopped"
            logger.info("✅ SimpleBeltController inicializado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando SimpleBeltController: {e}")
            return False
    
    async def start_belt(self, speed_percent: float = None) -> bool:
        """Inicia banda hacia adelante."""
        try:
            if not self.initialized:
                return await self.initialize()
                
            # Habilitar driver si hay pin enable
            if self.enable_pin:
                GPIO.output(self.enable_pin, GPIO.HIGH)
                await asyncio.sleep(0.01)
                
            # Activar motor adelante
            GPIO.output(self.relay2_pin, GPIO.LOW)   # Asegurar que atrás esté apagado
            GPIO.output(self.relay1_pin, GPIO.HIGH)  # Activar adelante
            self.current_state = "running"
            self.current_direction = "forward"
            logger.info("🟢 Banda: ADELANTE")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando banda adelante: {e}")
            return False
    
    async def reverse_direction(self) -> bool:
        """Inicia banda hacia atrás."""
        try:
            if not self.initialized:
                return await self.initialize()
                
            # Habilitar driver
            if self.enable_pin:
                GPIO.output(self.enable_pin, GPIO.HIGH)
                await asyncio.sleep(0.01)
                
            # Activar motor atrás
            GPIO.output(self.relay1_pin, GPIO.LOW)   # Asegurar que adelante esté apagado
            GPIO.output(self.relay2_pin, GPIO.HIGH)  # Activar atrás
            self.current_state = "running"
            self.current_direction = "backward"
            logger.info("🔴 Banda: ATRÁS")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando banda atrás: {e}")
            return False
    
    async def stop_belt(self) -> bool:
        """Detiene la banda."""
        try:
            if not self.initialized:
                return True  # Ya está "detenida"
                
            # Desactivar ambos relays
            GPIO.output(self.relay1_pin, GPIO.LOW)
            GPIO.output(self.relay2_pin, GPIO.LOW)
            
            self.current_state = "stopped"
            self.current_direction = "stopped"
            logger.info("⚫ Banda: PARADA")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo banda: {e}")
            return False
    
    async def emergency_brake(self) -> bool:
        """Parada de emergencia."""
        return await self.stop_belt()
    
    async def set_speed(self, speed_percent: float) -> bool:
        """Cambiar velocidad (no aplicable para ON/OFF, solo simular)."""
        logger.info(f"🎭 SIMULACIÓN: Velocidad establecida a {speed_percent}%")
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del driver."""
        return {
            "initialized": self.initialized,
            "running": self.current_state == "running",
            "direction": self.current_direction,
            "state": self.current_state,
            "gpio_mode": GPIO_MODE.value,
            "simulation": is_simulation_mode(),
            "control_type": "relay_simple",
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Limpia recursos."""
        try:
            if self.initialized:
                await self.stop_belt()
                GPIO.cleanup([self.relay1_pin, self.relay2_pin, self.enable_pin])
            logger.info("🧹 SimpleBeltController limpiado")
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")

class DemoWebServer:
    """Demo con servidor web para compatibilidad con frontend."""
    
    def __init__(self, port: int = 8002):
        self.port = port
        self.app: Optional[FastAPI] = None
        self.server_task: Optional[asyncio.Task] = None
        self.running = True
        
        # Componentes del sistema (igual que el demo original)
        self.belt_driver = None
        self.laser_stepper = None
        self.sensor_interface = None
        
        # Estado del sistema
        self.belt_running = False
        self.stepper_enabled = True
        self.laser_monitoring = False
        self.simulation_mode = False
        self.system_enabled = True
        
        # Configuración por defecto
        self.config = self._load_default_config()
        
        # Estadísticas
        self.stats = {
            'laser_triggers': 0,
            'stepper_activations': 0,
            'belt_starts': 0,
            'start_time': time.time(),
            'stepper_total_active_time_s': 0.0,
            'last_trigger_time': None,
            'last_stepper_activation_time': None,
            'api_requests': 0,
            'last_api_request': None
        }
        
        # Control de activación láser
        self.last_laser_activation = 0.0
        self.min_laser_interval = 0.15  # segundos
        self.sensor_to_labeler_delay_s = 0.0
        
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()
        
        logger.info(f"🌐 DemoWebServer inicializado para puerto {port}")
    
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
                "sensor_to_labeler_distance_m": 0.05
            },
            "conveyor_belt_settings": {
                "relay1_pin": 22,  # Adelante (BCM 22 → físico 15)
                "relay2_pin": 23,  # Atrás   (BCM 23 → físico 16)  
                "enable_pin": 27,   # Enable  (BCM 27 → físico 13)
                "belt_speed_mps": 0.15
            }
        }
    
    async def initialize(self) -> bool:
        """Inicializa todos los componentes del sistema."""
        logger.info("🔧 Inicializando componentes del demo web...")
        
        success = True
        
        # 1. Inicializar banda transportadora
        if BELT_AVAILABLE:
            success &= await self._initialize_belt()
        else:
            logger.info("⚠️ Controlador de banda no disponible - Modo simulación")
            self.simulation_mode = True
        
        # 2. Inicializar stepper DRV8825
        success &= await self._initialize_stepper()
        
        # 3. Inicializar sensor (MH Flying Fish)
        if SENSOR_AVAILABLE:
            success &= await self._initialize_sensor()
        else:
            logger.info("⚠️ Sensor interface no disponible - Modo simulación")
            self.simulation_mode = True
        
        # 4. Crear y configurar aplicación FastAPI
        self.app = self._create_fastapi_app()
        
        if success:
            logger.info("✅ Demo web inicializado correctamente")
        else:
            logger.warning("⚠️ Demo inicializado con algunos componentes en simulación")
        
        return True  # Siempre retorna True para permitir funcionamiento en simulación
    
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
                        logger.info("✅ Banda: Usando driver Pi5 (lgpio)")
                        return True
                except Exception as e:
                    logger.warning(f"⚠️ Driver Pi5 falló: {e}")
                    self.belt_driver = None
            
            if self.belt_driver is None and BELT_AVAILABLE:
                try:
                    self.belt_driver = create_relay_motor_driver(
                        relay1_pin=relay1_pin,
                        relay2_pin=relay2_pin,
                        enable_pin=enable_pin
                    )
                    if await self.belt_driver.initialize():
                        logger.info("✅ Banda: Usando driver legacy (RPi.GPIO)")
                        return True
                except Exception as e:
                    logger.warning(f"⚠️ Driver legacy falló: {e}")
                    self.belt_driver = None
            
            # Fallback final: GPIO wrapper directo
            if self.belt_driver is None and GPIO_AVAILABLE:
                self.belt_driver = SimpleBeltController(relay1_pin, relay2_pin, enable_pin)
                if await self.belt_driver.initialize():
                    logger.info(f"✅ Banda: Usando GPIO wrapper ({GPIO_MODE.value})")
                    return True
            
            logger.warning("❌ No se pudo inicializar controlador de banda")
            return False
                
        except Exception as e:
            logger.error(f"❌ Error inicializando banda: {e}")
            return False
    
    async def _initialize_stepper(self) -> bool:
        """Inicializa el stepper DRV8825."""
        try:
            stepper_config = self.config.get("laser_stepper_settings", {})
            stepper_config["type"] = "stepper"
            
            self.laser_stepper = LabelerActuator(stepper_config)
            
            if await self.laser_stepper.initialize():
                logger.info("✅ Stepper DRV8825 inicializado")
                return True
            else:
                logger.info("⚠️ Stepper DRV8825 en modo simulación")
                return True  # Continuar en modo simulación
                
        except Exception as e:
            logger.warning(f"⚠️ Stepper en modo simulación: {e}")
            return True  # Continuar en modo simulación
    
    async def _initialize_sensor(self) -> bool:
        """Inicializa el sensor digital."""
        try:
            sensor_config = self.config.get("sensor_settings", {})
            self.sensor_interface = SensorInterface(
                trigger_callback=self._laser_trigger_callback
            )
            
            if self.sensor_interface.initialize(sensor_config):
                try:
                    self.sensor_interface.enable_trigger_monitoring()
                    self.laser_monitoring = True
                    logger.info("✅ Sensor MH Flying Fish inicializado y monitoreo ACTIVO")
                except Exception as e:
                    logger.warning(f"⚠️ Sensor inicializado, pero no se pudo habilitar el monitoreo: {e}")
                return True
            else:
                logger.info("⚠️ Sensor en modo simulación")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Sensor en modo simulación: {e}")
            return True
    
    def _laser_trigger_callback(self):
        """Callback cuando se detecta el sensor."""
        try:
            current_time = time.time()
            
            # Control de debounce
            if (current_time - self.last_laser_activation) < self.min_laser_interval:
                return
            
            self.last_laser_activation = current_time
            self.stats['laser_triggers'] += 1
            self.stats['last_trigger_time'] = current_time
            
            logger.info(f"🔴 SENSOR DETECTADO #{self.stats['laser_triggers']}")
            
            # Activar stepper si está habilitado
            if self.stepper_enabled and self.laser_stepper:
                activation_config = self.config.get("laser_stepper_settings", {}).get("activation_on_laser", {})
                duration = activation_config.get("activation_duration_seconds", 0.6)
                intensity = activation_config.get("intensity_percent", 80.0)
                
                # Programar activación asíncrona
                asyncio.create_task(self._activate_stepper_async(duration, intensity))
                
        except Exception as e:
            logger.error(f"Error en callback de sensor: {e}")
    
    async def _activate_stepper_async(self, duration: float, intensity: float):
        """Activa el stepper de forma asíncrona."""
        try:
            if self.laser_stepper:
                success = await self.laser_stepper.activate_for_duration(duration, intensity)
                if success:
                    self.stats['stepper_activations'] += 1
                    self.stats['stepper_total_active_time_s'] += duration
                    self.stats['last_stepper_activation_time'] = time.time()
                    logger.info(f"✅ Stepper activado: {duration:.2f}s @ {intensity:.0f}%")
                else:
                    logger.error("❌ Error activando stepper")
            else:
                # Simulación
                logger.info(f"🎭 SIMULACIÓN: Stepper activado {duration:.2f}s @ {intensity:.0f}%")
                await asyncio.sleep(duration)
                self.stats['stepper_activations'] += 1
                self.stats['stepper_total_active_time_s'] += duration
                self.stats['last_stepper_activation_time'] = time.time()
                
        except Exception as e:
            logger.error(f"❌ Error activando stepper: {e}")
    
    def _create_fastapi_app(self) -> FastAPI:
        """Crea la aplicación FastAPI con endpoints compatibles."""
        app = FastAPI(
            title="VisiFruit Demo Web Server",
            description="Servidor web del demo sistema completo con endpoints compatibles",
            version="3.0.0-DEMO",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Middleware CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # ============ RUTAS BÁSICAS ============
        @app.get("/health")
        async def health_check():
            """Check de salud del sistema demo."""
            return {
                "status": "healthy" if self.running else "shutting_down",
                "system_state": "running" if self.running else "stopped",
                "uptime_seconds": time.time() - self.stats['start_time'],
                "version": "3.0.0-DEMO",
                "mode": "demo_web_server",
                "simulation": self.simulation_mode,
                "components": {
                    "belt": self.belt_driver is not None,
                    "stepper": self.laser_stepper is not None,
                    "sensor": self.sensor_interface is not None,
                }
            }
        
        @app.get("/status")
        async def get_status():
            """Estado detallado del sistema demo."""
            uptime = time.time() - self.stats['start_time']
            
            belt_status = {"connected": False, "running": False, "direction": "stopped"}
            if self.belt_driver:
                try:
                    belt_status = await self.belt_driver.get_status()
                except Exception:
                    pass
            
            return {
                "system": {
                    "name": "VisiFruit Demo Web Server",
                    "state": "running" if self.running else "stopped",
                    "uptime_seconds": uptime,
                    "version": "3.0.0-DEMO",
                    "mode": "demo_web_server",
                    "simulation": self.simulation_mode,
                    "enabled": self.system_enabled
                },
                "components": {
                    "belt": belt_status,
                    "stepper": {
                        "enabled": self.stepper_enabled,
                        "available": self.laser_stepper is not None,
                        "activations": self.stats['stepper_activations'],
                        "total_time": self.stats['stepper_total_active_time_s']
                    },
                    "sensor": {
                        "monitoring": self.laser_monitoring,
                        "available": self.sensor_interface is not None,
                        "triggers": self.stats['laser_triggers']
                    }
                },
                "stats": self.stats,
                "timestamp": datetime.now().isoformat()
            }
        
        # ============ CONTROL DE BANDA TRANSPORTADORA ============
        @app.post("/belt/start_forward")
        async def start_belt_forward():
            """Inicia la banda transportadora hacia adelante."""
            async with self._lock:
                self.stats['api_requests'] += 1
                self.stats['last_api_request'] = time.time()
                
                try:
                    if not self.system_enabled:
                        raise HTTPException(423, "Sistema deshabilitado")
                    
                    if not self.belt_driver:
                        # Simulación
                        self.belt_running = True
                        self.stats['belt_starts'] += 1
                        logger.info("🎭 SIMULACIÓN: Banda iniciada hacia adelante")
                        return {
                            "success": True,
                            "message": "Banda iniciada hacia adelante (simulación)",
                            "direction": "forward",
                            "simulation": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    success = await self.belt_driver.start_belt()
                    if success:
                        self.belt_running = True
                        self.stats['belt_starts'] += 1
                        return {
                            "success": True,
                            "message": "Banda iniciada hacia adelante",
                            "direction": "forward",
                            "simulation": False,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        raise HTTPException(500, "Error iniciando banda hacia adelante")
                        
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(500, f"Error en control de banda: {e}")
        
        @app.post("/belt/start_backward")
        async def start_belt_backward():
            """Inicia la banda transportadora hacia atrás."""
            async with self._lock:
                self.stats['api_requests'] += 1
                self.stats['last_api_request'] = time.time()
                
                try:
                    if not self.system_enabled:
                        raise HTTPException(423, "Sistema deshabilitado")
                    
                    if not self.belt_driver:
                        # Simulación
                        self.belt_running = True
                        self.stats['belt_starts'] += 1
                        logger.info("🎭 SIMULACIÓN: Banda iniciada hacia atrás")
                        return {
                            "success": True,
                            "message": "Banda iniciada hacia atrás (simulación)",
                            "direction": "backward",
                            "simulation": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    success = await self.belt_driver.reverse_direction()
                    if success:
                        self.belt_running = True
                        self.stats['belt_starts'] += 1
                        return {
                            "success": True,
                            "message": "Banda iniciada hacia atrás", 
                            "direction": "backward",
                            "simulation": False,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        raise HTTPException(500, "Error iniciando banda hacia atrás")
                        
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(500, f"Error en control de banda: {e}")
        
        @app.post("/belt/stop")
        async def stop_belt():
            """Detiene la banda transportadora."""
            async with self._lock:
                self.stats['api_requests'] += 1
                self.stats['last_api_request'] = time.time()
                
                try:
                    if not self.belt_driver:
                        # Simulación
                        self.belt_running = False
                        logger.info("🎭 SIMULACIÓN: Banda detenida")
                        return {
                            "success": True,
                            "message": "Banda detenida (simulación)",
                            "direction": "stopped",
                            "simulation": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    success = await self.belt_driver.stop_belt()
                    if success:
                        self.belt_running = False
                        return {
                            "success": True,
                            "message": "Banda detenida",
                            "direction": "stopped",
                            "simulation": False,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        raise HTTPException(500, "Error deteniendo banda")
                        
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(500, f"Error en control de banda: {e}")
        
        @app.post("/belt/emergency_stop")
        async def emergency_stop_belt():
            """Parada de emergencia de la banda transportadora."""
            async with self._lock:
                self.stats['api_requests'] += 1
                self.stats['last_api_request'] = time.time()
                
                try:
                    # Parada de emergencia deshabilita el sistema
                    self.system_enabled = False
                    self.belt_running = False
                    
                    if self.belt_driver:
                        try:
                            await self.belt_driver.emergency_brake()
                        except Exception:
                            pass
                    
                    logger.warning("🚨 PARADA DE EMERGENCIA EJECUTADA")
                    return {
                        "success": True,
                        "message": "PARADA DE EMERGENCIA EJECUTADA",
                        "direction": "emergency_stopped",
                        "system_disabled": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    raise HTTPException(500, f"Error en parada de emergencia: {e}")
        
        @app.post("/belt/set_speed")
        async def set_belt_speed(speed_data: dict):
            """Establece la velocidad de la banda transportadora."""
            async with self._lock:
                self.stats['api_requests'] += 1
                self.stats['last_api_request'] = time.time()
                
                try:
                    speed = speed_data.get("speed", 0.5)
                    if not (0.1 <= speed <= 2.5):
                        raise HTTPException(400, "Velocidad debe estar entre 0.1 y 2.5 m/s")
                    
                    if self.belt_driver and hasattr(self.belt_driver, 'set_speed'):
                        success = await self.belt_driver.set_speed(speed * 50)  # Convertir a porcentaje
                    else:
                        success = True  # Simulación
                    
                    if success:
                        return {
                            "success": True,
                            "message": f"Velocidad establecida a {speed} m/s",
                            "speed_ms": speed,
                            "simulation": self.belt_driver is None,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        raise HTTPException(500, "Error estableciendo velocidad")
                        
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(500, f"Error estableciendo velocidad: {e}")
        
        @app.post("/belt/toggle_enable")
        async def toggle_belt_enable():
            """Habilita o deshabilita el sistema de banda."""
            async with self._lock:
                self.stats['api_requests'] += 1
                self.stats['last_api_request'] = time.time()
                
                try:
                    self.system_enabled = not self.system_enabled
                    
                    if not self.system_enabled and self.belt_running:
                        # Si se deshabilita, parar banda
                        if self.belt_driver:
                            await self.belt_driver.stop_belt()
                        self.belt_running = False
                    
                    return {
                        "success": True,
                        "message": "Sistema habilitado" if self.system_enabled else "Sistema deshabilitado",
                        "enabled": self.system_enabled,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    raise HTTPException(500, f"Error en toggle de banda: {e}")
        
        @app.get("/belt/status")
        async def get_belt_status():
            """Obtiene el estado de la banda transportadora."""
            self.stats['api_requests'] += 1
            self.stats['last_api_request'] = time.time()
            
            try:
                if self.belt_driver:
                    belt_status = await self.belt_driver.get_status()
                else:
                    belt_status = {
                        "running": self.belt_running,
                        "direction": "forward" if self.belt_running else "stopped",
                        "simulation": True,
                        "initialized": True
                    }
                
                # Enriquecer el status
                enriched_status = {
                    **belt_status,
                    "system_enabled": self.system_enabled,
                    "timestamp": datetime.now().isoformat(),
                    "stats": {
                        "belt_starts": self.stats['belt_starts'],
                        "uptime_seconds": time.time() - self.stats['start_time'],
                    },
                    "demo_mode": True,
                    "last_update": datetime.now().isoformat()
                }
                
                return enriched_status
                
            except Exception as e:
                raise HTTPException(500, f"Error obteniendo estado de banda: {e}")
        
        # ============ CONTROL STEPPER LÁSER (DRV8825) ============
        @app.post("/laser_stepper/toggle")
        async def toggle_laser_stepper(payload: dict):
            """Habilita/deshabilita el stepper láser."""
            self.stats['api_requests'] += 1
            self.stats['last_api_request'] = time.time()
            
            enabled = payload.get("enabled", True)
            self.stepper_enabled = bool(enabled)
            
            return {
                "success": True,
                "enabled": self.stepper_enabled,
                "message": f"Stepper {'habilitado' if self.stepper_enabled else 'deshabilitado'}",
                "timestamp": datetime.now().isoformat()
            }
        
        @app.post("/laser_stepper/test")
        async def test_laser_stepper(payload: dict):
            """Prueba manual del stepper láser."""
            self.stats['api_requests'] += 1
            self.stats['last_api_request'] = time.time()
            
            try:
                duration = float(payload.get("duration", 0.5))
                intensity = float(payload.get("intensity", 80.0))
                
                await self._activate_stepper_async(duration, intensity)
                
                return {
                    "success": True,
                    "duration": duration,
                    "intensity": intensity,
                    "message": f"Stepper activado por {duration}s",
                    "simulation": self.laser_stepper is None,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                raise HTTPException(500, f"Error probando stepper: {e}")
        
        return app
    
    async def start_server(self):
        """Inicia el servidor web."""
        if not self.app:
            raise RuntimeError("Aplicación no inicializada")
        
        logger.info(f"🌐 Iniciando servidor web demo en puerto {self.port}...")
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(server.serve())
        
        # Esperar un momento para que el servidor esté listo
        await asyncio.sleep(0.5)
        
        logger.info(f"✅ Servidor web demo disponible en:")
        logger.info(f"   🌐 URL: http://localhost:{self.port}")
        logger.info(f"   📖 Docs: http://localhost:{self.port}/docs")
        logger.info(f"   ✅ Health: http://localhost:{self.port}/health")
        
        return self.server_task
    
    async def cleanup(self):
        """Limpia recursos del sistema."""
        logger.info("🧹 Limpiando recursos del demo web...")
        
        try:
            self.running = False
            
            # Parar servidor web
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass
            
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
            
            logger.info("✅ Limpieza completada")
            
        except Exception as e:
            logger.error(f"⚠️ Error en limpieza: {e}")

async def main():
    """Función principal del demo web."""
    demo_server = None
    
    try:
        logger.info("🚀 VisiFruit v3.0 RT-DETR - Demo Web Server")
        logger.info("🌐 Servidor web con endpoints compatibles")
        
        # Crear servidor demo
        demo_server = DemoWebServer(port=8002)
        
        # Configurar manejo de señales
        def signal_handler(signum, frame):
            logger.info(f"🛑 Señal {signum} recibida - Terminando servidor...")
            demo_server.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Inicializar sistema
        if not await demo_server.initialize():
            logger.error("❌ Error en inicialización")
            return 1
        
        # Iniciar servidor web
        server_task = await demo_server.start_server()
        
        logger.info("🎯 Demo web funcionando - Presiona Ctrl+C para detener")
        logger.info("")
        logger.info("📋 ENDPOINTS DISPONIBLES:")
        logger.info("   POST /belt/start_forward    - Iniciar banda adelante")
        logger.info("   POST /belt/start_backward   - Iniciar banda atrás")
        logger.info("   POST /belt/stop             - Parar banda")
        logger.info("   POST /belt/emergency_stop   - Parada de emergencia")
        logger.info("   POST /belt/set_speed        - Establecer velocidad")
        logger.info("   POST /belt/toggle_enable    - Habilitar/deshabilitar")
        logger.info("   GET  /belt/status           - Estado de banda")
        logger.info("   POST /laser_stepper/toggle  - Toggle stepper")
        logger.info("   POST /laser_stepper/test    - Prueba stepper")
        logger.info("   GET  /health                - Estado del sistema")
        logger.info("   GET  /status                - Estado detallado")
        logger.info("")
        
        # Mantener servidor funcionando
        while demo_server.running:
            await asyncio.sleep(1)
            
        # Cancelar servidor
        if server_task and not server_task.done():
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
    
    except KeyboardInterrupt:
        logger.info("⚡ Interrupción recibida - Iniciando apagado...")
    except Exception as e:
        logger.exception(f"💥 Error fatal en demo web: {e}")
        return 1
    finally:
        if demo_server:
            await demo_server.cleanup()
        logger.info("👋 Demo web terminado")
    
    return 0

if __name__ == "__main__":
    if not WEB_AVAILABLE:
        print("❌ Dependencias web no disponibles")
        sys.exit(1)
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        sys.exit(1)
