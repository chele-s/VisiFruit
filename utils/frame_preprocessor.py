# utils/frame_preprocessor.py
"""
Módulo de Pre-procesamiento de Frames para Detección IA
========================================================

Optimizaciones específicas para cámara OV5647 + YOLOv8 en Raspberry Pi 5:
- Corrección de distorsión de lente
- Ajuste automático de contraste y brillo
- Reducción de ruido inteligente
- Mejora de nitidez adaptativa
- Normalización de color para mejor detección

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Octubre 2025
Versión: 1.0 - OV5647 Edition
"""

import cv2
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PreprocessingMode(Enum):
    """Modos de pre-procesamiento."""
    NONE = "none"              # Sin procesamiento
    LIGHT = "light"            # Correcciones mínimas
    BALANCED = "balanced"      # Balance velocidad/calidad
    QUALITY = "quality"        # Máxima calidad (más lento)
    ADAPTIVE = "adaptive"      # Adaptativo según condiciones


@dataclass
class FrameMetrics:
    """Métricas de calidad del frame."""
    brightness: float = 0.0      # 0-255
    contrast: float = 0.0        # Desviación estándar
    sharpness: float = 0.0       # Varianza Laplaciano
    noise_level: float = 0.0     # Estimación de ruido
    color_balance: float = 0.0   # Balance de color


class FramePreprocessor:
    """
    Pre-procesador de frames optimizado para OV5647 + YOLOv8.
    
    Mejora la calidad de imagen específicamente para detección de objetos,
    corrigiendo problemas comunes de la cámara OV5647.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el pre-procesador.
        
        Args:
            config: Configuración de pre-procesamiento
        """
        self.config = config or {}
        
        # Modo de pre-procesamiento
        mode_str = self.config.get("preprocessing_mode", "balanced")
        self.mode = PreprocessingMode(mode_str)
        
        # Parámetros de corrección
        self.auto_brightness = self.config.get("auto_brightness", True)
        self.auto_contrast = self.config.get("auto_contrast", True)
        self.denoise_enabled = self.config.get("denoise", False)
        self.sharpen_enabled = self.config.get("sharpen", True)
        self.color_correction = self.config.get("color_correction", True)
        
        # Parámetros de corrección de distorsión (OV5647)
        self.lens_correction = self.config.get("lens_correction", False)
        self.camera_matrix = None
        self.dist_coeffs = None
        
        # Rangos objetivo para normalización
        self.target_brightness = 128  # Brillo objetivo
        self.brightness_tolerance = 30
        self.min_contrast = 40
        
        # Estadísticas adaptativas
        self.frame_history = []
        self.max_history = 30
        
        logger.info(f"FramePreprocessor inicializado - Modo: {self.mode.value}")
    
    def load_camera_calibration(self, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        """Carga datos de calibración de cámara para corrección de distorsión."""
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.lens_correction = True
        logger.info("Calibración de cámara cargada para corrección de distorsión")
    
    def analyze_frame(self, frame: np.ndarray) -> FrameMetrics:
        """
        Analiza métricas de calidad del frame.
        
        Args:
            frame: Frame BGR de OpenCV
            
        Returns:
            FrameMetrics con métricas del frame
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Brillo (luminosidad promedio)
        brightness = float(np.mean(gray))
        
        # Contraste (desviación estándar)
        contrast = float(np.std(gray))
        
        # Nitidez (varianza del Laplaciano)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(np.var(laplacian))
        
        # Estimación de ruido
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = gray.astype(float) - blur.astype(float)
        noise_level = float(np.std(noise))
        
        # Balance de color (diferencia entre canales)
        b, g, r = cv2.split(frame)
        color_balance = float(np.std([np.mean(b), np.mean(g), np.mean(r)]))
        
        return FrameMetrics(
            brightness=brightness,
            contrast=contrast,
            sharpness=sharpness,
            noise_level=noise_level,
            color_balance=color_balance
        )
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Pre-procesa un frame para optimizar detección de IA.
        
        Args:
            frame: Frame BGR de OpenCV
            
        Returns:
            Frame procesado
        """
        if self.mode == PreprocessingMode.NONE:
            return frame
        
        processed = frame.copy()
        
        # 1. Corrección de distorsión de lente (si está calibrado)
        if self.lens_correction and self.camera_matrix is not None:
            processed = self._correct_lens_distortion(processed)
        
        # 2. Analizar frame
        metrics = self.analyze_frame(processed)
        
        # 3. Corrección de brillo automática
        if self.auto_brightness:
            processed = self._adjust_brightness(processed, metrics.brightness)
        
        # 4. Mejora de contraste
        if self.auto_contrast:
            processed = self._enhance_contrast(processed, metrics.contrast)
        
        # 5. Reducción de ruido (solo si es necesario)
        if self.denoise_enabled and metrics.noise_level > 10:
            processed = self._reduce_noise(processed, metrics.noise_level)
        
        # 6. Mejora de nitidez
        if self.sharpen_enabled and metrics.sharpness < 500:
            processed = self._enhance_sharpness(processed)
        
        # 7. Corrección de color
        if self.color_correction:
            processed = self._correct_color_balance(processed)
        
        # Actualizar historial
        self._update_history(metrics)
        
        return processed
    
    def _correct_lens_distortion(self, frame: np.ndarray) -> np.ndarray:
        """Corrige distorsión de lente usando calibración."""
        h, w = frame.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
        )
        
        undistorted = cv2.undistort(
            frame, self.camera_matrix, self.dist_coeffs, None, new_camera_matrix
        )
        
        # Recortar área válida
        x, y, w, h = roi
        if w > 0 and h > 0:
            undistorted = undistorted[y:y+h, x:x+w]
        
        return undistorted
    
    def _adjust_brightness(self, frame: np.ndarray, current_brightness: float) -> np.ndarray:
        """Ajusta brillo del frame."""
        # Calcular ajuste necesario
        delta = self.target_brightness - current_brightness
        
        # Aplicar solo si está fuera de tolerancia
        if abs(delta) > self.brightness_tolerance:
            # Limitar ajuste para evitar cambios bruscos
            delta = np.clip(delta, -50, 50)
            
            # Convertir a espacio de color más apropiado (LAB)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Ajustar canal L (luminosidad)
            l = cv2.add(l, int(delta))
            
            # Recombinar y convertir de vuelta
            lab = cv2.merge([l, a, b])
            adjusted = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return adjusted
        
        return frame
    
    def _enhance_contrast(self, frame: np.ndarray, current_contrast: float) -> np.ndarray:
        """Mejora el contraste del frame."""
        if current_contrast < self.min_contrast:
            # Usar CLAHE (Contrast Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return enhanced
        
        return frame
    
    def _reduce_noise(self, frame: np.ndarray, noise_level: float) -> np.ndarray:
        """Reduce ruido del frame de forma inteligente."""
        # Usar filtro bilateral para preservar bordes
        # Parámetros basados en nivel de ruido
        d = 5 if noise_level < 15 else 7
        sigma_color = min(75, noise_level * 3)
        sigma_space = min(75, noise_level * 3)
        
        denoised = cv2.bilateralFilter(frame, d, sigma_color, sigma_space)
        return denoised
    
    def _enhance_sharpness(self, frame: np.ndarray) -> np.ndarray:
        """Mejora la nitidez del frame."""
        # Kernel de sharpening suave
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)
        
        sharpened = cv2.filter2D(frame, -1, kernel)
        
        # Mezclar con original para evitar sobre-procesamiento
        alpha = 0.6  # 60% sharpened, 40% original
        result = cv2.addWeighted(sharpened, alpha, frame, 1 - alpha, 0)
        
        return result
    
    def _correct_color_balance(self, frame: np.ndarray) -> np.ndarray:
        """Corrige el balance de color del frame."""
        # Algoritmo Simple White Balance
        result = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])
        
        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
        
        result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
        return result
    
    def _update_history(self, metrics: FrameMetrics):
        """Actualiza historial de métricas para análisis adaptativo."""
        self.frame_history.append(metrics)
        
        if len(self.frame_history) > self.max_history:
            self.frame_history.pop(0)
    
    def get_average_metrics(self) -> Optional[FrameMetrics]:
        """Obtiene métricas promedio del historial."""
        if not self.frame_history:
            return None
        
        return FrameMetrics(
            brightness=np.mean([m.brightness for m in self.frame_history]),
            contrast=np.mean([m.contrast for m in self.frame_history]),
            sharpness=np.mean([m.sharpness for m in self.frame_history]),
            noise_level=np.mean([m.noise_level for m in self.frame_history]),
            color_balance=np.mean([m.color_balance for m in self.frame_history])
        )


