#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Script de Prueba del Sistema de Servos - VisiFruit
=====================================================

Script para probar y validar el funcionamiento correcto del sistema
de control de servos MG995 en Raspberry Pi 5.

Autor: Sistema VisiFruit
Fecha: Enero 2025
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
            "movement_test": False,
            "config_test": False
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
        """Prueba la inicialización de servos."""
        print("\n🔧 Inicializando Servos...")
        print("-" * 40)
        
        try:
            # Servo 1 - GPIO 12
            success1 = self.multi_controller.add_servo(
                "servo1",
                pin=12,
                name="Servo_Test_1",
                profile=ServoProfile.MG995_EXTENDED,
                default_angle=90,
                activation_angle=0,
                direction=ServoDirection.FORWARD
            )
            
            if success1:
                print("✅ Servo 1 inicializado (GPIO 12)")
                self.test_results["servo1_test"] = True
            else:
                print("❌ Error inicializando Servo 1")
            
            # Servo 2 - GPIO 13
            success2 = self.multi_controller.add_servo(
                "servo2",
                pin=13,
                name="Servo_Test_2",
                profile=ServoProfile.MG995_EXTENDED,
                default_angle=90,
                activation_angle=180,
                direction=ServoDirection.FORWARD
            )
            
            if success2:
                print("✅ Servo 2 inicializado (GPIO 13)")
                self.test_results["servo2_test"] = True
            else:
                print("❌ Error inicializando Servo 2")
            
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
        
        return success1 and success2
    
    async def test_basic_movements(self):
        """Prueba movimientos básicos de los servos."""
        print("\n🎮 Probando Movimientos Básicos...")
        print("-" * 40)
        
        try:
            # Obtener controladores
            servo1 = self.multi_controller.get_servo("servo1")
            servo2 = self.multi_controller.get_servo("servo2")
            
            if not servo1 or not servo2:
                print("❌ No se pudieron obtener los controladores")
                return False
            
            print("\n📐 Moviendo Servo 1...")
            test_angles = [0, 45, 90, 135, 180, 90]
            
            for angle in test_angles:
                print(f"   → {angle}°")
                await servo1.set_angle_async(angle, smooth=True)
                await asyncio.sleep(0.8)
            
            print("\n📐 Moviendo Servo 2...")
            for angle in test_angles:
                print(f"   → {angle}°")
                await servo2.set_angle_async(angle, smooth=True)
                await asyncio.sleep(0.8)
            
            self.test_results["movement_test"] = True
            print("✅ Movimientos completados")
            return True
            
        except Exception as e:
            print(f"❌ Error en movimientos: {e}")
            return False
    
    async def test_synchronized_movement(self):
        """Prueba movimientos sincronizados."""
        print("\n🔄 Probando Movimientos Sincronizados...")
        print("-" * 40)
        
        try:
            angles = [0, 90, 180, 90]
            
            for angle in angles:
                print(f"   → Ambos servos a {angle}°")
                results = await self.multi_controller.move_all(angle, smooth=True)
                print(f"      Resultados: {results}")
                await asyncio.sleep(1.5)
            
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
        """Prueba secuencia de activación."""
        print("\n🎯 Probando Secuencia de Activación...")
        print("-" * 40)
        
        try:
            servo1 = self.multi_controller.get_servo("servo1")
            servo2 = self.multi_controller.get_servo("servo2")
            
            if not servo1 or not servo2:
                return False
            
            print("   Activando Servo 1...")
            await servo1.move_to_activation()
            await asyncio.sleep(1)
            await servo1.move_to_default()
            await asyncio.sleep(0.5)
            
            print("   Activando Servo 2...")
            await servo2.move_to_activation()
            await asyncio.sleep(1)
            await servo2.move_to_default()
            await asyncio.sleep(0.5)
            
            print("✅ Secuencia de activación completada")
            return True
            
        except Exception as e:
            print(f"❌ Error en activación: {e}")
            return False
    
    async def show_status(self):
        """Muestra el estado del sistema."""
        print("\n📊 Estado del Sistema")
        print("-" * 40)
        
        try:
            status = self.multi_controller.get_status()
            
            for servo_id, servo_status in status.items():
                print(f"\n📍 {servo_status['name']} ({servo_id}):")
                print(f"   Pin: GPIO {servo_status['pin']}")
                print(f"   Hardware PWM: {'✅' if servo_status['hardware_pwm'] else '❌'}")
                print(f"   Ángulo actual: {servo_status['current_angle']}°")
                print(f"   Dirección: {servo_status['direction']}")
                print(f"   Perfil: {servo_status['profile']}")
            
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
    """Modo de prueba interactivo."""
    print("\n" + "=" * 50)
    print("🎮 MODO INTERACTIVO - CONTROL DE SERVOS")
    print("=" * 50)
    
    controller = RPi5MultiServoController()
    
    # Configurar servos
    controller.add_servo("servo1", pin=12, name="Servo 1", profile=ServoProfile.MG995_EXTENDED)
    controller.add_servo("servo2", pin=13, name="Servo 2", profile=ServoProfile.MG995_EXTENDED)
    
    try:
        while True:
            print("\n📋 Opciones:")
            print("1. Mover Servo 1")
            print("2. Mover Servo 2")
            print("3. Mover ambos servos")
            print("4. Secuencia de prueba")
            print("5. Ver estado")
            print("0. Salir")
            
            choice = input("\nSelecciona opción: ").strip()
            
            if choice == "0":
                break
            
            elif choice == "1":
                angle = float(input("Ángulo para Servo 1 (0-180): "))
                servo1 = controller.get_servo("servo1")
                if servo1:
                    await servo1.set_angle_async(angle)
                    print(f"✅ Servo 1 movido a {angle}°")
            
            elif choice == "2":
                angle = float(input("Ángulo para Servo 2 (0-180): "))
                servo2 = controller.get_servo("servo2")
                if servo2:
                    await servo2.set_angle_async(angle)
                    print(f"✅ Servo 2 movido a {angle}°")
            
            elif choice == "3":
                angle = float(input("Ángulo para ambos servos (0-180): "))
                await controller.move_all(angle)
                print(f"✅ Ambos servos movidos a {angle}°")
            
            elif choice == "4":
                print("Ejecutando secuencia de prueba...")
                for angle in [0, 45, 90, 135, 180, 90]:
                    print(f"   → {angle}°")
                    await controller.move_all(angle)
                    await asyncio.sleep(1)
                print("✅ Secuencia completada")
            
            elif choice == "5":
                status = controller.get_status()
                for sid, info in status.items():
                    print(f"\n{info['name']}:")
                    print(f"   Ángulo: {info['current_angle']}°")
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
