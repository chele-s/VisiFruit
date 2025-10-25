#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 DEMO INTERACTIVA - Control Motor DC con Relays 12V
===================================================

Demo simple y directa para controlar motor DC usando 2 relays de 12V
con Raspberry Pi 5. Ideal para pruebas rápidas y demostración.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 1.0 - Demo Edition
"""

import asyncio
import logging
import time
import signal
import sys
from pathlib import Path

# Agregar directorio padre para importaciones
sys.path.append(str(Path(__file__).parent.parent))

try:
    # Intentar primero el controlador Pi5 (lgpio)
    from Control_Etiquetado.relay_motor_controller_pi5 import create_relay_motor_driver_pi5
    RELAY_MODULE_AVAILABLE = True
    USE_PI5_DRIVER = True
    print("🔧 Usando controlador Pi5 con lgpio")
except ImportError:
    try:
        # Fallback al controlador original (RPi.GPIO)
        from Control_Etiquetado.relay_motor_controller import create_relay_motor_driver
        RELAY_MODULE_AVAILABLE = True
        USE_PI5_DRIVER = False
        print("🔧 Usando controlador original con RPi.GPIO")
    except ImportError as e:
        print(f"⚠️ Módulo de relays no disponible: {e}")
        RELAY_MODULE_AVAILABLE = False
        USE_PI5_DRIVER = False

# Configuración de logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

class DemoRelayMotor:
    """Demo interactiva para control de motor con relays."""
    
    def __init__(self):
        self.driver = None
        self.running = False
        self.demo_active = True
        
        # Configuración de pines (puedes cambiarlos aquí)
        self.RELAY1_PIN = 18  # GPIO 18 - Adelante
        self.RELAY2_PIN = 19  # GPIO 19 - Atrás  
        self.ENABLE_PIN = 26  # GPIO 26 - Habilitación (opcional)
        
    async def initialize_demo(self):
        """Inicializar la demo."""
        print("\n" + "="*60)
        print("🚀 DEMO: Control Motor DC con Relays 12V")
        print("="*60)
        print(f"📌 Configuración de pines:")
        print(f"   • Relay 1 (Adelante): GPIO {self.RELAY1_PIN}")
        print(f"   • Relay 2 (Atrás):    GPIO {self.RELAY2_PIN}")
        print(f"   • Habilitación:       GPIO {self.ENABLE_PIN}")
        print("\n🔌 Asegúrate de que las conexiones estén correctas antes de continuar.")
        
        if not RELAY_MODULE_AVAILABLE:
            print("❌ Módulo de relays no disponible - Modo simulación")
            return False
        
        try:
            # Crear driver con configuración simple
            if USE_PI5_DRIVER:
                self.driver = create_relay_motor_driver_pi5(
                    relay1_pin=self.RELAY1_PIN,
                    relay2_pin=self.RELAY2_PIN, 
                    enable_pin=self.ENABLE_PIN
                )
                print("✅ Usando driver optimizado para Raspberry Pi 5")
            else:
                self.driver = create_relay_motor_driver(
                    relay1_pin=self.RELAY1_PIN,
                    relay2_pin=self.RELAY2_PIN, 
                    enable_pin=self.ENABLE_PIN
                )
                print("⚠️ Usando driver legacy (puede no funcionar en Pi 5)")
            
            # Inicializar
            if await self.driver.initialize():
                print("✅ Driver de relays inicializado correctamente")
                
                # Mostrar estado inicial
                status = await self.driver.get_status()
                print(f"📊 Estado inicial:")
                print(f"   • Relay 1: {status['relay_states']['relay1']}")
                print(f"   • Relay 2: {status['relay_states']['relay2']}")
                print(f"   • Motor:   {'Funcionando' if status['running'] else 'Parado'}")
                
                return True
            else:
                print("❌ Error inicializando driver de relays")
                return False
                
        except Exception as e:
            print(f"❌ Error en inicialización: {e}")
            return False
    
    async def demo_manual_control(self):
        """Demo de control manual interactivo."""
        print("\n" + "="*50)
        print("🎮 CONTROL MANUAL DEL MOTOR")
        print("="*50)
        print("Comandos disponibles:")
        print("  [A] - Motor ADELANTE")
        print("  [S] - Motor ATRÁS") 
        print("  [P] - PARAR motor")
        print("  [E] - EMERGENCIA")
        print("  [I] - Ver INFO")
        print("  [Q] - Salir")
        print("\n💡 Escribe el comando y presiona Enter...")
        
        while self.demo_active:
            try:
                command = input("\n🎯 Comando: ").strip().upper()
                
                if command == 'A':
                    await self._motor_adelante()
                elif command == 'S':
                    await self._motor_atras()
                elif command == 'P':
                    await self._motor_parar()
                elif command == 'E':
                    await self._motor_emergencia()
                elif command == 'I':
                    await self._mostrar_info()
                elif command == 'Q':
                    print("👋 Saliendo del control manual...")
                    await self._motor_parar()
                    break
                else:
                    print("❓ Comando no reconocido. Usa A, S, P, E, I o Q")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Ctrl+C detectado - Parando motor...")
                await self._motor_emergencia()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _motor_adelante(self):
        """Mover motor hacia adelante."""
        print("⏩ Iniciando motor ADELANTE...")
        try:
            if await self.driver.start_belt():
                self.running = True
                print("✅ Motor funcionando hacia ADELANTE")
                await self._mostrar_estado_relays()
            else:
                print("❌ Error iniciando motor")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _motor_atras(self):
        """Mover motor hacia atrás."""
        print("⏪ Cambiando motor hacia ATRÁS...")
        try:
            if await self.driver.reverse_direction():
                self.running = True
                print("✅ Motor funcionando hacia ATRÁS")
                await self._mostrar_estado_relays()
            else:
                print("❌ Error cambiando dirección")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _motor_parar(self):
        """Parar motor."""
        print("⏹️ Parando motor...")
        try:
            if await self.driver.stop_belt():
                self.running = False
                print("✅ Motor PARADO")
                await self._mostrar_estado_relays()
            else:
                print("❌ Error parando motor")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _motor_emergencia(self):
        """Parada de emergencia."""
        print("🚨 PARADA DE EMERGENCIA...")
        try:
            if await self.driver.emergency_brake():
                self.running = False
                print("✅ Parada de emergencia ejecutada")
                await self._mostrar_estado_relays()
            else:
                print("❌ Error en parada de emergencia")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _mostrar_estado_relays(self):
        """Mostrar estado actual de los relays."""
        try:
            status = await self.driver.get_status()
            relay1 = status['relay_states']['relay1']
            relay2 = status['relay_states']['relay2']
            direction = status['direction']
            
            print(f"   🔄 Relay 1: {relay1}")
            print(f"   🔄 Relay 2: {relay2}")
            print(f"   ➡️ Dirección: {direction}")
        except Exception as e:
            print(f"❌ Error obteniendo estado: {e}")
    
    async def _mostrar_info(self):
        """Mostrar información completa del sistema."""
        print("\n📊 INFORMACIÓN DEL SISTEMA")
        print("-" * 40)
        try:
            status = await self.driver.get_status()
            
            print(f"🔧 Estado general:")
            print(f"   • Inicializado: {status['initialized']}")
            print(f"   • Motor funcionando: {status['running']}")
            print(f"   • Dirección actual: {status['direction']}")
            print(f"   • Tipo control: {status['control_type']}")
            
            print(f"\n🔄 Estado de relays:")
            print(f"   • Relay 1 (Adelante): {status['relay_states']['relay1']}")
            print(f"   • Relay 2 (Atrás): {status['relay_states']['relay2']}")
            
            print(f"\n📌 Configuración de pines:")
            pins = status['pins']
            print(f"   • Relay 1: GPIO {pins['relay1_forward']}")
            print(f"   • Relay 2: GPIO {pins['relay2_backward']}")
            if pins['enable']:
                print(f"   • Enable: GPIO {pins['enable']}")
            
            if status.get('safety_timeout_active'):
                print(f"\n⏰ Timeout de seguridad: ACTIVO")
                
        except Exception as e:
            print(f"❌ Error obteniendo información: {e}")
    
    async def demo_automatica(self):
        """Demo automática con secuencia predefinida."""
        print("\n" + "="*50)
        print("🤖 DEMO AUTOMÁTICA")
        print("="*50)
        print("Ejecutando secuencia automática de pruebas...")
        
        secuencia = [
            ("Iniciando motor hacia adelante...", "adelante", 3),
            ("Parando motor...", "parar", 1),
            ("Iniciando motor hacia atrás...", "atras", 3),
            ("Parando motor...", "parar", 1),
            ("Probando cambio rápido de dirección...", "cambio_rapido", 4),
            ("Parada final...", "parar", 1)
        ]
        
        for descripcion, accion, duracion in secuencia:
            print(f"\n🔄 {descripcion}")
            
            try:
                if accion == "adelante":
                    await self.driver.start_belt()
                elif accion == "atras":
                    await self.driver.reverse_direction()
                elif accion == "parar":
                    await self.driver.stop_belt()
                elif accion == "cambio_rapido":
                    await self.driver.start_belt()
                    await asyncio.sleep(1)
                    await self.driver.reverse_direction()
                    await asyncio.sleep(1)
                    await self.driver.start_belt()
                
                # Mostrar estado
                await self._mostrar_estado_relays()
                
                # Esperar duración especificada
                print(f"   ⏱️ Esperando {duracion} segundos...")
                await asyncio.sleep(duracion)
                
            except Exception as e:
                print(f"❌ Error en paso automático: {e}")
                break
        
        print("\n✅ Demo automática completada")
    
    async def demo_seguridad(self):
        """Demo de características de seguridad."""
        print("\n" + "="*50)
        print("🛡️ DEMO DE SEGURIDAD")
        print("="*50)
        
        # Test 1: Timeout automático
        print("\n🔬 Test 1: Timeout de seguridad")
        print("   Configurando timeout corto (3 segundos)...")
        
        # Guardar timeout original
        timeout_original = self.driver.config.safety_timeout_s
        self.driver.config.safety_timeout_s = 3.0
        
        print("   Iniciando motor... debería parar automáticamente")
        await self.driver.start_belt()
        
        # Esperar más del timeout
        for i in range(4):
            await asyncio.sleep(1)
            status = await self.driver.get_status()
            print(f"   Segundo {i+1}: Motor {'ON' if status['running'] else 'OFF'}")
        
        # Restaurar timeout
        self.driver.config.safety_timeout_s = timeout_original
        print("   ✅ Test de timeout completado")
        
        # Test 2: Delay entre cambios
        print("\n🔬 Test 2: Delay entre cambios de dirección")
        start_time = time.time()
        await self.driver.start_belt()
        await self.driver.reverse_direction()
        end_time = time.time()
        
        delay = end_time - start_time
        print(f"   Tiempo de cambio: {delay:.3f} segundos")
        print(f"   Delay mínimo: {self.driver._direction_change_delay} segundos")
        print(f"   ✅ {'Correcto' if delay >= self.driver._direction_change_delay else 'Advertencia'}")
        
        await self.driver.stop_belt()
    
    async def cleanup_demo(self):
        """Limpiar recursos de la demo."""
        if self.driver:
            try:
                print("\n🧹 Limpiando recursos...")
                await self.driver.stop_belt()
                await self.driver.cleanup()
                print("✅ Limpieza completada")
            except Exception as e:
                print(f"⚠️ Error en limpieza: {e}")

async def main():
    """Función principal de la demo."""
    demo = DemoRelayMotor()
    
    # Configurar manejador de señales para limpieza
    def signal_handler(signum, frame):
        print(f"\n🛑 Señal {signum} recibida - Terminando demo...")
        demo.demo_active = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Mostrar información inicial
        print("🎯 Demo de Control de Motor DC con Relays 12V")
        print("🔧 Raspberry Pi 5 + Módulo Relays 2 Canales")
        print("\n⚠️  IMPORTANTE: Verifica las conexiones antes de continuar")
        
        input("\n📋 Presiona Enter para continuar...")
        
        # Inicializar demo
        if not await demo.initialize_demo():
            print("❌ No se pudo inicializar la demo")
            return
        
        # Menú principal
        while demo.demo_active:
            print("\n" + "="*50)
            print("🎮 MENÚ PRINCIPAL")
            print("="*50)
            print("1. 🎮 Control manual interactivo")
            print("2. 🤖 Demo automática")
            print("3. 🛡️ Demo de seguridad")
            print("4. 📊 Ver información del sistema")
            print("0. 🚪 Salir")
            
            try:
                opcion = input("\n🎯 Selecciona una opción: ").strip()
                
                if opcion == "1":
                    await demo.demo_manual_control()
                elif opcion == "2":
                    await demo.demo_automatica()
                elif opcion == "3":
                    await demo.demo_seguridad()
                elif opcion == "4":
                    await demo._mostrar_info()
                elif opcion == "0":
                    print("👋 Saliendo de la demo...")
                    break
                else:
                    print("❓ Opción no válida")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Interrupción detectada - Saliendo...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"💥 Error fatal en demo: {e}")
    
    finally:
        await demo.cleanup_demo()
        print("\n👋 Demo terminada. ¡Gracias por probar el sistema!")

if __name__ == "__main__":
    print("\n🚀 Iniciando Demo de Relays...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrumpida por usuario")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()
