#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Sincronización Posicional Cámara-Etiquetadores - VisiFruit System
============================================================================

Módulo especializado para sincronizar la detección de frutas por cámara
con la activación temporal precisa de etiquetadores, calculando automáticamente
los tiempos de delay basados en la velocidad de la banda y distancias físicas.

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Edición Industrial

PROBLEMA RESUELTO:
================
¿Cómo saber exactamente cuándo activar los etiquetadores después de que 
la cámara detecta una fruta, considerando que la fruta debe viajar una 
distancia específica en la banda transportadora?

SOLUCIÓN MATEMÁTICA:
==================
- Velocidad de banda: v (m/s)
- Distancia cámara-etiquetador: d (m)
- Tiempo de tránsito: t = d/v
- Delay de activación = t + tiempo_procesamiento + margen_seguridad
"""

import asyncio
import logging
import time
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum, auto
from pathlib import Path
import numpy as np
from collections import deque
import math

# Configuración de logging
logger = logging.getLogger(__name__)

class SyncState(Enum):
    """Estados del sistema de sincronización."""
    OFFLINE = auto()
    CALIBRATING = auto()
    READY = auto()
    TRACKING = auto()
    ERROR = auto()

@dataclass
class DetectionEvent:
    """Evento de detección de fruta por cámara."""
    timestamp: float = field(default_factory=time.time)
    fruit_type: str = ""
    confidence: float = 0.0
    position_x: float = 0.0  # Posición en píxeles
    position_y: float = 0.0
    bbox: Tuple[float, float, float, float] = (0, 0, 0, 0)  # x, y, w, h
    processed: bool = False
    activation_time: Optional[float] = None  # Tiempo calculado para activación

@dataclass
class EtiquetadorZone:
    """Zona de etiquetado con su configuración física."""
    etiquetador_id: int
    distance_from_camera_m: float  # Distancia desde cámara en metros
    width_coverage_m: float = 0.25  # Ancho que cubre (por defecto toda la banda)
    fruit_types: List[str] = field(default_factory=list)  # Tipos de fruta que maneja
    active: bool = True

@dataclass
class CalibrationData:
    """Datos de calibración del sistema."""
    belt_speed_mps: float = 0.15  # Velocidad de banda en m/s
    camera_position_m: float = 0.0  # Posición de cámara desde inicio de banda
    belt_length_m: float = 1.0  # Longitud total de banda
    belt_width_m: float = 0.25  # Ancho de banda
    pixels_per_meter: float = 640.0  # Resolución espacial (px/m)
    processing_delay_ms: float = 50.0  # Delay de procesamiento típico
    safety_margin_ms: float = 100.0  # Margen de seguridad
    last_calibration: Optional[datetime] = None

class PositionSynchronizer:
    """Sistema principal de sincronización posicional."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "Control_Etiquetado/sync_config.json"
        self.state = SyncState.OFFLINE
        
        # Datos de calibración
        self.calibration = CalibrationData()
        
        # Zonas de etiquetado
        self.etiquetador_zones: Dict[int, EtiquetadorZone] = {}
        
        # Cola de eventos de detección
        self.detection_queue = deque(maxlen=100)
        self.pending_activations: Dict[float, List[int]] = {}  # timestamp -> [etiquetador_ids]
        
        # Callbacks para activación de etiquetadores
        self.activation_callbacks: Dict[int, Callable] = {}
        
        # Monitoreo y estadísticas
        self.stats = {
            'detections_processed': 0,
            'activations_sent': 0,
            'missed_activations': 0,
            'average_delay_ms': 0.0,
            'last_detection_time': 0.0
        }
        
        # Control de threads
        self._running = False
        self._sync_thread = None
        self._lock = threading.Lock()
        
        # Cargar configuración
        self.load_configuration()
        
    def load_configuration(self):
        """Cargar configuración desde archivo."""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Cargar datos de calibración
                calib_data = config.get('calibration', {})
                self.calibration.belt_speed_mps = calib_data.get('belt_speed_mps', 0.15)
                self.calibration.camera_position_m = calib_data.get('camera_position_m', 0.0)
                self.calibration.belt_length_m = calib_data.get('belt_length_m', 1.0)
                self.calibration.belt_width_m = calib_data.get('belt_width_m', 0.25)
                self.calibration.pixels_per_meter = calib_data.get('pixels_per_meter', 640.0)
                self.calibration.processing_delay_ms = calib_data.get('processing_delay_ms', 50.0)
                self.calibration.safety_margin_ms = calib_data.get('safety_margin_ms', 100.0)
                
                # Cargar zonas de etiquetado
                zones_data = config.get('etiquetador_zones', {})
                for zone_id, zone_data in zones_data.items():
                    self.etiquetador_zones[int(zone_id)] = EtiquetadorZone(
                        etiquetador_id=int(zone_id),
                        distance_from_camera_m=zone_data.get('distance_from_camera_m', 0.5),
                        width_coverage_m=zone_data.get('width_coverage_m', 0.25),
                        fruit_types=zone_data.get('fruit_types', []),
                        active=zone_data.get('active', True)
                    )
                
                logger.info(f"✓ Configuración cargada desde: {self.config_file}")
                
            else:
                # Crear configuración por defecto
                self.create_default_configuration()
                
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Crear configuración por defecto para maqueta de 1m x 0.25m."""
        
        logger.info("Creando configuración por defecto para maqueta 1m x 0.25m")
        
        # Configuración para maqueta
        self.calibration = CalibrationData(
            belt_speed_mps=0.15,  # 15 cm/s - velocidad moderada
            camera_position_m=0.2,  # Cámara a 20cm del inicio
            belt_length_m=1.0,  # 1 metro total
            belt_width_m=0.25,  # 25 cm de ancho
            pixels_per_meter=2560.0,  # Asumiendo imagen 640px para 0.25m de ancho
            processing_delay_ms=50.0,
            safety_margin_ms=100.0
        )
        
        # Zona de etiquetado por defecto
        self.etiquetador_zones[1] = EtiquetadorZone(
            etiquetador_id=1,
            distance_from_camera_m=0.6,  # 60cm desde cámara (40cm desde posición cámara)
            width_coverage_m=0.25,
            fruit_types=['apple', 'orange', 'banana', 'grape', 'lemon'],
            active=True
        )
        
        # Guardar configuración
        self.save_configuration()
        
    def save_configuration(self):
        """Guardar configuración actual."""
        try:
            config = {
                'calibration': {
                    'belt_speed_mps': self.calibration.belt_speed_mps,
                    'camera_position_m': self.calibration.camera_position_m,
                    'belt_length_m': self.calibration.belt_length_m,
                    'belt_width_m': self.calibration.belt_width_m,
                    'pixels_per_meter': self.calibration.pixels_per_meter,
                    'processing_delay_ms': self.calibration.processing_delay_ms,
                    'safety_margin_ms': self.calibration.safety_margin_ms,
                    'last_calibration': datetime.now().isoformat()
                },
                'etiquetador_zones': {
                    zone.etiquetador_id: {
                        'distance_from_camera_m': zone.distance_from_camera_m,
                        'width_coverage_m': zone.width_coverage_m,
                        'fruit_types': zone.fruit_types,
                        'active': zone.active
                    }
                    for zone in self.etiquetador_zones.values()
                }
            }
            
            # Crear directorio si no existe
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            logger.info(f"✓ Configuración guardada en: {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def calculate_activation_delay(self, detection: DetectionEvent, etiquetador_id: int) -> float:
        """
        Calcular delay de activación para un etiquetador específico.
        
        FÓRMULA PRINCIPAL:
        delay = (distancia / velocidad) + delay_procesamiento + margen_seguridad
        
        Args:
            detection: Evento de detección
            etiquetador_id: ID del etiquetador
            
        Returns:
            Delay en segundos
        """
        
        if etiquetador_id not in self.etiquetador_zones:
            logger.error(f"Etiquetador {etiquetador_id} no encontrado")
            return 0.0
        
        zone = self.etiquetador_zones[etiquetador_id]
        
        # Distancia que debe recorrer la fruta
        travel_distance_m = zone.distance_from_camera_m
        
        # Tiempo de tránsito base
        travel_time_s = travel_distance_m / self.calibration.belt_speed_mps
        
        # Delays adicionales
        processing_delay_s = self.calibration.processing_delay_ms / 1000.0
        safety_margin_s = self.calibration.safety_margin_ms / 1000.0
        
        # Delay total
        total_delay_s = travel_time_s + processing_delay_s + safety_margin_s
        
        logger.debug(f"Cálculo delay para etiquetador {etiquetador_id}:")
        logger.debug(f"  - Distancia: {travel_distance_m:.3f}m")
        logger.debug(f"  - Velocidad banda: {self.calibration.belt_speed_mps:.3f}m/s")
        logger.debug(f"  - Tiempo tránsito: {travel_time_s:.3f}s")
        logger.debug(f"  - Delay procesamiento: {processing_delay_s:.3f}s")
        logger.debug(f"  - Margen seguridad: {safety_margin_s:.3f}s")
        logger.debug(f"  - DELAY TOTAL: {total_delay_s:.3f}s")
        
        return total_delay_s
    
    def process_detection(self, detection: DetectionEvent):
        """
        Procesar evento de detección y programar activaciones.
        
        Args:
            detection: Evento de detección de fruta
        """
        
        with self._lock:
            try:
                logger.info(f"Procesando detección: {detection.fruit_type} "
                           f"(confianza: {detection.confidence:.2f})")
                
                # Determinar qué etiquetadores deben activarse
                target_etiquetadores = self._get_target_etiquetadores(detection)
                
                if not target_etiquetadores:
                    logger.warning(f"No hay etiquetadores para {detection.fruit_type}")
                    return
                
                # Calcular delays y programar activaciones
                for etiquetador_id in target_etiquetadores:
                    delay_s = self.calculate_activation_delay(detection, etiquetador_id)
                    activation_time = time.time() + delay_s
                    
                    # Agregar a cola de activaciones pendientes
                    if activation_time not in self.pending_activations:
                        self.pending_activations[activation_time] = []
                    self.pending_activations[activation_time].append(etiquetador_id)
                    
                    logger.info(f"Etiquetador {etiquetador_id} programado para activar "
                               f"en {delay_s:.3f}s (a las {activation_time:.3f})")
                
                # Actualizar estadísticas
                self.stats['detections_processed'] += 1
                self.stats['last_detection_time'] = detection.timestamp
                
                # Marcar como procesado
                detection.processed = True
                
                # Agregar a cola histórica
                self.detection_queue.append(detection)
                
            except Exception as e:
                logger.error(f"Error procesando detección: {e}")
    
    def _get_target_etiquetadores(self, detection: DetectionEvent) -> List[int]:
        """Determinar qué etiquetadores deben activarse para una detección."""
        
        target_ids = []
        
        for zone_id, zone in self.etiquetador_zones.items():
            if not zone.active:
                continue
                
            # Verificar si el etiquetador maneja este tipo de fruta
            if zone.fruit_types and detection.fruit_type not in zone.fruit_types:
                continue
                
            # TODO: Verificar posición lateral (ancho de banda)
            # Por ahora asumimos que toda fruta está en el centro
            
            target_ids.append(zone_id)
        
        return target_ids
    
    def register_etiquetador_callback(self, etiquetador_id: int, callback: Callable):
        """
        Registrar callback para activación de etiquetador.
        
        Args:
            etiquetador_id: ID del etiquetador
            callback: Función a llamar para activar etiquetador
        """
        self.activation_callbacks[etiquetador_id] = callback
        logger.info(f"✓ Callback registrado para etiquetador {etiquetador_id}")
    
    def start_synchronization(self):
        """Iniciar sistema de sincronización."""
        
        if self._running:
            logger.warning("Sistema ya está ejecutándose")
            return
        
        self._running = True
        self.state = SyncState.READY
        self._sync_thread = threading.Thread(target=self._synchronization_loop, daemon=True)
        self._sync_thread.start()
        
        logger.info("✓ Sistema de sincronización iniciado")
    
    def stop_synchronization(self):
        """Detener sistema de sincronización."""
        
        self._running = False
        self.state = SyncState.OFFLINE
        
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=2.0)
        
        logger.info("✓ Sistema de sincronización detenido")
    
    def _synchronization_loop(self):
        """Loop principal de sincronización."""
        
        logger.info("Iniciando loop de sincronización...")
        
        while self._running:
            try:
                current_time = time.time()
                
                # Verificar activaciones pendientes
                activations_to_process = []
                
                with self._lock:
                    for activation_time in list(self.pending_activations.keys()):
                        if current_time >= activation_time:
                            activations_to_process.append((activation_time, self.pending_activations[activation_time]))
                            del self.pending_activations[activation_time]
                
                # Ejecutar activaciones
                for activation_time, etiquetador_ids in activations_to_process:
                    for etiquetador_id in etiquetador_ids:
                        self._activate_etiquetador(etiquetador_id, activation_time)
                
                # Dormir un poco para no saturar CPU
                time.sleep(0.010)  # 10ms
                
            except Exception as e:
                logger.error(f"Error en loop de sincronización: {e}")
                time.sleep(0.1)
        
        logger.info("Loop de sincronización finalizado")
    
    def _activate_etiquetador(self, etiquetador_id: int, scheduled_time: float):
        """
        Activar etiquetador específico.
        
        Args:
            etiquetador_id: ID del etiquetador
            scheduled_time: Tiempo programado para activación
        """
        
        try:
            current_time = time.time()
            actual_delay_ms = (current_time - scheduled_time) * 1000
            
            logger.info(f"🏷️  ACTIVANDO ETIQUETADOR {etiquetador_id} "
                       f"(delay real: {actual_delay_ms:.1f}ms)")
            
            # Llamar callback si existe
            if etiquetador_id in self.activation_callbacks:
                callback = self.activation_callbacks[etiquetador_id]
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error en callback etiquetador {etiquetador_id}: {e}")
            else:
                logger.warning(f"No hay callback para etiquetador {etiquetador_id}")
            
            # Actualizar estadísticas
            self.stats['activations_sent'] += 1
            
            # Actualizar delay promedio
            if self.stats['activations_sent'] > 0:
                current_avg = self.stats['average_delay_ms']
                new_avg = ((current_avg * (self.stats['activations_sent'] - 1)) + abs(actual_delay_ms)) / self.stats['activations_sent']
                self.stats['average_delay_ms'] = new_avg
                            
        except Exception as e:
            logger.error(f"Error activando etiquetador {etiquetador_id}: {e}")
            self.stats['missed_activations'] += 1
    
    def calibrate_belt_speed(self, manual_speed: Optional[float] = None) -> float:
        """
        Calibrar velocidad de banda transportadora.
        
        Args:
            manual_speed: Velocidad manual en m/s (si se conoce)
            
        Returns:
            Velocidad calibrada en m/s
        """
        
        if manual_speed is not None:
            self.calibration.belt_speed_mps = manual_speed
            logger.info(f"✓ Velocidad manual configurada: {manual_speed:.3f} m/s")
            
        else:
            # TODO: Implementar calibración automática con visión por computadora
            # Por ahora usar valor por defecto
            logger.warning("Calibración automática no implementada, usando valor por defecto")
        
        # Guardar calibración
        self.calibration.last_calibration = datetime.now()
        self.save_configuration()
        
        return self.calibration.belt_speed_mps
    
    def calibrate_distances(self, camera_to_etiquetador_distances: Dict[int, float]):
        """
        Calibrar distancias desde cámara a etiquetadores.
        
        Args:
            camera_to_etiquetador_distances: {etiquetador_id: distance_in_meters}
        """
        
        for etiquetador_id, distance_m in camera_to_etiquetador_distances.items():
            if etiquetador_id in self.etiquetador_zones:
                self.etiquetador_zones[etiquetador_id].distance_from_camera_m = distance_m
                logger.info(f"✓ Distancia etiquetador {etiquetador_id}: {distance_m:.3f}m")
            else:
                logger.warning(f"Etiquetador {etiquetador_id} no existe")
        
        # Guardar calibración
        self.calibration.last_calibration = datetime.now()
        self.save_configuration()
    
    def get_status(self) -> Dict:
        """Obtener estado actual del sistema."""
        
        return {
            'state': self.state.name,
            'running': self._running,
            'calibration': {
                'belt_speed_mps': self.calibration.belt_speed_mps,
                'belt_speed_cmps': self.calibration.belt_speed_mps * 100,  # Para mostrar en cm/s
                'camera_position_m': self.calibration.camera_position_m,
                'belt_dimensions': f"{self.calibration.belt_length_m}m x {self.calibration.belt_width_m}m",
                'last_calibration': self.calibration.last_calibration.isoformat() if self.calibration.last_calibration else None
            },
            'etiquetadores': {
                zone_id: {
                    'distance_from_camera_m': zone.distance_from_camera_m,
                    'estimated_delay_s': zone.distance_from_camera_m / self.calibration.belt_speed_mps,
                    'fruit_types': zone.fruit_types,
                    'active': zone.active,
                    'has_callback': zone_id in self.activation_callbacks
                }
                for zone_id, zone in self.etiquetador_zones.items()
            },
            'statistics': self.stats,
            'pending_activations': len(self.pending_activations),
            'recent_detections': len(self.detection_queue)
        }
    
    def get_timing_info_for_mockup(self) -> Dict:
        """Obtener información de tiempos específicamente para la maqueta de 1m."""
        
        info = {
            'belt_specs': {
                'length': f"{self.calibration.belt_length_m}m",
                'width': f"{self.calibration.belt_width_m}m", 
                'speed_mps': f"{self.calibration.belt_speed_mps:.3f} m/s",
                'speed_cmps': f"{self.calibration.belt_speed_mps * 100:.1f} cm/s"
            },
            'camera_position': f"{self.calibration.camera_position_m}m from start",
            'etiquetador_timing': {}
        }
        
        for zone_id, zone in self.etiquetador_zones.items():
            travel_time = zone.distance_from_camera_m / self.calibration.belt_speed_mps
            total_delay = travel_time + (self.calibration.processing_delay_ms + self.calibration.safety_margin_ms) / 1000.0
            
            info['etiquetador_timing'][f'etiquetador_{zone_id}'] = {
                'distance_from_camera': f"{zone.distance_from_camera_m:.3f}m",
                'travel_time': f"{travel_time:.3f}s",
                'processing_delay': f"{self.calibration.processing_delay_ms:.0f}ms",
                'safety_margin': f"{self.calibration.safety_margin_ms:.0f}ms", 
                'total_delay': f"{total_delay:.3f}s",
                'activation_delay_ms': f"{total_delay * 1000:.0f}ms"
            }
        
        return info


# Funciones de utilidad para integración fácil

def create_mockup_synchronizer() -> PositionSynchronizer:
    """Crear sincronizador configurado para maqueta de 1m x 0.25m."""
    
    sync = PositionSynchronizer()
    
    # Configuración específica para maqueta
    sync.calibration.belt_length_m = 1.0
    sync.calibration.belt_width_m = 0.25
    sync.calibration.belt_speed_mps = 0.15  # 15 cm/s
    sync.calibration.camera_position_m = 0.2  # Cámara a 20cm del inicio
    
    # Etiquetador al final de la banda
    sync.etiquetador_zones[1] = EtiquetadorZone(
        etiquetador_id=1,
        distance_from_camera_m=0.6,  # 60cm desde cámara
        fruit_types=['apple', 'orange', 'banana', 'grape', 'lemon'],
        active=True
    )
    
    logger.info("✓ Sincronizador creado para maqueta 1m x 0.25m")
    return sync

def simulate_detection_sequence():
    """Simular secuencia de detecciones para prueba."""
    
    logger.info("=== Simulación de Secuencia de Detecciones ===")
    
    # Crear sincronizador
    sync = create_mockup_synchronizer()
    
    # Callback de ejemplo
    def ejemplo_callback_etiquetador():
        logger.info("🏷️  ¡ETIQUETADOR ACTIVADO!")
    
    # Registrar callback
    sync.register_etiquetador_callback(1, ejemplo_callback_etiquetador)
    
    # Iniciar sincronización
    sync.start_synchronization()
    
    try:
        # Mostrar info de timing
        timing_info = sync.get_timing_info_for_mockup()
        logger.info("Información de timing para maqueta:")
        for key, value in timing_info.items():
            logger.info(f"  {key}: {value}")
        
        # Simular detecciones
        frutas_test = ['apple', 'orange', 'banana', 'grape']
        
        for i, fruta in enumerate(frutas_test):
            detection = DetectionEvent(
                fruit_type=fruta,
                confidence=0.85 + (i * 0.03),
                position_x=320,  # Centro de imagen
                position_y=240
            )
            
            logger.info(f"\n--- Detección {i+1}: {fruta} ---")
            sync.process_detection(detection)
            
            # Esperar antes de siguiente detección
            time.sleep(2.0)
        
        # Esperar a que se procesen todas las activaciones
        logger.info("\nEsperando activaciones pendientes...")
        time.sleep(10.0)
        
        # Mostrar estadísticas finales
        status = sync.get_status()
        logger.info("\n=== Estadísticas Finales ===")
        for key, value in status['statistics'].items():
            logger.info(f"{key}: {value}")
            
    finally:
        sync.stop_synchronization()

if __name__ == "__main__":
    # Ejecutar simulación de ejemplo
    simulate_detection_sequence()