#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Instalación RT-DETR para VisiFruit
===========================================

Script para instalar las dependencias RT-DETR de forma automática y optimizada.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 1.0
"""

import subprocess
import sys
import platform
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command):
    """Ejecuta un comando del sistema."""
    try:
        logger.info(f"Ejecutando: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✅ Comando exitoso: {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error ejecutando comando: {command}")
        logger.error(f"Error: {e.stderr}")
        return False

def check_gpu():
    """Verifica si hay GPU disponible."""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"🎮 GPU detectada: {gpu_name}")
        else:
            logger.info("💻 Solo CPU disponible")
        return gpu_available
    except ImportError:
        logger.info("PyTorch no instalado aún, asumiendo GPU disponible")
        return True

def install_paddle_rtdetr():
    """Instala RT-DETR usando PaddlePaddle."""
    logger.info("📦 Instalando RT-DETR con PaddlePaddle...")
    
    gpu_available = check_gpu()
    
    if gpu_available:
        logger.info("🚀 Instalando PaddlePaddle con soporte GPU...")
        commands = [
            "pip install paddlepaddle-gpu>=2.5.0",
            "pip install paddledet>=2.6.0"
        ]
    else:
        logger.info("💾 Instalando PaddlePaddle para CPU...")
        commands = [
            "pip install paddlepaddle>=2.5.0",
            "pip install paddledet>=2.6.0"
        ]
    
    for command in commands:
        if not run_command(command):
            return False
    
    logger.info("✅ PaddlePaddle RT-DETR instalado correctamente")
    return True

def install_torch_rtdetr():
    """Instala RT-DETR usando PyTorch/Transformers."""
    logger.info("📦 Instalando RT-DETR con PyTorch/Transformers...")
    
    commands = [
        "pip install transformers>=4.35.0",
        "pip install datasets>=2.14.0",
        "pip install accelerate>=0.24.0"
    ]
    
    for command in commands:
        if not run_command(command):
            return False
    
    logger.info("✅ PyTorch RT-DETR instalado correctamente")
    return True

def install_base_requirements():
    """Instala los requirements básicos."""
    logger.info("📦 Instalando dependencias básicas...")
    
    base_requirements = [
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
        "ultralytics>=8.0.0"  # Fallback YOLO
    ]
    
    for req in base_requirements:
        if not run_command(f"pip install {req}"):
            return False
    
    logger.info("✅ Dependencias básicas instaladas")
    return True

def test_installation():
    """Prueba que la instalación funcione."""
    logger.info("🧪 Probando instalación...")
    
    try:
        # Test básico de importación
        import torch
        logger.info(f"✅ PyTorch {torch.__version__} funcionando")
        
        # Test RT-DETR PaddlePaddle
        try:
            import paddle
            import paddledet
            logger.info(f"✅ PaddlePaddle RT-DETR disponible")
            return "paddle"
        except ImportError:
            pass
        
        # Test RT-DETR PyTorch
        try:
            import transformers
            logger.info(f"✅ PyTorch RT-DETR disponible")
            return "pytorch"
        except ImportError:
            pass
        
        # Test YOLO fallback
        try:
            import ultralytics
            logger.info("⚠️ Solo YOLO disponible (RT-DETR no instalado)")
            return "yolo"
        except ImportError:
            logger.error("❌ Ningún detector disponible")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error probando instalación: {e}")
        return None

def main():
    """Función principal de instalación."""
    logger.info("🚀 VisiFruit RT-DETR Installer")
    logger.info("=" * 50)
    
    # Mostrar información del sistema
    logger.info(f"Sistema: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version}")
    
    # Preguntar qué backend instalar
    print("\n¿Qué backend de RT-DETR quieres instalar?")
    print("1. PaddlePaddle (Recomendado para producción)")
    print("2. PyTorch/Transformers (Recomendado para desarrollo)")
    print("3. Ambos (Máxima compatibilidad)")
    print("4. Solo dependencias básicas + YOLO")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    success = True
    
    # Instalar dependencias básicas primero
    if not install_base_requirements():
        logger.error("❌ Fallo instalando dependencias básicas")
        return 1
    
    # Instalar backend seleccionado
    if choice == "1":
        success = install_paddle_rtdetr()
    elif choice == "2":
        success = install_torch_rtdetr()
    elif choice == "3":
        success = install_paddle_rtdetr() and install_torch_rtdetr()
    elif choice == "4":
        logger.info("✅ Solo dependencias básicas instaladas")
    else:
        logger.error("❌ Opción no válida")
        return 1
    
    if not success:
        logger.error("❌ Error durante la instalación")
        return 1
    
    # Probar instalación
    backend = test_installation()
    
    if backend:
        logger.info("\n" + "=" * 50)
        logger.info("🎉 ¡INSTALACIÓN COMPLETADA!")
        logger.info("=" * 50)
        logger.info(f"Backend disponible: {backend.upper()}")
        logger.info("\nPara usar RT-DETR:")
        logger.info("1. Asegúrate de que Config_Etiquetadora.json tenga:")
        logger.info('   "model_type": "rtdetr"')
        logger.info("2. Ejecuta: python main_etiquetadora.py")
        logger.info("\nEl sistema automáticamente:")
        logger.info("- Usará RT-DETR si está disponible")
        logger.info("- Hará fallback a YOLO si RT-DETR no funciona")
        return 0
    else:
        logger.error("❌ Instalación falló - ningún detector disponible")
        return 1

if __name__ == "__main__":
    sys.exit(main())
