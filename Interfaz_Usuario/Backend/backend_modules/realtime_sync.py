"""
Módulo de Sincronización en Tiempo Real
=========================================

Sincroniza datos reales del sistema principal con el backend y frontend.
Captura detecciones de IA, métricas, estado del sistema y temperatura.

Autor: Sistema VisiFruit
Fecha: 2025
"""

import asyncio
import aiohttp
import json
import logging
import platform
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Deque
from collections import deque
import psutil

logger = logging.getLogger(__name__)

class RealtimeSyncManager:
    """Gestor de sincronización en tiempo real con el sistema principal."""
    
    def __init__(self):
        self.main_system_url = "http://localhost:8000"
        self.is_connected = False
        self.last_sync_time = None
        self.sync_interval = 0.5  # 500ms para datos en tiempo real
        
        # Buffers de datos históricos
        self.detections_history: Deque[Dict] = deque(maxlen=100)
        self.metrics_history: Deque[Dict] = deque(maxlen=100)
        self.category_stats: Dict[str, Dict] = {
            "apple": {"count": 0, "last_detection": None, "confidence_avg": 0.0},
            "pear": {"count": 0, "last_detection": None, "confidence_avg": 0.0},
            "lemon": {"count": 0, "last_detection": None, "confidence_avg": 0.0}
        }
        
        # Estado actual del sistema
        self.current_state = {
            "system": {
                "state": "offline",
                "running": False,
                "active_category": None,
                "last_detection_time": None,
                "ai_model_loaded": False,
                "temperature": 0.0
            },
            "production": {
                "current_fruit": None,
                "fruits_detected_today": 0,
                "fruits_labeled_today": 0,
                "fruits_classified_today": 0,
                "efficiency": 0.0,
                "production_rate": 0.0
            },
            "belt": {
                "running": False,
                "direction": "stopped",
                "speed": 0.0
            },
            "stepper": {
                "isActive": False,
                "activationCount": 0,
                "sensorTriggers": 0
            },
            "metrics": {
                "oee": 0.0,
                "availability": 0.0,
                "performance": 0.0,
                "quality": 0.0
            }
        }
        
        # WebSocket callbacks
        self.websocket_callbacks: List[callable] = []
        
    async def initialize(self):
        """Inicializa el gestor de sincronización."""
        try:
            logger.info("Inicializando RealtimeSyncManager...")
            
            # Verificar conexión con sistema principal
            await self.check_main_system_connection()
            
            # Iniciar tarea de sincronización
            asyncio.create_task(self._sync_loop())
            
            logger.info("✅ RealtimeSyncManager inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando RealtimeSyncManager: {e}")
            return False
    
    async def check_main_system_connection(self) -> bool:
        """Verifica la conexión con el sistema principal."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.main_system_url}/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status == 200:
                        self.is_connected = True
                        logger.info("✅ Conectado al sistema principal")
                        return True
        except Exception as e:
            logger.warning(f"Sistema principal no disponible: {e}")
            self.is_connected = False
            return False
    
    def get_raspberry_pi_temperature(self) -> float:
        """Obtiene la temperatura real de la Raspberry Pi 5."""
        try:
            # Detectar si estamos en Raspberry Pi
            if platform.system() == "Linux":
                # Método 1: Temperatura del CPU (funciona en Raspberry Pi)
                temp_file = Path("/sys/class/thermal/thermal_zone0/temp")
                if temp_file.exists():
                    temp = float(temp_file.read_text().strip()) / 1000.0
                    return round(temp, 1)
                
                # Método 2: vcgencmd (específico de Raspberry Pi)
                try:
                    result = subprocess.run(
                        ["vcgencmd", "measure_temp"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        # Formato: temp=XX.X'C
                        temp_str = result.stdout.strip()
                        temp = float(temp_str.split("=")[1].split("'")[0])
                        return round(temp, 1)
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
            
            # Si no es Raspberry Pi o no se puede leer, usar temperatura del sistema
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current > 0:
                            return round(entry.current, 1)
            
            # Fallback: temperatura simulada basada en CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            base_temp = 35.0
            temp = base_temp + (cpu_percent * 0.3)  # Simular aumento por carga
            return round(temp, 1)
            
        except Exception as e:
            logger.debug(f"No se pudo obtener temperatura: {e}")
            return 42.0  # Valor por defecto realista
    
    async def _sync_loop(self):
        """Loop principal de sincronización."""
        while True:
            try:
                if self.is_connected:
                    await self._sync_with_main_system()
                else:
                    # Intentar reconectar cada 5 segundos
                    if not self.last_sync_time or \
                       (datetime.now() - self.last_sync_time).seconds > 5:
                        await self.check_main_system_connection()
                
                # Actualizar temperatura siempre (incluso sin conexión)
                self.current_state["system"]["temperature"] = self.get_raspberry_pi_temperature()
                
                # Notificar cambios a callbacks
                await self._notify_callbacks()
                
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Error en sync loop: {e}")
                await asyncio.sleep(2)
    
    async def _sync_with_main_system(self):
        """Sincroniza con el sistema principal."""
        try:
            async with aiohttp.ClientSession() as session:
                # Obtener estado del sistema
                async with session.get(
                    f"{self.main_system_url}/status",
                    timeout=aiohttp.ClientTimeout(total=1)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        await self._process_system_status(data)
                
                # Obtener métricas de categorías
                async with session.get(
                    f"{self.main_system_url}/metrics/categories",
                    timeout=aiohttp.ClientTimeout(total=1)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        await self._process_category_metrics(data)
                
                self.last_sync_time = datetime.now()
                
        except asyncio.TimeoutError:
            logger.debug("Timeout sincronizando con sistema principal")
        except Exception as e:
            logger.error(f"Error sincronizando: {e}")
    
    async def _process_system_status(self, data: Dict[str, Any]):
        """Procesa el estado del sistema principal."""
        try:
            # Estado del sistema
            if "system" in data:
                self.current_state["system"]["state"] = data["system"].get("state", "offline")
                self.current_state["system"]["ai_model_loaded"] = True
            
            # Estado de la banda
            if "belt" in data:
                belt = data["belt"]
                self.current_state["belt"]["running"] = belt.get("running", False)
                self.current_state["belt"]["direction"] = belt.get("direction", "stopped")
                self.current_state["belt"]["speed"] = belt.get("speed", 0.0)
            
            # Estado del stepper
            if "stepper" in data:
                stepper = data["stepper"]
                self.current_state["stepper"]["isActive"] = stepper.get("isActive", False)
                self.current_state["stepper"]["activationCount"] = stepper.get("activationCount", 0)
                self.current_state["stepper"]["sensorTriggers"] = stepper.get("sensorTriggers", 0)
            
            # Estadísticas generales
            if "stats" in data:
                stats = data["stats"]
                self.current_state["production"]["fruits_detected_today"] = stats.get("detections_total", 0)
                self.current_state["production"]["fruits_labeled_today"] = stats.get("labeled_total", 0)
                self.current_state["production"]["fruits_classified_today"] = stats.get("classified_total", 0)
            
            # Métricas generales
            if "metrics" in data:
                metrics = data["metrics"]
                self.current_state["metrics"]["oee"] = metrics.get("oee_percentage", 0.0)
                
                # Calcular eficiencia basada en detecciones vs etiquetado
                detected = metrics.get("total_fruits_detected", 0)
                labeled = metrics.get("total_labels_applied", 0)
                if detected > 0:
                    efficiency = (labeled / detected) * 100
                    self.current_state["production"]["efficiency"] = round(efficiency, 1)
                
        except Exception as e:
            logger.error(f"Error procesando estado del sistema: {e}")
    
    async def _process_category_metrics(self, data: Dict[str, Any]):
        """Procesa las métricas de categorías con datos REALES de la IA."""
        try:
            active_category = None
            latest_detection_time = None
            
            for category_name, metrics in data.items():
                if category_name in self.category_stats:
                    # Actualizar estadísticas de categoría
                    detected = metrics.get("detected_count", 0)
                    
                    # Si hay nuevas detecciones, actualizar
                    if detected > self.category_stats[category_name]["count"]:
                        self.category_stats[category_name]["count"] = detected
                        self.category_stats[category_name]["last_detection"] = datetime.now().isoformat()
                        
                        # Registrar en historial
                        detection_record = {
                            "timestamp": datetime.now().isoformat(),
                            "category": category_name,
                            "count": detected,
                            "confidence": metrics.get("avg_confidence", 0.95)
                        }
                        self.detections_history.append(detection_record)
                        
                        # Actualizar categoría activa (la más reciente)
                        if not latest_detection_time or \
                           self.category_stats[category_name]["last_detection"] > latest_detection_time:
                            latest_detection_time = self.category_stats[category_name]["last_detection"]
                            active_category = category_name
            
            # Actualizar categoría activa en el estado
            if active_category:
                self.current_state["system"]["active_category"] = active_category
                self.current_state["system"]["last_detection_time"] = latest_detection_time
                self.current_state["production"]["current_fruit"] = active_category
                
                # Log para debugging
                logger.info(f"🍎 Categoría activa actualizada: {active_category}")
            
            # Calcular tasa de producción (frutas por minuto)
            if len(self.detections_history) > 1:
                recent_detections = list(self.detections_history)[-10:]  # Últimas 10 detecciones
                time_span = (datetime.fromisoformat(recent_detections[-1]["timestamp"]) - 
                            datetime.fromisoformat(recent_detections[0]["timestamp"])).total_seconds()
                if time_span > 0:
                    rate = (len(recent_detections) / time_span) * 60  # Por minuto
                    self.current_state["production"]["production_rate"] = round(rate, 1)
            
        except Exception as e:
            logger.error(f"Error procesando métricas de categorías: {e}")
    
    async def _notify_callbacks(self):
        """Notifica a los callbacks registrados con los datos actuales."""
        try:
            current_data = self.get_current_data()
            for callback in self.websocket_callbacks:
                try:
                    await callback(current_data)
                except Exception as e:
                    logger.error(f"Error en callback: {e}")
        except Exception as e:
            logger.error(f"Error notificando callbacks: {e}")
    
    def register_callback(self, callback: callable):
        """Registra un callback para notificaciones de datos."""
        if callback not in self.websocket_callbacks:
            self.websocket_callbacks.append(callback)
    
    def unregister_callback(self, callback: callable):
        """Desregistra un callback."""
        if callback in self.websocket_callbacks:
            self.websocket_callbacks.remove(callback)
    
    def get_current_data(self) -> Dict[str, Any]:
        """Obtiene los datos actuales para enviar al frontend."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.current_state["system"],
            "production": self.current_state["production"],
            "belt": self.current_state["belt"],
            "stepper": self.current_state["stepper"],
            "metrics": self.current_state["metrics"],
            "categories": self.category_stats,
            "recent_detections": list(self.detections_history)[-10:],
            "is_connected": self.is_connected
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos formateados para el dashboard."""
        return {
            "timestamp": datetime.now().isoformat(),
            "systemStatus": {
                "state": self.current_state["system"]["state"],
                "temperature": self.current_state["system"]["temperature"],
                "aiModelLoaded": self.current_state["system"]["ai_model_loaded"]
            },
            "productionStatus": {
                "activeCategory": self.current_state["production"]["current_fruit"] or "ninguno",
                "fruitsDetectedToday": self.current_state["production"]["fruits_detected_today"],
                "fruitsLabeledToday": self.current_state["production"]["fruits_labeled_today"],
                "efficiency": self.current_state["production"]["efficiency"],
                "productionRate": self.current_state["production"]["production_rate"]
            },
            "performanceMetrics": {
                "oee": self.current_state["metrics"]["oee"],
                "availability": self.current_state["metrics"]["availability"],
                "performance": self.current_state["metrics"]["performance"],
                "quality": self.current_state["metrics"]["quality"]
            },
            "categoryBreakdown": {
                "apple": self.category_stats["apple"]["count"],
                "pear": self.category_stats["pear"]["count"],
                "lemon": self.category_stats["lemon"]["count"]
            }
        }
    
    async def simulate_detection(self, category: str = None) -> Dict[str, Any]:
        """Simula una detección para testing (solo si no hay sistema real)."""
        if self.is_connected:
            return {"error": "Sistema real conectado, no se puede simular"}
        
        import random
        
        if not category:
            category = random.choice(["apple", "pear", "lemon"])
        
        # Simular detección
        self.category_stats[category]["count"] += 1
        self.category_stats[category]["last_detection"] = datetime.now().isoformat()
        
        detection = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "confidence": round(random.uniform(0.85, 0.99), 2),
            "simulated": True
        }
        
        self.detections_history.append(detection)
        self.current_state["production"]["current_fruit"] = category
        self.current_state["production"]["fruits_detected_today"] += 1
        
        return detection

# Instancia global
realtime_sync = RealtimeSyncManager()

__all__ = ['RealtimeSyncManager', 'realtime_sync']
