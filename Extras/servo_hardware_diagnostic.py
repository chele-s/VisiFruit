#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Diagnóstico Completo de Hardware para Servos MG995
======================================================
Script de diagnóstico para identificar problemas con servos MG995
en Raspberry Pi 5 usando lgpio para hardware PWM.

Autor: Sistema VisiFruit
Fecha: Enero 2025
"""

import time
import sys
import os
try:
    import lgpio
except ImportError:
    print("❌ lgpio no instalado. Ejecuta: sudo apt install python3-lgpio")
    sys.exit(1)

# Configuración de pines y parámetros de servo
GPIO_PIN_1 = 12  # Hardware PWM channel 0
GPIO_PIN_2 = 13  # Hardware PWM channel 1
PWM_FREQUENCY = 50  # 50Hz para servos

class ServoHardwareDiagnostic:
    def __init__(self):
        self.chip_handle = None
        self.active_servos = {}
        
    def initialize(self):
        """Inicializa el chip GPIO."""
        try:
            self.chip_handle = lgpio.gpiochip_open(0)
            print("✅ Chip GPIO abierto correctamente")
            return True
        except Exception as e:
            print(f"❌ Error abriendo chip GPIO: {e}")
            return False
    
    def test_gpio_pin(self, pin):
        """Prueba básica de un pin GPIO."""
        print(f"\n📍 Probando GPIO {pin}")
        print("-" * 40)
        
        try:
            # Intentar reclamar el pin como salida
            try:
                lgpio.gpio_claim_output(self.chip_handle, pin, 0)
                print(f"✅ Pin {pin} reclamado como salida")
            except Exception as e:
                print(f"⚠️ Pin ya reclamado o en uso: {e}")
            
            # Probar salida digital simple
            print("   Probando salida digital...")
            lgpio.gpio_write(self.chip_handle, pin, 1)
            time.sleep(0.1)
            lgpio.gpio_write(self.chip_handle, pin, 0)
            print("   ✅ Salida digital funciona")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en prueba GPIO: {e}")
            return False
    
    def test_pwm_signal(self, pin, test_name="PWM Test"):
        """Prueba señal PWM con diferentes duty cycles."""
        print(f"\n🎛️ {test_name} en GPIO {pin}")
        print("-" * 40)
        
        try:
            # Prueba con diferentes duty cycles para servo
            test_positions = [
                ("0°", 2.5),    # 0.5ms pulse = 2.5% duty @ 50Hz
                ("45°", 5.0),   # 1.0ms pulse = 5.0% duty
                ("90°", 7.5),   # 1.5ms pulse = 7.5% duty  
                ("135°", 10.0), # 2.0ms pulse = 10.0% duty
                ("180°", 12.5)  # 2.5ms pulse = 12.5% duty
            ]
            
            print("Enviando señales PWM para diferentes posiciones:")
            print("(Si el servo no se mueve, revisa la alimentación)")
            
            for position, duty_percent in test_positions:
                print(f"   → {position}: {duty_percent:.1f}% duty cycle", end="")
                
                # Enviar señal PWM
                result = lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, duty_percent)
                
                if result < 0:
                    print(f" ❌ Error código: {result}")
                else:
                    print(f" ✅ OK")
                    self.active_servos[pin] = True
                    
                time.sleep(2)  # Esperar para observar el movimiento
                
            # Detener PWM
            lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, 0)
            print("   ⏹️ PWM detenido")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en prueba PWM: {e}")
            return False
    
    def test_calibration_sweep(self, pin):
        """Prueba barrido de calibración para encontrar límites reales."""
        print(f"\n🔄 Barrido de Calibración en GPIO {pin}")
        print("-" * 40)
        print("Observa el servo y anota los valores donde empieza/termina el movimiento")
        print("Presiona Ctrl+C para detener")
        
        try:
            # Barrido lento de 2% a 15% duty cycle
            for duty_tenth in range(20, 151, 5):  # 2.0% a 15.0% en pasos de 0.5%
                duty = duty_tenth / 10.0
                pulse_ms = (duty / 100.0) * 20.0  # Convertir a ms
                
                print(f"   Duty: {duty:.1f}% = {pulse_ms:.2f}ms pulse", end="\r")
                lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, duty)
                time.sleep(0.3)
                
        except KeyboardInterrupt:
            print("\n   ⏹️ Barrido detenido")
        finally:
            lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, 0)
    
    def test_power_diagnostic(self):
        """Diagnóstico de alimentación."""
        print("\n⚡ Diagnóstico de Alimentación")
        print("-" * 40)
        print("Verificaciones necesarias:")
        print("1. ¿Los servos están conectados a una fuente externa de 5V?")
        print("   (Los MG995 necesitan ~1A por servo bajo carga)")
        print("2. ¿La tierra (GND) está compartida entre Pi y fuente externa?")
        print("3. ¿El voltaje de la fuente es estable (5-6V)?")
        print("4. ¿Los cables de señal están bien conectados?")
        print("\nConexiones correctas:")
        print("   Servo Cable Marrón  → GND compartido")
        print("   Servo Cable Rojo    → 5V fuente externa")  
        print("   Servo Cable Naranja → GPIO 12 o 13")
        
    def interactive_test(self, pin):
        """Prueba interactiva de un servo."""
        print(f"\n🎮 Control Manual de Servo en GPIO {pin}")
        print("-" * 40)
        print("Comandos:")
        print("  Número (0-180): Mover a ese ángulo")
        print("  's': Detener señal PWM")
        print("  'c': Calibración sweep")
        print("  'q': Salir")
        
        while True:
            try:
                cmd = input(f"\nGPIO{pin}> ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == 's':
                    lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, 0)
                    print("   ⏹️ PWM detenido")
                elif cmd == 'c':
                    self.test_calibration_sweep(pin)
                else:
                    try:
                        angle = float(cmd)
                        if 0 <= angle <= 180:
                            # Mapear ángulo a duty cycle
                            # Para MG995: típicamente 1ms-2ms (5%-10% duty)
                            # Extendido: 0.5ms-2.5ms (2.5%-12.5% duty)
                            duty = 2.5 + (angle / 180.0) * 10.0
                            pulse_ms = (duty / 100.0) * 20.0
                            
                            print(f"   → {angle}° = {duty:.2f}% duty = {pulse_ms:.2f}ms pulse")
                            lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, duty)
                        else:
                            print("   ❌ Ángulo debe estar entre 0 y 180")
                    except ValueError:
                        print("   ❌ Comando no reconocido")
                        
            except KeyboardInterrupt:
                print("\n   ⏹️ Saliendo...")
                break
        
        lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, 0)
    
    def run_full_diagnostic(self):
        """Ejecuta diagnóstico completo."""
        print("\n" + "="*50)
        print("🔧 DIAGNÓSTICO COMPLETO DE SERVOS MG995")
        print("Raspberry Pi 5 - Hardware PWM")
        print("="*50)
        
        if not self.initialize():
            return
        
        try:
            # 1. Información del sistema
            print("\n📊 Información del Sistema:")
            print(f"   lgpio version: {lgpio.get_module_version()}")
            print(f"   Chip handle: {self.chip_handle}")
            
            # 2. Diagnóstico de alimentación
            self.test_power_diagnostic()
            input("\nPresiona Enter cuando hayas verificado las conexiones...")
            
            # 3. Prueba de pines GPIO
            for pin in [GPIO_PIN_1, GPIO_PIN_2]:
                if not self.test_gpio_pin(pin):
                    print(f"⚠️ Saltando pruebas PWM para GPIO {pin}")
                    continue
                
                # 4. Prueba PWM básica
                self.test_pwm_signal(pin, f"Prueba PWM Servo {1 if pin==12 else 2}")
                
                # 5. Preguntar si hacer prueba interactiva
                resp = input(f"\n¿Hacer prueba interactiva para GPIO {pin}? (s/n): ")
                if resp.lower() == 's':
                    self.interactive_test(pin)
            
            print("\n" + "="*50)
            print("✅ Diagnóstico completado")
            print("="*50)
            
            print("\n📝 Resumen de problemas comunes:")
            print("1. Servo no se mueve:")
            print("   - Verificar alimentación externa")
            print("   - Verificar GND compartido")
            print("   - Probar con duty cycle manual (2.5% - 12.5%)")
            
            print("\n2. Servo gira continuamente:")
            print("   - Posible servo de rotación continua")
            print("   - Verificar modelo exacto del servo")
            
            print("\n3. Movimiento errático:")
            print("   - Alimentación insuficiente")
            print("   - Ruido en la señal (usar cables cortos)")
            print("   - Calibración incorrecta")
            
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos."""
        print("\n🧹 Limpiando recursos...")
        
        if self.chip_handle is not None:
            # Detener todos los PWM activos
            for pin in self.active_servos:
                try:
                    lgpio.tx_pwm(self.chip_handle, pin, PWM_FREQUENCY, 0)
                    lgpio.gpio_free(self.chip_handle, pin)
                except:
                    pass
            
            # Cerrar chip
            try:
                lgpio.gpiochip_close(self.chip_handle)
                print("   ✅ Chip GPIO cerrado")
            except:
                pass


