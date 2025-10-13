#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Script de Prueba del Sistema de Servos MG995 - VisiFruit Prototipo
=======================================================================

Script mejorado para probar los 3 servomotores MG995 del prototipo:
- Servo 1 (GPIO 12): Clasificador manzanas - 90° actuado / 180° reposo
- Servo 2 (GPIO 13): Clasificador peras - 100° actuado / 150° reposo  
- Servo 3 (GPIO 20): Clasificador limones - Configurable

MODO DEMO: Solo usa ángulos de reposo
MODO PRODUCCIÓN: Usa ángulos de actuación en main_etiquetadora_v4.py

Autor: Sistema VisiFruit
Fecha: Enero 2025
Versión: 2.0 - 3 Servos Edition
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar controlador
try:
    from rpi5_servo_controller import (
        RPi5ServoController,
        RPi5MultiServoController,
        ServoConfig,
        ServoProfile,
        ServoDirection
    )
    CONTROLLER_AVAILABLE = True
except ImportError:
    logger.error("❌ No se pudo importar rpi5_servo_controller")
    logger.error("   Asegúrate de estar en el directorio correcto")
    CONTROLLER_AVAILABLE = False
    sys.exit(1)


class ServoSystemTester:
    """Clase para realizar pruebas del sistema de servos."""
    
    def __init__(self):
        """Inicializa el tester."""
        self.multi_controller = RPi5MultiServoController()
        self.test_results = {
            "hardware_pwm": False,
            "servo1_test": False,
            "servo2_test": False,
            "servo3_test": False,
            "movement_test": False,
            "config_test": False
        }
        
        # Configuración de ángulos según especificación del usuario
        # DEMO: Solo se usan los ángulos de reposo
        # PRODUCCIÓN: Los ángulos de actuación se usan en detección real
        self.servo_configs = {
            "servo1": {
                "name": "Clasificador_Manzanas",
                "pin": 12,
                "rest_angle": 180,      # Posición normal sin detector
                "actuation_angle": 90,  # Cuando detecta frutas
                "category": "apple"
            },
            "servo2": {
                "name": "Clasificador_Peras",
                "pin": 13,
                "rest_angle": 150,      # Cuando no detecta nada
                "actuation_angle": 100, # Cuando detecta frutas
                "category": "pear"
            },
            "servo3": {
                "name": "Clasificador_Limones",
                "pin": 20,
                "rest_angle": 90,       # Posición de reposo
                "actuation_angle": 10,  # Cuando detecta frutas
                "category": "lemon"
            }
        }
    
    async def test_hardware_pwm(self):
        """Prueba la disponibilidad de hardware PWM."""
        print("\n🔍 Probando Hardware PWM...")
        print("-" * 40)
        
        try:
            # Intentar crear servo en GPIO 12 (hardware PWM)
            config = ServoConfig(
                pin_bcm=12,
                name="Test_PWM",
                profile=ServoProfile.MG995_EXTENDED
            )
            
            controller = RPi5ServoController(config, auto_init=False)
            success = controller.initialize()
            
            if success:
                print("✅ Hardware PWM disponible en GPIO 12")
                self.test_results["hardware_pwm"] = True
                controller.cleanup()
            else:
                print("❌ No se pudo inicializar hardware PWM")
            
        except Exception as e:
            print(f"❌ Error probando hardware PWM: {e}")
        
        return self.test_results["hardware_pwm"]
    
    async def test_servo_initialization(self):
        """Prueba la inicialización de los 3 servos."""
        print("\n🔧 Inicializando 3 Servos MG995...")
        print("-" * 60)
        print("📝 Configuración de Ángulos:")
        print("   Servo 1 (GPIO 12): 180° reposo / 90° actuación")
        print("   Servo 2 (GPIO 13): 150° reposo / 100° actuación")
        print("   Servo 3 (GPIO 20): 90° reposo / 10° actuación")
        print("-" * 60)
        
        success_list = []
        
        try:
            # Inicializar los 3 servos con configuración especificada
            for servo_id, config in self.servo_configs.items():
                print(f"\n🔩 Inicializando {config['name']}...")
                
                success = self.multi_controller.add_servo(
                    servo_id,
                    pin=config['pin'],
                    name=config['name'],
                    profile=ServoProfile.MG995_EXTENDED,
                    default_angle=config['rest_angle'],
                    activation_angle=config['actuation_angle'],
                    direction=ServoDirection.FORWARD
                )
                
                if success:
                    print(f"✅ {config['name']} inicializado (GPIO {config['pin']})")
                    print(f"   📐 Reposo: {config['rest_angle']}° | Actuación: {config['actuation_angle']}°")
                    self.test_results[f"{servo_id}_test"] = True
                    success_list.append(True)
                else:
                    print(f"❌ Error inicializando {config['name']}")
                    success_list.append(False)
            
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
            return False
        
        return all(success_list)
    
    async def test_basic_movements(self):
        """Prueba movimientos básicos de los 3 servos."""
        print("\n🎮 Probando Movimientos Básicos de 3 Servos...")
        print("-" * 60)
        print("ℹ️  MODO DEMO: Solo se prueban posiciones de REPOSO")
        print("-" * 60)
        
        try:
            # Probar cada servo individualmente
            for servo_id, config in self.servo_configs.items():
                servo = self.multi_controller.get_servo(servo_id)
                
                if not servo:
                    print(f"❌ No se pudo obtener {config['name']}")
                    continue
                
                print(f"\n📐 Moviendo {config['name']} (GPIO {config['pin']})...")
                
                # Para el demo, solo usar ángulos de reposo + algunas posiciones intermedias
                rest = config['rest_angle']
                test_angles = [
                    rest,                           # Posición de reposo
                    rest - 30 if rest >= 30 else 0, # -30 grados
                    rest,                           # Volver a reposo
                    rest + 30 if rest <= 150 else 180, # +30 grados
                    rest                            # Volver a reposo
                ]
                
                for angle in test_angles:
                    print(f"   → {angle}°")
                    await servo.set_angle_async(angle, smooth=True)
                    await asyncio.sleep(0.8)
                
                print(f"   ✅ {config['name']} completado")
            
            self.test_results["movement_test"] = True
            print("\n✅ Movimientos básicos de 3 servos completados")
            return True
            
        except Exception as e:
            print(f"❌ Error en movimientos: {e}")
            return False
    
    async def test_synchronized_movement(self):
        """Prueba movimientos sincronizados de los 3 servos."""
        print("\n🔄 Probando Movimientos Sincronizados (3 servos)...")
        print("-" * 60)
        
        try:
            # Mover todos a sus posiciones de reposo
            print("   → Moviendo todos a posición de REPOSO")
            for servo_id, config in self.servo_configs.items():
                servo = self.multi_controller.get_servo(servo_id)
                if servo:
                    await servo.set_angle_async(config['rest_angle'], smooth=True)
            await asyncio.sleep(2.0)
            
            # Secuencia de prueba sincronizada
            print("   → Moviendo todos a 90° (centro)")
            await self.multi_controller.move_all(90, smooth=True)
            await asyncio.sleep(2.0)
            
            # Volver cada uno a su reposo
            print("   → Regresando cada servo a su posición de reposo")
            for servo_id, config in self.servo_configs.items():
                servo = self.multi_controller.get_servo(servo_id)
                if servo:
                    await servo.set_angle_async(config['rest_angle'], smooth=True)
            await asyncio.sleep(2.0)
            
            print("✅ Movimientos sincronizados completados")
            return True
            
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
            return False
    
    async def test_configuration_update(self):
        """Prueba actualización de configuración."""
        print("\n⚙️ Probando Actualización de Configuración...")
        print("-" * 40)
        
        try:
            servo1 = self.multi_controller.get_servo("servo1")
            if not servo1:
                print("❌ No se pudo obtener servo1")
                return False
            
            # Cambiar dirección
            print("   Cambiando dirección a REVERSE...")
            servo1.update_config(direction=ServoDirection.REVERSE)
            
            # Probar con nueva dirección
            print("   Moviendo con dirección invertida...")
            await servo1.set_angle_async(45)
            await asyncio.sleep(1)
            
            # Cambiar velocidad
            print("   Cambiando velocidad a 50%...")
            servo1.update_config(movement_speed=0.5)
            
            # Probar con nueva velocidad
            print("   Moviendo con velocidad reducida...")
            await servo1.set_angle_async(135)
            await asyncio.sleep(1.5)
            
            # Restaurar configuración
            servo1.update_config(
                direction=ServoDirection.FORWARD,
                movement_speed=0.8
            )
            
            self.test_results["config_test"] = True
            print("✅ Actualización de configuración exitosa")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando configuración: {e}")
            return False
    
    async def test_activation_sequence(self):
        """Prueba secuencia de activación con los 3 servos."""
        print("\n🎯 Probando Secuencia de Activación (DEMO - Solo Reposo)...")
        print("-" * 60)
        print("⚠️  En DEMO se usan posiciones de REPOSO")
        print("⚠️  En PRODUCCIÓN se usarán posiciones de ACTUACIÓN")
        print("-" * 60)
        
        try:
            # Probar secuencia de cada servo
            for servo_id, config in self.servo_configs.items():
                servo = self.multi_controller.get_servo(servo_id)
                
                if not servo:
                    print(f"❌ Servo {servo_id} no disponible")
                    continue
                
                print(f"\n   🔹 Probando {config['name']} ({config['category']})...")
                print(f"      Demo: Moviendo a reposo ({config['rest_angle']}°)")
                print(f"      [En producción usaría: {config['actuation_angle']}°]")
                
                # En demo, solo mover a posición de reposo
                await servo.move_to_default()  # Posición de reposo
                await asyncio.sleep(1.5)
                
                print(f"      ✅ {config['name']} completado")
            
            print("\n✅ Secuencia de activación DEMO completada")
            return True
            
        except Exception as e:
            print(f"❌ Error en activación: {e}")
            return False
    
    async def show_status(self):
        """Muestra el estado del sistema con 3 servos."""
        print("\n📊 Estado del Sistema - 3 Servos MG995")
        print("=" * 60)
        
        try:
            status = self.multi_controller.get_status()
            
            for servo_id, servo_status in status.items():
                config = self.servo_configs.get(servo_id, {})
                
                print(f"\n📍 {servo_status['name']} ({servo_id}):")
                print(f"   Pin: GPIO {servo_status['pin']}")
                print(f"   Hardware PWM: {'✅' if servo_status['hardware_pwm'] else '❌'}")
                print(f"   Ángulo actual: {servo_status['current_angle']}°")
                if config:
                    print(f"   Ángulo reposo: {config['rest_angle']}°")
                    print(f"   Ángulo actuación: {config['actuation_angle']}° (usado en producción)")
                    print(f"   Categoría: {config['category']}")
                print(f"   Dirección: {servo_status['direction']}")
                print(f"   Perfil: {servo_status['profile']}")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ Error obteniendo estado: {e}")
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        print("\n" + "=" * 50)
        print("🧪 INICIANDO PRUEBAS DEL SISTEMA DE SERVOS")
        print("=" * 50)
        
        try:
            # Pruebas secuenciales
            if await self.test_hardware_pwm():
                if await self.test_servo_initialization():
                    await self.test_basic_movements()
                    await self.test_synchronized_movement()
                    await self.test_configuration_update()
                    await self.test_activation_sequence()
                    await self.show_status()
            
            # Resumen de resultados
            print("\n" + "=" * 50)
            print("📋 RESUMEN DE RESULTADOS")
            print("=" * 50)
            
            for test_name, result in self.test_results.items():
                status = "✅ PASÓ" if result else "❌ FALLÓ"
                print(f"{test_name}: {status}")
            
            # Resultado general
            all_passed = all(self.test_results.values())
            if all_passed:
                print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
            else:
                print("\n⚠️ ALGUNAS PRUEBAS FALLARON")
                print("   Revisa la configuración y conexiones")
            
        except KeyboardInterrupt:
            print("\n⚡ Pruebas interrumpidas por usuario")
        
        finally:
            # Limpiar
            print("\n🧹 Limpiando recursos...")
            self.multi_controller.cleanup_all()
            print("✅ Limpieza completada")


