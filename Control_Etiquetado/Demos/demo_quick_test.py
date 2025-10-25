#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 DEMO RÁPIDA - Pruebas Específicas VisiFruit
===========================================

Script de pruebas rápidas para componentes individuales:
- Motor DC banda (solo adelante)
- Stepper DRV8825 (simulado o real)
- Sensor láser YK0008

Uso: python demo_quick_test.py [motor|stepper|laser|all]
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Importar GPIO wrapper para compatibilidad universal
from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, GPIO_MODE, get_gpio_info, is_simulation_mode

async def test_motor():
    """Prueba rápida del motor DC."""
    print("🎢 PRUEBA MOTOR DC - 5 segundos adelante")
    print(f"🔌 GPIO: {GPIO_MODE.value} ({'simulado' if is_simulation_mode() else 'hardware'})")
    
    driver = None
    
    # Intentar drivers específicos primero
    try:
        from Control_Etiquetado.relay_motor_controller_pi5 import create_relay_motor_driver_pi5
        driver = create_relay_motor_driver_pi5(relay1_pin=18, relay2_pin=19, enable_pin=26)
        print("✅ Usando driver Pi5")
    except:
        try:
            from Control_Etiquetado.relay_motor_controller import create_relay_motor_driver
            driver = create_relay_motor_driver(relay1_pin=18, relay2_pin=19, enable_pin=26)
            print("✅ Usando driver legacy")
        except:
            pass
    
    # Fallback: GPIO wrapper directo
    if driver is None and GPIO_AVAILABLE:
        print("🔧 Usando GPIO wrapper directo")
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(18, GPIO.OUT)  # Relay adelante
            GPIO.setup(19, GPIO.OUT)  # Relay atrás
            GPIO.setup(26, GPIO.OUT)  # Enable
            
            GPIO.output(26, GPIO.HIGH)  # Enable
            GPIO.output(19, GPIO.LOW)   # Atrás OFF
            GPIO.output(18, GPIO.HIGH)  # Adelante ON
            
            print("🟢 Motor adelante...")
            await asyncio.sleep(5.0)
            
            GPIO.output(18, GPIO.LOW)   # Parar
            print("⚫ Motor parado")
            
            GPIO.cleanup([18, 19, 26])
            print("✅ Prueba motor completada")
            return
            
        except Exception as e:
            print(f"❌ Error con GPIO wrapper: {e}")
            return
    
    if driver is None:
        print("❌ No hay drivers de motor disponibles")
        return
    
    # Usar driver específico
    try:
        if await driver.initialize():
            print("✅ Motor inicializado - Iniciando...")
            await driver.start_belt()
            await asyncio.sleep(5)
            await driver.stop_belt()
            print("✅ Prueba completada")
        else:
            print("❌ Error inicializando motor")
    finally:
        try:
            await driver.cleanup()
        except:
            pass

async def test_stepper():
    """Prueba rápida del stepper DRV8825."""
    print("🔧 PRUEBA STEPPER DRV8825 - Simulación 2 segundos")
    
    try:
        from Control_Etiquetado.labeler_actuator import LabelerActuator
        
        config = {
            "type": "stepper",
            "name": "TestStepper",
            "step_pin_bcm": 19,
            "dir_pin_bcm": 26,
            "enable_pin_bcm": 21,
            "base_speed_sps": 1500
        }
        
        stepper = LabelerActuator(config)
        
        if await stepper.initialize():
            print("✅ Stepper inicializado - Activando...")
            await stepper.activate_for_duration(2.0, 80.0)
            print("✅ Stepper completado")
        else:
            print("⚠️ Stepper en modo simulación")
            print("🎭 SIMULANDO: Stepper girando 2s...")
            await asyncio.sleep(2)
            print("✅ Simulación completada")
            
    except Exception as e:
        print(f"⚠️ Stepper simulado: {e}")
        print("🎭 SIMULANDO: Stepper girando 2s...")
        await asyncio.sleep(2)
        print("✅ Simulación completada")

async def test_laser():
    """Prueba rápida del sensor láser."""
    print("📡 PRUEBA SENSOR LÁSER - 10 segundos de monitoreo")
    
    try:
        from Control_Etiquetado.sensor_interface import SensorInterface
        
        config = {
            "trigger_sensor": {
                "pin_bcm": 17,
                "trigger_level": "falling",
                "debounce_time_ms": 30,
                "pull_up_down": "PUD_UP"
            }
        }
        
        triggers = 0
        def callback():
            nonlocal triggers
            triggers += 1
            print(f"🔴 Trigger #{triggers} detectado!")
        
        sensor = SensorInterface(trigger_callback=callback)
        
        if sensor.initialize(config):
            print("✅ Sensor inicializado - Monitoreo activo...")
            sensor.enable_trigger_monitoring()
            
            for i in range(10):
                print(f"⏱️ Esperando triggers... {10-i}s restantes")
                await asyncio.sleep(1)
            
            sensor.disable_trigger_monitoring()
            print(f"✅ Monitoreo completado - {triggers} triggers detectados")
        else:
            print("⚠️ Sensor en modo simulación")
            print("🎭 SIMULANDO: Triggers aleatorios...")
            for i in range(3):
                await asyncio.sleep(2)
                print(f"🔴 Trigger simulado #{i+1}")
            print("✅ Simulación completada")
            
    except Exception as e:
        print(f"⚠️ Sensor simulado: {e}")
        print("🎭 SIMULANDO: Triggers aleatorios...")
        for i in range(3):
            await asyncio.sleep(2)
            print(f"🔴 Trigger simulado #{i+1}")
        print("✅ Simulación completada")

async def test_all():
    """Prueba todos los componentes en secuencia."""
    print("🚀 PRUEBA COMPLETA - Todos los componentes")
    print("="*50)
    
    print("\n1/3 - Probando motor...")
    await test_motor()
    
    print("\n2/3 - Probando stepper...")
    await test_stepper()
    
    print("\n3/3 - Probando láser...")
    await test_laser()
    
    print("\n✅ Todas las pruebas completadas")

async def main():
    """Función principal."""
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print(f"🔧 VisiFruit v3.0 - Prueba Rápida: {test_type.upper()}")
    print("="*50)
    
    # Mostrar información del sistema GPIO
    gpio_info = get_gpio_info()
    print(f"🔌 Sistema GPIO: {gpio_info['mode']} ({'simulado' if is_simulation_mode() else 'hardware'})")
    print(f"💻 Plataforma: {gpio_info['platform']}")
    print(f"🔧 Tipo GPIO: {gpio_info['gpio_type']}")
    print("-"*50)
    
    if test_type == "motor":
        await test_motor()
    elif test_type == "stepper":
        await test_stepper()
    elif test_type == "laser":
        await test_laser()
    elif test_type == "all":
        await test_all()
    else:
        print("❌ Tipo de prueba inválido")
        print("Uso: python demo_quick_test.py [motor|stepper|laser|all]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Prueba interrumpida")
    except Exception as e:
        print(f"❌ Error: {e}")
