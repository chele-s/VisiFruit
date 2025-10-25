#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Test GPIO Wrapper - VisiFruit
===============================

Script simple para probar el funcionamiento del GPIO wrapper
en diferentes entornos (Windows, Pi5, Pi legacy).

Uso: python test_gpio_wrapper.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Importar el GPIO wrapper
from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, GPIO_MODE, get_gpio_info, is_simulation_mode

async def test_gpio_basic():
    """Test básico del GPIO wrapper."""
    print("🔌 TEST GPIO WRAPPER BÁSICO")
    print("="*40)
    
    # Mostrar información del sistema
    gpio_info = get_gpio_info()
    print(f"📋 Información del sistema:")
    print(f"   Modo: {gpio_info['mode']}")
    print(f"   Disponible: {gpio_info['available']}")
    print(f"   Plataforma: {gpio_info['platform']}")
    print(f"   Tipo GPIO: {gpio_info['gpio_type']}")
    print(f"   Simulación: {'Sí' if is_simulation_mode() else 'No'}")
    print()
    
    if not GPIO_AVAILABLE:
        print("❌ GPIO no disponible")
        return
    
    # Test básico de configuración
    try:
        print("🔧 Configurando GPIO...")
        GPIO.setmode(GPIO.BCM)
        
        # Configurar pines de prueba
        test_pins = [18, 19, 26]  # Pines típicos del motor
        
        for pin in test_pins:
            GPIO.setup(pin, GPIO.OUT)
            print(f"   Pin {pin}: configurado como salida")
        
        print("\n⚡ Probando salidas...")
        for pin in test_pins:
            GPIO.output(pin, GPIO.HIGH)
            print(f"   Pin {pin}: HIGH")
            await asyncio.sleep(0.5)
            
            GPIO.output(pin, GPIO.LOW)
            print(f"   Pin {pin}: LOW")
            await asyncio.sleep(0.5)
        
        print("\n🧹 Limpiando GPIO...")
        GPIO.cleanup(test_pins)
        print("✅ Test GPIO completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error en test GPIO: {e}")

async def test_motor_simulation():
    """Test de simulación de motor usando GPIO wrapper."""
    print("\n🎢 TEST SIMULACIÓN MOTOR")
    print("="*40)
    
    if not GPIO_AVAILABLE:
        print("❌ GPIO no disponible para test de motor")
        return
    
    try:
        # Configurar pines del motor
        relay1_pin = 18  # Adelante
        relay2_pin = 19  # Atrás
        enable_pin = 26  # Enable
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(relay1_pin, GPIO.OUT)
        GPIO.setup(relay2_pin, GPIO.OUT)
        GPIO.setup(enable_pin, GPIO.OUT)
        
        # Estado inicial
        GPIO.output(enable_pin, GPIO.HIGH)  # Habilitar driver
        GPIO.output(relay1_pin, GPIO.LOW)
        GPIO.output(relay2_pin, GPIO.LOW)
        print("🔧 Motor inicializado")
        
        # Secuencia de movimiento
        movements = [
            ("adelante", relay1_pin, relay2_pin, 2.0),
            ("parada", None, None, 1.0),
            ("atrás", relay2_pin, relay1_pin, 2.0),
            ("parada", None, None, 1.0)
        ]
        
        for direction, active_pin, inactive_pin, duration in movements:
            print(f"🎯 {direction.upper()}: {duration}s")
            
            if active_pin:
                GPIO.output(inactive_pin, GPIO.LOW)  # Asegurar que el otro esté apagado
                GPIO.output(active_pin, GPIO.HIGH)   # Activar movimiento
            else:
                GPIO.output(relay1_pin, GPIO.LOW)    # Parar todo
                GPIO.output(relay2_pin, GPIO.LOW)
            
            await asyncio.sleep(duration)
        
        # Limpieza final
        GPIO.output(relay1_pin, GPIO.LOW)
        GPIO.output(relay2_pin, GPIO.LOW)
        GPIO.output(enable_pin, GPIO.LOW)
        GPIO.cleanup([relay1_pin, relay2_pin, enable_pin])
        
        print("✅ Test simulación motor completado")
        
    except Exception as e:
        print(f"❌ Error en test motor: {e}")

async def test_stepper_simulation():
    """Test de simulación de stepper DRV8825."""
    print("\n🔧 TEST SIMULACIÓN STEPPER DRV8825")
    print("="*40)
    
    if not GPIO_AVAILABLE:
        print("❌ GPIO no disponible para test de stepper")
        return
    
    try:
        # Configurar pines del stepper
        step_pin = 19
        dir_pin = 26
        enable_pin = 21
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(step_pin, GPIO.OUT)
        GPIO.setup(dir_pin, GPIO.OUT)
        GPIO.setup(enable_pin, GPIO.OUT)
        
        # Habilitar stepper
        GPIO.output(enable_pin, GPIO.LOW)  # DRV8825 se habilita con LOW
        GPIO.output(dir_pin, GPIO.HIGH)    # Dirección (horario)
        print("🔧 Stepper habilitado, dirección: horario")
        
        # Simular pasos
        steps = 200  # Una revolución típica
        step_delay = 0.01  # 10ms entre pasos = ~100 pasos/seg
        
        print(f"🔄 Generando {steps} pasos...")
        
        for i in range(steps):
            GPIO.output(step_pin, GPIO.HIGH)
            await asyncio.sleep(step_delay / 2)
            GPIO.output(step_pin, GPIO.LOW)
            await asyncio.sleep(step_delay / 2)
            
            if (i + 1) % 50 == 0:  # Progreso cada 50 pasos
                print(f"   Paso {i + 1}/{steps}")
        
        # Cambiar dirección y hacer algunos pasos más
        GPIO.output(dir_pin, GPIO.LOW)  # Antihorario
        print("🔄 Cambiando dirección: antihorario")
        
        for i in range(50):  # Solo 50 pasos en reversa
            GPIO.output(step_pin, GPIO.HIGH)
            await asyncio.sleep(step_delay / 2)
            GPIO.output(step_pin, GPIO.LOW)
            await asyncio.sleep(step_delay / 2)
        
        # Deshabilitar stepper
        GPIO.output(enable_pin, GPIO.HIGH)  # Deshabilitar
        GPIO.cleanup([step_pin, dir_pin, enable_pin])
        
        print("✅ Test simulación stepper completado")
        
    except Exception as e:
        print(f"❌ Error en test stepper: {e}")

async def main():
    """Función principal."""
    print("🚀 VisiFruit v3.0 - Test GPIO Wrapper")
    print("="*50)
    
    # Test básico del GPIO
    await test_gpio_basic()
    
    # Test simulación motor
    await test_motor_simulation()
    
    # Test simulación stepper
    await test_stepper_simulation()
    
    print("\n🎉 Todos los tests completados")
    print("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por usuario")
        try:
            GPIO.cleanup()
        except:
            pass
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        try:
            GPIO.cleanup()
        except:
            pass
