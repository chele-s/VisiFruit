#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Módulo de Control de Servos para Backend - VisiFruit
========================================================

Módulo del backend para manejar la comunicación entre la interfaz web
y el controlador de servos MG995 optimizado para Raspberry Pi 5.

Características:
- API REST para control de servos
- Configuración dinámica desde la interfaz web
- Estado en tiempo real
- Gestión de múltiples servos
- Persistencia de configuración

Autor: Sistema VisiFruit
Fecha: Enero 2025
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import sys

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Importar el controlador de servos
try:
    from Prototipo_Clasificador.rpi5_servo_controller import (
        RPi5ServoController,
        RPi5MultiServoController,
        ServoConfig,
        ServoCalibration,
        ServoDirection,
        ServoProfile
    )
    SERVO_CONTROLLER_AVAILABLE = True
except ImportError:
    SERVO_CONTROLLER_AVAILABLE = False
    logging.warning("⚠️ RPi5ServoController no disponible")

logger = logging.getLogger(__name__)


class ServoControlModule:
    """
    Módulo de control de servos para el backend.
    
    Gestiona la comunicación entre la interfaz web y los servos físicos.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa el módulo de control de servos.
        
        Args:
            config_path: Ruta al archivo de configuración JSON
        """
        self.config_path = config_path or Path("servo_config.json")
        self.multi_controller: Optional[RPi5MultiServoController] = None
        self.servo_configs: Dict[str, Dict] = {}
        self.servo_status: Dict[str, Dict] = {}
        self.initialized = False
        
        # Estadísticas
        self.stats = {
            "total_movements": 0,
            "total_activations": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
        logger.info("🎮 ServoControlModule inicializado")
    
    async def initialize(self) -> bool:
        """
        Inicializa el sistema de control de servos.
        
        Returns:
            True si fue exitoso
        """
        try:
            if not SERVO_CONTROLLER_AVAILABLE:
                logger.error("❌ Controlador de servos no disponible")
                logger.info("   Continuando en modo simulación")
                self.initialized = True
                return True
            
            # Crear controlador multi-servo
            self.multi_controller = RPi5MultiServoController()
            
            # Cargar configuración
            await self.load_configuration()
            
            # Inicializar servos según configuración
            for servo_id, config in self.servo_configs.items():
                success = await self.add_servo(servo_id, config)
                if not success:
                    logger.warning(f"⚠️ No se pudo inicializar servo '{servo_id}'")
            
            self.initialized = True
            logger.info("✅ ServoControlModule inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando ServoControlModule: {e}")
            return False
    
    async def load_configuration(self) -> bool:
        """
        Carga la configuración de servos desde archivo.
        
        Returns:
            True si fue exitoso
        """
        try:
            # Configuración por defecto
            default_config = {
                "servo1": {
                    "name": "Servo Clasificador 1",
                    "pin_bcm": 12,  # Hardware PWM
                    "profile": "mg995_standard",
                    "default_angle": 90,
                    "activation_angle": 0,
                    "direction": "forward",
                    "movement_speed": 0.8,
                    "smooth_movement": True,
                    "min_safe_angle": 0,
                    "max_safe_angle": 180
                },
                "servo2": {
                    "name": "Servo Clasificador 2",
                    "pin_bcm": 13,  # Hardware PWM
                    "profile": "mg995_standard",
                    "default_angle": 90,
                    "activation_angle": 180,
                    "direction": "forward",
                    "movement_speed": 0.8,
                    "smooth_movement": True,
                    "min_safe_angle": 0,
                    "max_safe_angle": 180
                }
            }
            
            # Cargar configuración guardada si existe
            if self.config_path.exists():
                try:
                    with open(self.config_path, 'r') as f:
                        saved_config = json.load(f)
                        # Mezclar con configuración por defecto
                        for servo_id in saved_config:
                            if servo_id in default_config:
                                default_config[servo_id].update(saved_config[servo_id])
                            else:
                                default_config[servo_id] = saved_config[servo_id]
                    logger.info(f"✅ Configuración cargada desde {self.config_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando configuración: {e}")
                    logger.info("   Usando configuración por defecto")
            
            self.servo_configs = default_config
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            return False
    
    async def save_configuration(self) -> bool:
        """
        Guarda la configuración actual a archivo.
        
        Returns:
            True si fue exitoso
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.servo_configs, f, indent=2)
            logger.info(f"✅ Configuración guardada en {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")
            return False
    
    async def add_servo(self, servo_id: str, config: Dict) -> bool:
        """
        Añade un servo al sistema.
        
        Args:
            servo_id: ID único del servo
            config: Configuración del servo
            
        Returns:
            True si fue exitoso
        """
        try:
            if not self.multi_controller:
                logger.warning("⚠️ Controlador no inicializado (modo simulación)")
                self.servo_configs[servo_id] = config
                return True
            
            # Extraer parámetros
            profile = ServoProfile(config.get("profile", "mg995_standard"))
            direction = ServoDirection(config.get("direction", "forward"))
            
            # Añadir servo al controlador
            success = self.multi_controller.add_servo(
                servo_id=servo_id,
                pin=config["pin_bcm"],
                name=config.get("name", f"Servo_{servo_id}"),
                profile=profile,
                default_angle=config.get("default_angle", 90),
                activation_angle=config.get("activation_angle", 0),
                direction=direction,
                movement_speed=config.get("movement_speed", 0.8),
                smooth_movement=config.get("smooth_movement", True),
                min_safe_angle=config.get("min_safe_angle", 0),
                max_safe_angle=config.get("max_safe_angle", 180),
                hold_torque=config.get("hold_torque", True)
            )
            
            if success:
                self.servo_configs[servo_id] = config
                logger.info(f"✅ Servo '{servo_id}' añadido")
            else:
                logger.error(f"❌ Error añadiendo servo '{servo_id}'")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error añadiendo servo: {e}")
            return False
    
    async def remove_servo(self, servo_id: str) -> bool:
        """
        Elimina un servo del sistema.
        
        Args:
            servo_id: ID del servo
            
        Returns:
            True si fue exitoso
        """
        try:
            if self.multi_controller:
                success = self.multi_controller.remove_servo(servo_id)
            else:
                success = servo_id in self.servo_configs
            
            if success and servo_id in self.servo_configs:
                del self.servo_configs[servo_id]
                logger.info(f"✅ Servo '{servo_id}' eliminado")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error eliminando servo: {e}")
            return False
    
    async def move_servo(self, servo_id: str, angle: float, smooth: bool = True) -> bool:
        """
        Mueve un servo a un ángulo específico.
        
        Args:
            servo_id: ID del servo
            angle: Ángulo objetivo (0-180)
            smooth: Si True, usa movimiento suave
            
        Returns:
            True si fue exitoso
        """
        try:
            if not self.multi_controller:
                logger.info(f"🎭 SIMULACIÓN: Moviendo servo '{servo_id}' a {angle}°")
                # Actualizar estado simulado
                if servo_id not in self.servo_status:
                    self.servo_status[servo_id] = {}
                self.servo_status[servo_id]["current_angle"] = angle
                self.servo_status[servo_id]["last_move"] = datetime.now().isoformat()
                self.stats["total_movements"] += 1
                return True
            
            controller = self.multi_controller.get_servo(servo_id)
            if not controller:
                logger.error(f"❌ Servo '{servo_id}' no encontrado")
                return False
            
            success = await controller.set_angle_async(angle, smooth)
            
            if success:
                self.stats["total_movements"] += 1
                logger.info(f"✅ Servo '{servo_id}' movido a {angle}°")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error moviendo servo: {e}")
            self.stats["errors"] += 1
            return False
    
    async def activate_servo(self, servo_id: str) -> bool:
        """
        Activa un servo (mueve a posición de activación y regresa).
        
        Args:
            servo_id: ID del servo
            
        Returns:
            True si fue exitoso
        """
        try:
            config = self.servo_configs.get(servo_id)
            if not config:
                logger.error(f"❌ Configuración de servo '{servo_id}' no encontrada")
                return False
            
            # Mover a posición de activación
            activation_angle = config.get("activation_angle", 0)
            default_angle = config.get("default_angle", 90)
            
            logger.info(f"🎯 Activando servo '{servo_id}': {default_angle}° → {activation_angle}°")
            
            # Mover a activación
            await self.move_servo(servo_id, activation_angle, smooth=True)
            await asyncio.sleep(1.0)  # Mantener posición
            
            # Regresar a default
            await self.move_servo(servo_id, default_angle, smooth=True)
            
            self.stats["total_activations"] += 1
            
            # Actualizar estado
            if servo_id not in self.servo_status:
                self.servo_status[servo_id] = {}
            self.servo_status[servo_id]["activation_count"] = \
                self.servo_status[servo_id].get("activation_count", 0) + 1
            self.servo_status[servo_id]["last_activation"] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error activando servo: {e}")
            self.stats["errors"] += 1
            return False
    
    async def reset_servo(self, servo_id: str) -> bool:
        """
        Resetea un servo a su posición por defecto.
        
        Args:
            servo_id: ID del servo
            
        Returns:
            True si fue exitoso
        """
        try:
            config = self.servo_configs.get(servo_id)
            if not config:
                return False
            
            default_angle = config.get("default_angle", 90)
            return await self.move_servo(servo_id, default_angle, smooth=True)
            
        except Exception as e:
            logger.error(f"❌ Error reseteando servo: {e}")
            return False
    
    async def update_servo_config(self, servo_id: str, updates: Dict) -> bool:
        """
        Actualiza la configuración de un servo.
        
        Args:
            servo_id: ID del servo
            updates: Diccionario con actualizaciones
            
        Returns:
            True si fue exitoso
        """
        try:
            if servo_id not in self.servo_configs:
                logger.error(f"❌ Servo '{servo_id}' no encontrado")
                return False
            
            # Actualizar configuración local
            self.servo_configs[servo_id].update(updates)
            
            # Si hay controlador, actualizar también
            if self.multi_controller:
                controller = self.multi_controller.get_servo(servo_id)
                if controller:
                    # Convertir formato si es necesario
                    if "direction" in updates:
                        updates["direction"] = ServoDirection(updates["direction"])
                    if "profile" in updates:
                        updates["profile"] = ServoProfile(updates["profile"])
                    
                    controller.update_config(**updates)
            
            # Guardar configuración
            await self.save_configuration()
            
            logger.info(f"✅ Configuración de servo '{servo_id}' actualizada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando configuración: {e}")
            return False
    
    async def get_servo_status(self, servo_id: Optional[str] = None) -> Dict:
        """
        Obtiene el estado de uno o todos los servos.
        
        Args:
            servo_id: ID del servo (None para todos)
            
        Returns:
            Diccionario con estado
        """
        try:
            if servo_id:
                # Estado de un servo específico
                if self.multi_controller:
                    controller = self.multi_controller.get_servo(servo_id)
                    if controller:
                        status = controller.get_status()
                    else:
                        status = {"error": "Servo no encontrado"}
                else:
                    # Modo simulación
                    status = self.servo_status.get(servo_id, {
                        "id": servo_id,
                        "initialized": False,
                        "simulation_mode": True,
                        "current_angle": self.servo_configs.get(servo_id, {}).get("default_angle", 90)
                    })
                
                # Añadir estadísticas
                if servo_id in self.servo_status:
                    status.update(self.servo_status[servo_id])
                
                return status
            
            else:
                # Estado de todos los servos
                all_status = {}
                
                if self.multi_controller:
                    all_status = self.multi_controller.get_status()
                else:
                    # Modo simulación
                    for sid in self.servo_configs:
                        all_status[sid] = await self.get_servo_status(sid)
                
                return all_status
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas del sistema.
        
        Returns:
            Diccionario con estadísticas
        """
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_movements": self.stats["total_movements"],
            "total_activations": self.stats["total_activations"],
            "errors": self.stats["errors"],
            "servos_configured": len(self.servo_configs),
            "hardware_pwm": SERVO_CONTROLLER_AVAILABLE,
            "simulation_mode": not self.multi_controller
        }
    
    async def emergency_stop(self) -> bool:
        """
        Detiene todos los servos inmediatamente.
        
        Returns:
            True si fue exitoso
        """
        try:
            logger.warning("🚨 Parada de emergencia de servos")
            
            if self.multi_controller:
                # Resetear todos los servos a posición segura
                for servo_id in self.servo_configs:
                    await self.reset_servo(servo_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en parada de emergencia: {e}")
            return False
    
    async def cleanup(self):
        """Limpia recursos del módulo."""
        try:
            logger.info("🧹 Limpiando ServoControlModule...")
            
            # Resetear servos
            for servo_id in self.servo_configs:
                await self.reset_servo(servo_id)
            
            # Limpiar controlador
            if self.multi_controller:
                self.multi_controller.cleanup_all()
            
            # Guardar configuración final
            await self.save_configuration()
            
            logger.info("✅ ServoControlModule limpiado")
            
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")


# ==================== API HANDLERS ====================

async def handle_servo_request(module: ServoControlModule, request: Dict) -> Dict:
    """
    Maneja una solicitud de la API para control de servos.
    
    Args:
        module: Instancia del módulo de control
        request: Diccionario con la solicitud
        
    Returns:
        Diccionario con la respuesta
    """
    try:
        action = request.get("action")
        servo_id = request.get("servo_id")
        params = request.get("params", {})
        
        # Procesar según la acción
        if action == "move":
            angle = params.get("angle", 90)
            smooth = params.get("smooth", True)
            success = await module.move_servo(servo_id, angle, smooth)
            return {"success": success, "angle": angle}
        
        elif action == "activate":
            success = await module.activate_servo(servo_id)
            return {"success": success}
        
        elif action == "reset":
            success = await module.reset_servo(servo_id)
            return {"success": success}
        
        elif action == "update_config":
            updates = params.get("updates", {})
            success = await module.update_servo_config(servo_id, updates)
            return {"success": success}
        
        elif action == "get_status":
            status = await module.get_servo_status(servo_id)
            return {"success": True, "status": status}
        
        elif action == "get_all_status":
            status = await module.get_servo_status()
            return {"success": True, "status": status}
        
        elif action == "get_statistics":
            stats = await module.get_statistics()
            return {"success": True, "statistics": stats}
        
        elif action == "emergency_stop":
            success = await module.emergency_stop()
            return {"success": success}
        
        else:
            return {"success": False, "error": f"Acción desconocida: {action}"}
            
    except Exception as e:
        logger.error(f"❌ Error manejando solicitud: {e}")
        return {"success": False, "error": str(e)}


# ==================== TEST ====================

async def test_module():
    """Función de prueba del módulo."""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Probando ServoControlModule...")
    print("=" * 50)
    
    module = ServoControlModule()
    
    try:
        # Inicializar
        await module.initialize()
        
        # Obtener estado
        print("\n📊 Estado inicial:")
        status = await module.get_servo_status()
        print(json.dumps(status, indent=2))
        
        # Probar movimientos
        print("\n🎯 Probando movimientos...")
        await module.move_servo("servo1", 0)
        await asyncio.sleep(1)
        await module.move_servo("servo1", 180)
        await asyncio.sleep(1)
        await module.move_servo("servo1", 90)
        
        # Probar activación
        print("\n⚡ Probando activación...")
        await module.activate_servo("servo1")
        
        # Estadísticas
        print("\n📈 Estadísticas:")
        stats = await module.get_statistics()
        print(json.dumps(stats, indent=2))
        
    except KeyboardInterrupt:
        print("\n⚡ Interrumpido")
    finally:
        await module.cleanup()


if __name__ == "__main__":
    asyncio.run(test_module())
