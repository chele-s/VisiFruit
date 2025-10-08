#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Script de Prueba y Calibración de Servos MG995
=================================================

Este script te permite probar y calibrar los servomotores MG995
del sistema de clasificación del prototipo VisiFruit.

Características:
- Prueba individual de cada servo (manzanas, peras, limones)
- Prueba secuencial de todos los servos
- Calibración de ángulos
- Verificación de sistema de hold rígido
- Monitoreo de oscilaciones

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 1.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# Añadir directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Prototipo_Clasificador.mg995_servo_controller import MG995ServoController, FruitCategory
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def load_config() -> dict:
    """Carga la configuración del prototipo."""
    config_path = Path("Prototipo_Clasificador/Config_Prototipo.json")
    if not config_path.exists():
        logger.error(f"❌ No se encontró el archivo de configuración: {config_path}")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def test_individual_servo(controller: MG995ServoController, category: FruitCategory):
    """
    Prueba un servo individual.
    
    Args:
        controller: Controlador de servos
        category: Categoría a probar
    """
    print(f"\n{'='*60}")
    print(f"🧪 Probando Servo: {category.value.upper()}")
    print(f"{'='*60}")
    
    servo = controller.servos.get(category)
    if not servo:
        print(f"❌ Servo {category.value} no encontrado")
        return
    
    # Mostrar configuración
    print(f"\n📋 Configuración:")
    print(f"   Pin BCM: {servo.pin_bcm}")
    print(f"   Posición default: {servo.default_angle}°")
    print(f"   Posición activación: {servo.activation_angle}°")
    print(f"   Movimiento: {servo.activation_angle - servo.default_angle:+.0f}°")
    print(f"   Duración hold: {servo.hold_duration_s}s")
    print(f"   Retorno suave: {'Sí' if servo.return_smoothly else 'No'}")
    
    input(f"\n👉 Presiona ENTER para activar el servo {category.value}...")
    
    # Activar servo
    print(f"\n🚀 Activando servo...")
    success = await controller.activate_servo(category)
    
    if success:
        print(f"✅ Servo {category.value} activado correctamente")
        print(f"\n🔍 Verifica visualmente:")
        print(f"   1. El servo se movió {servo.activation_angle - servo.default_angle:+.0f}° sin oscilaciones")
        print(f"   2. Se mantuvo RÍGIDO en la posición por {servo.hold_duration_s}s")
        print(f"   3. Regresó suavemente a la posición inicial")
        print(f"   4. Se detuvo completamente sin vibrar")
    else:
        print(f"❌ Error activando servo {category.value}")

async def test_all_servos_sequence(controller: MG995ServoController):
    """Prueba todos los servos en secuencia."""
    print(f"\n{'='*60}")
    print(f"🔄 PRUEBA SECUENCIAL DE TODOS LOS SERVOS")
    print(f"{'='*60}")
    print(f"\nSe activarán los servos en orden:")
    print(f"   1. 🍎 Manzanas")
    print(f"   2. 🍐 Peras")
    print(f"   3. 🍋 Limones")
    
    input(f"\n👉 Presiona ENTER para iniciar la secuencia...")
    
    categories = [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]
    
    for i, category in enumerate(categories, 1):
        print(f"\n{'='*60}")
        print(f"Servo {i}/3: {category.value.upper()}")
        print(f"{'='*60}")
        
        success = await controller.activate_servo(category)
        
        if success:
            print(f"✅ Servo {category.value} completado")
        else:
            print(f"❌ Error en servo {category.value}")
        
        # Pausa entre servos
        if i < len(categories):
            print(f"\n⏳ Esperando 2 segundos antes del siguiente servo...")
            await asyncio.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"✅ Secuencia completada")
    print(f"{'='*60}")

async def test_rapid_activation(controller: MG995ServoController, category: FruitCategory):
    """Prueba activación rápida para verificar protección."""
    print(f"\n{'='*60}")
    print(f"⚡ PRUEBA DE ACTIVACIÓN RÁPIDA - {category.value.upper()}")
    print(f"{'='*60}")
    print(f"\nEsta prueba verifica que el sistema evite activaciones simultáneas")
    
    input(f"\n👉 Presiona ENTER para probar activaciones rápidas...")
    
    print(f"\n🚀 Intentando 3 activaciones rápidas...")
    
    for i in range(3):
        print(f"\n   Activación {i+1}/3:")
        success = await controller.activate_servo(category)
        if success:
            print(f"   ✅ Activación {i+1} aceptada")
        else:
            print(f"   ⚠️ Activación {i+1} rechazada (esperado - protección activa)")
        
        # Intentar activar rápidamente
        await asyncio.sleep(0.1)
    
    print(f"\n✅ Prueba completada")
    print(f"   Solo una activación debería haberse ejecutado")

