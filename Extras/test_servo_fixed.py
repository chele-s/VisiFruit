#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Prueba Rápida de Servos con Corrección PWM
==============================================
Script para probar si las correcciones al duty cycle funcionan.
"""

import time
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    import lgpio
    print(f"✅ lgpio disponible - version: {lgpio.get_module_version()}")
except ImportError:
    print("❌ lgpio no disponible")
    exit(1)

def test_direct_pwm():
    """Prueba directa con lgpio usando duty cycle correcto."""
    print("\n" + "="*50)
    print("🎯 Prueba Directa con lgpio (duty cycle en %)")
    print("="*50)
    
    chip_handle = None
    pin = 12  # GPIO 12 - Hardware PWM
    
    try:
        # Abrir chip GPIO
        chip_handle = lgpio.gpiochip_open(0)
        print(f"✅ Chip GPIO abierto: handle={chip_handle}")
        
        # Reclamar el pin
        try:
            lgpio.gpio_claim_output(chip_handle, pin, 0)
            print(f"✅ GPIO {pin} reclamado como salida")
        except Exception as e:
            print(f"⚠️ Pin ya reclamado: {e}")
        
        print("\nProbando diferentes posiciones del servo:")
        print("(Observa si el servo se mueve)")
        
        # Mapeo de ángulos a duty cycle para MG995
        # 50Hz = 20ms periodo
        # 0° = 1ms pulse = 5% duty cycle
        # 90° = 1.5ms pulse = 7.5% duty cycle  
        # 180° = 2ms pulse = 10% duty cycle
        
        test_positions = [
            (0, 5.0, 1.0),      # 0°, 5% duty, 1ms pulse
            (45, 6.25, 1.25),   # 45°, 6.25% duty, 1.25ms pulse
            (90, 7.5, 1.5),     # 90°, 7.5% duty, 1.5ms pulse
            (135, 8.75, 1.75),  # 135°, 8.75% duty, 1.75ms pulse
            (180, 10.0, 2.0),   # 180°, 10% duty, 2ms pulse
            (90, 7.5, 1.5),     # Volver a 90°
        ]
        
        for angle, duty_percent, pulse_ms in test_positions:
            print(f"\n→ Moviendo a {angle}°:")
            print(f"  Duty cycle: {duty_percent:.2f}%")
            print(f"  Ancho pulso: {pulse_ms:.2f}ms")
            
            # Enviar señal PWM
            result = lgpio.tx_pwm(chip_handle, pin, 50, duty_percent)
            
            if result < 0:
                print(f"  ❌ Error código: {result}")
            else:
                print(f"  ✅ Señal PWM enviada")
            
            # Esperar para observar el movimiento
            time.sleep(2)
        
        # Detener PWM
        print("\n⏹️ Deteniendo señal PWM...")
        lgpio.tx_pwm(chip_handle, pin, 50, 0)
        
        print("\n✅ Prueba completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar recursos
        if chip_handle is not None:
            try:
                lgpio.tx_pwm(chip_handle, pin, 50, 0)
                lgpio.gpio_free(chip_handle, pin)
                lgpio.gpiochip_close(chip_handle)
                print("🧹 Recursos liberados")
            except:
                pass

def test_with_controller():
    """Prueba usando el controlador corregido."""
    from rpi5_servo_controller import RPi5ServoController, ServoConfig, ServoProfile, ServoDirection
    
    print("\n" + "="*50)
    print("🎮 Prueba con Controlador Corregido")
    print("="*50)
    
    # Configurar servo
    config = ServoConfig(
        pin_bcm=12,
        name="Servo Test",
        profile=ServoProfile.MG995_STANDARD,  # 1ms - 2ms (5% - 10% duty)
        default_angle=90,
        direction=ServoDirection.FORWARD,
        smooth_movement=False,  # Sin suavizado para ver movimientos directos
        initial_delay_ms=500
    )
    
    controller = RPi5ServoController(config)
    
    if not controller.initialized:
        print("❌ Error inicializando controlador")
        return
    
    try:
        print("\nProbando movimientos con el controlador:")
        
        test_angles = [0, 45, 90, 135, 180, 90]
        for angle in test_angles:
            print(f"\n→ Moviendo a {angle}°")
            success = controller.set_angle(angle)
            if success:
                print(f"  ✅ Comando enviado")
            else:
                print(f"  ❌ Error enviando comando")
            time.sleep(2)
        
        print("\n📊 Estado final del servo:")
        status = controller.get_status()
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        
        print("\n✅ Prueba completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        controller.cleanup()

def main():
    """Función principal."""
    print("\n🔧 PRUEBA DE SERVOS MG995 - CORRECCIÓN PWM")
    print("Raspberry Pi 5 - Hardware PWM en GPIO 12/13")
    print()
    print("Asegúrate de que:")
    print("1. El servo está conectado a GPIO 12")
    print("2. Tiene alimentación externa de 5V")
    print("3. GND compartido entre Pi y fuente externa")
    
    print("\nOpciones:")
    print("1. Prueba directa con lgpio")
    print("2. Prueba con controlador corregido")
    print("3. Ambas pruebas")
    
    try:
        opcion = input("\nSelecciona opción (1-3): ").strip()
        
        if opcion == "1":
            test_direct_pwm()
        elif opcion == "2":
            test_with_controller()
        elif opcion == "3":
            test_direct_pwm()
            input("\nPresiona Enter para continuar con la siguiente prueba...")
            test_with_controller()
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por usuario")

if __name__ == "__main__":
    main()
