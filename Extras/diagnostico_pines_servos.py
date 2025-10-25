#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Diagnóstico de Pines de Servos MG995
========================================

Script para diagnosticar y probar los pines de servos individualmente.
Útil para verificar si los pines GPIO están dañados o funcionando.

Uso:
    python3 diagnostico_pines_servos.py           # Probar todos los pines
    python3 diagnostico_pines_servos.py --pin 12  # Probar pin específico

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Enero 2025
"""

import sys
import time
import argparse
from pathlib import Path

# Importar pigpio
try:
    import pigpio
    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    print("❌ pigpio no disponible. Instalar con: sudo apt install python3-pigpio")
    sys.exit(1)

# Configuración de pines
SERVO_PINS = {
    12: "Servo Manzanas 🍎 (GPIO 12 - PWM0)",
    13: "Servo Peras 🍐 (GPIO 13 - PWM1)",
    18: "Servo Limones 🍋 (GPIO 18 - PWM0 alt)"
}

DAMAGED_PINS = {
    5: "GPIO 5 (DAÑADO - era Servo Manzanas)",
    6: "GPIO 6 (DAÑADO - era Servo Peras)",
    7: "GPIO 7 (DAÑADO - era Servo Limones)"
}

def check_daemon():
    """Verifica si el daemon pigpio está corriendo."""
    try:
        pi = pigpio.pi()
        connected = pi.connected
        pi.stop()
        return connected
    except:
        return False

def test_pin(pi, pin, name):
    """
    Prueba un pin específico con un servo.
    
    Args:
        pi: Instancia de pigpio
        pin: Número de pin GPIO
        name: Nombre descriptivo del pin
    """
    print(f"\n{'='*70}")
    print(f"🧪 Probando: {name}")
    print(f"{'='*70}")
    
    try:
        # Configurar pin
        pi.set_mode(pin, pigpio.OUTPUT)
        pi.set_PWM_frequency(pin, 50)  # 50Hz para servos
        
        print(f"✅ Pin {pin} configurado correctamente")
        print(f"\nMoviendo servo a diferentes posiciones...")
        print(f"(Observa si el servo se mueve suavemente)\n")
        
        # Secuencia de prueba
        positions = [
            (1500, "90° - Centro"),
            (1000, "0° - Mínimo"),
            (2000, "180° - Máximo"),
            (1500, "90° - Centro"),
            (1250, "45° - Intermedio"),
            (1750, "135° - Intermedio"),
            (1500, "90° - Centro final")
        ]
        
        for pulse_us, description in positions:
            print(f"  → {description} (pulso: {pulse_us}μs)")
            pi.set_servo_pulsewidth(pin, pulse_us)
            time.sleep(1.0)
        
        # Desactivar
        pi.set_servo_pulsewidth(pin, 0)
        print(f"\n✅ Prueba completada")
        
        # Preguntar resultado
        response = input(f"\n¿El servo se movió correctamente? (s/n): ").strip().lower()
        
        if response == 's':
            print(f"✅ Pin {pin} FUNCIONAL")
            return True
        else:
            print(f"❌ Pin {pin} POSIBLE PROBLEMA")
            return False
            
    except Exception as e:
        print(f"❌ Error probando pin {pin}: {e}")
        return False

def test_all_pins(pi):
    """Prueba todos los pines de servos."""
    print(f"\n{'='*70}")
    print(f"🔍 DIAGNÓSTICO COMPLETO DE PINES DE SERVOS")
    print(f"{'='*70}")
    
    results = {}
    
    # Probar pines nuevos
    print(f"\n📍 Probando PINES NUEVOS (deben funcionar):")
    for pin, name in SERVO_PINS.items():
        results[pin] = test_pin(pi, pin, name)
        time.sleep(0.5)
    
    # Advertencia sobre pines dañados
    print(f"\n{'='*70}")
    print(f"⚠️  PINES DAÑADOS (NO PROBAR - pueden dañar más el hardware):")
    print(f"{'='*70}")
    for pin, name in DAMAGED_PINS.items():
        print(f"  ❌ Pin {pin}: {name}")
    
    # Resumen
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN DEL DIAGNÓSTICO")
    print(f"{'='*70}")
    
    for pin, status in results.items():
        name = SERVO_PINS.get(pin, f"GPIO {pin}")
        status_str = "✅ FUNCIONAL" if status else "❌ PROBLEMA"
        print(f"  {status_str}: Pin {pin} - {name}")
    
    # Recomendaciones
    print(f"\n{'='*70}")
    print(f"💡 RECOMENDACIONES")
    print(f"{'='*70}")
    
    all_ok = all(results.values())
    
    if all_ok:
        print(f"✅ Todos los pines funcionan correctamente")
        print(f"   Puedes usar el sistema normalmente")
    else:
        print(f"⚠️ Algunos pines tienen problemas")
        print(f"\n   Verifica:")
        print(f"   1. Conexiones físicas (cables sueltos)")
        print(f"   2. Alimentación 5V de servos (debe ser externa)")
        print(f"   3. GND común entre Pi y fuente externa")
        print(f"   4. Estado del servo (puede estar dañado)")
        print(f"\n   Si persiste, considera usar pines alternativos:")
        print(f"   GPIO 16, 17, 20, 24, 25 (disponibles)")

def interactive_test(pi):
    """Modo interactivo de prueba."""
    print(f"\n{'='*70}")
    print(f"🎮 MODO INTERACTIVO - Control Manual de Servos")
    print(f"{'='*70}")
    
    while True:
        print(f"\nPines disponibles:")
        for pin, name in SERVO_PINS.items():
            print(f"  [{pin}] {name}")
        print(f"  [0] Salir")
        
        try:
            choice = int(input(f"\n👉 Selecciona pin: ").strip())
            
            if choice == 0:
                break
            
            if choice not in SERVO_PINS:
                print(f"❌ Pin inválido")
                continue
            
            # Configurar pin
            pi.set_mode(choice, pigpio.OUTPUT)
            pi.set_PWM_frequency(choice, 50)
            
            # Solicitar ángulo
            angle = float(input(f"   Ángulo (0-180°): ").strip())
            angle = max(0, min(180, angle))
            
            # Convertir ángulo a pulso (1000-2000μs)
            pulse_us = int(1000 + (angle / 180.0) * 1000)
            
            print(f"\n🔄 Moviendo a {angle}° (pulso: {pulse_us}μs)...")
            pi.set_servo_pulsewidth(choice, pulse_us)
            
            # Preguntar si mantener o desactivar
            hold = input(f"   ¿Mantener posición? (s/n): ").strip().lower()
            if hold != 's':
                pi.set_servo_pulsewidth(choice, 0)
                print(f"   PWM desactivado")
            
        except ValueError:
            print(f"❌ Entrada inválida")
        except KeyboardInterrupt:
            break

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Diagnóstico de pines de servos MG995')
    parser.add_argument('--pin', type=int, help='Probar pin específico (12, 13 o 18)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Modo interactivo')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO DE PINES DE SERVOS MG995")
    print("="*70)
    print("\nNuevos pines (tras daño de GPIO 5, 6, 7):")
    for pin, name in SERVO_PINS.items():
        print(f"  GPIO {pin}: {name}")
    print("\nEste script probará los pines con señales PWM para servos")
    print("="*70)
    
    # Verificar daemon
    print(f"\n🔍 Verificando daemon pigpio...")
    if not check_daemon():
        print(f"❌ Daemon pigpio no está corriendo")
        print(f"\nInicia el daemon con:")
        print(f"  sudo pigpiod -s 10")
        print(f"\nO usa el script:")
        print(f"  ./start_pigpio_daemon.sh start")
        return 1
    
    print(f"✅ Daemon pigpio conectado")
    
    # Conectar a pigpio
    pi = pigpio.pi()
    if not pi.connected:
        print(f"❌ No se pudo conectar a pigpio")
        return 1
    
    print(f"✅ Conexión pigpio establecida")
    
    try:
        if args.interactive:
            # Modo interactivo
            interactive_test(pi)
        elif args.pin:
            # Probar pin específico
            if args.pin not in SERVO_PINS:
                print(f"❌ Pin {args.pin} no está en la lista de servos")
                print(f"   Pines válidos: {list(SERVO_PINS.keys())}")
                return 1
            
            name = SERVO_PINS[args.pin]
            test_pin(pi, args.pin, name)
        else:
            # Probar todos
            test_all_pins(pi)
        
        print(f"\n{'='*70}")
        print(f"📝 NOTAS IMPORTANTES")
        print(f"{'='*70}")
        print(f"\n✅ Pines NUEVOS (usar estos):")
        for pin, name in SERVO_PINS.items():
            print(f"   GPIO {pin}: {name}")
        
        print(f"\n❌ Pines DAÑADOS (NO usar):")
        for pin, name in DAMAGED_PINS.items():
            print(f"   GPIO {pin}: {name}")
        
        print(f"\n💡 Verifica:")
        print(f"   1. Alimentación 5-6V externa para servos")
        print(f"   2. GND común entre Pi y fuente")
        print(f"   3. Cables de señal en GPIO 12, 13, 18")
        print(f"   4. Servos en buen estado físico")
        
        print(f"\n✅ Diagnóstico completado")
        
    except KeyboardInterrupt:
        print(f"\n\n⚡ Interrumpido por usuario")
    finally:
        # Desactivar todos los PWM
        for pin in SERVO_PINS.keys():
            try:
                pi.set_servo_pulsewidth(pin, 0)
            except:
                pass
        
        pi.stop()
        print(f"\n🧹 Recursos liberados")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

