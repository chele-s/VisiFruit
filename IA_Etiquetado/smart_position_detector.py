#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Detección Posicional Inteligente - VisiFruit System
=============================================================

Sistema avanzado que no solo detecta frutas, sino que analiza su distribución espacial
para calcular dinámicamente los tiempos de activación del etiquetador basado en:
- Número de frutas en línea (profundidad/largo)
- Número de frutas en ancho (lateral)
- Densidad y agrupación de frutas
- Velocidad de banda y tamaño de frutas

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Detección Posicional Inteligente
"""

import numpy as np
import cv2
import logging
import time
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Any
from pathlib import Path
from sklearn.cluster import DBSCAN
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FruitPosition:
    """Posición detallada de una fruta con información espacial."""
    fruit_id: str
    fruit_type: str
    confidence: float
    center_x: float  # Posición X en píxeles
    center_y: float  # Posición Y en píxeles
    center_x_m: float  # Posición X en metros (mundo real)
    center_y_m: float  # Posición Y en metros (mundo real)
    width_px: float
    height_px: float
    width_m: float   # Ancho en metros
    height_m: float  # Alto en metros
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    
    # Información de agrupación
    cluster_id: int = -1
    row_position: int = -1  # Posición en la fila (0, 1, 2...)
    col_position: int = -1  # Posición en la columna (0, 1, 2...)
    
    @property 
    def area_m2(self) -> float:
        """Área de la fruta en metros cuadrados."""
        return self.width_m * self.height_m

@dataclass 
class FruitCluster:
    """Grupo/clúster de frutas con información espacial."""
    cluster_id: int
    fruits: List[FruitPosition] = field(default_factory=list)
    center_x_m: float = 0.0
    center_y_m: float = 0.0
    width_m: float = 0.0   # Ancho total del clúster
    length_m: float = 0.0  # Largo total del clúster
    
    # Organización espacial
    rows: int = 0      # Número de filas (en dirección del ancho de banda)
    cols: int = 0      # Número de columnas (en dirección de movimiento)
    density: float = 0.0  # Frutas por metro cuadrado
    
    # Información de timing
    estimated_duration_s: float = 0.0  # Tiempo estimado que tomará pasar
    activation_start_delay_s: float = 0.0  # Delay hasta activación
    activation_duration_s: float = 0.0     # Tiempo total de activación
    
    def calculate_dimensions(self):
        """Calcular dimensiones del clúster."""
        if not self.fruits:
            return
            
        # Encontrar límites
        x_positions = [f.center_x_m for f in self.fruits]
        y_positions = [f.center_y_m for f in self.fruits]
        
        self.center_x_m = sum(x_positions) / len(x_positions)
        self.center_y_m = sum(y_positions) / len(y_positions)
        
        if len(x_positions) > 1:
            self.width_m = max(x_positions) - min(x_positions) + 0.05  # + tamaño promedio fruta
            self.length_m = max(y_positions) - min(y_positions) + 0.05
        else:
            self.width_m = 0.05  # Tamaño promedio de una fruta
            self.length_m = 0.05
            
        # Calcular densidad
        cluster_area = max(self.width_m * self.length_m, 0.0025)  # Mínimo 5cm x 5cm
        self.density = len(self.fruits) / cluster_area
    
    def organize_spatial_grid(self):
        """Organizar frutas en una grilla espacial."""
        if not self.fruits:
            return
            
        # Agrupar por posiciones Y (filas - ancho de banda)
        y_positions = sorted(set(round(f.center_y_m, 2) for f in self.fruits))
        y_tolerance = 0.03  # 3cm de tolerancia
        
        rows = []
        for y_target in y_positions:
            row_fruits = [f for f in self.fruits if abs(f.center_y_m - y_target) <= y_tolerance]
            if row_fruits:
                rows.append(sorted(row_fruits, key=lambda x: x.center_x_m))
        
        # Agrupar por posiciones X (columnas - dirección de movimiento)
        x_positions = sorted(set(round(f.center_x_m, 2) for f in self.fruits))
        x_tolerance = 0.03
        
        cols = []
        for x_target in x_positions:
            col_fruits = [f for f in self.fruits if abs(f.center_x_m - x_target) <= x_tolerance]
            if col_fruits:
                cols.append(sorted(col_fruits, key=lambda x: x.center_y_m))
        
        self.rows = len(rows)
        self.cols = len(cols)
        
        # Asignar posiciones en grilla
        for row_idx, row in enumerate(rows):
            for col_idx, fruit in enumerate(row):
                fruit.row_position = row_idx
                fruit.col_position = col_idx

@dataclass
class SpatialCalibration:
    """Calibración espacial del sistema."""
    # Conversión píxeles a metros
    pixels_per_meter_x: float = 2560.0  # px/m en X
    pixels_per_meter_y: float = 2560.0  # px/m en Y
    
    # Dimensiones de la banda
    belt_width_m: float = 0.25
    belt_length_m: float = 1.0
    belt_speed_mps: float = 0.15
    
    # Posiciones de referencia
    camera_position_x_m: float = 0.125  # Centro del ancho
    camera_position_y_m: float = 0.2    # 20cm desde inicio
    etiquetador_position_y_m: float = 0.8  # 80cm desde inicio
    
    # ROI de detección
    roi_x_start: int = 200
    roi_y_start: int = 100  
    roi_width: int = 1520
    roi_height: int = 880
    
    # Parámetros de clustering
    cluster_eps_m: float = 0.08  # 8cm - distancia máxima para agrupar
    cluster_min_samples: int = 1
    
    # Tiempos base
    base_activation_time_ms: float = 200.0  # Tiempo base por fruta
    time_per_additional_fruit_ms: float = 150.0  # Tiempo adicional por fruta extra
    safety_margin_ms: float = 50.0
    
    def pixels_to_meters(self, x_px: float, y_px: float) -> Tuple[float, float]:
        """Convertir píxeles a metros en el mundo real."""
        # Ajustar por ROI
        x_relative = x_px - self.roi_x_start
        y_relative = y_px - self.roi_y_start
        
        # Convertir a metros
        x_m = x_relative / self.pixels_per_meter_x
        y_m = y_relative / self.pixels_per_meter_y
        
        # Ajustar por posición de cámara
        x_world = x_m + (self.camera_position_x_m - self.belt_width_m/2)
        y_world = y_m + self.camera_position_y_m
        
        return x_world, y_world
    
    def meters_to_pixels(self, x_m: float, y_m: float) -> Tuple[int, int]:
        """Convertir metros a píxeles."""
        # Ajustar por posición de cámara
        x_relative = x_m - (self.camera_position_x_m - self.belt_width_m/2)
        y_relative = y_m - self.camera_position_y_m
        
        # Convertir a píxeles
        x_px = int(x_relative * self.pixels_per_meter_x + self.roi_x_start)
        y_px = int(y_relative * self.pixels_per_meter_y + self.roi_y_start)
        
        return x_px, y_px

class SmartPositionDetector:
    """Detector de posición inteligente para frutas."""
    
    def __init__(self, calibration: Optional[SpatialCalibration] = None):
        self.calibration = calibration or SpatialCalibration()
        self.detection_history: List[List[FruitPosition]] = []
        self.cluster_history: List[List[FruitCluster]] = []
        
        # Estadísticas
        self.stats = {
            'total_detections': 0,
            'total_clusters': 0,
            'avg_fruits_per_cluster': 0.0,
            'max_cluster_size': 0,
            'processing_time_ms': 0.0
        }
    
    def process_detections(self, raw_detections: List[Dict]) -> List[FruitCluster]:
        """
        Procesar detecciones brutas y convertirlas en clústeres inteligentes.
        
        Args:
            raw_detections: Lista de detecciones en formato:
                [{'class_name': 'apple', 'confidence': 0.85, 'bbox': (x1,y1,x2,y2)}, ...]
        
        Returns:
            Lista de clústeres de frutas con información espacial
        """
        start_time = time.time()
        
        try:
            # 1. Convertir detecciones a posiciones espaciales
            fruit_positions = self._convert_to_positions(raw_detections)
            
            # 2. Agrupar frutas en clústeres espaciales
            clusters = self._cluster_fruits(fruit_positions)
            
            # 3. Analizar cada clúster
            for cluster in clusters:
                cluster.calculate_dimensions()
                cluster.organize_spatial_grid()
                self._calculate_timing(cluster)
            
            # 4. Actualizar estadísticas
            self._update_stats(fruit_positions, clusters)
            
            # 5. Guardar en historial
            self.detection_history.append(fruit_positions)
            self.cluster_history.append(clusters)
            
            # Limpiar historial antiguo
            if len(self.detection_history) > 100:
                self.detection_history.pop(0)
                self.cluster_history.pop(0)
            
            processing_time = (time.time() - start_time) * 1000
            self.stats['processing_time_ms'] = processing_time
            
            logger.info(f"Procesadas {len(fruit_positions)} frutas en {len(clusters)} clústeres "
                       f"({processing_time:.1f}ms)")
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error procesando detecciones: {e}")
            return []
    
    def _convert_to_positions(self, raw_detections: List[Dict]) -> List[FruitPosition]:
        """Convertir detecciones brutas a posiciones espaciales."""
        
        fruit_positions = []
        
        for i, detection in enumerate(raw_detections):
            try:
                # Extraer información básica
                x1, y1, x2, y2 = detection['bbox']
                center_x_px = (x1 + x2) / 2
                center_y_px = (y1 + y2) / 2
                width_px = x2 - x1
                height_px = y2 - y1
                
                # Convertir a coordenadas del mundo real
                center_x_m, center_y_m = self.calibration.pixels_to_meters(center_x_px, center_y_px)
                width_m = width_px / self.calibration.pixels_per_meter_x
                height_m = height_px / self.calibration.pixels_per_meter_y
                
                # Crear posición de fruta
                fruit_pos = FruitPosition(
                    fruit_id=f"fruit_{i}_{int(time.time()*1000)}",
                    fruit_type=detection.get('class_name', 'unknown'),
                    confidence=detection.get('confidence', 0.0),
                    center_x=center_x_px,
                    center_y=center_y_px,
                    center_x_m=center_x_m,
                    center_y_m=center_y_m,
                    width_px=width_px,
                    height_px=height_px,
                    width_m=width_m,
                    height_m=height_m,
                    bbox=(x1, y1, x2, y2)
                )
                
                fruit_positions.append(fruit_pos)
                
            except Exception as e:
                logger.error(f"Error procesando detección {i}: {e}")
                continue
        
        return fruit_positions
    
    def _cluster_fruits(self, fruit_positions: List[FruitPosition]) -> List[FruitCluster]:
        """Agrupar frutas en clústeres espaciales usando DBSCAN."""
        
        if not fruit_positions:
            return []
        
        # Preparar datos para clustering
        positions = np.array([[f.center_x_m, f.center_y_m] for f in fruit_positions])
        
        # Aplicar DBSCAN
        clustering = DBSCAN(
            eps=self.calibration.cluster_eps_m,
            min_samples=self.calibration.cluster_min_samples
        ).fit(positions)
        
        # Organizar en clústeres
        clusters_dict = defaultdict(list)
        
        for fruit, cluster_id in zip(fruit_positions, clustering.labels_):
            fruit.cluster_id = cluster_id
            clusters_dict[cluster_id].append(fruit)
        
        # Crear objetos FruitCluster
        clusters = []
        for cluster_id, fruits in clusters_dict.items():
            if cluster_id >= 0:  # Ignorar ruido (-1)
                cluster = FruitCluster(cluster_id=cluster_id, fruits=fruits)
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_timing(self, cluster: FruitCluster):
        """Calcular tiempos de activación para un clúster."""
        
        if not cluster.fruits:
            return
        
        # Tiempo base por número de frutas
        num_fruits = len(cluster.fruits)
        base_time = self.calibration.base_activation_time_ms
        additional_time = (num_fruits - 1) * self.calibration.time_per_additional_fruit_ms
        
        # Ajuste por distribución espacial
        spatial_factor = 1.0
        
        # Si hay múltiples filas, necesita más tiempo
        if cluster.rows > 1:
            spatial_factor += 0.3 * (cluster.rows - 1)
        
        # Si hay múltiples columnas, necesita más tiempo
        if cluster.cols > 1:
            spatial_factor += 0.2 * (cluster.cols - 1)
        
        # Ajuste por densidad (clústeres muy densos necesitan más tiempo)
        if cluster.density > 20:  # Más de 20 frutas/m²
            spatial_factor += 0.4
        
        # Calcular tiempo total de activación
        total_activation_time = (base_time + additional_time) * spatial_factor
        cluster.activation_duration_s = (total_activation_time + self.calibration.safety_margin_ms) / 1000.0
        
        # Calcular delay hasta activación (basado en posición del clúster)
        distance_to_etiquetador = self.calibration.etiquetador_position_y_m - cluster.center_y_m
        travel_time = distance_to_etiquetador / self.calibration.belt_speed_mps
        cluster.activation_start_delay_s = max(0, travel_time)
        
        # Tiempo estimado que tomará todo el clúster en pasar
        cluster.estimated_duration_s = cluster.length_m / self.calibration.belt_speed_mps
        
        logger.debug(f"Clúster {cluster.cluster_id}: {num_fruits} frutas, "
                    f"{cluster.rows}x{cluster.cols}, "
                    f"activación: {cluster.activation_duration_s:.2f}s, "
                    f"delay: {cluster.activation_start_delay_s:.2f}s")
    
    def _update_stats(self, fruit_positions: List[FruitPosition], clusters: List[FruitCluster]):
        """Actualizar estadísticas del sistema."""
        
        self.stats['total_detections'] += len(fruit_positions)
        self.stats['total_clusters'] += len(clusters)
        
        if clusters:
            cluster_sizes = [len(c.fruits) for c in clusters]
            self.stats['avg_fruits_per_cluster'] = sum(cluster_sizes) / len(cluster_sizes)
            self.stats['max_cluster_size'] = max(cluster_sizes)
    
    def visualize_detection(self, image: np.ndarray, clusters: List[FruitCluster], 
                           save_path: Optional[str] = None) -> np.ndarray:
        """
        Visualizar detecciones y clústeres en la imagen.
        
        Args:
            image: Imagen original
            clusters: Lista de clústeres detectados
            save_path: Ruta opcional para guardar imagen
            
        Returns:
            Imagen con visualizaciones
        """
        
        vis_image = image.copy()
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
                 (255, 0, 255), (0, 255, 255), (128, 128, 128)]
        
        for cluster in clusters:
            color = colors[cluster.cluster_id % len(colors)]
            
            # Dibujar frutas individuales
            for fruit in cluster.fruits:
                x1, y1, x2, y2 = fruit.bbox
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
                
                # Etiqueta con información
                label = f"{fruit.fruit_type} {fruit.confidence:.2f}"
                cv2.putText(vis_image, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # Posición en grilla
                if fruit.row_position >= 0 and fruit.col_position >= 0:
                    grid_label = f"R{fruit.row_position}C{fruit.col_position}"
                    cv2.putText(vis_image, grid_label, (x1, y2+15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Dibujar información del clúster
            if cluster.fruits:
                cluster_center_px = self.calibration.meters_to_pixels(
                    cluster.center_x_m, cluster.center_y_m)
                
                cluster_info = [
                    f"Cluster {cluster.cluster_id}",
                    f"{len(cluster.fruits)} frutas",
                    f"{cluster.rows}x{cluster.cols}",
                    f"Act: {cluster.activation_duration_s:.2f}s",
                    f"Delay: {cluster.activation_start_delay_s:.2f}s"
                ]
                
                for i, line in enumerate(cluster_info):
                    cv2.putText(vis_image, line, 
                               (cluster_center_px[0], cluster_center_px[1] + i*15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Dibujar ROI
        cv2.rectangle(vis_image, 
                     (self.calibration.roi_x_start, self.calibration.roi_y_start),
                     (self.calibration.roi_x_start + self.calibration.roi_width,
                      self.calibration.roi_y_start + self.calibration.roi_height),
                     (0, 255, 255), 2)
        
        # Información general
        info_text = [
            f"Total frutas: {sum(len(c.fruits) for c in clusters)}",
            f"Clusters: {len(clusters)}",
            f"Tiempo proc: {self.stats['processing_time_ms']:.1f}ms"
        ]
        
        for i, line in enumerate(info_text):
            cv2.putText(vis_image, line, (10, 30 + i*20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        if save_path:
            cv2.imwrite(save_path, vis_image)
        
        return vis_image
    
    def get_activation_commands(self, clusters: List[FruitCluster]) -> List[Dict]:
        """
        Generar comandos de activación para etiquetadores.
        
        Returns:
            Lista de comandos: [{'delay_s': float, 'duration_s': float, 'cluster_info': dict}]
        """
        
        commands = []
        
        for cluster in clusters:
            if cluster.fruits:  # Solo clústeres con frutas
                command = {
                    'delay_s': cluster.activation_start_delay_s,
                    'duration_s': cluster.activation_duration_s,
                    'cluster_info': {
                        'id': cluster.cluster_id,
                        'fruit_count': len(cluster.fruits),
                        'rows': cluster.rows,
                        'cols': cluster.cols,
                        'center_position_m': (cluster.center_x_m, cluster.center_y_m),
                        'dimensions_m': (cluster.width_m, cluster.length_m),
                        'density': cluster.density,
                        'fruit_types': [f.fruit_type for f in cluster.fruits]
                    }
                }
                commands.append(command)
        
        # Ordenar por delay (primero los que se activan antes)
        commands.sort(key=lambda x: x['delay_s'])
        
        return commands
    
    def save_calibration(self, filepath: str):
        """Guardar calibración actual."""
        calib_data = {
            'pixels_per_meter_x': self.calibration.pixels_per_meter_x,
            'pixels_per_meter_y': self.calibration.pixels_per_meter_y,
            'belt_width_m': self.calibration.belt_width_m,
            'belt_length_m': self.calibration.belt_length_m,
            'belt_speed_mps': self.calibration.belt_speed_mps,
            'camera_position_x_m': self.calibration.camera_position_x_m,
            'camera_position_y_m': self.calibration.camera_position_y_m,
            'etiquetador_position_y_m': self.calibration.etiquetador_position_y_m,
            'roi_x_start': self.calibration.roi_x_start,
            'roi_y_start': self.calibration.roi_y_start,
            'roi_width': self.calibration.roi_width,
            'roi_height': self.calibration.roi_height,
            'cluster_eps_m': self.calibration.cluster_eps_m,
            'cluster_min_samples': self.calibration.cluster_min_samples,
            'base_activation_time_ms': self.calibration.base_activation_time_ms,
            'time_per_additional_fruit_ms': self.calibration.time_per_additional_fruit_ms,
            'safety_margin_ms': self.calibration.safety_margin_ms,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(calib_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Calibración guardada en: {filepath}")
    
    def load_calibration(self, filepath: str) -> bool:
        """Cargar calibración desde archivo."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                calib_data = json.load(f)
            
            # Actualizar calibración
            for key, value in calib_data.items():
                if hasattr(self.calibration, key):
                    setattr(self.calibration, key, value)
            
            logger.info(f"Calibración cargada desde: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando calibración: {e}")
            return False

