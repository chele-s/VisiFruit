#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Entrenamiento YOLOv12 para Detección de Frutas - VisiFruit System
==========================================================================

Sistema completo de entrenamiento de modelos YOLOv12 para detección y clasificación
de frutas en tiempo real. Incluye dataset management, data augmentation, 
entrenamiento optimizado y validación de métricas.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Edición Industrial
"""

import os
import sys
import json
import yaml
import logging
import shutil
import random
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime
import argparse

# Imports de YOLO y ML
try:
    from ultralytics import YOLO
    import torch
    import torchvision.transforms as transforms
    from PIL import Image, ImageDraw, ImageEnhance
    import cv2
    YOLO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Dependencias YOLO no disponibles: {e}")
    print("Instalar con: pip install ultralytics torch torchvision pillow opencv-python")
    YOLO_AVAILABLE = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FruitDatasetManager:
    """Gestor del dataset de frutas para entrenamiento YOLO."""
    
    def __init__(self, dataset_path: str = "IA_Etiquetado/Dataset_Frutas"):
        self.dataset_path = Path(dataset_path)
        self.images_path = self.dataset_path / "images"
        self.labels_path = self.dataset_path / "labels"
        self.yaml_path = self.dataset_path / "Data.yaml"
        
        # Clases de frutas soportadas
        self.fruit_classes = {
            'apple': 0,
            'orange': 1, 
            'banana': 2,
            'grape': 3,
            'strawberry': 4,
            'pineapple': 5,
            'mango': 6,
            'watermelon': 7,
            'lemon': 8,
            'peach': 9
        }
        
        self.setup_directories()
        
    def setup_directories(self):
        """Crear estructura de directorios del dataset."""
        try:
            # Crear directorios principales
            self.dataset_path.mkdir(exist_ok=True)
            
            # Crear subdirectorios para train/val/test
            for split in ['train', 'val', 'test']:
                (self.images_path / split).mkdir(parents=True, exist_ok=True)
                (self.labels_path / split).mkdir(parents=True, exist_ok=True)
                
            logger.info(f"✓ Estructura de directorios creada en: {self.dataset_path}")
            
        except Exception as e:
            logger.error(f"Error creando directorios: {e}")
            
    def create_dataset_yaml(self):
        """Crear archivo de configuración YAML para YOLO."""
        
        yaml_config = {
            'path': str(self.dataset_path.absolute()),
            'train': 'images/train',
            'val': 'images/val', 
            'test': 'images/test',
            'nc': len(self.fruit_classes),  # número de clases
            'names': list(self.fruit_classes.keys())
        }
        
        try:
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_config, f, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"✓ Archivo YAML creado: {self.yaml_path}")
            return str(self.yaml_path)
            
        except Exception as e:
            logger.error(f"Error creando YAML: {e}")
            return None
    
    def augment_images(self, input_dir: Path, output_dir: Path, augmentations_per_image: int = 5):
        """Aplicar data augmentation a las imágenes."""
        
        if not input_dir.exists():
            logger.warning(f"Directorio no existe: {input_dir}")
            return
            
        augmentation_transforms = [
            self._random_brightness,
            self._random_contrast,
            self._random_saturation,
            self._random_flip,
            self._random_rotation,
            self._random_scale,
            self._add_noise,
            self._random_blur
        ]
        
        image_files = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))
        logger.info(f"Procesando {len(image_files)} imágenes para augmentation...")
        
        for img_path in image_files:
            try:
                # Cargar imagen original
                img = Image.open(img_path)
                base_name = img_path.stem
                
                # Generar versiones aumentadas
                for i in range(augmentations_per_image):
                    augmented_img = img.copy()
                    
                    # Aplicar 2-3 transformaciones aleatorias
                    num_transforms = random.randint(2, 3)
                    selected_transforms = random.sample(augmentation_transforms, num_transforms)
                    
                    for transform in selected_transforms:
                        augmented_img = transform(augmented_img)
                    
                    # Guardar imagen aumentada
                    output_path = output_dir / f"{base_name}_aug_{i:03d}.jpg"
                    augmented_img.save(output_path, quality=95)
                    
                    # Copiar/modificar archivo de etiquetas si existe
                    self._copy_augmented_labels(img_path, output_path)
                    
            except Exception as e:
                logger.error(f"Error procesando {img_path}: {e}")
                
        logger.info(f"✓ Data augmentation completado")
    
    def _random_brightness(self, img: Image.Image) -> Image.Image:
        """Ajustar brillo aleatoriamente."""
        factor = random.uniform(0.7, 1.3)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(factor)
    
    def _random_contrast(self, img: Image.Image) -> Image.Image:
        """Ajustar contraste aleatoriamente."""
        factor = random.uniform(0.8, 1.2)
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)
    
    def _random_saturation(self, img: Image.Image) -> Image.Image:
        """Ajustar saturación aleatoriamente."""
        factor = random.uniform(0.8, 1.2)
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)
    
    def _random_flip(self, img: Image.Image) -> Image.Image:
        """Voltear imagen horizontalmente."""
        if random.random() > 0.5:
            return img.transpose(Image.FLIP_LEFT_RIGHT)
        return img
    
    def _random_rotation(self, img: Image.Image) -> Image.Image:
        """Rotar imagen ligeramente."""
        angle = random.uniform(-15, 15)
        return img.rotate(angle, expand=False, fillcolor=(255, 255, 255))
    
    def _random_scale(self, img: Image.Image) -> Image.Image:
        """Escalar imagen."""
        scale = random.uniform(0.8, 1.2)
        w, h = img.size
        new_w, new_h = int(w * scale), int(h * scale)
        scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Crop o pad para mantener tamaño original
        if scale > 1.0:
            # Crop desde el centro
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            scaled = scaled.crop((left, top, left + w, top + h))
        else:
            # Pad con blanco
            result = Image.new('RGB', (w, h), (255, 255, 255))
            paste_x = (w - new_w) // 2
            paste_y = (h - new_h) // 2
            result.paste(scaled, (paste_x, paste_y))
            scaled = result
            
        return scaled
    
    def _add_noise(self, img: Image.Image) -> Image.Image:
        """Agregar ruido gaussiano."""
        np_img = np.array(img)
        noise = np.random.normal(0, 25, np_img.shape).astype(np.uint8)
        noisy_img = np.clip(np_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_img)
    
    def _random_blur(self, img: Image.Image) -> Image.Image:
        """Aplicar desenfoque aleatorio."""
        if random.random() > 0.7:  # 30% probabilidad
            np_img = np.array(img)
            kernel_size = random.choice([3, 5])
            blurred = cv2.GaussianBlur(np_img, (kernel_size, kernel_size), 0)
            return Image.fromarray(blurred)
        return img
    
    def _copy_augmented_labels(self, original_img_path: Path, new_img_path: Path):
        """Copiar archivo de etiquetas para imagen aumentada."""
        # Buscar archivo .txt correspondiente
        original_label = original_img_path.parent.parent / "labels" / original_img_path.parent.name / f"{original_img_path.stem}.txt"
        
        if original_label.exists():
            new_label_dir = new_img_path.parent.parent / "labels" / new_img_path.parent.name
            new_label_dir.mkdir(parents=True, exist_ok=True)
            new_label_path = new_label_dir / f"{new_img_path.stem}.txt"
            
            shutil.copy2(original_label, new_label_path)
    
    def split_dataset(self, train_ratio: float = 0.7, val_ratio: float = 0.2, test_ratio: float = 0.1):
        """Dividir dataset en train/val/test."""
        
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
            raise ValueError("Las proporciones deben sumar 1.0")
        
        # Recopilar todas las imágenes
        all_images = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            all_images.extend(self.images_path.glob(ext))
        
        if not all_images:
            logger.warning("No se encontraron imágenes para dividir")
            return
        
        # Mezclar aleatoriamente
        random.shuffle(all_images)
        
        # Calcular índices de división
        total = len(all_images)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        
        # Dividir archivos
        train_files = all_images[:train_end]
        val_files = all_images[train_end:val_end]
        test_files = all_images[val_end:]
        
        logger.info(f"División del dataset:")
        logger.info(f"  - Entrenamiento: {len(train_files)} imágenes")
        logger.info(f"  - Validación: {len(val_files)} imágenes")
        logger.info(f"  - Prueba: {len(test_files)} imágenes")
        
        # Mover archivos a subdirectorios
        self._move_files_to_split('train', train_files)
        self._move_files_to_split('val', val_files)
        self._move_files_to_split('test', test_files)
        
    def _move_files_to_split(self, split_name: str, files: List[Path]):
        """Mover archivos a directorio de división específico."""
        
        split_img_dir = self.images_path / split_name
        split_label_dir = self.labels_path / split_name
        
        for img_file in files:
            try:
                # Mover imagen
                new_img_path = split_img_dir / img_file.name
                shutil.move(str(img_file), str(new_img_path))
                
                # Mover etiqueta correspondiente si existe
                label_file = self.labels_path / f"{img_file.stem}.txt"
                if label_file.exists():
                    new_label_path = split_label_dir / f"{img_file.stem}.txt"
                    shutil.move(str(label_file), str(new_label_path))
                    
            except Exception as e:
                logger.error(f"Error moviendo {img_file}: {e}")
    
    def validate_dataset(self) -> Dict[str, int]:
        """Validar integridad del dataset."""
        
        stats = {
            'train_images': 0,
            'train_labels': 0,
            'val_images': 0,
            'val_labels': 0,
            'test_images': 0,
            'test_labels': 0,
            'missing_labels': 0,
            'empty_labels': 0
        }
        
        for split in ['train', 'val', 'test']:
            img_dir = self.images_path / split
            label_dir = self.labels_path / split
            
            # Contar imágenes
            images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
            stats[f'{split}_images'] = len(images)
            
            # Contar y validar etiquetas
            labels = list(label_dir.glob("*.txt"))
            stats[f'{split}_labels'] = len(labels)
            
            # Verificar etiquetas faltantes o vacías
            for img in images:
                label_file = label_dir / f"{img.stem}.txt"
                if not label_file.exists():
                    stats['missing_labels'] += 1
                elif label_file.stat().st_size == 0:
                    stats['empty_labels'] += 1
        
        # Mostrar estadísticas
        logger.info("=== Validación del Dataset ===")
        for key, value in stats.items():
            logger.info(f"{key}: {value}")
            
        return stats

class YOLOv12Trainer:
    """Entrenador optimizado para modelos YOLOv12."""
    
    def __init__(self, dataset_yaml: str, model_name: str = "yolov8n.pt"):
        self.dataset_yaml = dataset_yaml
        self.model_name = model_name
        self.results_dir = Path("IA_Etiquetado/Training_Results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Configuración de entrenamiento
        self.training_config = {
            'epochs': 100,
            'batch_size': 16,
            'image_size': 640,
            'learning_rate': 0.01,
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3,
            'patience': 10,  # early stopping
            'save_period': 10,  # guardar cada N epochs
            'workers': 4,
            'device': 'auto',  # auto, cpu, 0, 1, etc.
        }
        
    def setup_training_environment(self):
        """Configurar ambiente de entrenamiento."""
        
        # Verificar disponibilidad de CUDA
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"✓ CUDA disponible - GPUs: {gpu_count} ({gpu_name})")
            self.training_config['device'] = 0
        else:
            logger.warning("⚠️  CUDA no disponible - usando CPU")
            self.training_config['device'] = 'cpu'
            # Reducir batch size para CPU
            self.training_config['batch_size'] = 8
            
        # Configurar semillas para reproducibilidad
        torch.manual_seed(42)
        np.random.seed(42)
        random.seed(42)
        
        logger.info("✓ Ambiente de entrenamiento configurado")
    
    def train_model(self, custom_config: Optional[Dict] = None) -> str:
        """Entrenar modelo YOLOv12."""
        
        if not YOLO_AVAILABLE:
            raise ImportError("Ultralytics YOLO no está disponible")
        
        # Actualizar configuración si se proporciona
        if custom_config:
            self.training_config.update(custom_config)
            
        logger.info("=== Iniciando Entrenamiento YOLOv12 ===")
        logger.info(f"Configuración: {self.training_config}")
        
        try:
            # Cargar modelo base
            model = YOLO(self.model_name)
            logger.info(f"✓ Modelo base cargado: {self.model_name}")
            
            # Configurar directorio de resultados con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = self.results_dir / f"train_{timestamp}"
            
            # Iniciar entrenamiento
            results = model.train(
                data=self.dataset_yaml,
                epochs=self.training_config['epochs'],
                batch=self.training_config['batch_size'],
                imgsz=self.training_config['image_size'],
                lr0=self.training_config['learning_rate'],
                momentum=self.training_config['momentum'],
                weight_decay=self.training_config['weight_decay'],
                warmup_epochs=self.training_config['warmup_epochs'],
                patience=self.training_config['patience'],
                save_period=self.training_config['save_period'],
                workers=self.training_config['workers'],
                device=self.training_config['device'],
                project=str(self.results_dir),
                name=f"train_{timestamp}",
                exist_ok=True,
                pretrained=True,
                optimizer='AdamW',
                verbose=True,
                seed=42,
                deterministic=True,
                single_cls=False,
                rect=False,  # rectangular training
                cos_lr=True,  # cosine learning rate scheduler
                close_mosaic=10,  # disable mosaic last N epochs
                resume=False,  # resume from last checkpoint
                amp=True,  # Automatic Mixed Precision
                fraction=1.0,  # dataset fraction to train on
                profile=False,  # profile ONNX and TensorRT speeds
                freeze=None,  # freeze layers: backbone=10, first3=0:3, etc
                # Augmentations
                hsv_h=0.015,  # image HSV-Hue augmentation (fraction)
                hsv_s=0.7,    # image HSV-Saturation augmentation (fraction)  
                hsv_v=0.4,    # image HSV-Value augmentation (fraction)
                degrees=0.0,  # image rotation (+/- deg)
                translate=0.1, # image translation (+/- fraction)
                scale=0.5,    # image scale (+/- gain)
                shear=0.0,    # image shear (+/- deg)
                perspective=0.0, # image perspective (+/- fraction), range 0-0.001
                flipud=0.0,   # image flip up-down (probability)
                fliplr=0.5,   # image flip left-right (probability)
                mosaic=1.0,   # image mosaic (probability)
                mixup=0.0,    # image mixup (probability)
                copy_paste=0.0, # segment copy-paste (probability)
            )
            
            # Obtener ruta del mejor modelo
            best_model_path = run_dir / "weights" / "best.pt"
            
            logger.info("=== Entrenamiento Completado ===")
            logger.info(f"✓ Mejor modelo guardado en: {best_model_path}")
            
            # Guardar métricas de entrenamiento
            self._save_training_metrics(results, run_dir)
            
            return str(best_model_path)
            
        except Exception as e:
            logger.error(f"Error durante entrenamiento: {e}")
            raise
    
    def _save_training_metrics(self, results, run_dir: Path):
        """Guardar métricas de entrenamiento en JSON."""
        
        try:
            metrics = {
                'training_completed': datetime.now().isoformat(),
                'config': self.training_config,
                'dataset': self.dataset_yaml,
                'results_dir': str(run_dir),
                'best_model': str(run_dir / "weights" / "best.pt"),
                'last_model': str(run_dir / "weights" / "last.pt"),
            }
            
            # Agregar métricas de resultados si están disponibles
            if hasattr(results, 'results_dict'):
                metrics['final_metrics'] = results.results_dict
            
            metrics_file = run_dir / "training_metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=4, ensure_ascii=False)
                
            logger.info(f"✓ Métricas guardadas en: {metrics_file}")
            
        except Exception as e:
            logger.error(f"Error guardando métricas: {e}")
    
    def validate_model(self, model_path: str) -> Dict:
        """Validar modelo entrenado."""
        
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        try:
            # Cargar modelo
            model = YOLO(model_path)
            logger.info(f"✓ Modelo cargado para validación: {model_path}")
            
            # Ejecutar validación
            results = model.val(
                data=self.dataset_yaml,
                imgsz=self.training_config['image_size'],
                batch=self.training_config['batch_size'],
                device=self.training_config['device'],
                workers=self.training_config['workers'],
                verbose=True,
                save_json=True,
                save_hybrid=False,
                conf=0.001,  # confidence threshold
                iou=0.6,     # IoU threshold for NMS
                max_det=300, # maximum detections per image
                half=True,   # use FP16 half-precision inference
                dnn=False,   # use OpenCV DNN for ONNX inference
                plots=True,  # save plots and images during validation
            )
            
            # Extraer métricas principales
            metrics = {
                'mAP50': float(results.box.map50) if hasattr(results.box, 'map50') else 0.0,
                'mAP50-95': float(results.box.map) if hasattr(results.box, 'map') else 0.0,
                'precision': float(results.box.mp) if hasattr(results.box, 'mp') else 0.0,
                'recall': float(results.box.mr) if hasattr(results.box, 'mr') else 0.0,
                'validation_completed': datetime.now().isoformat()
            }
            
            logger.info("=== Resultados de Validación ===")
            for key, value in metrics.items():
                if isinstance(value, float):
                    logger.info(f"{key}: {value:.4f}")
                else:
                    logger.info(f"{key}: {value}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error durante validación: {e}")
            raise
    
    def export_model(self, model_path: str, formats: List[str] = ['onnx']) -> Dict[str, str]:
        """Exportar modelo a diferentes formatos."""
        
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        exported_models = {}
        
        try:
            model = YOLO(model_path)
            logger.info(f"Exportando modelo: {model_path}")
            
            for format_name in formats:
                try:
                    logger.info(f"Exportando a formato: {format_name}")
                    
                    export_path = model.export(
                        format=format_name,
                        imgsz=self.training_config['image_size'],
                        half=True,  # FP16 quantization
                        int8=False, # INT8 quantization
                        dynamic=False, # dynamic axes
                        simplify=True, # simplify ONNX model
                        opset=17,   # ONNX opset version
                        workspace=4, # TensorRT workspace size (GB)
                        nms=True,   # add NMS to model
                        lr=0.01,    # learning rate for QAT
                        decay=0.0005, # weight decay for QAT
                    )
                    
                    exported_models[format_name] = str(export_path)
                    logger.info(f"✓ Exportado {format_name}: {export_path}")
                    
                except Exception as e:
                    logger.error(f"Error exportando {format_name}: {e}")
                    
            return exported_models
            
        except Exception as e:
            logger.error(f"Error durante exportación: {e}")
            raise

def create_sample_dataset():
    """Crear dataset de ejemplo con imágenes sintéticas."""
    
    logger.info("Creando dataset de ejemplo...")
    
    dataset_manager = FruitDatasetManager()
    
    # Crear algunas imágenes de ejemplo (simuladas)
    sample_dir = dataset_manager.images_path / "samples"
    sample_dir.mkdir(exist_ok=True)
    
    # Generar imágenes sintéticas simples para prueba
    colors = {
        'apple': (255, 0, 0),      # Rojo
        'orange': (255, 165, 0),   # Naranja
        'banana': (255, 255, 0),   # Amarillo
        'grape': (128, 0, 128),    # Morado
        'lemon': (255, 255, 100),  # Amarillo limón
    }
    
    for fruit_name, color in colors.items():
        for i in range(10):  # 10 imágenes por fruta
            # Crear imagen simple
            img = Image.new('RGB', (640, 640), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # Dibujar círculo de fruta
            center_x = random.randint(100, 540)
            center_y = random.randint(100, 540)
            radius = random.randint(30, 80)
            
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], fill=color, outline=(0, 0, 0), width=2)
            
            # Guardar imagen
            img_path = sample_dir / f"{fruit_name}_{i:03d}.jpg"
            img.save(img_path, quality=95)
            
            # Crear etiqueta YOLO
            label_dir = dataset_manager.labels_path / "samples"
            label_dir.mkdir(exist_ok=True)
            
            # Formato YOLO: class_id center_x center_y width height (normalized)
            class_id = dataset_manager.fruit_classes[fruit_name]
            norm_x = center_x / 640
            norm_y = center_y / 640
            norm_w = (radius * 2) / 640
            norm_h = (radius * 2) / 640
            
            label_path = label_dir / f"{fruit_name}_{i:03d}.txt"
            with open(label_path, 'w') as f:
                f.write(f"{class_id} {norm_x:.6f} {norm_y:.6f} {norm_w:.6f} {norm_h:.6f}\n")
    
    logger.info(f"✓ Dataset de ejemplo creado con {len(colors) * 10} imágenes")
    return dataset_manager

def main():
    """Función principal de entrenamiento."""
    
    parser = argparse.ArgumentParser(description='Entrenamiento YOLOv12 para VisiFruit')
    parser.add_argument('--dataset', type=str, default='IA_Etiquetado/Dataset_Frutas', 
                       help='Ruta del dataset')
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                       help='Modelo base a usar')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Número de epochs')
    parser.add_argument('--batch-size', type=int, default=16,
                       help='Batch size')
    parser.add_argument('--img-size', type=int, default=640,
                       help='Tamaño de imagen')
    parser.add_argument('--create-sample', action='store_true',
                       help='Crear dataset de ejemplo')
    parser.add_argument('--augment', action='store_true',
                       help='Aplicar data augmentation')
    parser.add_argument('--validate-only', type=str,
                       help='Solo validar modelo existente')
    
    args = parser.parse_args()
    
    try:
        if not YOLO_AVAILABLE:
            logger.error("YOLO no está disponible. Instalar dependencias:")
            logger.error("pip install ultralytics torch torchvision pillow opencv-python")
            return
        
        # Crear dataset de ejemplo si se solicita
        if args.create_sample:
            dataset_manager = create_sample_dataset()
        else:
            dataset_manager = FruitDatasetManager(args.dataset)
        
        # Aplicar data augmentation si se solicita
        if args.augment:
            logger.info("Aplicando data augmentation...")
            for split in ['train']:  # Solo en train
                input_dir = dataset_manager.images_path / split
                dataset_manager.augment_images(input_dir, input_dir, augmentations_per_image=3)
        
        # Crear configuración YAML
        yaml_path = dataset_manager.create_dataset_yaml()
        if not yaml_path:
            logger.error("Error creando archivo YAML")
            return
        
        # Dividir dataset
        dataset_manager.split_dataset()
        
        # Validar dataset
        stats = dataset_manager.validate_dataset()
        if stats['train_images'] == 0:
            logger.error("No hay imágenes de entrenamiento disponibles")
            return
        
        # Solo validación si se especifica
        if args.validate_only:
            trainer = YOLOv12Trainer(yaml_path, args.model)
            trainer.setup_training_environment()
            metrics = trainer.validate_model(args.validate_only)
            logger.info(f"Validación completada: {metrics}")
            return
        
        # Entrenar modelo
        trainer = YOLOv12Trainer(yaml_path, args.model)
        trainer.setup_training_environment()
        
        # Configuración personalizada
        custom_config = {
            'epochs': args.epochs,
            'batch_size': args.batch_size,
            'image_size': args.img_size,
        }
        
        # Iniciar entrenamiento
        best_model_path = trainer.train_model(custom_config)
        
        # Validar modelo entrenado
        logger.info("Validando modelo entrenado...")
        validation_metrics = trainer.validate_model(best_model_path)
        
        # Exportar modelo
        logger.info("Exportando modelo...")
        exported_models = trainer.export_model(best_model_path, ['onnx', 'torchscript'])
        
        logger.info("=== Entrenamiento Completado Exitosamente ===")
        logger.info(f"Mejor modelo: {best_model_path}")
        logger.info(f"Métricas finales: {validation_metrics}")
        logger.info(f"Modelos exportados: {exported_models}")
        
    except Exception as e:
        logger.error(f"Error durante entrenamiento: {e}")
        raise

if __name__ == "__main__":
    main()