def main():
    """Función principal."""
    diagnostic = ServoHardwareDiagnostic()
    
    print("Opciones de diagnóstico:")
    print("1. Diagnóstico completo")
    print("2. Prueba rápida GPIO 12")
    print("3. Prueba rápida GPIO 13")
    print("4. Control manual GPIO 12")
    print("5. Control manual GPIO 13")
    
    try:
        opcion = input("\nSelecciona opción (1-5): ").strip()
        
        if opcion == "1":
            diagnostic.run_full_diagnostic()
        elif opcion == "2":
            if diagnostic.initialize():
                diagnostic.test_pwm_signal(12)
                diagnostic.cleanup()
        elif opcion == "3":
            if diagnostic.initialize():
                diagnostic.test_pwm_signal(13)
                diagnostic.cleanup()
        elif opcion == "4":
            if diagnostic.initialize():
                diagnostic.interactive_test(12)
                diagnostic.cleanup()
        elif opcion == "5":
            if diagnostic.initialize():
                diagnostic.interactive_test(13)
                diagnostic.cleanup()
        else:
            print("❌ Opción no válida")
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido por usuario")
        diagnostic.cleanup()
    except Exception as e:
        print(f"❌ Error: {e}")
        diagnostic.cleanup()


if __name__ == "__main__":
    main()
