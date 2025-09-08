#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Test Rápido Sensor MH Flying Fish
===================================

Script simple para probar el sensor MH Flying Fish sin necesidad
de ejecutar todo el sistema completo.

Uso:
    python Control_Etiquetado/test_mh_sensor_simple.py

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez  
Fecha: Enero 2025
"""

import sys
import time
from pathlib import Path

# Agregar directorio padre para importaciones
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, is_simulation_mode
    print(f"✅ GPIO wrapper cargado - Modo: {'Simulación' if is_simulation_mode() else 'Hardware'}")
except ImportError as e:
    print(f"❌ Error importando GPIO wrapper: {e}")
    sys.exit(1)

# Configuración del sensor (desde Config_Etiquetadora.json actualizado)
SENSOR_PIN_BCM = 4  # Cambiado de 17 a 4
SENSOR_NAME = "MH Flying Fish"
TRIGGER_ON_STATE = "LOW"  # Cuando detecta algo, voltaje baja (0.10V)
DEBOUNCE_MS = 50  # Aumentado de 5ms a 50ms

def test_sensor_basic():
    """Test básico del sensor con lecturas directas."""
    print(f"\n🔍 TEST BÁSICO SENSOR {SENSOR_NAME}")
    print("="*50)
    print(f"📍 Pin: BCM {SENSOR_PIN_BCM}")
    print(f"⚡ Trigger: {TRIGGER_ON_STATE} (cuando detecta objeto)")
    print(f"🕰️ Debounce: {DEBOUNCE_MS}ms")
    
    if not GPIO_AVAILABLE:
        print("⚠️ GPIO no disponible - Ejecutándose en modo simulación")
        return False
    
    try:
        # Configurar GPIO
        print("\n🔧 Configurando GPIO...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR_PIN_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Estabilización
        time.sleep(0.2)
        
        print(f"✅ Pin BCM {SENSOR_PIN_BCM} configurado como entrada con pull-up")
        
        # Test de lecturas básicas
        print(f"\n📊 Tomando 20 lecturas del sensor...")
        high_count = 0
        low_count = 0
        
        for i in range(20):
            state = GPIO.input(SENSOR_PIN_BCM)
            if state == GPIO.HIGH:
                high_count += 1
                print(f"  Lectura {i+1:2d}: 🟢 HIGH (~2.70V) - Sin detección")
            else:
                low_count += 1
                print(f"  Lectura {i+1:2d}: 🔴 LOW  (~0.10V) - DETECCIÓN")
            time.sleep(0.1)
        
        print(f"\n📈 RESULTADOS:")
        print(f"   🟢 HIGH: {high_count}/20 ({high_count/20*100:.0f}%)")
        print(f"   🔴 LOW:  {low_count}/20 ({low_count/20*100:.0f}%)")
        
        if high_count == 20:
            print(f"\n💡 El sensor siempre lee HIGH - Esto es normal cuando NO hay detección")
            print(f"   ✅ Voltajes esperados: ~2.70V cuando LED OUT está apagado")
        elif low_count == 20:
            print(f"\n🎯 El sensor siempre lee LOW - Posible detección continua")
            print(f"   ✅ Voltajes esperados: ~0.10V cuando LED OUT está encendido")
        else:
            print(f"\n⚡ Estados mixtos detectados - Sensor puede estar funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test básico: {e}")
        return False
    
    finally:
        try:
            GPIO.cleanup([SENSOR_PIN_BCM])
            print(f"🧹 GPIO limpiado")
        except:
            pass

def test_sensor_interactive():
    """Test interactivo con monitoreo continuo."""
    print(f"\n🎮 TEST INTERACTIVO SENSOR {SENSOR_NAME}")
    print("="*50)
    print(f"📍 Pin: BCM {SENSOR_PIN_BCM}")
    print(f"🔄 Presiona Ctrl+C para salir")
    
    if not GPIO_AVAILABLE:
        print("⚠️ GPIO no disponible - modo simulación")
        return
    
    try:
        # Configurar GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR_PIN_BCM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.2)
        
        print(f"\n🔄 Iniciando monitoreo continuo...")
        print(f"   🎯 Activa el sensor manualmente (bloquea el haz de luz)")
        print(f"   📊 Estados: HIGH=sin detección, LOW=con detección\n")
        
        last_state = None
        trigger_count = 0
        start_time = time.time()
        
        while True:
            current_state = GPIO.input(SENSOR_PIN_BCM)
            current_time = time.time()
            
            # Detectar cambios de estado
            if last_state is not None and last_state != current_state:
                elapsed = current_time - start_time
                
                if current_state == GPIO.LOW:
                    trigger_count += 1
                    print(f"🔴 TRIGGER #{trigger_count} - DETECCIÓN a los {elapsed:.1f}s")
                else:
                    print(f"🟢 RELEASE #{trigger_count} - Sin detección a los {elapsed:.1f}s")
            
            last_state = current_state
            time.sleep(0.01)  # 10ms polling
            
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n✅ Test completado después de {elapsed:.1f}s")
        print(f"🎯 Total triggers detectados: {trigger_count}")
        
        if trigger_count == 0:
            print(f"\n💡 SUGERENCIAS:")
            print(f"   - Verifica conexión del sensor al pin BCM {SENSOR_PIN_BCM}")
            print(f"   - Bloquea manualmente el haz de luz del sensor")
            print(f"   - Verifica alimentación 3.3V")
            print(f"   - Revisa que el LED OUT del sensor cambie de estado")
            
    except Exception as e:
        print(f"❌ Error en test interactivo: {e}")
    
    finally:
        try:
            GPIO.cleanup([SENSOR_PIN_BCM])
            print(f"🧹 GPIO limpiado")
        except:
            pass

def main():
    """Función principal."""
    print(f"\n🚀 TEST SENSOR MH FLYING FISH")
    print(f"🔧 Pin cambiado de BCM 17 → BCM {SENSOR_PIN_BCM}")
    print(f"⚡ Configuración optimizada para detección 3.3V")
    
    try:
        # Test básico primero
        if test_sensor_basic():
            print(f"\n🎮 ¿Continuar con test interactivo? (y/N): ", end="")
            response = input().strip().lower()
            
            if response in ['y', 'yes', 'si', 's']:
                test_sensor_interactive()
        
    except KeyboardInterrupt:
        print(f"\n👋 Test interrumpido por usuario")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
    
    print(f"\n✅ Test del sensor finalizado")

if __name__ == "__main__":
    main()