# Funciones de utilidad

def create_sample_detections() -> List[Dict]:
    """Crear detecciones de ejemplo para pruebas."""
    
    # Simular 3 manzanas en línea y 2 naranjas al lado
    detections = [
        # Línea de manzanas (en dirección de movimiento)
        {'class_name': 'apple', 'confidence': 0.85, 'bbox': (300, 200, 380, 280)},
        {'class_name': 'apple', 'confidence': 0.82, 'bbox': (300, 320, 380, 400)},
        {'class_name': 'apple', 'confidence': 0.88, 'bbox': (300, 440, 380, 520)},
        
        # Naranjas al lado (ancho)
        {'class_name': 'orange', 'confidence': 0.79, 'bbox': (450, 250, 530, 330)},
        {'class_name': 'orange', 'confidence': 0.83, 'bbox': (600, 250, 680, 330)},
        
        # Uvas solitarias
        {'class_name': 'grape', 'confidence': 0.91, 'bbox': (500, 450, 560, 510)},
    ]
    
    return detections

def test_smart_detection():
    """Función de prueba del detector inteligente."""
    
    logger.info("=== Prueba del Detector de Posición Inteligente ===")
    
    # Crear detector
    detector = SmartPositionDetector()
    
    # Crear detecciones de ejemplo
    sample_detections = create_sample_detections()
    
    logger.info(f"Procesando {len(sample_detections)} detecciones de ejemplo...")
    
    # Procesar detecciones
    clusters = detector.process_detections(sample_detections)
    
    # Mostrar resultados
    logger.info(f"\n=== RESULTADOS ===")
    logger.info(f"Clusters detectados: {len(clusters)}")
    
    for cluster in clusters:
        logger.info(f"\nCluster {cluster.cluster_id}:")
        logger.info(f"  - Frutas: {len(cluster.fruits)}")
        logger.info(f"  - Organización: {cluster.rows} filas x {cluster.cols} columnas")
        logger.info(f"  - Dimensiones: {cluster.width_m:.3f}m x {cluster.length_m:.3f}m")
        logger.info(f"  - Centro: ({cluster.center_x_m:.3f}, {cluster.center_y_m:.3f})m")
        logger.info(f"  - Densidad: {cluster.density:.1f} frutas/m²")
        logger.info(f"  - Tiempo activación: {cluster.activation_duration_s:.3f}s")
        logger.info(f"  - Delay activación: {cluster.activation_start_delay_s:.3f}s")
        
        for fruit in cluster.fruits:
            logger.info(f"    * {fruit.fruit_type} en R{fruit.row_position}C{fruit.col_position}")
    
    # Generar comandos de activación
    commands = detector.get_activation_commands(clusters)
    
    logger.info(f"\n=== COMANDOS DE ACTIVACIÓN ===")
    for i, cmd in enumerate(commands):
        logger.info(f"Comando {i+1}:")
        logger.info(f"  - Delay: {cmd['delay_s']:.3f}s")
        logger.info(f"  - Duración: {cmd['duration_s']:.3f}s")
        logger.info(f"  - Frutas: {cmd['cluster_info']['fruit_count']}")
        logger.info(f"  - Grilla: {cmd['cluster_info']['rows']}x{cmd['cluster_info']['cols']}")
    
    # Guardar calibración de ejemplo
    detector.save_calibration("smart_detection_calibration.json")
    
    logger.info(f"\n=== ESTADÍSTICAS ===")
    for key, value in detector.stats.items():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    test_smart_detection()