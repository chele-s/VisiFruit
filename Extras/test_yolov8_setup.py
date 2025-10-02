#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar la instalación de YOLOv8
=========================================================

Este script verifica que:
1. Todas las dependencias estén instaladas
2. El modelo YOLOv8 se pueda cargar
3. La inferencia funcione correctamente
4. El detector sea compatible con el sistema

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Versión: 4.0
"""

import sys
import time
from pathlib import Path

def print_header(text):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_dependency(name, import_statement):
    """Verifica si una dependencia está instalada."""
    try:
        exec(import_statement)
        print(f"[OK] {name} instalado correctamente")
        return True
    except ImportError as e:
        print(f"[ERROR] {name} NO instalado: {e}")
        return False

def main():
    print_header("Test de Instalacion YOLOv8 para VisiFruit v4.0")
    
    # Verificar versión de Python
    print(f"\n[PYTHON] Version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    if sys.version_info < (3, 7):
        print("[ERROR] Se requiere Python 3.7 o superior")
        return 1
    print("[OK] Version de Python compatible")
    
    # Verificar dependencias principales
    print_header("Verificando Dependencias")
    
    dependencies = {
        "NumPy": "import numpy",
        "OpenCV": "import cv2",
        "PyTorch": "import torch",
        "TorchVision": "import torchvision",
        "Ultralytics (YOLOv8)": "from ultralytics import YOLO",
        "Psutil": "import psutil",
        "Asyncio": "import asyncio"
    }
    
    all_ok = True
    for name, import_stmt in dependencies.items():
        if not check_dependency(name, import_stmt):
            all_ok = False
    
    if not all_ok:
        print("\n[ERROR] Faltan dependencias. Instala con:")
        print("   pip install -r requirements_yolov8.txt")
        return 1
    
    # Verificar información del sistema
    print_header("Informacion del Sistema")
    
    import psutil
    import torch
    
    cpu_count = psutil.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"[CPU] CPUs disponibles: {cpu_count}")
    print(f"[RAM] RAM total: {memory_gb:.1f} GB")
    print(f"[PYTORCH] Version: {torch.__version__}")
    print(f"[CUDA] Disponible: {torch.cuda.is_available()}")
    
    # Verificar estructura de carpetas
    print_header("Verificando Estructura de Carpetas")
    
    required_paths = {
        "weights/": "Carpeta de modelos",
        "IA_Etiquetado/": "Carpeta de IA",
        "Config_Etiquetadora.json": "Archivo de configuracion"
    }
    
    for path, description in required_paths.items():
        if Path(path).exists():
            print(f"[OK] {description}: {path}")
        else:
            print(f"[WARNING] {description} no encontrado: {path}")
    
    # Verificar modelo YOLOv8
    print_header("Verificando Modelo YOLOv8")
    
    model_path = Path("weights/best.pt")
    
    if not model_path.exists():
        print(f"[WARNING] Modelo no encontrado en: {model_path}")
        print("\n[INFO] Para continuar:")
        print("   1. Descarga tu modelo de Roboflow")
        print("   2. Renombralo a 'best.pt'")
        print("   3. Colocalo en la carpeta 'weights/'")
        print("\n[OK] Todas las dependencias estan instaladas")
        print("   El sistema esta listo cuando agregues el modelo")
        return 0
    
    print(f"[OK] Modelo encontrado: {model_path}")
    print(f"   Tamaño: {model_path.stat().st_size / (1024**2):.1f} MB")
    
    # Probar carga del modelo
    print_header("Probando Carga del Modelo")
    
    try:
        from ultralytics import YOLO
        
        print("[LOADING] Cargando modelo YOLOv8...")
        start_time = time.time()
        
        model = YOLO(str(model_path))
        
        load_time = time.time() - start_time
        print(f"[OK] Modelo cargado en {load_time:.2f} segundos")
        
        # Información del modelo
        print(f"\n[INFO] Informacion del Modelo:")
        print(f"   Tipo: {model.task}")
        if hasattr(model, 'names'):
            print(f"   Clases: {', '.join(model.names.values())}")
        
    except Exception as e:
        print(f"[ERROR] Error cargando modelo: {e}")
        return 1
    
    # Probar inferencia
    print_header("Probando Inferencia")
    
    try:
        import numpy as np
        
        # Crear imagen de prueba
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        print("[TEST] Ejecutando inferencia de prueba...")
        start_time = time.time()
        
        results = model.predict(
            test_image,
            conf=0.5,
            device='cpu',
            verbose=False
        )
        
        inference_time = (time.time() - start_time) * 1000
        print(f"[OK] Inferencia completada en {inference_time:.1f} ms")
        
        # Estimar FPS
        fps_estimate = 1000 / inference_time
        print(f"[FPS] FPS estimado: {fps_estimate:.1f}")
        
        if fps_estimate < 10:
            print("\n[WARNING] Rendimiento bajo. Considera:")
            print("   - Reducir input_size a 480")
            print("   - Usar num_workers=1")
            print("   - Verificar procesos en segundo plano")
        elif fps_estimate >= 15:
            print("\n[OK] Rendimiento excelente para Raspberry Pi 5")
        else:
            print("\n[OK] Rendimiento adecuado")
        
    except Exception as e:
        print(f"[ERROR] Error en inferencia: {e}")
        return 1
    
    # Verificar detector personalizado
    print_header("Verificando Detector Personalizado")
    
    try:
        from IA_Etiquetado.YOLOv8_detector import EnterpriseFruitDetector
        print("[OK] YOLOv8_detector.py importado correctamente")
        
        # Verificar clases de datos
        from IA_Etiquetado.Fruit_detector import (
            FruitDetection, FrameAnalysisResult, ProcessingPriority
        )
        print("[OK] Clases de datos importadas correctamente")
        
    except ImportError as e:
        print(f"[ERROR] Error importando detector: {e}")
        return 1
    
    # Resumen final
    print_header("Resumen de Verificacion")
    
    print("\n[SUCCESS] TODAS LAS VERIFICACIONES PASARON")
    print("\n[INFO] El sistema esta listo para ejecutarse:")
    print("   python main_etiquetadora_v4.py")
    print("\n[DOCS] Para mas informacion, consulta:")
    print("   - weights/model_config.json")
    print("   - requirements_yolov8.txt")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Prueba interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
