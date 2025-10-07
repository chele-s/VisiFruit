#!/usr/bin/env python3
# test_camera_ai_optimized.py
"""
Script de Prueba y Calibración - Cámara OV5647 + YOLOv8
=======================================================

Valida y optimiza la integración entre la cámara OV5647 y YOLOv8.

Funcionalidades:
- Test de captura de cámara con métricas
- Benchmark de velocidad de inferencia IA
- Análisis de calidad de frames
- Optimización automática de parámetros
- Generación de reporte de rendimiento

Uso:
    python test_camera_ai_optimized.py [opciones]
    
Opciones:
    --quick     : Test rápido (10 frames)
    --full      : Test completo (100 frames)
    --benchmark : Solo benchmark de IA
    --save      : Guardar frames de ejemplo

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Octubre 2025
"""

import asyncio
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
import cv2

# Configurar logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CameraAITest")

# Importar módulos del sistema
try:
    from utils.camera_controller import CameraController
    from utils.frame_preprocessor import create_ov5647_preprocessor, FrameMetrics
    CAMERA_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importando módulos de cámara: {e}")
    CAMERA_AVAILABLE = False

try:
    from IA_Etiquetado.YOLOv8_detector import EnterpriseFruitDetector
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Detector IA no disponible: {e}")
    AI_AVAILABLE = False


