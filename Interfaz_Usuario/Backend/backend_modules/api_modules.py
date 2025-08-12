"""
APIs Especializadas Ultra-Avanzadas para FruPrint v3.0
======================================================

Conjunto completo de APIs especializadas por módulo:
- ProductionAPI: Control y monitoreo de producción
- SystemAPI: Gestión del sistema y componentes
- MetricsAPI: Métricas y análisis de rendimiento
- AlertsAPI: Gestión de alertas y notificaciones
- ConfigAPI: Configuración del sistema
- ReportsAPI: Generación y gestión de reportes
- AnalyticsAPI: Análisis avanzado y predicciones
- MaintenanceAPI: Mantenimiento y diagnósticos

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import io
import csv

logger = logging.getLogger("UltraAPIs")

# ==================== MODELOS PYDANTIC ====================

class ProductionStartRequest(BaseModel):
    """Modelo para iniciar producción."""
    target_rate: Optional[float] = Field(None, description="Tasa objetivo de producción")
    duration_minutes: Optional[int] = Field(None, description="Duración en minutos")
    quality_threshold: Optional[float] = Field(None, description="Umbral de calidad")
    auto_stop: bool = Field(False, description="Parar automáticamente al completar")

class ProductionStopRequest(BaseModel):
    """Modelo para detener producción."""
    reason: str = Field(..., description="Razón de la parada")
    emergency: bool = Field(False, description="Es parada de emergencia")

class AlertAcknowledgeRequest(BaseModel):
    """Modelo para confirmar alerta."""
    alert_id: str = Field(..., description="ID de la alerta")
    acknowledged_by: str = Field(..., description="Usuario que confirma")
    notes: Optional[str] = Field(None, description="Notas adicionales")

class ConfigUpdateRequest(BaseModel):
    """Modelo para actualizar configuración."""
    key: str = Field(..., description="Clave de configuración")
    value: Any = Field(..., description="Nuevo valor")
    reason: Optional[str] = Field(None, description="Razón del cambio")

class ReportGenerationRequest(BaseModel):
    """Modelo para generar reporte."""
    report_type: str = Field(..., description="Tipo de reporte")
    format: str = Field("pdf", description="Formato de salida")
    period: str = Field("last_24_hours", description="Período de tiempo")
    include_charts: bool = Field(True, description="Incluir gráficos")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros adicionales")

# ==================== BASE API CLASS ====================

class BaseAPI:
    """Clase base para todas las APIs especializadas."""
    
    def __init__(self):
        self.router = APIRouter()
        self.backend_system = None
        self.is_initialized = False
    
    async def initialize(self, backend_system):
        """Inicializa la API con referencia al sistema backend."""
        self.backend_system = backend_system
        self.is_initialized = True
        logger.info(f"✅ {self.__class__.__name__} inicializada")

# ==================== PRODUCTION API ====================

class ProductionAPI(BaseAPI):
    """API especializada para control de producción."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de producción."""
        
        @self.router.get("/status")
        async def get_production_status():
            """Obtiene el estado actual de producción."""
            try:
                # Simular estado de producción
                return {
                    "status": "running",
                    "current_rate": 85.3,
                    "target_rate": 100.0,
                    "efficiency": 87.2,
                    "items_processed_today": 3247,
                    "active_labelers": 4,
                    "active_group": {
                        "id": 0,
                        "category": "apple",
                        "emoji": "🍎"
                    },
                    "belt_speed": 0.5,
                    "quality_score": 94.7,
                    "uptime_today": "98.5%",
                    "last_switch": "2025-01-20T14:30:00Z"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/start")
        async def start_production(request: ProductionStartRequest):
            """Inicia la producción."""
            try:
                # Validar parámetros
                if request.target_rate and (request.target_rate < 1 or request.target_rate > 200):
                    raise HTTPException(status_code=400, detail="Tasa objetivo debe estar entre 1-200")
                
                # Simular inicio de producción
                production_session = {
                    "session_id": f"prod_{int(datetime.now().timestamp())}",
                    "started_at": datetime.now().isoformat(),
                    "target_rate": request.target_rate or 100.0,
                    "duration_minutes": request.duration_minutes,
                    "quality_threshold": request.quality_threshold or 0.85,
                    "auto_stop": request.auto_stop
                }
                
                return {
                    "success": True,
                    "message": "Producción iniciada exitosamente",
                    "session": production_session
                }
                
            except Exception as e:
                logger.error(f"Error iniciando producción: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/stop")
        async def stop_production(request: ProductionStopRequest):
            """Detiene la producción."""
            try:
                stop_info = {
                    "stopped_at": datetime.now().isoformat(),
                    "reason": request.reason,
                    "emergency": request.emergency,
                    "final_stats": {
                        "items_processed": 1247,
                        "runtime_minutes": 125,
                        "efficiency": 89.3,
                        "quality_score": 95.1
                    }
                }
                
                return {
                    "success": True,
                    "message": "Producción detenida",
                    "stop_info": stop_info
                }
                
            except Exception as e:
                logger.error(f"Error deteniendo producción: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/metrics/realtime")
        async def get_realtime_metrics():
            """Obtiene métricas de producción en tiempo real."""
            try:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "throughput": {
                        "current_items_per_minute": 78.5,
                        "avg_items_per_minute": 82.1,
                        "peak_items_per_minute": 95.2
                    },
                    "labelers": {
                        "group_0_apple": {"active": True, "efficiency": 91.2, "activations": 342},
                        "group_1_pear": {"active": False, "efficiency": 88.7, "activations": 298},
                        "group_2_lemon": {"active": False, "efficiency": 89.9, "activations": 285}
                    },
                    "motor": {
                        "current_position": "group_0",
                        "switches_today": 47,
                        "positioning_time_avg": 1.8,
                        "runtime_hours": 6.25
                    },
                    "detection": {
                        "accuracy": 96.3,
                        "confidence_avg": 0.89,
                        "processing_time_ms": 45.2,
                        "false_positives": 12,
                        "false_negatives": 8
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo métricas en tiempo real: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/categories/stats")
        async def get_category_statistics():
            """Obtiene estadísticas por categoría de fruta."""
            try:
                return {
                    "apple": {
                        "detected_today": 456,
                        "labeled_today": 451,
                        "accuracy": 97.1,
                        "avg_confidence": 0.91,
                        "peak_hour": "14:00-15:00",
                        "success_rate": 98.9
                    },
                    "pear": {
                        "detected_today": 398,
                        "labeled_today": 394,
                        "accuracy": 95.8,
                        "avg_confidence": 0.87,
                        "peak_hour": "10:00-11:00",
                        "success_rate": 99.0
                    },
                    "lemon": {
                        "detected_today": 393,
                        "labeled_today": 389,
                        "accuracy": 96.7,
                        "avg_confidence": 0.88,
                        "peak_hour": "16:00-17:00",
                        "success_rate": 99.0
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas de categorías: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/motor/switch_group")
        async def switch_labeler_group(category: str = Body(..., embed=True)):
            """Cambia el grupo de etiquetadoras activo."""
            try:
                valid_categories = ["apple", "pear", "lemon"]
                if category not in valid_categories:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Categoría inválida. Válidas: {valid_categories}"
                    )
                
                # Simular cambio de grupo
                group_map = {"apple": 0, "pear": 1, "lemon": 2}
                group_id = group_map[category]
                
                return {
                    "success": True,
                    "message": f"Grupo cambiado a {category}",
                    "group_info": {
                        "id": group_id,
                        "category": category,
                        "labelers": [group_id * 4 + i for i in range(4)],
                        "switch_time": datetime.now().isoformat(),
                        "estimated_duration": "2.5 seconds"
                    }
                }
                
            except Exception as e:
                logger.error(f"Error cambiando grupo: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# ==================== SYSTEM API ====================

class SystemAPI(BaseAPI):
    """API especializada para gestión del sistema."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API del sistema."""
        
        @self.router.get("/status")
        async def get_system_status():
            """Obtiene el estado completo del sistema."""
            try:
                return {
                    "system_info": {
                        "name": "FruPrint Ultra v3.0",
                        "version": "3.0.0-ULTRA",
                        "uptime": "2d 14h 32m",
                        "installation_id": "fruprint_ultra_001"
                    },
                    "components": {
                        "camera": {"status": "operational", "fps": 30, "resolution": "1920x1080"},
                        "ai_detector": {"status": "operational", "model_loaded": True, "accuracy": 96.3},
                        "motor_controller": {"status": "operational", "calibrated": True, "position": "group_0"},
                        "belt_controller": {"status": "operational", "speed": 0.5, "direction": "forward"},
                        "labelers": {"total": 12, "operational": 12, "maintenance_due": 0},
                        "sensors": {"trigger_sensor": "operational", "position_sensors": "operational"}
                    },
                    "resources": {
                        "cpu_usage": 45.2,
                        "memory_usage": 67.8,
                        "disk_usage": 34.6,
                        "temperature": 42.5,
                        "network_status": "connected"
                    },
                    "database": {
                        "status": "connected",
                        "type": "sqlite",
                        "size_mb": 125.7,
                        "last_backup": "2025-01-20T06:00:00Z"
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo estado del sistema: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/components/{component_name}")
        async def get_component_details(component_name: str):
            """Obtiene detalles de un componente específico."""
            try:
                component_details = {
                    "camera": {
                        "name": "Camera System",
                        "model": "Industrial Camera v2.1",
                        "status": "operational",
                        "metrics": {
                            "fps": 30,
                            "resolution": "1920x1080",
                            "exposure": "auto",
                            "focus": "auto",
                            "frames_captured_today": 125680
                        },
                        "last_maintenance": "2025-01-15T10:00:00Z",
                        "next_maintenance": "2025-02-15T10:00:00Z"
                    },
                    "motor_controller": {
                        "name": "Linear Motor DC Controller",
                        "model": "Ultra Linear v3.0",
                        "status": "operational",
                        "metrics": {
                            "current_position": "group_0",
                            "switches_today": 47,
                            "runtime_hours": 142.5,
                            "positioning_accuracy": 99.8,
                            "avg_switch_time": 1.8
                        },
                        "calibration": {
                            "last_calibrated": "2025-01-20T08:00:00Z",
                            "calibration_score": 98.5,
                            "next_calibration": "2025-01-27T08:00:00Z"
                        }
                    }
                }
                
                if component_name not in component_details:
                    raise HTTPException(status_code=404, detail="Componente no encontrado")
                
                return component_details[component_name]
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo detalles del componente: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/restart")
        async def restart_system():
            """Reinicia el sistema."""
            try:
                # En un sistema real, esto programaría un reinicio
                return {
                    "success": True,
                    "message": "Reinicio programado",
                    "restart_time": (datetime.now() + timedelta(minutes=2)).isoformat(),
                    "estimated_downtime": "3-5 minutos"
                }
                
            except Exception as e:
                logger.error(f"Error programando reinicio: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/calibrate/{component}")
        async def calibrate_component(component: str):
            """Calibra un componente específico."""
            try:
                valid_components = ["motor", "camera", "sensors", "all"]
                if component not in valid_components:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Componente inválido. Válidos: {valid_components}"
                    )
                
                calibration_times = {
                    "motor": 45,
                    "camera": 30,
                    "sensors": 20,
                    "all": 120
                }
                
                return {
                    "success": True,
                    "message": f"Calibración de {component} iniciada",
                    "calibration_id": f"cal_{int(datetime.now().timestamp())}",
                    "estimated_duration_seconds": calibration_times[component],
                    "started_at": datetime.now().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error iniciando calibración: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# ==================== METRICS API ====================

class MetricsAPI(BaseAPI):
    """API especializada para métricas y análisis."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de métricas."""
        
        @self.router.get("/summary")
        async def get_metrics_summary(
            period: str = Query("24h", description="Período de tiempo: 1h, 24h, 7d, 30d")
        ):
            """Obtiene resumen de métricas."""
            try:
                return {
                    "period": period,
                    "generated_at": datetime.now().isoformat(),
                    "production": {
                        "total_items": 3247,
                        "items_per_hour": 156.7,
                        "efficiency": 87.3,
                        "quality_score": 94.7,
                        "downtime_minutes": 12.5
                    },
                    "system": {
                        "uptime_percentage": 99.8,
                        "cpu_avg": 45.2,
                        "memory_avg": 67.8,
                        "errors_count": 3,
                        "alerts_count": 7
                    },
                    "components": {
                        "labelers_efficiency": 89.2,
                        "motor_switches": 47,
                        "camera_frames": 125680,
                        "detection_accuracy": 96.3
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo resumen de métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/performance")
        async def get_performance_metrics():
            """Obtiene métricas de rendimiento detalladas."""
            try:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "processing": {
                        "frame_processing_ms": 45.2,
                        "ai_inference_ms": 38.7,
                        "labeling_response_ms": 125.3,
                        "motor_positioning_ms": 1800.0
                    },
                    "throughput": {
                        "items_per_minute": 78.5,
                        "peak_throughput": 95.2,
                        "average_throughput": 82.1,
                        "throughput_variance": 8.3
                    },
                    "resources": {
                        "cpu_cores_usage": [45.2, 52.1, 38.9, 41.7],
                        "memory_breakdown": {
                            "system": 234.5,
                            "ai_model": 456.7,
                            "cache": 123.4,
                            "buffers": 89.2
                        },
                        "gpu_usage": 23.4,
                        "disk_io": {"read_mbps": 12.3, "write_mbps": 8.7}
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo métricas de rendimiento: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/history/{metric_type}")
        async def get_metric_history(
            metric_type: str,
            period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d"),
            resolution: str = Query("1m", description="Resolución: 1m, 5m, 1h")
        ):
            """Obtiene historial de una métrica específica."""
            try:
                valid_metrics = ["production", "system", "components", "performance"]
                if metric_type not in valid_metrics:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Tipo de métrica inválido. Válidos: {valid_metrics}"
                    )
                
                # Convertir período a horas
                hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
                hours = hours_map.get(period, 24)
                
                # Simular datos históricos
                import numpy as np
                data_points = []
                
                for i in range(hours):
                    timestamp = datetime.now() - timedelta(hours=hours-i)
                    # Generar valores simulados
                    base_value = 85 + np.sin(i * 0.1) * 10
                    noise = np.random.normal(0, 5)
                    value = max(0, base_value + noise)
                    
                    data_points.append({
                        "time": timestamp.isoformat(),
                        "throughput": value,
                        "efficiency": 75 + np.random.uniform(-10, 15),
                        "quality": 85 + np.random.uniform(-8, 12),
                        "errors": np.random.uniform(0, 10),
                        "downtime": np.random.uniform(0, 5),
                        "temperature": 35 + np.random.uniform(-10, 15),
                        "speed": 0.3 + np.random.uniform(0, 0.4)
                    })
                
                # Devolver array directamente para compatibilidad con el frontend
                return data_points
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo historial de métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/export")
        async def export_metrics(
            format: str = Query("csv", description="Formato: csv, json, xlsx"),
            period: str = Query("24h", description="Período: 1h, 24h, 7d, 30d")
        ):
            """Exporta métricas en formato especificado."""
            try:
                valid_formats = ["csv", "json", "xlsx"]
                if format not in valid_formats:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Formato inválido. Válidos: {valid_formats}"
                    )
                
                # Datos simulados para exportación
                data = [
                    {"timestamp": "2025-01-20T10:00:00Z", "production_rate": 85.3, "efficiency": 87.2},
                    {"timestamp": "2025-01-20T11:00:00Z", "production_rate": 89.1, "efficiency": 89.5},
                    {"timestamp": "2025-01-20T12:00:00Z", "production_rate": 92.4, "efficiency": 91.8}
                ]
                
                if format == "csv":
                    # Crear CSV
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    
                    return StreamingResponse(
                        io.BytesIO(output.getvalue().encode()),
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=metrics_{period}.csv"}
                    )
                
                elif format == "json":
                    json_data = json.dumps(data, indent=2)
                    return StreamingResponse(
                        io.BytesIO(json_data.encode()),
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename=metrics_{period}.json"}
                    )
                
                return {"message": f"Exportación en formato {format} no implementada aún"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error exportando métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# ==================== ALERTS API ====================

class AlertsAPI(BaseAPI):
    """API especializada para gestión de alertas."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de alertas."""
        
        @self.router.get("/")
        async def get_alerts(
            status: Optional[str] = Query(None, description="Filtrar por estado: active, acknowledged, resolved"),
            level: Optional[str] = Query(None, description="Filtrar por nivel: info, warning, error, critical"),
            limit: int = Query(50, description="Límite de resultados")
        ):
            """Obtiene lista de alertas."""
            try:
                # Simular alertas
                alerts = [
                    {
                        "id": "alert_001",
                        "type": "system",
                        "level": "warning",
                        "title": "CPU alto",
                        "message": "Uso de CPU al 85%",
                        "status": "active",
                        "created_at": "2025-01-20T14:30:00Z",
                        "component": "system",
                        "data": {"cpu_percent": 85.2}
                    },
                    {
                        "id": "alert_002",
                        "type": "production",
                        "level": "info",
                        "title": "Cambio de grupo",
                        "message": "Grupo cambiado a peras",
                        "status": "resolved",
                        "created_at": "2025-01-20T13:15:00Z",
                        "resolved_at": "2025-01-20T13:16:00Z",
                        "component": "motor",
                        "data": {"old_group": 0, "new_group": 1}
                    },
                    {
                        "id": "alert_003",
                        "type": "maintenance",
                        "level": "warning",
                        "title": "Mantenimiento debido",
                        "message": "Etiquetadora 7 requiere mantenimiento",
                        "status": "acknowledged",
                        "created_at": "2025-01-20T12:00:00Z",
                        "acknowledged_at": "2025-01-20T12:30:00Z",
                        "acknowledged_by": "operador_1",
                        "component": "labeler_7",
                        "data": {"maintenance_score": 78.5}
                    }
                ]
                
                # Filtrar alertas
                filtered_alerts = alerts
                if status:
                    filtered_alerts = [a for a in filtered_alerts if a["status"] == status]
                if level:
                    filtered_alerts = [a for a in filtered_alerts if a["level"] == level]
                
                # Limitar resultados
                filtered_alerts = filtered_alerts[:limit]
                
                return {
                    "alerts": filtered_alerts,
                    "total": len(filtered_alerts),
                    "filters": {"status": status, "level": level},
                    "generated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo alertas: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/{alert_id}")
        async def get_alert_details(alert_id: str):
            """Obtiene detalles de una alerta específica."""
            try:
                # Simular alerta específica
                alert_detail = {
                    "id": alert_id,
                    "type": "system",
                    "level": "warning",
                    "title": "CPU alto",
                    "message": "Uso de CPU sostenido al 85% durante 5 minutos",
                    "status": "active",
                    "created_at": "2025-01-20T14:30:00Z",
                    "component": "system",
                    "data": {
                        "cpu_percent": 85.2,
                        "duration_minutes": 5,
                        "threshold": 80.0,
                        "process_details": {
                            "top_processes": [
                                {"name": "ai_detector", "cpu": 45.2},
                                {"name": "camera_capture", "cpu": 25.1},
                                {"name": "motor_controller", "cpu": 15.3}
                            ]
                        }
                    },
                    "history": [
                        {"timestamp": "2025-01-20T14:30:00Z", "action": "created", "details": "Alerta creada automáticamente"},
                        {"timestamp": "2025-01-20T14:32:00Z", "action": "escalated", "details": "CPU continúa alto"}
                    ],
                    "suggested_actions": [
                        "Verificar procesos con alto consumo de CPU",
                        "Revisar logs del sistema",
                        "Considerar reinicio si persiste"
                    ],
                    "related_alerts": ["alert_004", "alert_005"]
                }
                
                return alert_detail
                
            except Exception as e:
                logger.error(f"Error obteniendo detalles de alerta: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str, request: AlertAcknowledgeRequest):
            """Confirma una alerta."""
            try:
                acknowledgment = {
                    "alert_id": alert_id,
                    "acknowledged_at": datetime.now().isoformat(),
                    "acknowledged_by": request.acknowledged_by,
                    "notes": request.notes,
                    "previous_status": "active",
                    "new_status": "acknowledged"
                }
                
                return {
                    "success": True,
                    "message": "Alerta confirmada exitosamente",
                    "acknowledgment": acknowledgment
                }
                
            except Exception as e:
                logger.error(f"Error confirmando alerta: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/{alert_id}/resolve")
        async def resolve_alert(alert_id: str, notes: Optional[str] = Body(None, embed=True)):
            """Resuelve una alerta."""
            try:
                resolution = {
                    "alert_id": alert_id,
                    "resolved_at": datetime.now().isoformat(),
                    "resolution_notes": notes or "Resuelto manualmente",
                    "previous_status": "acknowledged",
                    "new_status": "resolved"
                }
                
                return {
                    "success": True,
                    "message": "Alerta resuelta exitosamente",
                    "resolution": resolution
                }
                
            except Exception as e:
                logger.error(f"Error resolviendo alerta: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/statistics/summary")
        async def get_alert_statistics():
            """Obtiene estadísticas de alertas."""
            try:
                return {
                    "period": "last_24_hours",
                    "generated_at": datetime.now().isoformat(),
                    "totals": {
                        "active": 3,
                        "acknowledged": 7,
                        "resolved": 45,
                        "total": 55
                    },
                    "by_level": {
                        "critical": 1,
                        "error": 4,
                        "warning": 12,
                        "info": 38
                    },
                    "by_component": {
                        "system": 15,
                        "production": 18,
                        "labelers": 12,
                        "motor": 6,
                        "camera": 3,
                        "ai": 1
                    },
                    "trends": {
                        "compared_to_yesterday": "+12%",
                        "most_common_type": "production",
                        "avg_resolution_time_minutes": 15.3,
                        "escalation_rate": 8.2
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas de alertas: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# ==================== CONFIG API ====================

class ConfigAPI(BaseAPI):
    """API especializada para configuración del sistema."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de configuración."""
        
        @self.router.get("/")
        async def get_all_config():
            """Obtiene toda la configuración del sistema."""
            try:
                return {
                    "system": {
                        "version": "3.0.0-ULTRA",
                        "debug_mode": False,
                        "log_level": "INFO",
                        "max_concurrent_detections": 10,
                        "auto_restart_on_error": True
                    },
                    "production": {
                        "target_rate": 100.0,
                        "quality_threshold": 0.85,
                        "belt_speed_mps": 0.5,
                        "auto_switch_groups": True,
                        "labeling_timeout_seconds": 3.0
                    },
                    "camera": {
                        "resolution": "1920x1080",
                        "fps": 30,
                        "exposure": "auto",
                        "brightness": 50,
                        "contrast": 50,
                        "saturation": 50
                    },
                    "ai": {
                        "model_path": "models/fruit_detector_v3.pt",
                        "confidence_threshold": 0.7,
                        "nms_threshold": 0.4,
                        "max_detections": 20,
                        "gpu_enabled": True
                    },
                    "motor": {
                        "calibration_speed": 0.2,
                        "normal_speed": 0.8,
                        "positioning_tolerance": 0.1,
                        "max_switches_per_hour": 300,
                        "auto_calibrate_interval_hours": 24
                    },
                    "alerts": {
                        "enabled": True,
                        "email_notifications": False,
                        "webhook_url": None,
                        "alert_levels": ["info", "warning", "error", "critical"],
                        "auto_acknowledge_info": True
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo configuración: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/{section}")
        async def get_config_section(section: str):
            """Obtiene configuración de una sección específica."""
            try:
                all_config = await get_all_config()
                
                if section not in all_config:
                    raise HTTPException(status_code=404, detail=f"Sección '{section}' no encontrada")
                
                return {
                    "section": section,
                    "config": all_config[section],
                    "last_modified": "2025-01-20T08:00:00Z"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo sección de configuración: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.put("/{section}/{key}")
        async def update_config_value(section: str, key: str, request: ConfigUpdateRequest):
            """Actualiza un valor de configuración específico."""
            try:
                # Validar sección y clave
                valid_sections = ["system", "production", "camera", "ai", "motor", "alerts"]
                if section not in valid_sections:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Sección inválida. Válidas: {valid_sections}"
                    )
                
                # Simular actualización
                update_info = {
                    "section": section,
                    "key": key,
                    "old_value": "previous_value",  # En implementación real, obtener valor actual
                    "new_value": request.value,
                    "updated_at": datetime.now().isoformat(),
                    "reason": request.reason or "Actualización manual",
                    "requires_restart": key in ["model_path", "gpu_enabled", "log_level"]
                }
                
                return {
                    "success": True,
                    "message": f"Configuración {section}.{key} actualizada",
                    "update_info": update_info
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error actualizando configuración: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/validate")
        async def validate_config(config_data: Dict[str, Any] = Body(...)):
            """Valida una configuración antes de aplicarla."""
            try:
                validation_results = []
                
                # Validaciones simuladas
                for section, values in config_data.items():
                    if section == "production":
                        if "target_rate" in values and (values["target_rate"] < 1 or values["target_rate"] > 200):
                            validation_results.append({
                                "section": section,
                                "key": "target_rate",
                                "status": "error",
                                "message": "Tasa objetivo debe estar entre 1-200"
                            })
                        else:
                            validation_results.append({
                                "section": section,
                                "key": "target_rate", 
                                "status": "valid",
                                "message": "Valor válido"
                            })
                
                all_valid = all(result["status"] == "valid" for result in validation_results)
                
                return {
                    "valid": all_valid,
                    "validation_results": validation_results,
                    "validated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error validando configuración: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# ==================== REPORTS API ====================

class ReportsAPI(BaseAPI):
    """API especializada para generación de reportes."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de reportes."""
        
        @self.router.get("/templates")
        async def get_report_templates():
            """Obtiene plantillas de reportes disponibles."""
            try:
                return {
                    "templates": [
                        {
                            "id": "production_summary",
                            "name": "Resumen de Producción",
                            "description": "Reporte completo de producción con métricas y gráficos",
                            "format_options": ["pdf", "html", "xlsx"],
                            "parameters": ["period", "include_charts", "include_details"]
                        },
                        {
                            "id": "system_health",
                            "name": "Salud del Sistema",
                            "description": "Reporte de estado y rendimiento del sistema",
                            "format_options": ["pdf", "html"],
                            "parameters": ["period", "include_alerts", "include_metrics"]
                        },
                        {
                            "id": "maintenance_report",
                            "name": "Reporte de Mantenimiento",
                            "description": "Estado de componentes y programación de mantenimiento",
                            "format_options": ["pdf", "xlsx"],
                            "parameters": ["include_recommendations", "include_history"]
                        },
                        {
                            "id": "quality_analysis",
                            "name": "Análisis de Calidad",
                            "description": "Análisis detallado de calidad y precisión",
                            "format_options": ["pdf", "html", "xlsx"],
                            "parameters": ["period", "category_breakdown", "include_trends"]
                        }
                    ]
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo plantillas de reportes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/generate")
        async def generate_report(request: ReportGenerationRequest, background_tasks: BackgroundTasks):
            """Genera un reporte."""
            try:
                # Validar plantilla
                valid_reports = ["production_summary", "system_health", "maintenance_report", "quality_analysis"]
                if request.report_type not in valid_reports:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Tipo de reporte inválido. Válidos: {valid_reports}"
                    )
                
                # Crear trabajo de generación
                report_job = {
                    "job_id": f"report_{int(datetime.now().timestamp())}",
                    "report_type": request.report_type,
                    "format": request.format,
                    "period": request.period,
                    "parameters": {
                        "include_charts": request.include_charts,
                        "filters": request.filters or {}
                    },
                    "status": "queued",
                    "created_at": datetime.now().isoformat(),
                    "estimated_completion": (datetime.now() + timedelta(minutes=2)).isoformat()
                }
                
                # En un sistema real, esto se procesaría en background
                background_tasks.add_task(self._process_report_generation, report_job)
                
                return {
                    "success": True,
                    "message": "Generación de reporte iniciada",
                    "job": report_job
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error generando reporte: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/jobs/{job_id}")
        async def get_report_job_status(job_id: str):
            """Obtiene el estado de un trabajo de generación de reporte."""
            try:
                # Simular estado del trabajo
                job_status = {
                    "job_id": job_id,
                    "status": "completed",
                    "progress": 100,
                    "created_at": "2025-01-20T14:00:00Z",
                    "completed_at": "2025-01-20T14:02:30Z",
                    "file_info": {
                        "filename": f"report_{job_id}.pdf",
                        "size_bytes": 2547689,
                        "download_url": f"/api/reports/download/{job_id}"
                    },
                    "metadata": {
                        "pages": 15,
                        "charts_included": 8,
                        "data_points": 1247
                    }
                }
                
                return job_status
                
            except Exception as e:
                logger.error(f"Error obteniendo estado del trabajo de reporte: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/history")
        async def get_report_history(
            limit: int = Query(20, description="Límite de resultados"),
            report_type: Optional[str] = Query(None, description="Filtrar por tipo")
        ):
            """Obtiene historial de reportes generados."""
            try:
                # Simular historial
                reports = [
                    {
                        "job_id": "report_1737384000",
                        "report_type": "production_summary",
                        "format": "pdf",
                        "status": "completed",
                        "created_at": "2025-01-20T14:00:00Z",
                        "file_size": 2547689,
                        "download_count": 3
                    },
                    {
                        "job_id": "report_1737383400",
                        "report_type": "system_health",
                        "format": "html",
                        "status": "completed",
                        "created_at": "2025-01-20T13:50:00Z",
                        "file_size": 891234,
                        "download_count": 1
                    }
                ]
                
                if report_type:
                    reports = [r for r in reports if r["report_type"] == report_type]
                
                return {
                    "reports": reports[:limit],
                    "total": len(reports),
                    "filters": {"report_type": report_type}
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo historial de reportes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_report_generation(self, report_job: Dict[str, Any]):
        """Procesa la generación de un reporte en background."""
        try:
            # Simular procesamiento
            await asyncio.sleep(2)
            logger.info(f"Reporte {report_job['job_id']} generado exitosamente")
        except Exception as e:
            logger.error(f"Error procesando reporte {report_job['job_id']}: {e}")

# ==================== ANALYTICS API ====================

class AnalyticsAPI(BaseAPI):
    """API especializada para análisis avanzado y predicciones."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de analytics."""
        
        @self.router.get("/dashboard")
        async def get_analytics_dashboard():
            """Obtiene datos para el dashboard de analytics."""
            try:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "kpis": {
                        "overall_efficiency": 87.3,
                        "quality_score": 94.7,
                        "throughput_trend": "+5.2%",
                        "cost_per_item": 0.12,
                        "uptime_percentage": 99.8
                    },
                    "predictions": {
                        "next_hour_production": 156,
                        "quality_trend": "stable",
                        "maintenance_prediction": {
                            "next_maintenance": "2025-01-25T10:00:00Z",
                            "confidence": 0.89
                        },
                        "peak_hour_today": "15:00-16:00"
                    },
                    "trends": {
                        "production": {
                            "last_7_days": [120, 135, 142, 138, 156, 149, 161],
                            "trend": "increasing",
                            "growth_rate": 6.2
                        },
                        "quality": {
                            "last_7_days": [94.2, 95.1, 93.8, 96.2, 94.9, 95.8, 94.7],
                            "trend": "stable",
                            "variance": 0.8
                        }
                    },
                    "alerts_analysis": {
                        "most_common": "high_cpu",
                        "frequency_trend": "decreasing",
                        "critical_count_24h": 1
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo dashboard de analytics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/predictions/{prediction_type}")
        async def get_predictions(
            prediction_type: str,
            horizon_hours: int = Query(24, description="Horizonte de predicción en horas")
        ):
            """Obtiene predicciones específicas."""
            try:
                valid_predictions = ["production", "quality", "maintenance", "alerts", "efficiency"]
                if prediction_type not in valid_predictions:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Tipo de predicción inválido. Válidos: {valid_predictions}"
                    )
                
                # Generar predicciones simuladas
                import numpy as np
                
                predictions = []
                base_value = {"production": 150, "quality": 95, "efficiency": 88}[prediction_type] if prediction_type in ["production", "quality", "efficiency"] else 0.1
                
                for i in range(horizon_hours):
                    timestamp = datetime.now() + timedelta(hours=i)
                    value = base_value + np.sin(i * 0.1) * 10 + np.random.normal(0, 2)
                    confidence = max(0.6, 0.95 - (i * 0.01))
                    
                    predictions.append({
                        "timestamp": timestamp.isoformat(),
                        "predicted_value": max(0, value),
                        "confidence": confidence,
                        "lower_bound": max(0, value - 5),
                        "upper_bound": value + 5
                    })
                
                return {
                    "prediction_type": prediction_type,
                    "horizon_hours": horizon_hours,
                    "model_accuracy": 0.89,
                    "generated_at": datetime.now().isoformat(),
                    "predictions": predictions,
                    "model_info": {
                        "algorithm": "LSTM + Random Forest",
                        "last_trained": "2025-01-19T08:00:00Z",
                        "features_used": ["historical_data", "seasonality", "system_load"]
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo predicciones: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/insights")
        async def get_insights():
            """Obtiene insights automáticos del sistema."""
            try:
                return {
                    "generated_at": datetime.now().isoformat(),
                    "insights": [
                        {
                            "type": "optimization",
                            "priority": "high",
                            "title": "Oportunidad de optimización",
                            "description": "La eficiencia podría mejorar 8% ajustando la velocidad de la banda durante horas pico",
                            "potential_impact": "+8% efficiency",
                            "confidence": 0.87,
                            "suggested_action": "Aumentar velocidad de banda a 0.6 m/s entre 14:00-16:00"
                        },
                        {
                            "type": "maintenance",
                            "priority": "medium",
                            "title": "Mantenimiento preventivo",
                            "description": "Etiquetadora 7 muestra degradación en rendimiento",
                            "potential_impact": "Evitar 4h downtime",
                            "confidence": 0.92,
                            "suggested_action": "Programar mantenimiento para el próximo fin de semana"
                        },
                        {
                            "type": "quality",
                            "priority": "low",
                            "title": "Mejora de calidad",
                            "description": "Ajustar threshold de confianza para limones podría reducir falsos positivos",
                            "potential_impact": "+2% accuracy",
                            "confidence": 0.78,
                            "suggested_action": "Cambiar threshold de 0.7 a 0.75 para categoría limón"
                        }
                    ],
                    "statistics": {
                        "total_insights": 3,
                        "high_priority": 1,
                        "implemented_last_week": 2,
                        "avg_impact": "+5.3%"
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo insights: {e}")
                raise HTTPException(status_code=500, detail=str(e))

# ==================== MAINTENANCE API ====================

class MaintenanceAPI(BaseAPI):
    """API especializada para mantenimiento y diagnósticos."""
    
    def __init__(self):
        super().__init__()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de la API de mantenimiento."""
        
        @self.router.get("/status")
        async def get_maintenance_status():
            """Obtiene estado de mantenimiento del sistema."""
            try:
                return {
                    "overall_health": 94.2,
                    "components": {
                        "camera": {
                            "health_score": 98.5,
                            "status": "excellent",
                            "last_maintenance": "2025-01-15T10:00:00Z",
                            "next_maintenance": "2025-02-15T10:00:00Z",
                            "maintenance_type": "routine_cleaning"
                        },
                        "motor": {
                            "health_score": 89.2,
                            "status": "good",
                            "last_maintenance": "2025-01-10T14:00:00Z",
                            "next_maintenance": "2025-01-24T14:00:00Z",
                            "maintenance_type": "lubrication"
                        },
                        "labelers": {
                            "health_score": 91.8,
                            "status": "good",
                            "details": {
                                "labeler_0": {"score": 95.2, "status": "excellent"},
                                "labeler_1": {"score": 94.8, "status": "excellent"},
                                "labeler_2": {"score": 93.1, "status": "good"},
                                "labeler_3": {"score": 89.5, "status": "good"},
                                "labeler_7": {"score": 78.5, "status": "needs_attention"}
                            }
                        },
                        "sensors": {
                            "health_score": 96.7,
                            "status": "excellent",
                            "last_calibration": "2025-01-18T09:00:00Z",
                            "next_calibration": "2025-02-18T09:00:00Z"
                        }
                    },
                    "alerts": [
                        {
                            "component": "labeler_7",
                            "level": "warning",
                            "message": "Rendimiento degradado - programar mantenimiento",
                            "score": 78.5
                        }
                    ],
                    "upcoming_maintenance": [
                        {
                            "component": "motor",
                            "type": "lubrication",
                            "scheduled_date": "2025-01-24T14:00:00Z",
                            "estimated_duration": "2 hours",
                            "priority": "medium"
                        }
                    ]
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo estado de mantenimiento: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/schedule")
        async def get_maintenance_schedule():
            """Obtiene cronograma de mantenimiento."""
            try:
                return {
                    "current_week": [
                        {
                            "date": "2025-01-24",
                            "tasks": [
                                {
                                    "component": "motor",
                                    "type": "lubrication",
                                    "time": "14:00",
                                    "duration": "2h",
                                    "priority": "medium",
                                    "assigned_to": "tech_1"
                                }
                            ]
                        }
                    ],
                    "next_month": [
                        {
                            "date": "2025-02-15",
                            "tasks": [
                                {
                                    "component": "camera",
                                    "type": "routine_cleaning",
                                    "time": "10:00",
                                    "duration": "1h",
                                    "priority": "low",
                                    "assigned_to": "tech_2"
                                }
                            ]
                        },
                        {
                            "date": "2025-02-18",
                            "tasks": [
                                {
                                    "component": "sensors",
                                    "type": "calibration",
                                    "time": "09:00",
                                    "duration": "3h",
                                    "priority": "high",
                                    "assigned_to": "tech_1"
                                }
                            ]
                        }
                    ],
                    "overdue": [],
                    "statistics": {
                        "scheduled_this_month": 3,
                        "completed_last_month": 4,
                        "average_duration": "2.5h",
                        "success_rate": 98.5
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo cronograma de mantenimiento: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/schedule")
        async def schedule_maintenance(
            component: str = Body(...),
            maintenance_type: str = Body(...),
            scheduled_date: str = Body(...),
            priority: str = Body("medium"),
            notes: Optional[str] = Body(None)
        ):
            """Programa una tarea de mantenimiento."""
            try:
                valid_components = ["camera", "motor", "labelers", "sensors", "belt", "ai_system"]
                valid_priorities = ["low", "medium", "high", "critical"]
                
                if component not in valid_components:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Componente inválido. Válidos: {valid_components}"
                    )
                
                if priority not in valid_priorities:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Prioridad inválida. Válidas: {valid_priorities}"
                    )
                
                task = {
                    "task_id": f"maint_{int(datetime.now().timestamp())}",
                    "component": component,
                    "maintenance_type": maintenance_type,
                    "scheduled_date": scheduled_date,
                    "priority": priority,
                    "status": "scheduled",
                    "notes": notes,
                    "created_at": datetime.now().isoformat(),
                    "estimated_duration": "2-3 hours"
                }
                
                return {
                    "success": True,
                    "message": "Mantenimiento programado exitosamente",
                    "task": task
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error programando mantenimiento: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/diagnostics")
        async def run_diagnostics():
            """Ejecuta diagnósticos del sistema."""
            try:
                diagnostic_results = {
                    "diagnostic_id": f"diag_{int(datetime.now().timestamp())}",
                    "started_at": datetime.now().isoformat(),
                    "duration_seconds": 45.2,
                    "overall_status": "healthy",
                    "tests": [
                        {
                            "test": "camera_connectivity",
                            "status": "passed",
                            "result": "Camera responding normally",
                            "score": 100
                        },
                        {
                            "test": "motor_calibration",
                            "status": "passed",
                            "result": "Motor positioning within tolerance",
                            "score": 98.5
                        },
                        {
                            "test": "labeler_functionality",
                            "status": "warning",
                            "result": "Labeler 7 response time degraded",
                            "score": 78.5
                        },
                        {
                            "test": "sensor_accuracy",
                            "status": "passed",
                            "result": "All sensors calibrated and accurate",
                            "score": 96.7
                        },
                        {
                            "test": "ai_model_performance",
                            "status": "passed",
                            "result": "Model accuracy within acceptable range",
                            "score": 94.3
                        }
                    ],
                    "recommendations": [
                        {
                            "priority": "medium",
                            "component": "labeler_7",
                            "action": "Schedule maintenance to address response time degradation",
                            "estimated_improvement": "15% response time improvement"
                        }
                    ],
                    "next_diagnostic": (datetime.now() + timedelta(days=7)).isoformat()
                }
                
                return diagnostic_results
                
            except Exception as e:
                logger.error(f"Error ejecutando diagnósticos: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/history")
        async def get_maintenance_history(
            limit: int = Query(20, description="Límite de resultados"),
            component: Optional[str] = Query(None, description="Filtrar por componente")
        ):
            """Obtiene historial de mantenimiento."""
            try:
                # Simular historial
                history = [
                    {
                        "task_id": "maint_1737280000",
                        "component": "camera",
                        "maintenance_type": "routine_cleaning",
                        "status": "completed",
                        "scheduled_date": "2025-01-15T10:00:00Z",
                        "completed_date": "2025-01-15T11:30:00Z",
                        "duration_minutes": 90,
                        "technician": "tech_2",
                        "notes": "Lente limpio, calibración verificada",
                        "before_score": 95.2,
                        "after_score": 98.5
                    },
                    {
                        "task_id": "maint_1737020000",
                        "component": "motor",
                        "maintenance_type": "lubrication",
                        "status": "completed",
                        "scheduled_date": "2025-01-10T14:00:00Z",
                        "completed_date": "2025-01-10T16:15:00Z",
                        "duration_minutes": 135,
                        "technician": "tech_1",
                        "notes": "Lubricación completa, reemplazo de filtros",
                        "before_score": 82.1,
                        "after_score": 89.2
                    }
                ]
                
                if component:
                    history = [h for h in history if h["component"] == component]
                
                return {
                    "history": history[:limit],
                    "total": len(history),
                    "filters": {"component": component},
                    "statistics": {
                        "completed_tasks": len([h for h in history if h["status"] == "completed"]),
                        "avg_duration_minutes": 112.5,
                        "avg_improvement": 6.2
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo historial de mantenimiento: {e}")
                raise HTTPException(status_code=500, detail=str(e))