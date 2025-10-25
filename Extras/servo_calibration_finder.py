#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔬 Buscador de Calibración para Servos MG995
=============================================
Encuentra los valores exactos de duty cycle para tu servo específico.
"""

import time
import sys
try:
    import lgpio
except ImportError:
    print("❌ lgpio no instalado. Ejecuta: sudo apt install python3-lgpio")
    sys.exit(1)

class ServoCalibrationFinder:
    def __init__(self, pin=12):
        self.pin = pin
        self.chip_handle = None
        self.current_duty = 7.5  # Empezar en el centro (90°)
        
    def initialize(self):
        """Inicializa el chip GPIO."""
        try:
            self.chip_handle = lgpio.gpiochip_open(0)
            print(f"✅ Chip GPIO abierto")
            
            # Reclamar pin
            try:
                lgpio.gpio_claim_output(self.chip_handle, self.pin, 0)
            except:
                pass  # Ya reclamado
                
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def set_duty(self, duty_percent):
        """Establece el duty cycle."""
        try:
            self.current_duty = duty_percent
            lgpio.tx_pwm(self.chip_handle, self.pin, 50, duty_percent)
            pulse_ms = (duty_percent / 100.0) * 20.0
            print(f"  Duty: {duty_percent:.2f}% = {pulse_ms:.3f}ms pulse")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def interactive_calibration(self):
        """Calibración interactiva."""
        print("\n" + "="*50)
        print("🔬 CALIBRACIÓN INTERACTIVA DE SERVO")
        print("="*50)
        print("\nComandos:")
        print("  +     : Aumentar duty 0.1%")
        print("  ++    : Aumentar duty 0.5%")
        print("  +++   : Aumentar duty 1.0%")
        print("  -     : Disminuir duty 0.1%")
        print("  --    : Disminuir duty 0.5%") 
        print("  ---   : Disminuir duty 1.0%")
        print("  [num] : Establecer duty específico (ej: 7.5)")
        print("  s     : Detener PWM")
        print("  r     : Reset a 7.5% (90°)")
        print("  test  : Probar rango actual")
        print("  save  : Guardar calibración actual")
        print("  q     : Salir")
        print("\n💡 Tip: Los servos MG995 típicamente usan 2.5-12.5% duty")
        print("    pero algunos pueden necesitar 5-10% o valores diferentes")
        
        # Variables para guardar calibración
        min_duty = None
        max_duty = None
        center_duty = 7.5
        
        # Establecer posición inicial
        self.set_duty(self.current_duty)
        
        while True:
            try:
                current_pulse = (self.current_duty / 100.0) * 20.0
                cmd = input(f"\n[Duty: {self.current_duty:.2f}% = {current_pulse:.3f}ms]> ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == 's':
                    lgpio.tx_pwm(self.chip_handle, self.pin, 50, 0)
                    print("⏹️ PWM detenido")
                elif cmd == 'r':
                    self.set_duty(7.5)
                elif cmd == '+':
                    self.set_duty(min(100, self.current_duty + 0.1))
                elif cmd == '++':
                    self.set_duty(min(100, self.current_duty + 0.5))
                elif cmd == '+++':
                    self.set_duty(min(100, self.current_duty + 1.0))
                elif cmd == '-':
                    self.set_duty(max(0, self.current_duty - 0.1))
                elif cmd == '--':
                    self.set_duty(max(0, self.current_duty - 0.5))
                elif cmd == '---':
                    self.set_duty(max(0, self.current_duty - 1.0))
                elif cmd == 'test':
                    self.test_range(min_duty, max_duty)
                elif cmd == 'save':
                    print("\n📝 Calibración actual:")
                    
                    # Preguntar por los valores
                    try:
                        if min_duty is None:
                            min_input = input("  Duty para 0° (actual si Enter): ").strip()
                            min_duty = float(min_input) if min_input else self.current_duty
                        
                        if max_duty is None:
                            max_input = input("  Duty para 180° (actual si Enter): ").strip()
                            max_duty = float(max_input) if max_input else self.current_duty
                        
                        center_input = input(f"  Duty para 90° (default {center_duty}): ").strip()
                        if center_input:
                            center_duty = float(center_input)
                        
                        self.save_calibration(min_duty, max_duty, center_duty)
                    except ValueError:
                        print("❌ Valor no válido")
                        
                elif cmd.startswith('min='):
                    try:
                        min_duty = float(cmd[4:])
                        print(f"✅ Min duty establecido: {min_duty}%")
                    except:
                        print("❌ Formato: min=5.0")
                elif cmd.startswith('max='):
                    try:
                        max_duty = float(cmd[4:])
                        print(f"✅ Max duty establecido: {max_duty}%")
                    except:
                        print("❌ Formato: max=10.0")
                else:
                    # Intentar interpretar como número
                    try:
                        duty = float(cmd)
                        if 0 <= duty <= 100:
                            self.set_duty(duty)
                        else:
                            print("❌ Duty debe estar entre 0 y 100")
                    except ValueError:
                        print("❌ Comando no reconocido")
                        
            except KeyboardInterrupt:
                break
        
        print("\n🧹 Limpiando...")
        self.cleanup()
    
    def test_range(self, min_duty=None, max_duty=None):
        """Prueba un rango de movimiento."""
        if min_duty is None:
            min_duty = 2.5
        if max_duty is None:
            max_duty = 12.5
            
        center_duty = (min_duty + max_duty) / 2.0
        
        print(f"\n🔄 Probando rango: {min_duty}% - {max_duty}%")
        
        test_sequence = [
            ("Min (0°)", min_duty),
            ("Centro (90°)", center_duty),
            ("Max (180°)", max_duty),
            ("Centro (90°)", center_duty),
        ]
        
        for name, duty in test_sequence:
            print(f"  → {name}: {duty:.2f}%")
            self.set_duty(duty)
            time.sleep(1.5)
    
    def save_calibration(self, min_duty, max_duty, center_duty):
        """Guarda la calibración encontrada."""
        min_pulse = (min_duty / 100.0) * 20.0
        max_pulse = (max_duty / 100.0) * 20.0
        center_pulse = (center_duty / 100.0) * 20.0
        
        calibration_text = f"""
