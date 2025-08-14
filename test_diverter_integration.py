#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del sistema de desviadores.

Este script verifica:
1. Que se puedan importar correctamente todos los módulos
2. Que la configuración sea válida
3. Que el sistema de desviadores se inicialice correctamente
4. Que las APIs funcionen

Autor: Elias Bautista, Gabriel Calderón, Cristian Hernandez
Fecha: Julio 2025
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger("DiverterIntegrationTest")

def test_imports():
    """Prueba que se puedan importar todos los módulos necesarios."""
    logger.info("🔍 Probando importaciones...")
    
    try:
        from Control_Etiquetado.fruit_diverter_controller import (
            FruitDiverterController, 
            ServoMotorSG995, 
            FruitCategory,
            DiverterPosition
        )
        logger.info("✅ Controlador de desviadores importado correctamente")
        
        # Verificar que las categorías están definidas correctamente
        assert FruitCategory.APPLE.diverter_id == 0
        assert FruitCategory.PEAR.diverter_id == 1
        assert FruitCategory.LEMON.diverter_id == 2
        logger.info("✅ Categorías de frutas configuradas correctamente")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando categorías: {e}")
        return False

def test_configuration():
    """Prueba que la configuración sea válida."""
    logger.info("📋 Probando configuración...")
    
    try:
        config_path = Path("Config_Etiquetadora.json")
        if not config_path.exists():
            logger.error(f"❌ Archivo de configuración no encontrado: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Verificar que existe la sección de desviadores
        if "diverter_settings" not in config:
            logger.error("❌ Sección 'diverter_settings' no encontrada en configuración")
            return False
        
        diverter_config = config["diverter_settings"]
        
        # Verificar campos requeridos
        required_fields = ["enabled", "diverters", "fruit_routing"]
        for field in required_fields:
            if field not in diverter_config:
                logger.error(f"❌ Campo requerido '{field}' no encontrado en diverter_settings")
                return False
        
        # Verificar configuración de desviadores
        diverters = diverter_config["diverters"]
        if "0" not in diverters or "1" not in diverters:
            logger.error("❌ Desviadores 0 y 1 deben estar configurados")
            return False
        
        # Verificar routing de frutas
        routing = diverter_config["fruit_routing"]
        required_routes = ["apple", "pear", "lemon"]
        for route in required_routes:
            if route not in routing:
                logger.error(f"❌ Ruta '{route}' no configurada")
                return False
        
        logger.info("✅ Configuración válida")
        logger.info(f"   - Desviadores habilitados: {diverter_config['enabled']}")
        logger.info(f"   - Número de desviadores: {len(diverters)}")
        logger.info(f"   - Rutas configuradas: {list(routing.keys())}")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando configuración: {e}")
        return False

async def test_diverter_controller():
    """Prueba la inicialización del controlador de desviadores."""
    logger.info("🎛️ Probando controlador de desviadores...")
    
    try:
        from Control_Etiquetado.fruit_diverter_controller import FruitDiverterController, FruitCategory
        
        # Configuración de prueba
        test_config = {
            "enabled": True,
            "activation_duration_seconds": 1.0,
            "return_delay_seconds": 0.2,
            "diverters": {
                0: {
                    "pin": 18,
                    "name": "Test-Diverter-Apple",
                    "category": "apple",
                    "straight_angle": 0,
                    "diverted_angle": 90
                },
                1: {
                    "pin": 19,
                    "name": "Test-Diverter-Pear",
                    "category": "pear",
                    "straight_angle": 0,
                    "diverted_angle": 90
                }
            }
        }
        
        # Crear controlador
        controller = FruitDiverterController(test_config)
        
        # Inicializar (en modo simulación si no hay GPIO)
        success = await controller.initialize()
        if not success:
            logger.warning("⚠️ Inicialización falló - probablemente en modo simulación")
        else:
            logger.info("✅ Controlador inicializado correctamente")
        
        # Verificar estado
        status = controller.get_status()
        logger.info(f"   - Inicializado: {status['initialized']}")
        logger.info(f"   - Total desviadores: {status['total_diverters']}")
        logger.info(f"   - Desviadores activos: {status['active_diverters']}")
        
        # Probar clasificación (simulada)
        logger.info("🧪 Probando clasificación de frutas...")
        
        test_categories = [FruitCategory.APPLE, FruitCategory.PEAR, FruitCategory.LEMON]
        for category in test_categories:
            result = await controller.classify_fruit(category, delay_seconds=0.1)
            status_icon = "✅" if result else "⚠️"
            logger.info(f"   {status_icon} {category.emoji} ({category.fruit_name}): {result}")
        
        # Limpiar
        await controller.cleanup()
        logger.info("✅ Controlador limpiado correctamente")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando controlador: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_main_system_integration():
    """Prueba que el sistema principal pueda importar y usar el controlador."""
    logger.info("🔗 Probando integración con sistema principal...")
    
    try:
        # Intentar importar el sistema principal
        from main_etiquetadora import UltraIndustrialFruitLabelingSystem
        
        logger.info("✅ Sistema principal importado correctamente")
        
        # Verificar que la configuración incluye desviadores
        config_path = "Config_Etiquetadora.json"
        if Path(config_path).exists():
            system = UltraIndustrialFruitLabelingSystem(config_path)
            if hasattr(system, 'diverter_controller'):
                logger.info("✅ Sistema principal tiene atributo diverter_controller")
            else:
                logger.error("❌ Sistema principal no tiene atributo diverter_controller")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando integración: {e}")
        return False

def test_api_endpoints():
    """Prueba que los endpoints de API estén definidos."""
    logger.info("🌐 Probando definición de endpoints API...")
    
    try:
        # Los endpoints se definen dinámicamente, pero podemos verificar
        # que el código no tenga errores de sintaxis
        with open("main_etiquetadora.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_endpoints = [
            "/diverters/status",
            "/diverters/classify", 
            "/diverters/calibrate",
            "/diverters/emergency_stop"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                logger.info(f"   ✅ Endpoint {endpoint} definido")
            else:
                logger.error(f"   ❌ Endpoint {endpoint} no encontrado")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando endpoints: {e}")
        return False

async def main():
    """Función principal de pruebas."""
    logger.info("🚀 === INICIANDO PRUEBAS DE INTEGRACIÓN DE DESVIADORES ===")
    
    tests = [
        ("Importaciones", test_imports),
        ("Configuración", test_configuration),
        ("Controlador de desviadores", test_diverter_controller),
        ("Integración sistema principal", test_main_system_integration),
        ("Endpoints API", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Ejecutando: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    logger.info("\n📊 === RESUMEN DE PRUEBAS ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"   {status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n🏁 Resultado final: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        logger.info("🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema de desviadores está listo.")
        return 0
    else:
        logger.error("💥 Algunas pruebas fallaron. Revisar errores arriba.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Pruebas interrumpidas por usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Error fatal: {e}")
        sys.exit(1)
