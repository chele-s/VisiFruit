#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de Uso del Driver de Relays para Motor DC - VisiFruit System
===================================================================

Este archivo demuestra cómo usar el driver de relays de 12V para
controlar un motor DC de banda transportadora con Raspberry Pi 5.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 1.0
"""

import asyncio
import logging
import json
import sys
import os
import time
from pathlib import Path

# Agregar el directorio padre al path para importar el módulo
sys.path.append(str(Path(__file__).parent.parent))

from Control_Etiquetado.relay_motor_controller import RelayMotorDriver, create_relay_motor_driver
from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController, BeltConfiguration

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def create_relay_config_file():
    """
    Crear archivo de configuración para relays de 12V.
    
    Conexiones físicas recomendadas para Raspberry Pi 5:
    ===================================================
    Relay Module Pin  →    Raspberry Pi 5 Pin    →    Función
    ------------------------------------------------
    VCC              →    5V (Pin 2 o 4)         →    Alimentación lógica
    GND              →    GND (Pin 6, 14...)     →    Tierra común
    IN1              →    GPIO 18 (Pin 12)       →    Control Relay 1 (Adelante)
    IN2              →    GPIO 19 (Pin 35)       →    Control Relay 2 (Atrás)
    EN (opcional)    →    GPIO 26 (Pin 37)       →    Habilitación general
    
    Conexiones de potencia:
    ======================
    Motor DC 12V     →    Conectar a terminales COM de relays
    Fuente 12V+      →    Conectar a terminales NC de ambos relays
    Fuente 12V-      →    Conectar a motor (terminal negativo)
    """
    
    config = {
        "system_settings": {
            "installation_id": "VISIFRUIT-RELAY-DEMO",
            "system_name": "Demo Relay Motor VisiFruit",
            "log_level": "INFO"
        },
        "conveyor_belt_settings": {
            "control_type": "relay_motor",
            "relay1_pin_bcm": 18,        # GPIO 18 - Relay 1 (Adelante)
            "relay2_pin_bcm": 19,        # GPIO 19 - Relay 2 (Atrás)
            "enable_pin_bcm": 26,        # GPIO 26 - Habilitación (opcional)
            "active_state_on": "LOW",    # Relays se activan con señal LOW
            "safety_timeout_s": 10.0,    # Timeout automático
            "recovery_attempts": 3,
            "health_check_interval_s": 1.0,
            "direction_change_delay_s": 0.5,  # Delay entre cambios de dirección
            "belt_speed_mps": 0.5
        },
        "relay_specifications": {
            "module_type": "2-Channel 5V Relay Module",
            "coil_voltage": "5V",
            "contact_rating": "10A/250VAC",
            "isolation": "Optocoupler 4000V",
            "switching_time_ms": 10,
            "control_logic": "Active LOW"
        },
        "api_settings": {
            "enabled": true,
            "host": "0.0.0.0",
            "port": 8000
        }
    }
    
    # Guardar configuración en archivo
    config_path = "config_relay_motor_demo.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Configuración de relays guardada en: {config_path}")
    return config_path

async def test_relay_basic():
    """Prueba básica del driver de relays."""
    logger.info("=== Prueba Básica del Driver de Relays ===")
    
    # Crear driver directamente
    driver = create_relay_motor_driver(
        relay1_pin=18,  # Adelante
        relay2_pin=19,  # Atrás  
        enable_pin=26   # Habilitación
    )
    
    try:
        # Inicializar
        if await driver.initialize():
            logger.info("✓ Driver de relays inicializado correctamente")
            
            # Mostrar estado inicial
            status = await driver.get_status()
            logger.info(f"Estado inicial: {status}")
            
            # Test 1: Motor adelante
            logger.info("\n--- Test 1: Motor adelante ---")
            if await driver.start_belt():
                logger.info("✓ Motor iniciado hacia adelante")
                await asyncio.sleep(3)
                
                # Mostrar estado de relays
                status = await driver.get_status()
                logger.info(f"Estado relays: {status['relay_states']}")
                logger.info(f"Dirección: {status['direction']}")
                
                # Test 2: Parar motor
                logger.info("\n--- Test 2: Parar motor ---")
                if await driver.stop_belt():
                    logger.info("✓ Motor detenido")
                    await asyncio.sleep(1)
                
                # Test 3: Motor atrás
                logger.info("\n--- Test 3: Motor atrás ---")
                if await driver.reverse_direction():
                    logger.info("✓ Motor en dirección reversa")
                    await asyncio.sleep(3)
                    
                    # Mostrar estado
                    status = await driver.get_status()
                    logger.info(f"Estado relays: {status['relay_states']}")
                    
                # Test 4: Frenado de emergencia
                logger.info("\n--- Test 4: Frenado de emergencia ---")
                if await driver.emergency_brake():
                    logger.info("✓ Frenado de emergencia ejecutado")
                
            else:
                logger.error("✗ Error iniciando motor")
                
        else:
            logger.error("✗ Error inicializando driver")
            
    except KeyboardInterrupt:
        logger.info("Prueba interrumpida por usuario")
    except Exception as e:
        logger.error(f"Error en prueba: {e}")
    finally:
        await driver.cleanup()
        logger.info("=== Prueba Finalizada ===")

async def test_relay_with_controller():
    """Prueba usando el controlador completo de VisiFruit."""
    logger.info("=== Prueba con Controlador VisiFruit ===")
    
    # Crear configuración
    config_file = create_relay_config_file()
    
    # Crear controlador
    controller = ConveyorBeltController(config_file)
    
    try:
        # Inicializar
        if await controller.initialize():
            logger.info("✓ Controlador VisiFruit inicializado")
            
            # Verificar que es driver de relays
            if hasattr(controller.driver, 'current_direction'):
                logger.info("✓ Driver de relays detectado")
                
                # Secuencia de pruebas
                test_sequence = [
                    ("start_belt", "Iniciar hacia adelante", 3),
                    ("stop_belt", "Parar motor", 1),
                    ("start_belt", "Reiniciar", 2),
                    ("emergency_stop", "Parada de emergencia", 1)
                ]
                
                for method, description, duration in test_sequence:
                    logger.info(f"\n--- {description} ---")
                    
                    if method == "start_belt":
                        success = await controller.start_belt()
                    elif method == "stop_belt":
                        success = await controller.stop_belt()
                    elif method == "emergency_stop":
                        success = await controller.emergency_stop()
                    
                    if success:
                        logger.info(f"✓ {description} ejecutado")
                        
                        # Mostrar estado
                        status = controller.get_status()
                        logger.info(f"Estado sistema: {status['status']['state']}")
                        logger.info(f"Motor funcionando: {status['status']['is_running']}")
                        
                        await asyncio.sleep(duration)
                    else:
                        logger.error(f"✗ Error en {description}")
                
                # Mostrar métricas finales
                logger.info("\n--- Métricas Finales ---")
                metrics = controller.get_metrics()
                logger.info(f"Tiempo funcionamiento: {metrics['performance']['total_runtime_hours']:.3f}h")
                logger.info(f"Número de arranques: {metrics['performance']['start_count']}")
                logger.info(f"Score de eficiencia: {metrics['performance']['efficiency_score']:.1f}%")
                
            else:
                logger.error("✗ Driver de relays no detectado")
                
        else:
            logger.error("✗ Error inicializando controlador")
            
    except Exception as e:
        logger.error(f"Error en prueba con controlador: {e}")
    finally:
        await controller.cleanup()

async def test_relay_safety_features():
    """Prueba de características de seguridad."""
    logger.info("=== Prueba de Características de Seguridad ===")
    
    driver = create_relay_motor_driver(18, 19, 26)
    
    try:
        await driver.initialize()
        
        # Test 1: Timeout de seguridad
        logger.info("\n--- Test 1: Timeout de Seguridad ---")
        logger.info("Configurando timeout de 3 segundos...")
        
        # Modificar timeout temporalmente
        original_timeout = driver.config.safety_timeout_s
        driver.config.safety_timeout_s = 3.0
        
        logger.info("Iniciando motor... debería parar automáticamente en 3s")
        await driver.start_belt()
        
        # Esperar más del timeout
        await asyncio.sleep(4)
        
        status = await driver.get_status()
        if not status['running']:
            logger.info("✓ Timeout de seguridad funcionó correctamente")
        else:
            logger.error("✗ Timeout de seguridad falló")
        
        # Restaurar timeout original
        driver.config.safety_timeout_s = original_timeout
        
        # Test 2: Delay entre cambios de dirección
        logger.info("\n--- Test 2: Delay entre Cambios de Dirección ---")
        
        start_time = time.time()
        await driver.start_belt()  # Adelante
        await driver.reverse_direction()  # Cambio a atrás
        end_time = time.time()
        
        change_time = end_time - start_time
        if change_time >= driver._direction_change_delay:
            logger.info(f"✓ Delay de cambio respetado: {change_time:.3f}s")
        else:
            logger.warning(f"⚠️ Delay muy corto: {change_time:.3f}s")
        
        await driver.stop_belt()
        
        # Test 3: Verificación anti-cortocircuito
        logger.info("\n--- Test 3: Anti-Cortocircuito ---")
        
        # Intentar activar ambos relays (internamente se debe prevenir)
        await driver._set_relay_direction("forward")
        status1 = await driver.get_status()
        
        await driver._set_relay_direction("backward")
        status2 = await driver.get_status()
        
        # Verificar que nunca ambos estén ON simultáneamente
        relay1_on = status1['relay_states']['relay1'] == 'ON'
        relay2_on = status1['relay_states']['relay2'] == 'ON'
        
        if not (relay1_on and relay2_on):
            logger.info("✓ Protección anti-cortocircuito funcionando")
        else:
            logger.error("✗ PELIGRO: Ambos relays activos simultáneamente")
        
    except Exception as e:
        logger.error(f"Error en pruebas de seguridad: {e}")
    finally:
        await driver.cleanup()

async def demo_integration_visifruit():
    """Demostración de integración completa con VisiFruit."""
    logger.info("=== Demo: Integración Completa VisiFruit ===")
    
    config_file = create_relay_config_file()
    
    # Simular sistema VisiFruit completo
    logger.info("Simulando sistema de etiquetado con banda de relays...")
    
    controller = ConveyorBeltController(config_file)
    
    try:
        await controller.initialize()
        
        # Simular ciclo de producción
        logger.info("\n🍎 Iniciando ciclo de producción simulado...")
        
        cycles = [
            ("Detectando frutas...", 1),
            ("Iniciando banda transportadora", "start"),
            ("Procesando fila de frutas", 4),
            ("Pausando para etiquetado", "stop"),
            ("Continuando procesamiento", "start"),
            ("Finalizando ciclo", 2),
            ("Parando banda", "stop")
        ]
        
        for step, action in cycles:
            logger.info(f"\n📋 {step}")
            
            if action == "start":
                await controller.start_belt()
                logger.info("   ➡️ Banda en movimiento")
            elif action == "stop":
                await controller.stop_belt()
                logger.info("   ⏸️ Banda detenida")
            else:
                await asyncio.sleep(action)
            
            # Mostrar estado cada paso
            status = controller.get_status()
            logger.info(f"   📊 Estado: {status['status']['state']}")
        
        # Mostrar métricas finales
        logger.info("\n📈 === MÉTRICAS FINALES ===")
        metrics = controller.get_metrics()
        logger.info(f"⏱️ Tiempo total: {metrics['performance']['total_runtime_hours']:.3f}h")
        logger.info(f"🔄 Arranques: {metrics['performance']['start_count']}")
        logger.info(f"⚡ Eficiencia: {metrics['performance']['efficiency_score']:.1f}%")
        logger.info(f"🏥 Salud sistema: {metrics['performance']['health_score']:.1f}%")
        
    except Exception as e:
        logger.error(f"Error en demo de integración: {e}")
    finally:
        await controller.cleanup()

def show_wiring_diagram():
    """Mostrar diagrama de conexiones para relays."""
    
    diagram = """
    DIAGRAMA DE CONEXIONES - RELAYS 12V + RASPBERRY PI 5
    ====================================================
    
    Raspberry Pi 5        Módulo Relays 2Ch      Motor DC 12V
    ==============        =================      ============
    
    GPIO 18 (Pin 12) ---> IN1                
    GPIO 19 (Pin 35) ---> IN2                
    GPIO 26 (Pin 37) ---> EN (opcional)      
    5V (Pin 2)       ---> VCC               
    GND (Pin 6)      ---> GND               
                          
                          Relay 1:
                          NC1 <----- 12V+
                          COM1 ----> Motor (+)
                          NO1        (sin usar)
                          
                          Relay 2:
                          NC2 <----- 12V+
                          COM2 ----> Motor (-)
                          NO2        (sin usar)
                          
    Fuente Externa 12V/5A:
    ======================
    12V+ --------> NC1 y NC2 de relays
    12V- --------> GND común del sistema
    
    TABLA DE FUNCIONAMIENTO:
    =======================
    IN1  | IN2  | Relay1 | Relay2 | Motor
    -----|------|--------|--------|----------
    HIGH | HIGH |  OFF   |  OFF   | PARADO
    LOW  | HIGH |  ON    |  OFF   | ADELANTE
    HIGH | LOW  |  OFF   |  ON    | ATRÁS
    LOW  | LOW  |  ❌ PROHIBIDO ❌ | CORTOCIRCUITO
    
    NOTAS IMPORTANTES:
    ==================
    1. Usar SOLO terminales NC (Normally Closed) de los relays
    2. Nunca activar ambos relays simultáneamente
    3. Instalar fusible de 7A en línea 12V+
    4. Verificar todas las conexiones antes de energizar
    5. El módulo relay se activa con señal LOW (active low)
    6. Usar fuente de RPi de mínimo 3A para alimentar relays
    """
    
    print(diagram)

def show_troubleshooting():
    """Mostrar guía de solución de problemas."""
    
    guide = """
    GUÍA DE SOLUCIÓN DE PROBLEMAS - RELAYS
    ======================================
    
    🔍 PROBLEMA: Motor no responde
    --------------------------------
    ✅ Verificar:
       - Conexiones GPIO 18 y 19
       - Alimentación 5V del módulo relays
       - Fusible de 7A no fundido
       - Motor conectado a terminales COM
       - Fuente 12V funcionando
    
    🔍 PROBLEMA: Solo funciona una dirección
    ----------------------------------------
    ✅ Verificar:
       - LED de relay se enciende al activar
       - Continuidad en terminales del relay
       - Conexiones del motor intercambiadas
       - Relay defectuoso (reemplazar)
    
    🔍 PROBLEMA: RPi se reinicia o congela
    --------------------------------------
    ✅ Verificar:
       - Fuente RPi de mínimo 3A
       - Conexión USB-C firme
       - No sobrecargar GPIO 5V
       - Temperatura del RPi (<80°C)
    
    🔍 PROBLEMA: Relays hacen click pero motor no gira
    --------------------------------------------------
    ✅ Verificar:
       - Tensión 12V en terminales NC
       - Continuidad motor (2-10 ohms típico)
       - Fusible íntegro
       - Motor no bloqueado mecánicamente
    
    🔍 PROBLEMA: Sistema funciona irregular
    ---------------------------------------
    ✅ Verificar:
       - Logs del sistema (errores GPIO)
       - Temperatura componentes
       - Interferencia electromagnética
       - Conexiones flojas en terminales
    
    COMANDOS DE DIAGNÓSTICO:
    ========================
    
    # Verificar GPIO RPi
    gpio readall
    
    # Probar relay individual
    echo "18" > /sys/class/gpio/export
    echo "out" > /sys/class/gpio/gpio18/direction
    echo "0" > /sys/class/gpio/gpio18/value    # Activar relay
    echo "1" > /sys/class/gpio/gpio18/value    # Desactivar relay
    
    # Ver logs del sistema
    journalctl -f | grep gpio
    
    # Verificar temperatura RPi
    vcgencmd measure_temp
    """
    
    print(guide)

async def main():
    """Función principal del ejemplo."""
    logger.info("🚀 Driver de Relays para VisiFruit - Raspberry Pi 5")
    
    # Mostrar información inicial
    show_wiring_diagram()
    
    # Menú de opciones
    while True:
        print("\n" + "="*60)
        print("🔧 MENÚ DE PRUEBAS - RELAYS MOTOR DC")
        print("="*60)
        print("1. Prueba básica del driver")
        print("2. Prueba con controlador VisiFruit") 
        print("3. Prueba de características de seguridad")
        print("4. Demo integración completa")
        print("5. Mostrar diagrama de conexiones")
        print("6. Crear configuración de ejemplo")
        print("7. Guía de solución de problemas")
        print("0. Salir")
        
        try:
            opcion = input("\n🎯 Seleccione una opción: ").strip()
            
            if opcion == "1":
                await test_relay_basic()
            elif opcion == "2":
                await test_relay_with_controller()
            elif opcion == "3":
                await test_relay_safety_features()
            elif opcion == "4":
                await demo_integration_visifruit()
            elif opcion == "5":
                show_wiring_diagram()
            elif opcion == "6":
                config_file = create_relay_config_file()
                print(f"✅ Configuración creada: {config_file}")
            elif opcion == "7":
                show_troubleshooting()
            elif opcion == "0":
                print("👋 ¡Adiós!")
                break
            else:
                print("❌ Opción no válida")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Adiós!")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    # Configurar logging para el ejemplo
    import colorama
    colorama.init()  # Para colores en Windows
    
    # Ejecutar programa principal
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido por usuario")
    except Exception as e:
        logger.error(f"💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()