class CameraAIBenchmark:
    """Sistema de benchmark para cámara + IA."""
    
    def __init__(self, config_path: str = "Prototipo_Clasificador/Config_Prototipo.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        self.camera = None
        self.ai_detector = None
        self.preprocessor = None
        
        # Resultados
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "config_file": str(self.config_path),
            "camera": {},
            "ai": {},
            "integration": {},
            "recommendations": []
        }
    
    def _load_config(self) -> Dict:
        """Carga configuración del sistema."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return {}
    
    async def initialize(self) -> bool:
        """Inicializa componentes."""
        logger.info("=" * 70)
        logger.info("🚀 INICIANDO TEST DE CÁMARA OV5647 + YOLOv8")
        logger.info("=" * 70)
        
        # Inicializar cámara
        if not await self._init_camera():
            return False
        
        # Inicializar pre-procesador
        self._init_preprocessor()
        
        # Inicializar IA
        if not await self._init_ai():
            logger.warning("⚠️ IA no disponible - solo test de cámara")
        
        return True
    
    async def _init_camera(self) -> bool:
        """Inicializa cámara."""
        try:
            logger.info("📷 Inicializando cámara OV5647...")
            camera_config = self.config.get("camera_settings", {})
            
            self.camera = CameraController(camera_config)
            
            if not self.camera.initialize():
                logger.error("❌ Fallo al inicializar cámara")
                return False
            
            # Obtener status
            status = self.camera.get_status()
            logger.info(f"✅ Cámara inicializada:")
            logger.info(f"   Tipo: {status['type']}")
            logger.info(f"   Estado: {status['state']}")
            
            self.results["camera"]["status"] = "initialized"
            self.results["camera"]["type"] = status['type']
            
            return True
            
        except Exception as e:
            logger.exception(f"❌ Error inicializando cámara: {e}")
            return False
    
    def _init_preprocessor(self):
        """Inicializa pre-procesador."""
        try:
            logger.info("🎨 Inicializando pre-procesador de frames...")
            preprocess_config = {
                "preprocessing_mode": "balanced",
                "auto_brightness": True,
                "auto_contrast": True,
                "sharpen": True,
                "color_correction": True
            }
            
            self.preprocessor = create_ov5647_preprocessor(preprocess_config)
            logger.info("✅ Pre-procesador inicializado")
            
        except Exception as e:
            logger.warning(f"⚠️ Pre-procesador no disponible: {e}")
    
    async def _init_ai(self) -> bool:
        """Inicializa detector IA."""
        try:
            if not AI_AVAILABLE:
                return False
            
            logger.info("🤖 Inicializando detector YOLOv8...")
            self.ai_detector = EnterpriseFruitDetector(self.config)
            
            if not await self.ai_detector.initialize():
                logger.error("❌ Fallo al inicializar IA")
                return False
            
            logger.info("✅ YOLOv8 inicializado correctamente")
            self.results["ai"]["status"] = "initialized"
            
            return True
            
        except Exception as e:
            logger.exception(f"❌ Error inicializando IA: {e}")
            return False
    
    async def run_camera_test(self, num_frames: int = 30) -> Dict:
        """Test de rendimiento de cámara."""
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"📷 TEST DE CÁMARA - {num_frames} frames")
        logger.info("=" * 70)
        
        frame_times = []
        frame_qualities = []
        frames_captured = 0
        
        for i in range(num_frames):
            start = time.time()
            
            # Capturar frame
            frame = self.camera.capture_frame()
            
            if frame is not None:
                capture_time = (time.time() - start) * 1000
                frame_times.append(capture_time)
                frames_captured += 1
                
                # Analizar calidad
                if self.preprocessor:
                    metrics = self.preprocessor.analyze_frame(frame)
                    frame_qualities.append(metrics)
                
                if i % 10 == 0:
                    logger.info(f"   Frame {i+1}/{num_frames} - {capture_time:.1f}ms")
            else:
                logger.warning(f"   Frame {i+1} falló")
            
            await asyncio.sleep(0.033)  # ~30 FPS
        
        # Calcular estadísticas
        avg_time = np.mean(frame_times) if frame_times else 0
        avg_fps = 1000 / avg_time if avg_time > 0 else 0
        
        results = {
            "frames_requested": num_frames,
            "frames_captured": frames_captured,
            "success_rate": frames_captured / num_frames * 100,
            "avg_capture_time_ms": round(avg_time, 2),
            "avg_fps": round(avg_fps, 1),
            "min_time_ms": round(min(frame_times), 2) if frame_times else 0,
            "max_time_ms": round(max(frame_times), 2) if frame_times else 0
        }
        
        # Estadísticas de calidad
        if frame_qualities:
            results["quality"] = {
                "avg_brightness": round(np.mean([m.brightness for m in frame_qualities]), 1),
                "avg_contrast": round(np.mean([m.contrast for m in frame_qualities]), 1),
                "avg_sharpness": round(np.mean([m.sharpness for m in frame_qualities]), 1),
                "avg_noise": round(np.mean([m.noise_level for m in frame_qualities]), 1)
            }
        
        self.results["camera"]["performance"] = results
        
        # Mostrar resultados
        logger.info("")
        logger.info("📊 RESULTADOS DE CÁMARA:")
        logger.info(f"   ✓ Capturados: {frames_captured}/{num_frames} ({results['success_rate']:.1f}%)")
        logger.info(f"   ⏱️ Tiempo promedio: {avg_time:.1f}ms")
        logger.info(f"   📹 FPS promedio: {avg_fps:.1f}")
        
        if "quality" in results:
            q = results["quality"]
            logger.info(f"   🎨 Calidad:")
            logger.info(f"      Brillo: {q['avg_brightness']:.1f}")
            logger.info(f"      Contraste: {q['avg_contrast']:.1f}")
            logger.info(f"      Nitidez: {q['avg_sharpness']:.1f}")
        
        return results
    
    async def run_ai_benchmark(self, num_frames: int = 20) -> Dict:
        """Benchmark de detección IA."""
        if not self.ai_detector:
            logger.warning("⚠️ IA no disponible - saltando benchmark")
            return {}
        
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"🤖 BENCHMARK DE IA - {num_frames} frames")
        logger.info("=" * 70)
        
        inference_times = []
        total_detections = 0
        detections_by_class = {}
        
        for i in range(num_frames):
            # Capturar frame
            frame = self.camera.capture_frame()
            
            if frame is None:
                continue
            
            # Pre-procesar si está disponible
            if self.preprocessor:
                frame = self.preprocessor.preprocess(frame)
            
            # Detectar
            start = time.time()
            from core_modules.system_types import ProcessingPriority
            result = await self.ai_detector.detect_fruits(frame, ProcessingPriority.HIGH)
            inference_time = (time.time() - start) * 1000
            
            if result:
                inference_times.append(inference_time)
                total_detections += result.fruit_count
                
                # Contar por clase
                for det in result.detections:
                    class_name = det.class_name
                    detections_by_class[class_name] = detections_by_class.get(class_name, 0) + 1
                
                if i % 5 == 0:
                    logger.info(f"   Frame {i+1}/{num_frames} - {inference_time:.0f}ms - {result.fruit_count} detecciones")
        
        # Calcular estadísticas
        avg_inference = np.mean(inference_times) if inference_times else 0
        avg_fps = 1000 / avg_inference if avg_inference > 0 else 0
        
        results = {
            "frames_processed": len(inference_times),
            "total_detections": total_detections,
            "avg_detections_per_frame": round(total_detections / len(inference_times), 2) if inference_times else 0,
            "avg_inference_time_ms": round(avg_inference, 1),
            "max_fps": round(avg_fps, 1),
            "min_time_ms": round(min(inference_times), 1) if inference_times else 0,
            "max_time_ms": round(max(inference_times), 1) if inference_times else 0,
            "detections_by_class": detections_by_class
        }
        
        self.results["ai"]["performance"] = results
        
        # Mostrar resultados
        logger.info("")
        logger.info("📊 RESULTADOS DE IA:")
        logger.info(f"   🎯 Total detecciones: {total_detections}")
        logger.info(f"   📈 Promedio por frame: {results['avg_detections_per_frame']}")
        logger.info(f"   ⏱️ Tiempo inferencia: {avg_inference:.1f}ms")
        logger.info(f"   🚀 FPS máximo: {avg_fps:.1f}")
        
        if detections_by_class:
            logger.info(f"   📦 Por clase:")
            for class_name, count in detections_by_class.items():
                logger.info(f"      {class_name}: {count}")
        
        return results
    
    async def run_integration_test(self, num_frames: int = 10) -> Dict:
        """Test de integración completa (cámara + pre-procesamiento + IA)."""
        if not self.ai_detector or not self.preprocessor:
            logger.warning("⚠️ Componentes no disponibles para test de integración")
            return {}
        
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"🔗 TEST DE INTEGRACIÓN COMPLETA - {num_frames} frames")
        logger.info("=" * 70)
        
        pipeline_times = []
        preprocessing_times = []
        
        for i in range(num_frames):
            pipeline_start = time.time()
            
            # 1. Capturar
            frame = self.camera.capture_frame()
            if frame is None:
                continue
            
            capture_time = time.time() - pipeline_start
            
            # 2. Pre-procesar
            preprocess_start = time.time()
            processed = self.preprocessor.preprocess(frame)
            preprocess_time = (time.time() - preprocess_start) * 1000
            preprocessing_times.append(preprocess_time)
            
            # 3. Detectar
            from core_modules.system_types import ProcessingPriority
            result = await self.ai_detector.detect_fruits(processed, ProcessingPriority.HIGH)
            
            total_time = (time.time() - pipeline_start) * 1000
            pipeline_times.append(total_time)
            
            if i % 3 == 0:
                logger.info(f"   Frame {i+1}: {total_time:.0f}ms total")
        
        # Estadísticas
        avg_pipeline = np.mean(pipeline_times) if pipeline_times else 0
        avg_preprocess = np.mean(preprocessing_times) if preprocessing_times else 0
        throughput_fps = 1000 / avg_pipeline if avg_pipeline > 0 else 0
        
        results = {
            "frames_processed": len(pipeline_times),
            "avg_total_time_ms": round(avg_pipeline, 1),
            "avg_preprocessing_time_ms": round(avg_preprocess, 1),
            "throughput_fps": round(throughput_fps, 1),
            "preprocessing_overhead_percent": round((avg_preprocess / avg_pipeline) * 100, 1) if avg_pipeline > 0 else 0
        }
        
        self.results["integration"] = results
        
        logger.info("")
        logger.info("📊 RESULTADOS DE INTEGRACIÓN:")
        logger.info(f"   ⏱️ Tiempo total promedio: {avg_pipeline:.1f}ms")
        logger.info(f"   🎨 Pre-procesamiento: {avg_preprocess:.1f}ms ({results['preprocessing_overhead_percent']:.1f}%)")
        logger.info(f"   🚀 Throughput: {throughput_fps:.1f} FPS")
        
        return results
    
    def generate_recommendations(self):
        """Genera recomendaciones basadas en resultados."""
        recommendations = []
        
        # Analizar rendimiento de cámara
        if "camera" in self.results and "performance" in self.results["camera"]:
            cam_perf = self.results["camera"]["performance"]
            
            if cam_perf["avg_fps"] < 25:
                recommendations.append({
                    "component": "camera",
                    "severity": "warning",
                    "message": f"FPS de cámara bajo ({cam_perf['avg_fps']:.1f}). Considera reducir resolución."
                })
            
            if "quality" in cam_perf:
                brightness = cam_perf["quality"]["avg_brightness"]
                if brightness < 80 or brightness > 180:
                    recommendations.append({
                        "component": "camera",
                        "severity": "info",
                        "message": f"Brillo no óptimo ({brightness:.0f}). Ajusta iluminación o configuración de cámara."
                    })
                
                sharpness = cam_perf["quality"]["avg_sharpness"]
                if sharpness < 300:
                    recommendations.append({
                        "component": "camera",
                        "severity": "warning",
                        "message": f"Nitidez baja ({sharpness:.0f}). Verifica enfoque de la cámara."
                    })
        
        # Analizar rendimiento de IA
        if "ai" in self.results and "performance" in self.results["ai"]:
            ai_perf = self.results["ai"]["performance"]
            
            if ai_perf["max_fps"] < 10:
                recommendations.append({
                    "component": "ai",
                    "severity": "warning",
                    "message": f"Inferencia muy lenta ({ai_perf['avg_inference_time_ms']:.0f}ms). Considera reducir input_size a 480."
                })
            elif ai_perf["max_fps"] > 20:
                recommendations.append({
                    "component": "ai",
                    "severity": "success",
                    "message": f"Excelente rendimiento de IA ({ai_perf['max_fps']:.1f} FPS). Sistema bien optimizado."
                })
        
        # Analizar integración
        if "integration" in self.results:
            integ = self.results["integration"]
            
            if integ["throughput_fps"] < 8:
                recommendations.append({
                    "component": "integration",
                    "severity": "critical",
                    "message": f"Throughput muy bajo ({integ['throughput_fps']:.1f} FPS). Sistema no viable para producción."
                })
            elif integ["throughput_fps"] >= 15:
                recommendations.append({
                    "component": "integration",
                    "severity": "success",
                    "message": f"Throughput excelente ({integ['throughput_fps']:.1f} FPS). Listo para producción."
                })
        
        self.results["recommendations"] = recommendations
        
        # Mostrar recomendaciones
        if recommendations:
            logger.info("")
            logger.info("=" * 70)
            logger.info("💡 RECOMENDACIONES")
            logger.info("=" * 70)
            
            for rec in recommendations:
                icon = {"critical": "🔴", "warning": "⚠️", "info": "ℹ️", "success": "✅"}.get(rec["severity"], "•")
                logger.info(f"{icon} [{rec['component'].upper()}] {rec['message']}")
    
    def save_report(self, filename: str = "camera_ai_benchmark_report.json"):
        """Guarda reporte de resultados."""
        try:
            output_path = Path("logs") / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Reporte guardado en: {output_path}")
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
    
    async def cleanup(self):
        """Limpia recursos."""
        logger.info("")
        logger.info("🧹 Limpiando recursos...")
        
        if self.ai_detector:
            await self.ai_detector.shutdown()
        
        if self.camera:
            self.camera.shutdown()
        
        logger.info("✅ Limpieza completada")


async def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(description="Test de Cámara OV5647 + YOLOv8")
    parser.add_argument("--quick", action="store_true", help="Test rápido (10 frames)")
    parser.add_argument("--full", action="store_true", help="Test completo (100 frames)")
    parser.add_argument("--benchmark", action="store_true", help="Solo benchmark de IA")
    parser.add_argument("--save", action="store_true", help="Guardar frames de ejemplo")
    
    args = parser.parse_args()
    
    # Determinar número de frames
    if args.quick:
        num_frames = 10
    elif args.full:
        num_frames = 100
    else:
        num_frames = 30  # Default
    
    # Crear benchmark
    benchmark = CameraAIBenchmark()
    
    try:
        # Inicializar
        if not await benchmark.initialize():
            logger.error("❌ Fallo en inicialización")
            return 1
        
        # Ejecutar tests
        if not args.benchmark:
            await benchmark.run_camera_test(num_frames)
        
        if benchmark.ai_detector:
            await benchmark.run_ai_benchmark(max(10, num_frames // 2))
            await benchmark.run_integration_test(max(5, num_frames // 4))
        
        # Generar recomendaciones
        benchmark.generate_recommendations()
        
        # Guardar reporte
        benchmark.save_report()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ TEST COMPLETADO EXITOSAMENTE")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⚡ Test interrumpido por usuario")
        return 1
    except Exception as e:
        logger.exception(f"❌ Error durante test: {e}")
        return 1
    finally:
        await benchmark.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)