async def interactive_test():
    """Modo de prueba interactivo con 3 servos."""
    print("\n" + "=" * 60)
    print("🎮 MODO INTERACTIVO - CONTROL DE 3 SERVOS MG995")
    print("=" * 60)
    
    controller = RPi5MultiServoController()
    
    # Configurar los 3 servos
    servo_configs = {
        "servo1": {"pin": 12, "name": "Clasificador Manzanas", "rest": 180, "act": 90},
        "servo2": {"pin": 13, "name": "Clasificador Peras", "rest": 150, "act": 100},
        "servo3": {"pin": 20, "name": "Clasificador Limones", "rest": 90, "act": 10}
    }
    
    for sid, cfg in servo_configs.items():
        controller.add_servo(
            sid, 
            pin=cfg["pin"], 
            name=cfg["name"], 
            profile=ServoProfile.MG995_EXTENDED,
            default_angle=cfg["rest"],
            activation_angle=cfg["act"]
        )
    
    try:
        while True:
            print("\n📋 Opciones:")
            print("1. Mover Servo 1 (Manzanas - GPIO 12)")
            print("2. Mover Servo 2 (Peras - GPIO 13)")
            print("3. Mover Servo 3 (Limones - GPIO 20)")
            print("4. Mover todos los servos")
            print("5. Secuencia de prueba (3 servos)")
            print("6. Todos a posición de REPOSO")
            print("7. Todos a posición de ACTUACIÓN")
            print("8. Ver estado")
            print("0. Salir")
            
            choice = input("\nSelecciona opción: ").strip()
            
            if choice == "0":
                break
            
            elif choice in ["1", "2", "3"]:
                servo_map = {"1": "servo1", "2": "servo2", "3": "servo3"}
                servo_id = servo_map[choice]
                cfg = servo_configs[servo_id]
                
                angle = float(input(f"Ángulo para {cfg['name']} (0-180): "))
                servo = controller.get_servo(servo_id)
                if servo:
                    await servo.set_angle_async(angle)
                    print(f"✅ {cfg['name']} movido a {angle}°")
            
            elif choice == "4":
                angle = float(input("Ángulo para todos los servos (0-180): "))
                await controller.move_all(angle)
                print(f"✅ Todos los servos movidos a {angle}°")
            
            elif choice == "5":
                print("Ejecutando secuencia de prueba con 3 servos...")
                for angle in [0, 45, 90, 135, 180, 90]:
                    print(f"   → {angle}°")
                    await controller.move_all(angle)
                    await asyncio.sleep(1)
                print("✅ Secuencia completada")
            
            elif choice == "6":
                print("Moviendo todos a posición de REPOSO...")
                for sid, cfg in servo_configs.items():
                    servo = controller.get_servo(sid)
                    if servo:
                        await servo.set_angle_async(cfg["rest"])
                        print(f"   {cfg['name']}: {cfg['rest']}°")
                print("✅ Todos en posición de reposo")
            
            elif choice == "7":
                print("⚠️  CUIDADO: Moviendo todos a posición de ACTUACIÓN...")
                for sid, cfg in servo_configs.items():
                    servo = controller.get_servo(sid)
                    if servo:
                        await servo.set_angle_async(cfg["act"])
                        print(f"   {cfg['name']}: {cfg['act']}°")
                print("✅ Todos en posición de actuación")
            
            elif choice == "8":
                status = controller.get_status()
                for sid, info in status.items():
                    cfg = servo_configs.get(sid, {})
                    print(f"\n{info['name']}:")
                    print(f"   Ángulo: {info['current_angle']}°")
                    if cfg:
                        print(f"   Reposo: {cfg['rest']}° | Actuación: {cfg['act']}°")
                    print(f"   Hardware PWM: {info['hardware_pwm']}")
            
    except KeyboardInterrupt:
        print("\n⚡ Saliendo...")
    
    finally:
        controller.cleanup_all()
        print("✅ Recursos limpiados")


async def main():
    """Función principal."""
    print("\n🎮 Sistema de Prueba de Servos MG995 - VisiFruit")
    print("Raspberry Pi 5 - Hardware PWM Optimizado")
    print("\nOpciones:")
    print("1. Ejecutar todas las pruebas")
    print("2. Modo interactivo")
    print("3. Salir")
    
    choice = input("\nSelecciona opción: ").strip()
    
    if choice == "1":
        tester = ServoSystemTester()
        await tester.run_all_tests()
    
    elif choice == "2":
        await interactive_test()
    
    else:
        print("👋 Saliendo...")


if __name__ == "__main__":
    asyncio.run(main())
