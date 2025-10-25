#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de Uso del Driver L298N para Motor DC - FruPrint System
=============================================================

Este archivo demuestra cómo usar el nuevo driver L298N integrado
en el sistema de control de banda transportadora.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 1.0
"""

import asyncio
import logging
import json
import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para importar el módulo
sys.path.append(str(Path(__file__).parent.parent))

from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController, BeltConfiguration

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def create_l298n_config():
    """
    Crear archivo de configuración para L298N.
    
    Conexiones físicas recomendadas:
    ================================
    L298N Pin    →    Raspberry Pi Pin    →    Función
    ----------------------------------------
    ENA          →    GPIO 13 (Pin 33)    →    PWM para velocidad
    IN1          →    GPIO 20 (Pin 38)    →    Control dirección 1
    IN2          →    GPIO 21 (Pin 40)    →    Control dirección 2
    VCC (5V)     →    5V (Pin 2 o 4)     →    Alimentación lógica
    GND          →    GND (Pin 6, 14...)  →    Tierra común
    VIN (Motor)  →    12V externa         →    Alimentación motor
    Motor +      →    Terminal del motor
    Motor -      →    Terminal del motor
    
    Opcional:
    ENB          →    GPIO 12 (Pin 32)    →    Habilitación adicional
    """
    
    config = {
        "conveyor_belt_settings": {
            "control_type": "l298n_motor",
            "motor_pin_bcm": 13,         # ENA - Pin PWM para velocidad
            "enable_pin_bcm": 12,        # Pin opcional de habilitación
            "direction_pin_bcm": 20,     # IN1 - Primera señal de dirección
            "direction_pin2_bcm": 21,    # IN2 - Segunda señal de dirección
            "pwm_frequency_hz": 1000,    # Frecuencia PWM (1 kHz recomendado)
            "min_duty_cycle": 30,        # Duty cycle mínimo (30% para arranque)
            "max_duty_cycle": 100,       # Duty cycle máximo (100%)
            "default_speed_percent": 75, # Velocidad por defecto (75%)
            "safety_timeout_s": 10.0,    # Timeout de seguridad
            "recovery_attempts": 3,      # Intentos de recuperación
            "health_check_interval_s": 1.0
        }
    }
    
    # Guardar configuración en archivo
    config_path = "config_l298n_example.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Configuración L298N guardada en: {config_path}")
    return config_path

async def test_l298n_basic():
    """Prueba básica del driver L298N."""
    logger.info("=== Prueba Básica del Driver L298N ===")
    
    # Crear configuración
    config_file = create_l298n_config()
    
    # Crear controlador
    controller = ConveyorBeltController(config_file)
    
    try:
        # Inicializar
        if await controller.initialize():
            logger.info("✓ Controlador L298N inicializado correctamente")
            
            # Mostrar estado inicial
            status = controller.get_status()
            logger.info(f"Estado inicial: {status['status']['state']}")
            
            # Test 1: Arranque hacia adelante
            logger.info("\n--- Test 1: Arranque hacia adelante ---")
            if await controller.start_belt(50):  # 50% velocidad
                logger.info("✓ Motor iniciado hacia adelante al 50%")
                await asyncio.sleep(3)
                
                # Mostrar estado actual
                status = controller.get_status()
                logger.info(f"Estado actual: {status['status']}")
                
                # Test 2: Cambio de velocidad
                logger.info("\n--- Test 2: Cambio de velocidad ---")
                if await controller.set_speed(80):  # 80% velocidad
                    logger.info("✓ Velocidad cambiada a 80%")
                    await asyncio.sleep(2)
                
                # Test 3: Parada
                logger.info("\n--- Test 3: Parada normal ---")
                if await controller.stop_belt():
                    logger.info("✓ Motor detenido correctamente")
                    await asyncio.sleep(1)
                
            else:
                logger.error("✗ Error iniciando motor")
                
        else:
            logger.error("✗ Error inicializando controlador")
            
    except KeyboardInterrupt:
        logger.info("Prueba interrumpida por usuario")
    except Exception as e:
        logger.error(f"Error en prueba: {e}")
    finally:
        await controller.cleanup()
        logger.info("=== Prueba Finalizada ===")

async def test_l298n_advanced():
    """Prueba avanzada con control de dirección."""
    logger.info("=== Prueba Avanzada del Driver L298N ===")
    
    config_file = create_l298n_config()
    controller = ConveyorBeltController(config_file)
    
    try:
        if await controller.initialize():
            # Verificar que sea driver L298N
            status = controller.get_status()
            if status.get('status', {}).get('control_type') != 'l298n':
                logger.warning("Driver no es L298N, funcionalidad limitada")
                return
                
            # Test de movimientos secuenciales
            movements = [
                ("forward", 40, 2),    # Adelante 40% por 2 segundos
                ("forward", 70, 3),    # Adelante 70% por 3 segundos
                ("stop", 0, 1),        # Parar por 1 segundo
                ("backward", 50, 2),   # Atrás 50% por 2 segundos
                ("brake", 0, 1),       # Freno por 1 segundo
            ]
            
            for direction, speed, duration in movements:
                logger.info(f"\n--- Movimiento: {direction} al {speed}% por {duration}s ---")
                
                if direction == "forward":
                    success = await controller.start_belt(speed)
                elif direction == "backward":
                    # Para reversa, necesitamos acceso directo al driver
                    if hasattr(controller.driver, 'reverse_direction'):
                        success = await controller.driver.reverse_direction(speed)
                    else:
                        logger.warning("Función de reversa no disponible")
                        continue
                elif direction == "stop":
                    success = await controller.stop_belt()
                elif direction == "brake":
                    if hasattr(controller.driver, 'emergency_brake'):
                        success = await controller.driver.emergency_brake()
                    else:
                        success = await controller.stop_belt()
                
                if success:
                    logger.info(f"✓ Movimiento {direction} ejecutado")
                    await asyncio.sleep(duration)
                    
                    # Mostrar métricas
                    metrics = controller.get_metrics()
                    logger.info(f"Estado motor: {metrics['current']}")
                else:
                    logger.error(f"✗ Error ejecutando movimiento {direction}")
                    
    except Exception as e:
        logger.error(f"Error en prueba avanzada: {e}")
    finally:
        await controller.cleanup()

def show_wiring_diagram():
    """Mostrar diagrama de conexiones L298N."""
    
    diagram = """
    DIAGRAMA DE CONEXIONES L298N
    ============================
    
    Raspberry Pi          L298N Module          Motor DC
    ============          ============          ========
    
    GPIO 13 (Pin 33) ---> ENA               
    GPIO 20 (Pin 38) ---> IN1               
    GPIO 21 (Pin 40) ---> IN2               
    GPIO 12 (Pin 32) ---> EN (opcional)     
    5V (Pin 2)       ---> VCC              
    GND (Pin 6)      ---> GND              
                          OUT1 -----------> Motor (+)
                          OUT2 -----------> Motor (-)
                          VIN <------------ 12V Externa
                          GND <------------ GND Externa
    
    TABLA DE VERDAD L298N:
    =====================
    ENA  | IN1  | IN2  | Motor
    -----|------|------|----------
    PWM  | HIGH | LOW  | Adelante
    PWM  | LOW  | HIGH | Atrás  
    PWM  | LOW  | LOW  | Parado
    PWM  | HIGH | HIGH | Freno
    0    | X    | X    | Parado
    
    NOTAS IMPORTANTES:
    ==================
    1. ENA controla la velocidad con PWM (0-100%)
    2. IN1 e IN2 controlan la dirección del motor
    3. VIN debe ser la tensión del motor (6-12V típico)
    4. VCC es para la lógica (5V desde RPi)
    5. Usar disipador térmico en el L298N
    6. Verificar que el motor no exceda 2A por canal
    """
    
    print(diagram)

async def main():
    """Función principal de ejemplo."""
    logger.info("Driver L298N para VisiFruit - Ejemplos de Uso")
    
    # Mostrar diagrama de conexiones
    show_wiring_diagram()
    
    # Menú de opciones
    while True:
        print("\n" + "="*50)
        print("MENÚ DE PRUEBAS L298N")
        print("="*50)
        print("1. Prueba básica (arranque/parada)")
        print("2. Prueba avanzada (con dirección)")
        print("3. Mostrar diagrama de conexiones")
        print("4. Crear configuración de ejemplo")
        print("0. Salir")
        
        try:
            opcion = input("\nSeleccione una opción: ").strip()
            
            if opcion == "1":
                await test_l298n_basic()
            elif opcion == "2":
                await test_l298n_advanced()
            elif opcion == "3":
                show_wiring_diagram()
            elif opcion == "4":
                create_l298n_config()
                print("Configuración creada: config_l298n_example.json")
            elif opcion == "0":
                print("¡Adiós!")
                break
            else:
                print("Opción no válida")
                
        except KeyboardInterrupt:
            print("\n¡Adiós!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Ejecutar programa principal
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")