def create_ov5647_preprocessor(config: Optional[Dict[str, Any]] = None) -> FramePreprocessor:
    """
    Factory function para crear pre-procesador optimizado para OV5647.
    
    Args:
        config: Configuración opcional
        
    Returns:
        FramePreprocessor configurado para OV5647
    """
    default_config = {
        "preprocessing_mode": "balanced",
        "auto_brightness": True,
        "auto_contrast": True,
        "denoise": False,  # La OV5647 tiene buena calidad en buena luz
        "sharpen": True,
        "color_correction": True,
        "lens_correction": False  # Activar si tienes calibración
    }
    
    if config:
        default_config.update(config)
    
    preprocessor = FramePreprocessor(default_config)
    
    logger.info("Pre-procesador OV5647 creado con configuración optimizada")
    return preprocessor


# Ejemplo de uso
if __name__ == "__main__":
    import time
    
    print("=== Test del Pre-procesador de Frames ===")
    
    # Crear pre-procesador
    preprocessor = create_ov5647_preprocessor()
    
    # Crear frame de prueba
    test_frame = np.random.randint(0, 255, (972, 1296, 3), dtype=np.uint8)
    
    # Medir rendimiento
    start = time.time()
    processed = preprocessor.preprocess(test_frame)
    duration = (time.time() - start) * 1000
    
    print(f"✓ Frame procesado en {duration:.2f}ms")
    
    # Analizar métricas
    metrics = preprocessor.analyze_frame(processed)
    print(f"📊 Métricas:")
    print(f"   Brillo: {metrics.brightness:.1f}")
    print(f"   Contraste: {metrics.contrast:.1f}")
    print(f"   Nitidez: {metrics.sharpness:.1f}")
    print(f"   Ruido: {metrics.noise_level:.1f}")
