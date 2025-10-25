#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de Uso Rápido - Sistema de Detección Posicional Inteligente
==================================================================

Ejemplo simple que muestra cómo usar el sistema de detección inteligente
en solo unas pocas líneas de código.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

# Imports principales
from IA_Etiquetado.smart_position_detector import SmartPositionDetector

def ejemplo_uso_basico():
    """Ejemplo básico de uso del detector inteligente."""
    
    print("🚀 EJEMPLO DE USO RÁPIDO - DETECCIÓN INTELIGENTE")
    print("=" * 50)
    
    # 1. Crear detector
    detector = SmartPositionDetector()
    print("✅ Detector inteligente creado")
    
    # 2. Simular detecciones de frutas (como las que vienen de YOLO)
    detecciones_ejemplo = [
        # 3 manzanas en línea (simulando una fila)
        {'class_name': 'apple', 'confidence': 0.85, 'bbox': (300, 200, 380, 280)},
        {'class_name': 'apple', 'confidence': 0.82, 'bbox': (300, 320, 380, 400)},
        {'class_name': 'apple', 'confidence': 0.88, 'bbox': (300, 440, 380, 520)},
        
        # 2 naranjas lado a lado (ancho)
        {'class_name': 'orange', 'confidence': 0.79, 'bbox': (450, 250, 530, 330)},
        {'class_name': 'orange', 'confidence': 0.83, 'bbox': (600, 250, 680, 330)},
    ]
    
    print(f"📱 Procesando {len(detecciones_ejemplo)} frutas detectadas...")
    
    # 3. Procesar con inteligencia artificial
    clusters = detector.process_detections(detecciones_ejemplo)
    
    # 4. Generar comandos de activación
    comandos = detector.get_activation_commands(clusters)
    
    # 5. Mostrar resultados
    print(f"\n🧠 RESULTADOS INTELIGENTES:")
    print(f"   📦 Grupos detectados: {len(clusters)}")
    print(f"   🎯 Comandos generados: {len(comandos)}")
    
    for i, comando in enumerate(comandos, 1):
        info = comando['cluster_info']
        print(f"\n   Comando {i}:")
        print(f"      ⏱️  Esperar: {comando['delay_s']:.2f} segundos")
        print(f"      🏷️  Activar: {comando['duration_s']:.2f} segundos")
        print(f"      🍎 Frutas: {info['fruit_count']} ({info['rows']}×{info['cols']})")
        print(f"      🏷️  Tipos: {', '.join(set(info['fruit_types']))}")
    
    print(f"\n✨ ¡Sistema inteligente funcionando perfectamente!")
    
    return comandos

def ejemplo_integracion_hardware():
    """Ejemplo de cómo integrar con hardware real."""
    
    print("\n🔧 EJEMPLO DE INTEGRACIÓN CON HARDWARE")
    print("=" * 40)
    
    # Obtener comandos del ejemplo anterior
    comandos = ejemplo_uso_basico()
    
    print("\n💡 Código para integrar con tu L298N:")
    print("-" * 40)
    
    codigo_ejemplo = '''
# En tu código principal:
from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController

async def activar_etiquetador_inteligente(comando):
    delay_s = comando['delay_s']
    duration_s = comando['duration_s']
    cluster_info = comando['cluster_info']
    
    # Esperar el tiempo calculado
    await asyncio.sleep(delay_s)
    
    # Activar por el tiempo exacto necesario
    if cluster_info['rows'] > 1:
        # Múltiples filas - movimiento lateral
        print(f"🔄 Activando movimiento lateral para {cluster_info['rows']} filas")
    
    if cluster_info['cols'] > 1:
        # Múltiples columnas - activación extendida
        print(f"🔄 Activación extendida para {cluster_info['cols']} columnas")
    
    # Activar motor L298N por tiempo calculado
    belt_controller = ConveyorBeltController("Config_Etiquetadora.json")
    await belt_controller.start_belt(75)  # 75% velocidad
    await asyncio.sleep(duration_s)      # Tiempo inteligente
    await belt_controller.stop_belt()
    
    print(f"✅ Etiquetado completado para {cluster_info['fruit_count']} frutas")
'''
    
    print(codigo_ejemplo)

def ejemplo_calibracion_facil():
    """Ejemplo de calibración fácil."""
    
    print("\n🎛️ CALIBRACIÓN SÚPER FÁCIL")
    print("=" * 30)
    
    print("1. 📐 Para tu maqueta de 1m x 0.25m:")
    print("   - Ancho: 0.25m")
    print("   - Largo: 1.0m") 
    print("   - Velocidad: 0.15 m/s (15 cm/s)")
    
    print("\n2. 📍 Posiciones:")
    print("   - Cámara: 20cm desde el inicio")
    print("   - Etiquetador: 80cm desde el inicio")
    print("   - Distancia cámara→etiquetador: 60cm")
    
    print("\n3. ⏱️ Tiempos automáticos:")
    print("   - 1 fruta: ~250ms")
    print("   - 3 frutas en línea: ~550ms")
    print("   - 2×3 frutas: ~800ms")
    
    print("\n4. 🎯 Para calibrar visualmente:")
    print("   python IA_Etiquetado/visual_calibrator.py")

if __name__ == "__main__":
    try:
        # Ejecutar ejemplos
        ejemplo_uso_basico()
        ejemplo_integracion_hardware()
        ejemplo_calibracion_facil()
        
        print("\n" + "🎉" * 20)
        print("¡SISTEMA INTELIGENTE LISTO PARA USAR!")
        print("🎉" * 20)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de tener instaladas las dependencias:")
        print("   pip install scikit-learn numpy")