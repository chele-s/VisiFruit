#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de Integración: YOLOv12 + Sincronización Posicional - VisiFruit System
==============================================================================

Este ejemplo muestra cómo integrar completamente:
1. Detección de frutas con YOLOv12
2. Sincronización temporal con etiquetadores L298N
3. Control de banda transportadora

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Ejemplo de Integración
"""

import asyncio
import logging
import time
import cv2
import numpy as np
from pathlib import Path
import sys
from typing import Dict, List, Optional

# Agregar paths
sys.path.append(str(Path(__file__).parent.parent))

# Imports del sistema VisiFruit
from IA_Etiquetado.Train_Yolo import FruitDatasetManager, YOLOv12Trainer
from Control_Etiquetado.position_synchronizer import PositionSynchronizer, DetectionEvent, create_mockup_synchronizer
from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController
from IA_Etiquetado.smart_position_detector import SmartPositionDetector, SpatialCalibration

# Imports de YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  YOLO no disponible - modo simulación")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class VisiFruitIntegratedSystem:
    """Sistema integrado completo VisiFruit con detección posicional inteligente."""
    
    def __init__(self, model_path: Optional[str] = None, config_file: str = "Config_Etiquetadora.json"):
        # Componentes principales
        self.model_path = model_path
        self.config_file = config_file
        
        # Sistemas
        self.yolo_model = None
        self.synchronizer = None
        self.belt_controller = None
        self.smart_detector = None  # Detector de posición inteligente
        
        # Estado
        self.running = False
        self.processing_frame = False
        
        # Control de activación inteligente
        self.active_activations = {}  # {activation_id: {'start_time': float, 'duration': float}}
        
        # Estadísticas mejoradas
        self.stats = {
            'frames_processed': 0,
            'fruits_detected': 0,
            'clusters_detected': 0,
            'labels_applied': 0,
            'smart_activations': 0,
            'total_activation_time': 0.0,
            'avg_cluster_size': 0.0,
            'fps': 0.0,
            'start_time': time.time()
        }
        
    async def initialize_systems(self):
        """Inicializar todos los subsistemas."""
        
        logger.info("=== Inicializando Sistema VisiFruit Integrado ===")
        
        try:
            # 1. Inicializar modelo YOLO
            if self.model_path and YOLO_AVAILABLE:
                logger.info(f"Cargando modelo YOLO: {self.model_path}")
                self.yolo_model = YOLO(self.model_path)
                logger.info("✓ Modelo YOLO cargado")
            else:
                logger.warning("⚠️  Modo simulación - sin modelo YOLO real")
            
            # 2. Inicializar detector de posición inteligente
            logger.info("Inicializando detector de posición inteligente...")
            self.smart_detector = SmartPositionDetector()
            logger.info("✓ Detector inteligente inicializado")
            
            # 3. Inicializar sincronizador de posición (para compatibilidad)
            logger.info("Inicializando sincronizador posicional...")
            self.synchronizer = create_mockup_synchronizer()
            
            # Registrar callback para etiquetadores
            def etiquetador_callback():
                self._activate_physical_labeler()
            
            self.synchronizer.register_etiquetador_callback(1, etiquetador_callback)
            self.synchronizer.start_synchronization()
            logger.info("✓ Sincronizador iniciado")
            
            # 4. Inicializar controlador de banda
            logger.info("Inicializando controlador de banda...")
            self.belt_controller = ConveyorBeltController(self.config_file)
            success = await self.belt_controller.initialize()
            
            if success:
                logger.info("✓ Controlador de banda inicializado")
                
                # Calibrar velocidad del sincronizador con la banda
                belt_status = self.belt_controller.get_status()
                belt_speed = belt_status.get('config', {}).get('default_speed_percent', 75) / 100.0
                actual_speed_mps = belt_speed * 0.2  # Estimar velocidad real
                
                self.synchronizer.calibrate_belt_speed(actual_speed_mps)
                logger.info(f"✓ Velocidad sincronizada: {actual_speed_mps:.3f} m/s")
            else:
                logger.error("✗ Error inicializando controlador de banda")
            
            logger.info("=== Sistema VisiFruit Inicializado Correctamente ===")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            return False
    
    def _activate_physical_labeler(self):
        """Activar etiquetador físico (callback del sincronizador)."""
        
        logger.info("🏷️  ACTIVANDO ETIQUETADOR FÍSICO!")
        self.stats['labels_applied'] += 1
        
        # Aquí iría el código para activar el hardware real
        # Por ejemplo, activar solenoide, servo, etc.
        
        # TODO: Integrar con labeler_actuator.py
        # await self.labeler_actuator.activate_labeler(1, duration_ms=100)
    
    async def _schedule_smart_activation(self, command: Dict):
        """
        Programar activación inteligente basada en comando.
        
        Args:
            command: Comando de activación con delay_s, duration_s y cluster_info
        """
        
        try:
            activation_id = f"smart_{int(time.time() * 1000)}"
            delay_s = command['delay_s']
            duration_s = command['duration_s']
            cluster_info = command['cluster_info']
            
            logger.info(f"📅 Programando activación inteligente:")
            logger.info(f"  - ID: {activation_id}")
            logger.info(f"  - Delay: {delay_s:.2f}s")
            logger.info(f"  - Duración: {duration_s:.2f}s")
            logger.info(f"  - Frutas: {cluster_info['fruit_count']} ({cluster_info['rows']}x{cluster_info['cols']})")
            logger.info(f"  - Tipos: {', '.join(set(cluster_info['fruit_types']))}")
            
            # Guardar información de activación
            self.active_activations[activation_id] = {
                'start_time': time.time() + delay_s,
                'duration': duration_s,
                'cluster_info': cluster_info,
                'activated': False
            }
            
            # Programar activación usando asyncio
            asyncio.create_task(self._execute_smart_activation(activation_id))
            
        except Exception as e:
            logger.error(f"Error programando activación inteligente: {e}")
    
    async def _execute_smart_activation(self, activation_id: str):
        """
        Ejecutar activación inteligente programada.
        
        Args:
            activation_id: ID único de la activación
        """
        
        try:
            if activation_id not in self.active_activations:
                return
            
            activation_info = self.active_activations[activation_id]
            start_time = activation_info['start_time']
            duration = activation_info['duration']
            cluster_info = activation_info['cluster_info']
            
            # Esperar hasta el momento de activación
            delay = start_time - time.time()
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Marcar como activado
            activation_info['activated'] = True
            
            logger.info(f"🏷️  INICIANDO ACTIVACIÓN INTELIGENTE {activation_id}:")
            logger.info(f"  - Duración: {duration:.2f}s")
            logger.info(f"  - Grupo: {cluster_info['fruit_count']} frutas en {cluster_info['rows']}x{cluster_info['cols']}")
            
            # Activar etiquetador por la duración calculada
            start_activation = time.time()
            
            # Simular activación del hardware (reemplazar con código real)
            # Aquí iría la activación del L298N, solenoide, etc.
            await self._activate_smart_labeler(duration, cluster_info)
            
            # Estadísticas
            actual_duration = time.time() - start_activation
            self.stats['labels_applied'] += cluster_info['fruit_count']
            self.stats['total_activation_time'] += actual_duration
            
            logger.info(f"✅ Activación {activation_id} completada ({actual_duration:.2f}s)")
            
            # Limpiar de activaciones activas
            if activation_id in self.active_activations:
                del self.active_activations[activation_id]
            
        except Exception as e:
            logger.error(f"Error ejecutando activación {activation_id}: {e}")
    
    async def _activate_smart_labeler(self, duration_s: float, cluster_info: Dict):
        """
        Activar etiquetador de forma inteligente.
        
        Args:
            duration_s: Duración de la activación
            cluster_info: Información del clúster de frutas
        """
        
        try:
            # Aquí iría la lógica específica para el hardware
            # Por ejemplo, para L298N:
            
            # Calcular velocidad de etiquetado basada en distribución
            rows = cluster_info['rows']
            cols = cluster_info['cols']
            
            if rows > 1:
                # Múltiples filas - movimiento lateral del etiquetador
                logger.info(f"🔄 Activación multi-fila: {rows} filas")
                # Aquí activarías servo para movimiento lateral
                
            if cols > 1:
                # Múltiples columnas - activación extendida
                logger.info(f"🔄 Activación multi-columna: {cols} columnas")
                # Aquí mantendrías la activación más tiempo
            
            # Simular activación durante la duración calculada
            await asyncio.sleep(duration_s)
            
            logger.info("🏷️  Etiquetador inteligente activado correctamente")
            
        except Exception as e:
            logger.error(f"Error en activación inteligente del etiquetador: {e}")
    
    def detect_fruits_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        Detectar frutas en un frame usando YOLO y procesar con detección inteligente.
        
        Args:
            frame: Frame de video (numpy array)
            
        Returns:
            Lista de comandos de activación inteligentes
        """
        
        raw_detections = []
        
        try:
            if self.yolo_model and YOLO_AVAILABLE:
                # Detección real con YOLO
                results = self.yolo_model(frame, conf=0.5, iou=0.4, verbose=False)
                
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            # Extraer información de la detección
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            # Mapear class_id a nombre de fruta
                            fruit_names = ['apple', 'orange', 'banana', 'grape', 'strawberry', 
                                         'pineapple', 'mango', 'watermelon', 'lemon', 'peach']
                            fruit_name = fruit_names[class_id] if class_id < len(fruit_names) else 'unknown'
                            
                            # Crear detección en formato para procesamiento inteligente
                            detection = {
                                'class_name': fruit_name,
                                'confidence': confidence,
                                'bbox': (int(x1), int(y1), int(x2), int(y2))
                            }
                            
                            raw_detections.append(detection)
            
            else:
                # Simulación para pruebas sin modelo real - generar múltiples frutas
                if np.random.random() > 0.6:  # 40% probabilidad de detección simulada
                    simulated_fruits = ['apple', 'orange', 'banana', 'grape', 'lemon']
                    
                    # Simular entre 1-5 frutas por frame
                    num_fruits = np.random.randint(1, 6)
                    
                    for i in range(num_fruits):
                        fruit_type = np.random.choice(simulated_fruits)
                        
                        # Posiciones más realistas para simular agrupaciones
                        if i == 0:
                            # Primera fruta en posición aleatoria
                            base_x = np.random.randint(300, 600)
                            base_y = np.random.randint(200, 400)
                        else:
                            # Frutas subsecuentes cerca de la primera (simula agrupación)
                            base_x += np.random.randint(-80, 80)
                            base_y += np.random.randint(-80, 80)
                        
                        # Tamaño de fruta simulado
                        size = np.random.randint(60, 100)
                        
                        detection = {
                            'class_name': fruit_type,
                            'confidence': 0.75 + np.random.random() * 0.2,
                            'bbox': (base_x - size//2, base_y - size//2, 
                                   base_x + size//2, base_y + size//2)
                        }
                        
                        raw_detections.append(detection)
            
            # Procesar detecciones con sistema inteligente
            if raw_detections and self.smart_detector:
                clusters = self.smart_detector.process_detections(raw_detections)
                activation_commands = self.smart_detector.get_activation_commands(clusters)
                
                # Actualizar estadísticas
                self.stats['fruits_detected'] += len(raw_detections)
                self.stats['clusters_detected'] += len(clusters)
                
                if clusters:
                    cluster_sizes = [len(c.fruits) for c in clusters]
                    self.stats['avg_cluster_size'] = sum(cluster_sizes) / len(cluster_sizes)
                
                # Log información detallada
                if clusters:
                    logger.info(f"🍎 Detectadas {len(raw_detections)} frutas en {len(clusters)} grupos:")
                    for cluster in clusters:
                        logger.info(f"  - Grupo {cluster.cluster_id}: {len(cluster.fruits)} frutas "
                                   f"({cluster.rows}x{cluster.cols}), "
                                   f"activar {cluster.activation_duration_s:.2f}s en {cluster.activation_start_delay_s:.2f}s")
                
                return activation_commands
            
        except Exception as e:
            logger.error(f"Error en detección inteligente: {e}")
        
        return []
    
    async def process_camera_feed(self, camera_id: int = 0, duration_seconds: float = 30.0):
        """
        Procesar feed de cámara en tiempo real.
        
        Args:
            camera_id: ID de la cámara
            duration_seconds: Duración de procesamiento
        """
        
        logger.info(f"Iniciando procesamiento de cámara (duración: {duration_seconds}s)")
        
        # Inicializar cámara
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            logger.error("No se pudo abrir la cámara")
            return
        
        # Configurar cámara
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        try:
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration_seconds:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("No se pudo leer frame de cámara")
                    continue
                
                # Procesar frame
                if not self.processing_frame:
                    self.processing_frame = True
                    
                    try:
                        # Detectar frutas con sistema inteligente
                        activation_commands = self.detect_fruits_in_frame(frame)
                        
                        # Procesar comandos de activación inteligentes
                        for command in activation_commands:
                            await self._schedule_smart_activation(command)
                            self.stats['smart_activations'] += 1
                        
                        # Actualizar estadísticas
                        frame_count += 1
                        self.stats['frames_processed'] = frame_count
                        
                        if frame_count % 30 == 0:  # Cada 30 frames
                            elapsed = time.time() - start_time
                            self.stats['fps'] = frame_count / elapsed
                            
                            # Mostrar estadísticas
                            logger.info(f"📊 Stats: {frame_count} frames, "
                                       f"{self.stats['fruits_detected']} frutas, "
                                       f"{self.stats['labels_applied']} etiquetas, "
                                       f"{self.stats['fps']:.1f} FPS")
                        
                        # Mostrar frame (opcional)
                        # cv2.imshow('VisiFruit', frame)
                        # if cv2.waitKey(1) & 0xFF == ord('q'):
                        #     break
                            
                    finally:
                        self.processing_frame = False
                
                # Pequeña pausa para no saturar CPU
                await asyncio.sleep(0.01)
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info("✓ Procesamiento de cámara finalizado")
    
    async def run_production_cycle(self, duration_minutes: float = 5.0):
        """
        Ejecutar ciclo completo de producción.
        
        Args:
            duration_minutes: Duración del ciclo en minutos
        """
        
        logger.info("=== Iniciando Ciclo de Producción ===")
        
        try:
            # 1. Inicializar banda transportadora
            if self.belt_controller:
                logger.info("Iniciando banda transportadora...")
                success = await self.belt_controller.start_belt(75)  # 75% velocidad
                if not success:
                    logger.error("Error iniciando banda")
                    return
                logger.info("✓ Banda transportadora iniciada")
            
            # 2. Procesar cámara en paralelo
            duration_seconds = duration_minutes * 60
            await self.process_camera_feed(duration_seconds=duration_seconds)
            
            # 3. Detener banda
            if self.belt_controller:
                logger.info("Deteniendo banda transportadora...")
                await self.belt_controller.stop_belt()
                logger.info("✓ Banda detenida")
            
            # 4. Mostrar estadísticas finales
            self._show_final_statistics()
            
        except Exception as e:
            logger.error(f"Error en ciclo de producción: {e}")
        finally:
            logger.info("=== Ciclo de Producción Finalizado ===")
    
    def _show_final_statistics(self):
        """Mostrar estadísticas finales del ciclo."""
        
        elapsed_time = time.time() - self.stats['start_time']
        
        logger.info("=== ESTADÍSTICAS FINALES INTELIGENTES ===")
        logger.info(f"⏱️  Tiempo total: {elapsed_time:.1f}s")
        logger.info(f"🎬 Frames procesados: {self.stats['frames_processed']}")
        logger.info(f"🍎 Frutas detectadas: {self.stats['fruits_detected']}")
        logger.info(f"📦 Grupos detectados: {self.stats['clusters_detected']}")
        logger.info(f"🔢 Tamaño promedio grupo: {self.stats['avg_cluster_size']:.1f} frutas")
        logger.info(f"🏷️  Etiquetas aplicadas: {self.stats['labels_applied']}")
        logger.info(f"🧠 Activaciones inteligentes: {self.stats['smart_activations']}")
        logger.info(f"⏱️  Tiempo total activación: {self.stats['total_activation_time']:.1f}s")
        logger.info(f"📊 FPS promedio: {self.stats['fps']:.1f}")
        
        # Métricas de eficiencia avanzadas
        if self.stats['fruits_detected'] > 0:
            detection_efficiency = (self.stats['labels_applied'] / self.stats['fruits_detected']) * 100
            logger.info(f"⚡ Eficiencia detección: {detection_efficiency:.1f}%")
        
        if self.stats['clusters_detected'] > 0:
            cluster_efficiency = (self.stats['smart_activations'] / self.stats['clusters_detected']) * 100
            logger.info(f"🎯 Eficiencia agrupación: {cluster_efficiency:.1f}%")
        
        if self.stats['smart_activations'] > 0:
            avg_activation_time = self.stats['total_activation_time'] / self.stats['smart_activations']
            logger.info(f"⏱️  Tiempo promedio activación: {avg_activation_time:.2f}s")
        
        # Estadísticas del detector inteligente
        if self.smart_detector:
            smart_stats = self.smart_detector.stats
            logger.info(f"🧠 Procesamiento IA: {smart_stats['processing_time_ms']:.1f}ms promedio")
            logger.info(f"🔍 Max grupo detectado: {smart_stats['max_cluster_size']} frutas")
        
        # Activaciones pendientes
        if self.active_activations:
            logger.info(f"⏳ Activaciones pendientes: {len(self.active_activations)}")
        
        # Estadísticas del sincronizador (compatibilidad)
        if self.synchronizer:
            sync_status = self.synchronizer.get_status()
            logger.info(f"🔄 Sistema sincronización: {sync_status['statistics']['detections_processed']} detecciones")
    
    async def cleanup(self):
        """Limpiar recursos del sistema."""
        
        logger.info("Limpiando recursos del sistema...")
        
        if self.synchronizer:
            self.synchronizer.stop_synchronization()
        
        if self.belt_controller:
            await self.belt_controller.cleanup()
        
        logger.info("✓ Limpieza completada")

async def demo_complete_system():
    """Demostración completa del sistema integrado."""
    
    logger.info("🚀 DEMO: Sistema VisiFruit Completo")
    
    # Crear sistema integrado
    system = VisiFruitIntegratedSystem()
    
    try:
        # Inicializar todos los componentes
        success = await system.initialize_systems()
        if not success:
            logger.error("Error inicializando sistema")
            return
        
        # Mostrar información de timing
        timing_info = system.synchronizer.get_timing_info_for_mockup()
        logger.info("\n📏 INFORMACIÓN DE TIMING PARA MAQUETA 1M:")
        for section, data in timing_info.items():
            logger.info(f"  {section}: {data}")
        
        # Ejecutar ciclo de producción de prueba
        logger.info("\n🏭 Iniciando ciclo de producción de 2 minutos...")
        await system.run_production_cycle(duration_minutes=2.0)
        
    except KeyboardInterrupt:
        logger.info("Demo interrumpida por usuario")
    except Exception as e:
        logger.error(f"Error en demo: {e}")
    finally:
        await system.cleanup()

async def test_synchronization_only():
    """Probar solo el sistema de sincronización."""
    
    logger.info("🔄 PRUEBA: Solo Sistema de Sincronización")
    
    # Crear sincronizador
    sync = create_mockup_synchronizer()
    
    # Callback de prueba
    activations_count = 0
    def test_callback():
        nonlocal activations_count
        activations_count += 1
        logger.info(f"🏷️  ETIQUETADOR ACTIVADO #{activations_count}")
    
    # Configurar y iniciar
    sync.register_etiquetador_callback(1, test_callback)
    sync.start_synchronization()
    
    try:
        # Mostrar información de configuración
        status = sync.get_status()
        logger.info("📊 Estado del sincronizador:")
        for key, value in status.items():
            logger.info(f"  {key}: {value}")
        
        # Simular detecciones periódicas
        fruits = ['apple', 'orange', 'banana', 'grape', 'lemon']
        
        for i in range(5):
            fruit = fruits[i % len(fruits)]
            detection = DetectionEvent(
                fruit_type=fruit,
                confidence=0.80 + (i * 0.02),
                position_x=320,
                position_y=240
            )
            
            logger.info(f"\n🍎 Procesando detección #{i+1}: {fruit}")
            sync.process_detection(detection)
            
            # Esperar entre detecciones
            await asyncio.sleep(3.0)
        
        # Esperar activaciones pendientes
        logger.info("\n⏳ Esperando activaciones pendientes...")
        await asyncio.sleep(10.0)
        
        # Estadísticas finales
        final_status = sync.get_status()
        logger.info(f"\n📈 RESULTADOS:")
        logger.info(f"Detecciones procesadas: {final_status['statistics']['detections_processed']}")
        logger.info(f"Activaciones enviadas: {final_status['statistics']['activations_sent']}")
        logger.info(f"Activaciones físicas: {activations_count}")
        
    finally:
        sync.stop_synchronization()

def main():
    """Función principal con menú de opciones."""
    
    print("\n" + "="*60)
    print("SISTEMA INTEGRADO VISIFRUIT - DETECCIÓN INTELIGENTE")
    print("="*60)
    print("1. Demo completo (YOLO + Detección Inteligente + Banda)")
    print("2. Solo sincronización posicional (clásica)")
    print("3. Prueba detección inteligente")
    print("4. Calibrador visual")
    print("5. Entrenar modelo YOLO")
    print("6. Mostrar información de timing")
    print("0. Salir")
    
    try:
        opcion = input("\nSeleccione una opción: ").strip()
        
        if opcion == "1":
            asyncio.run(demo_complete_system())
        elif opcion == "2":
            asyncio.run(test_synchronization_only())
        elif opcion == "3":
            # Prueba detección inteligente
            from IA_Etiquetado.smart_position_detector import test_smart_detection
            test_smart_detection()
        elif opcion == "4":
            # Calibrador visual
            from IA_Etiquetado.visual_calibrator import main as calibrator_main
            calibrator_main()
        elif opcion == "5":
            # Ejecutar entrenamiento YOLO
            from IA_Etiquetado.Train_Yolo import main as train_main
            train_main()
        elif opcion == "6":
            # Mostrar información de timing
            sync = create_mockup_synchronizer()
            timing_info = sync.get_timing_info_for_mockup()
            print("\n📏 INFORMACIÓN DE TIMING PARA MAQUETA 1M x 0.25M:")
            print("="*50)
            for section, data in timing_info.items():
                print(f"{section}:")
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {data}")
                print()
        elif opcion == "0":
            print("¡Adiós!")
        else:
            print("Opción no válida")
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por usuario")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()