# Calibración encontrada para Servo MG995
# GPIO Pin: {self.pin}

ServoCalibration(
    min_pulse_ms={min_pulse:.3f},      # {min_duty:.2f}% duty = 0°
    max_pulse_ms={max_pulse:.3f},      # {max_duty:.2f}% duty = 180°
    center_pulse_ms={center_pulse:.3f},  # {center_duty:.2f}% duty = 90°
    min_angle=0.0,
    max_angle=180.0,
    center_angle=90.0,
    deadband_ms=0.01
)

# Para usar en rpi5_servo_controller.py:
# 1. Importar ServoCalibration
# 2. Crear la calibración con los valores anteriores
# 3. Pasar al ServoConfig con profile=ServoProfile.CUSTOM
"""
        
        print(calibration_text)
        
        # Guardar a archivo
        try:
            filename = f"servo_calibration_pin{self.pin}.txt"
            with open(filename, 'w') as f:
                f.write(calibration_text)
            print(f"\n✅ Calibración guardada en: {filename}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar archivo: {e}")
    
    def cleanup(self):
        """Limpia recursos."""
        if self.chip_handle is not None:
            try:
                lgpio.tx_pwm(self.chip_handle, self.pin, 50, 0)
                lgpio.gpio_free(self.chip_handle, self.pin)
                lgpio.gpiochip_close(self.chip_handle)
            except:
                pass

def automatic_sweep(pin=12):
    """Barrido automático para observar límites."""
    print("\n" + "="*50)
    print("🔄 BARRIDO AUTOMÁTICO DE CALIBRACIÓN")
    print("="*50)
    print("Observa el servo y anota donde empieza/termina el movimiento")
    print("Presiona Ctrl+C para detener\n")
    
    chip_handle = None
    try:
        chip_handle = lgpio.gpiochip_open(0)
        try:
            lgpio.gpio_claim_output(chip_handle, pin, 0)
        except:
            pass
        
        print("Barriendo de 1% a 15% duty cycle...")
        print("(Los valores típicos están entre 2.5% y 12.5%)\n")
        
        direction = 1  # 1 = subiendo, -1 = bajando
        duty = 1.0
        
        while True:
            pulse_ms = (duty / 100.0) * 20.0
            print(f"Duty: {duty:.1f}% = {pulse_ms:.2f}ms pulse     ", end='\r')
            
            lgpio.tx_pwm(chip_handle, pin, 50, duty)
            time.sleep(0.1)
            
            duty += direction * 0.2
            
            if duty >= 15:
                duty = 15
                direction = -1
            elif duty <= 1:
                duty = 1
                direction = 1
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Barrido detenido")
    finally:
        if chip_handle is not None:
            lgpio.tx_pwm(chip_handle, pin, 50, 0)
            lgpio.gpiochip_close(chip_handle)

def main():
    """Función principal."""
    print("🔬 BUSCADOR DE CALIBRACIÓN PARA SERVOS MG995")
    print("Raspberry Pi 5 - Hardware PWM")
    print()
    
    print("Selecciona el pin GPIO:")
    print("1. GPIO 12 (Hardware PWM)")
    print("2. GPIO 13 (Hardware PWM)")
    
    pin_choice = input("\nOpción (1-2): ").strip()
    pin = 12 if pin_choice == "1" else 13
    
    print(f"\nUsando GPIO {pin}")
    print("\nModos de calibración:")
    print("1. Calibración interactiva (recomendado)")
    print("2. Barrido automático")
    print("3. Test rápido (2.5% - 12.5%)")
    
    mode = input("\nSelecciona modo (1-3): ").strip()
    
    if mode == "1":
        finder = ServoCalibrationFinder(pin)
        if finder.initialize():
            finder.interactive_calibration()
    elif mode == "2":
        automatic_sweep(pin)
    elif mode == "3":
        finder = ServoCalibrationFinder(pin)
        if finder.initialize():
            finder.test_range(2.5, 12.5)
            finder.cleanup()
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main()
