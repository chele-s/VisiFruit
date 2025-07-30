#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calibrador Visual para Sistema de Detección Posicional - VisiFruit System
========================================================================

Herramienta visual e interactiva para calibrar fácilmente el sistema de detección
posicional. Permite:
- Calibración visual de dimensiones
- Configuración de ROI con arrastrar y soltar
- Ajuste de parámetros en tiempo real
- Vista previa de detecciones
- Exportación de configuración

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Calibrador Visual Interactivo
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import threading
import time

from smart_position_detector import SmartPositionDetector, SpatialCalibration

logger = logging.getLogger(__name__)

class VisualCalibrator:
    """Calibrador visual interactivo."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VisiFruit - Calibrador Visual de Posición")
        self.root.geometry("1400x900")
        
        # Estado
        self.current_image = None
        self.tk_image = None
        self.detector = SmartPositionDetector()
        self.camera = None
        self.is_capturing = False
        
        # Variables de ROI
        self.roi_start_x = tk.IntVar(value=200)
        self.roi_start_y = tk.IntVar(value=100)
        self.roi_width = tk.IntVar(value=1520)
        self.roi_height = tk.IntVar(value=880)
        
        # Variables de calibración
        self.belt_width_m = tk.DoubleVar(value=0.25)
        self.belt_length_m = tk.DoubleVar(value=1.0)
        self.belt_speed_mps = tk.DoubleVar(value=0.15)
        self.camera_pos_x_m = tk.DoubleVar(value=0.125)
        self.camera_pos_y_m = tk.DoubleVar(value=0.2)
        self.etiquetador_pos_y_m = tk.DoubleVar(value=0.8)
        
        # Variables de clustering
        self.cluster_eps_m = tk.DoubleVar(value=0.08)
        self.cluster_min_samples = tk.IntVar(value=1)
        
        # Variables de timing
        self.base_activation_time_ms = tk.DoubleVar(value=200.0)
        self.time_per_fruit_ms = tk.DoubleVar(value=150.0)
        self.safety_margin_ms = tk.DoubleVar(value=50.0)
        
        self.setup_ui()
        self.update_calibration()
        
    def setup_ui(self):
        """Configurar interfaz de usuario."""
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Controles
        control_frame = ttk.Frame(main_frame, width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Panel derecho - Vista
        view_frame = ttk.Frame(main_frame)
        view_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_control_panel(control_frame)
        self.setup_view_panel(view_frame)
    
    def setup_control_panel(self, parent):
        """Configurar panel de controles."""
        
        # Título
        title_label = ttk.Label(parent, text="Calibrador Visual VisiFruit", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Notebook para pestañas
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña 1: Cámara y ROI
        camera_frame = ttk.Frame(notebook)
        notebook.add(camera_frame, text="Cámara y ROI")
        self.setup_camera_tab(camera_frame)
        
        # Pestaña 2: Dimensiones Físicas
        dimensions_frame = ttk.Frame(notebook)
        notebook.add(dimensions_frame, text="Dimensiones")
        self.setup_dimensions_tab(dimensions_frame)
        
        # Pestaña 3: Clustering
        clustering_frame = ttk.Frame(notebook)
        notebook.add(clustering_frame, text="Agrupación")
        self.setup_clustering_tab(clustering_frame)
        
        # Pestaña 4: Tiempos
        timing_frame = ttk.Frame(notebook)
        notebook.add(timing_frame, text="Tiempos")
        self.setup_timing_tab(timing_frame)
        
        # Botones principales
        button_frame = ttk.Frame(parent)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Cargar Imagen", 
                  command=self.load_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Iniciar Cámara", 
                  command=self.start_camera).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Guardar Config", 
                  command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cargar Config", 
                  command=self.load_config).pack(side=tk.LEFT, padx=(5, 0))
    
    def setup_camera_tab(self, parent):
        """Configurar pestaña de cámara y ROI."""
        
        # ROI Configuration
        roi_group = ttk.LabelFrame(parent, text="Región de Interés (ROI)")
        roi_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(roi_group, text="X inicio:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(roi_group, from_=0, to=1920, variable=self.roi_start_x, 
                 orient=tk.HORIZONTAL, command=self.update_roi).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(roi_group, textvariable=self.roi_start_x).grid(row=0, column=2, padx=5)
        
        ttk.Label(roi_group, text="Y inicio:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(roi_group, from_=0, to=1080, variable=self.roi_start_y, 
                 orient=tk.HORIZONTAL, command=self.update_roi).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(roi_group, textvariable=self.roi_start_y).grid(row=1, column=2, padx=5)
        
        ttk.Label(roi_group, text="Ancho:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(roi_group, from_=100, to=1920, variable=self.roi_width, 
                 orient=tk.HORIZONTAL, command=self.update_roi).grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(roi_group, textvariable=self.roi_width).grid(row=2, column=2, padx=5)
        
        ttk.Label(roi_group, text="Alto:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(roi_group, from_=100, to=1080, variable=self.roi_height, 
                 orient=tk.HORIZONTAL, command=self.update_roi).grid(row=3, column=1, sticky=tk.EW, padx=5)
        ttk.Label(roi_group, textvariable=self.roi_height).grid(row=3, column=2, padx=5)
        
        roi_group.columnconfigure(1, weight=1)
        
        # Botones de ROI preconfigurados
        preset_frame = ttk.Frame(parent)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(preset_frame, text="Presets ROI:").pack(anchor=tk.W)
        
        presets = [
            ("Completo", lambda: self.set_roi_preset(0, 0, 1920, 1080)),
            ("Centro", lambda: self.set_roi_preset(200, 100, 1520, 880)),
            ("Superior", lambda: self.set_roi_preset(100, 50, 1720, 400)),
            ("Inferior", lambda: self.set_roi_preset(100, 600, 1720, 400))
        ]
        
        for name, command in presets:
            ttk.Button(preset_frame, text=name, command=command, 
                      width=8).pack(side=tk.LEFT, padx=2)
    
    def setup_dimensions_tab(self, parent):
        """Configurar pestaña de dimensiones físicas."""
        
        # Dimensiones de banda
        belt_group = ttk.LabelFrame(parent, text="Dimensiones de Banda (metros)")
        belt_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(belt_group, text="Ancho:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(belt_group, from_=0.1, to=1.0, variable=self.belt_width_m, 
                 orient=tk.HORIZONTAL, command=self.update_calibration, 
                 resolution=0.01).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(belt_group, textvariable=self.belt_width_m).grid(row=0, column=2, padx=5)
        
        ttk.Label(belt_group, text="Largo:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(belt_group, from_=0.5, to=3.0, variable=self.belt_length_m, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=0.1).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(belt_group, textvariable=self.belt_length_m).grid(row=1, column=2, padx=5)
        
        ttk.Label(belt_group, text="Velocidad (m/s):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(belt_group, from_=0.05, to=0.5, variable=self.belt_speed_mps, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=0.01).grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(belt_group, textvariable=self.belt_speed_mps).grid(row=2, column=2, padx=5)
        
        belt_group.columnconfigure(1, weight=1)
        
        # Posiciones
        pos_group = ttk.LabelFrame(parent, text="Posiciones (metros)")
        pos_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pos_group, text="Cámara X:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(pos_group, from_=0.0, to=0.5, variable=self.camera_pos_x_m, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=0.01).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(pos_group, textvariable=self.camera_pos_x_m).grid(row=0, column=2, padx=5)
        
        ttk.Label(pos_group, text="Cámara Y:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(pos_group, from_=0.0, to=1.0, variable=self.camera_pos_y_m, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=0.01).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(pos_group, textvariable=self.camera_pos_y_m).grid(row=1, column=2, padx=5)
        
        ttk.Label(pos_group, text="Etiquetador Y:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(pos_group, from_=0.2, to=2.0, variable=self.etiquetador_pos_y_m, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=0.01).grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(pos_group, textvariable=self.etiquetador_pos_y_m).grid(row=2, column=2, padx=5)
        
        pos_group.columnconfigure(1, weight=1)
        
        # Presets comunes
        preset_frame = ttk.Frame(parent)
        preset_frame.pack(fill=tk.X)
        
        ttk.Label(preset_frame, text="Presets Comunes:").pack(anchor=tk.W)
        
        ttk.Button(preset_frame, text="Maqueta 1m", 
                  command=lambda: self.set_dimensions_preset(0.25, 1.0, 0.15, 0.125, 0.2, 0.8),
                  width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Industrial 2m", 
                  command=lambda: self.set_dimensions_preset(0.5, 2.0, 0.3, 0.25, 0.3, 1.5),
                  width=12).pack(side=tk.LEFT, padx=2)
    
    def setup_clustering_tab(self, parent):
        """Configurar pestaña de clustering."""
        
        cluster_group = ttk.LabelFrame(parent, text="Parámetros de Agrupación")
        cluster_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(cluster_group, text="Distancia máxima (m):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(cluster_group, from_=0.02, to=0.2, variable=self.cluster_eps_m, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=0.01).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(cluster_group, textvariable=self.cluster_eps_m).grid(row=0, column=2, padx=5)
        
        ttk.Label(cluster_group, text="Mínimo frutas:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(cluster_group, from_=1, to=5, variable=self.cluster_min_samples, 
                 orient=tk.HORIZONTAL, command=self.update_calibration).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(cluster_group, textvariable=self.cluster_min_samples).grid(row=1, column=2, padx=5)
        
        cluster_group.columnconfigure(1, weight=1)
        
        # Información
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = """
        📍 Distancia máxima: Frutas más cercanas que esta distancia se agrupan juntas.
        
        👥 Mínimo frutas: Número mínimo de frutas para formar un grupo.
        
        💡 Sugerencias:
        • Para frutas pequeñas: 0.05-0.08m
        • Para frutas grandes: 0.08-0.12m
        • Mínimo 1 para detectar frutas solitarias
        """
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                 font=("Arial", 8)).pack(anchor=tk.W)
    
    def setup_timing_tab(self, parent):
        """Configurar pestaña de tiempos."""
        
        timing_group = ttk.LabelFrame(parent, text="Tiempos de Activación (ms)")
        timing_group.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(timing_group, text="Tiempo base:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(timing_group, from_=50, to=500, variable=self.base_activation_time_ms, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=10).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(timing_group, textvariable=self.base_activation_time_ms).grid(row=0, column=2, padx=5)
        
        ttk.Label(timing_group, text="Por fruta extra:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(timing_group, from_=50, to=300, variable=self.time_per_fruit_ms, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=10).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(timing_group, textvariable=self.time_per_fruit_ms).grid(row=1, column=2, padx=5)
        
        ttk.Label(timing_group, text="Margen seguridad:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Scale(timing_group, from_=0, to=200, variable=self.safety_margin_ms, 
                 orient=tk.HORIZONTAL, command=self.update_calibration,
                 resolution=10).grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(timing_group, textvariable=self.safety_margin_ms).grid(row=2, column=2, padx=5)
        
        timing_group.columnconfigure(1, weight=1)
        
        # Calculadora de ejemplo
        calc_frame = ttk.LabelFrame(parent, text="Calculadora de Ejemplo")
        calc_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.example_label = ttk.Label(calc_frame, text="", justify=tk.LEFT, font=("Arial", 8))
        self.example_label.pack(anchor=tk.W, padx=5, pady=5)
        
        self.update_timing_example()
    
    def setup_view_panel(self, parent):
        """Configurar panel de visualización."""
        
        # Canvas para imagen
        self.canvas = tk.Canvas(parent, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scroll = ttk.Scrollbar(parent, orient="horizontal", command=self.canvas.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=h_scroll.set)
        
        v_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=v_scroll.set)
        
        # Eventos del canvas
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        
        # Frame de información
        info_frame = ttk.Frame(parent)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        self.info_label = ttk.Label(info_frame, text="Carga una imagen o inicia la cámara para comenzar")
        self.info_label.pack(side=tk.LEFT)
        
        self.coords_label = ttk.Label(info_frame, text="")
        self.coords_label.pack(side=tk.RIGHT)
    
    def set_roi_preset(self, x, y, w, h):
        """Establecer preset de ROI."""
        self.roi_start_x.set(x)
        self.roi_start_y.set(y)
        self.roi_width.set(w)
        self.roi_height.set(h)
        self.update_roi()
    
    def set_dimensions_preset(self, width, length, speed, cam_x, cam_y, etiq_y):
        """Establecer preset de dimensiones."""
        self.belt_width_m.set(width)
        self.belt_length_m.set(length)
        self.belt_speed_mps.set(speed)
        self.camera_pos_x_m.set(cam_x)
        self.camera_pos_y_m.set(cam_y)
        self.etiquetador_pos_y_m.set(etiq_y)
        self.update_calibration()
    
    def update_roi(self, event=None):
        """Actualizar ROI y recalibrar."""
        self.update_calibration()
        self.update_display()
    
    def update_calibration(self, event=None):
        """Actualizar calibración del detector."""
        
        # Calcular píxeles por metro basado en ROI y dimensiones
        pixels_per_meter_x = self.roi_width.get() / self.belt_width_m.get()
        pixels_per_meter_y = self.roi_height.get() / self.belt_length_m.get()
        
        # Actualizar calibración
        calib = self.detector.calibration
        calib.pixels_per_meter_x = pixels_per_meter_x
        calib.pixels_per_meter_y = pixels_per_meter_y
        calib.belt_width_m = self.belt_width_m.get()
        calib.belt_length_m = self.belt_length_m.get()
        calib.belt_speed_mps = self.belt_speed_mps.get()
        calib.camera_position_x_m = self.camera_pos_x_m.get()
        calib.camera_position_y_m = self.camera_pos_y_m.get()
        calib.etiquetador_position_y_m = self.etiquetador_pos_y_m.get()
        calib.roi_x_start = self.roi_start_x.get()
        calib.roi_y_start = self.roi_start_y.get()
        calib.roi_width = self.roi_width.get()
        calib.roi_height = self.roi_height.get()
        calib.cluster_eps_m = self.cluster_eps_m.get()
        calib.cluster_min_samples = self.cluster_min_samples.get()
        calib.base_activation_time_ms = self.base_activation_time_ms.get()
        calib.time_per_additional_fruit_ms = self.time_per_fruit_ms.get()
        calib.safety_margin_ms = self.safety_margin_ms.get()
        
        self.update_timing_example()
    
    def update_timing_example(self):
        """Actualizar ejemplo de cálculo de timing."""
        if hasattr(self, 'example_label'):
            examples = [
                f"1 fruta: {self.base_activation_time_ms.get() + self.safety_margin_ms.get():.0f}ms",
                f"3 frutas: {self.base_activation_time_ms.get() + 2*self.time_per_fruit_ms.get() + self.safety_margin_ms.get():.0f}ms",
                f"5 frutas: {self.base_activation_time_ms.get() + 4*self.time_per_fruit_ms.get() + self.safety_margin_ms.get():.0f}ms"
            ]
            self.example_label.config(text="\n".join(examples))
    
    def load_image(self):
        """Cargar imagen desde archivo."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            try:
                self.current_image = cv2.imread(file_path)
                if self.current_image is not None:
                    self.update_display()
                    self.info_label.config(text=f"Imagen cargada: {Path(file_path).name}")
                else:
                    messagebox.showerror("Error", "No se pudo cargar la imagen")
            except Exception as e:
                messagebox.showerror("Error", f"Error cargando imagen: {e}")
    
    def start_camera(self):
        """Iniciar/detener captura de cámara."""
        if not self.is_capturing:
            try:
                self.camera = cv2.VideoCapture(0)
                if self.camera.isOpened():
                    self.is_capturing = True
                    self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
                    self.camera_thread.start()
                    self.info_label.config(text="Cámara iniciada")
                else:
                    messagebox.showerror("Error", "No se pudo iniciar la cámara")
            except Exception as e:
                messagebox.showerror("Error", f"Error iniciando cámara: {e}")
        else:
            self.is_capturing = False
            if self.camera:
                self.camera.release()
            self.info_label.config(text="Cámara detenida")
    
    def camera_loop(self):
        """Loop de captura de cámara."""
        while self.is_capturing:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    self.current_image = frame
                    self.root.after(0, self.update_display)
            time.sleep(0.1)  # ~10 FPS para no saturar la UI
    
    def update_display(self):
        """Actualizar visualización."""
        if self.current_image is None:
            return
        
        # Crear imagen con visualizaciones
        display_image = self.current_image.copy()
        
        # Dibujar ROI
        roi_x = self.roi_start_x.get()
        roi_y = self.roi_start_y.get()
        roi_w = self.roi_width.get()
        roi_h = self.roi_height.get()
        
        cv2.rectangle(display_image, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), 
                     (0, 255, 255), 2)
        
        # Dibujar grid de referencia en ROI
        grid_lines = 5
        for i in range(1, grid_lines):
            # Líneas verticales
            x = roi_x + (roi_w * i // grid_lines)
            cv2.line(display_image, (x, roi_y), (x, roi_y + roi_h), (0, 255, 255), 1)
            
            # Líneas horizontales
            y = roi_y + (roi_h * i // grid_lines)
            cv2.line(display_image, (roi_x, y), (roi_x + roi_w, y), (0, 255, 255), 1)
        
        # Dibujar posiciones importantes
        calib = self.detector.calibration
        
        # Posición de cámara
        cam_px = calib.meters_to_pixels(calib.camera_position_x_m, calib.camera_position_y_m)
        cv2.circle(display_image, cam_px, 10, (0, 255, 0), -1)
        cv2.putText(display_image, "CAMARA", (cam_px[0]-30, cam_px[1]-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Posición de etiquetador
        etiq_px = calib.meters_to_pixels(calib.camera_position_x_m, calib.etiquetador_position_y_m)
        cv2.circle(display_image, etiq_px, 10, (255, 0, 0), -1)
        cv2.putText(display_image, "ETIQUETADOR", (etiq_px[0]-50, etiq_px[1]-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Información de calibración
        info_text = [
            f"ROI: {roi_w}x{roi_h} px",
            f"Banda: {calib.belt_width_m:.2f}x{calib.belt_length_m:.2f}m",
            f"Resolucion: {calib.pixels_per_meter_x:.0f}px/m",
            f"Velocidad: {calib.belt_speed_mps:.2f}m/s"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(display_image, text, (10, 30 + i*20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Convertir a formato Tkinter
        height, width = display_image.shape[:2]
        
        # Escalar si es necesario
        max_width, max_height = 800, 600
        if width > max_width or height > max_height:
            scale = min(max_width/width, max_height/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            display_image = cv2.resize(display_image, (new_width, new_height))
        
        # Convertir BGR a RGB
        display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        
        # Crear imagen Tkinter
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(display_image))
        
        # Actualizar canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_click(self, event):
        """Manejar click en canvas."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convertir a coordenadas de imagen (considerando escalado)
        if self.current_image is not None:
            height, width = self.current_image.shape[:2]
            max_width, max_height = 800, 600
            
            if width > max_width or height > max_height:
                scale = min(max_width/width, max_height/height)
                img_x = int(canvas_x / scale)
                img_y = int(canvas_y / scale)
            else:
                img_x = int(canvas_x)
                img_y = int(canvas_y)
            
            # Convertir a coordenadas del mundo real
            world_x, world_y = self.detector.calibration.pixels_to_meters(img_x, img_y)
            
            # Actualizar etiqueta de coordenadas
            self.coords_label.config(text=f"Píxel: ({img_x}, {img_y}) | Mundo: ({world_x:.3f}, {world_y:.3f})m")
    
    def on_canvas_drag(self, event):
        """Manejar arrastre en canvas."""
        self.on_canvas_click(event)  # Actualizar coordenadas
    
    def save_config(self):
        """Guardar configuración actual."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar configuración",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        
        if file_path:
            try:
                self.detector.save_calibration(file_path)
                messagebox.showinfo("Éxito", f"Configuración guardada en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error guardando configuración: {e}")
    
    def load_config(self):
        """Cargar configuración desde archivo."""
        file_path = filedialog.askopenfilename(
            title="Cargar configuración",
            filetypes=[("JSON", "*.json")]
        )
        
        if file_path:
            try:
                if self.detector.load_calibration(file_path):
                    # Actualizar variables de UI
                    calib = self.detector.calibration
                    self.roi_start_x.set(calib.roi_x_start)
                    self.roi_start_y.set(calib.roi_y_start)
                    self.roi_width.set(calib.roi_width)
                    self.roi_height.set(calib.roi_height)
                    self.belt_width_m.set(calib.belt_width_m)
                    self.belt_length_m.set(calib.belt_length_m)
                    self.belt_speed_mps.set(calib.belt_speed_mps)
                    self.camera_pos_x_m.set(calib.camera_position_x_m)
                    self.camera_pos_y_m.set(calib.camera_position_y_m)
                    self.etiquetador_pos_y_m.set(calib.etiquetador_position_y_m)
                    self.cluster_eps_m.set(calib.cluster_eps_m)
                    self.cluster_min_samples.set(calib.cluster_min_samples)
                    self.base_activation_time_ms.set(calib.base_activation_time_ms)
                    self.time_per_fruit_ms.set(calib.time_per_additional_fruit_ms)
                    self.safety_margin_ms.set(calib.safety_margin_ms)
                    
                    self.update_display()
                    messagebox.showinfo("Éxito", f"Configuración cargada desde:\n{file_path}")
                else:
                    messagebox.showerror("Error", "No se pudo cargar la configuración")
            except Exception as e:
                messagebox.showerror("Error", f"Error cargando configuración: {e}")
    
    def run(self):
        """Ejecutar aplicación."""
        try:
            self.root.mainloop()
        finally:
            if self.is_capturing and self.camera:
                self.is_capturing = False
                self.camera.release()

def main():
    """Función principal."""
    app = VisualCalibrator()
    app.run()

if __name__ == "__main__":
    main()