async def calibration_mode(controller: MG995ServoController):
    """Modo de calibración interactivo."""
    print(f"\n{'='*60}")
    print(f"🔧 MODO DE CALIBRACIÓN")
    print(f"{'='*60}")
    print(f"\nEste modo te permite mover los servos manualmente")
    print(f"para calibrar los ángulos correctos.\n")
    
    while True:
        print(f"\n{'='*60}")
        print(f"Selecciona un servo para calibrar:")
        print(f"  [1] 🍎 Manzanas")
        print(f"  [2] 🍐 Peras")
        print(f"  [3] 🍋 Limones")
        print(f"  [4] 🏠 Todos a posición inicial")
        print(f"  [0] Salir")
        print(f"{'='*60}")
        
        choice = input("\n👉 Opción: ").strip()
        
        if choice == "0":
            break
        elif choice == "4":
            await controller.home_all_servos()
            print("✅ Todos los servos en posición inicial")
            continue
        
        # Mapear opción a categoría
        category_map = {
            "1": FruitCategory.APPLE,
            "2": FruitCategory.PEAR,
            "3": FruitCategory.LEMON
        }
        
        category = category_map.get(choice)
        if not category:
            print("❌ Opción inválida")
            continue
        
        # Solicitar ángulo
        try:
            angle_str = input(f"   Ángulo (0-180°): ").strip()
            angle = float(angle_str)
            
            if angle < 0 or angle > 180:
                print("❌ Ángulo debe estar entre 0 y 180")
                continue
            
            print(f"\n🔄 Moviendo servo {category.value} a {angle}°...")
            success = await controller.set_servo_angle(category, angle, hold=True)
            
            if success:
                print(f"✅ Servo movido a {angle}°")
                print(f"   El servo se mantiene en posición")
                
                hold = input(f"\n   ¿Mantener esta posición? (s/n): ").strip().lower()
                if hold != 's':
                    # Desactivar PWM
                    pwm = controller.pwm_objects.get(controller.servos[category].pin_bcm)
                    if pwm:
                        pwm.ChangeDutyCycle(0)
                    print("   PWM desactivado")
            else:
                print(f"❌ Error moviendo servo")
                
        except ValueError:
            print("❌ Ángulo inválido")

async def main():
    """Función principal del script de prueba."""
    print("\n" + "="*60)
    print("🧪 VISIFRUIT - PRUEBA DE SERVOS MG995")
    print("="*60)
    print("\nScript de prueba y calibración de servomotores")
    print("para el sistema de clasificación del prototipo\n")
    
    # Cargar configuración
    config = await load_config()
    if not config:
        print("❌ Error cargando configuración")
        return 1
    
    # Crear controlador
    controller = MG995ServoController(config)
    
    # Inicializar
    print("🔧 Inicializando controlador de servos...")
    if not await controller.initialize():
        print("❌ Error inicializando controlador")
        return 1
    
    print("✅ Controlador inicializado correctamente\n")
    
    try:
        while True:
            print("\n" + "="*60)
            print("MENÚ DE PRUEBAS")
            print("="*60)
            print("  [1] Probar servo de MANZANAS 🍎")
            print("  [2] Probar servo de PERAS 🍐")
            print("  [3] Probar servo de LIMONES 🍋")
            print("  [4] Probar TODOS los servos en secuencia")
            print("  [5] Prueba de activación rápida (protección)")
            print("  [6] Modo de CALIBRACIÓN")
            print("  [7] Resetear todos a posición inicial")
            print("  [0] Salir")
            print("="*60)
            
            choice = input("\n👉 Selecciona una opción: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                await test_individual_servo(controller, FruitCategory.APPLE)
            elif choice == "2":
                await test_individual_servo(controller, FruitCategory.PEAR)
            elif choice == "3":
                await test_individual_servo(controller, FruitCategory.LEMON)
            elif choice == "4":
                await test_all_servos_sequence(controller)
            elif choice == "5":
                print("\nSelecciona servo para prueba rápida:")
                print("  [1] Manzanas")
                print("  [2] Peras")
                print("  [3] Limones")
                test_choice = input("👉 Opción: ").strip()
                cat_map = {"1": FruitCategory.APPLE, "2": FruitCategory.PEAR, "3": FruitCategory.LEMON}
                if test_choice in cat_map:
                    await test_rapid_activation(controller, cat_map[test_choice])
            elif choice == "6":
                await calibration_mode(controller)
            elif choice == "7":
                print("\n🏠 Regresando todos los servos a posición inicial...")
                await controller.home_all_servos()
                print("✅ Completado")
            else:
                print("❌ Opción inválida")
    
    except KeyboardInterrupt:
        print("\n\n⚡ Interrumpido por usuario")
    finally:
        print("\n🧹 Limpiando recursos...")
        await controller.cleanup()
        print("✅ Limpieza completada")
    
    print("\n👋 ¡Hasta luego!\n")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
