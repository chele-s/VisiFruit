# health_monitor.py
"""
Sistema de Monitoreo de Salud Proactivo FruPrint v4.0
=====================================================

Sistema de monitoreo continuo de salud del sistema con alertas
proactivas, diagnóstico automático y recomendaciones.

Características:
- Monitoreo continuo de componentes críticos
- Detección temprana de problemas
- Alertas proactivas antes de fallos
- Diagnóstico automático
- Recomendaciones de mantenimiento
- Score de salud del sistema

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Septiembre 2025
Versión: 4.0 - MODULAR ARCHITECTURE
"""

import asyncio
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ComponentStatus(Enum):
    """Estado de componentes del sistema."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class HealthCheckResult:
    """Resultado de verificación de salud."""
    component: str
    status: ComponentStatus
    score: float  # 0-100
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

class SystemHealthMonitor:
    """Monitor de salud del sistema con checks proactivos."""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheckResult] = {}
        self.monitoring = False
        self.check_interval = 30  # segundos
        
        # Umbrales
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "temperature_c": 75,
            "error_rate": 0.05,
            "throughput_min": 10
        }
    
    async def start_monitoring(self):
        """Inicia el monitoreo continuo."""
        self.monitoring = True
        logger.info("🏥 Monitor de salud iniciado")
        
        while self.monitoring:
            try:
                await self._run_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en monitoreo de salud: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Detiene el monitoreo."""
        self.monitoring = False
        logger.info("🛑 Monitor de salud detenido")
    
    async def _run_health_checks(self):
        """Ejecuta todas las verificaciones de salud."""
        checks = [
            self._check_system_resources(),
            self._check_disk_space(),
            self._check_process_health(),
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, HealthCheckResult):
                self.health_checks[result.component] = result
                
                # Alertar si hay problemas
                if result.status in (ComponentStatus.WARNING, ComponentStatus.CRITICAL):
                    logger.warning(f"⚠️ {result.component}: {result.message}")
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Verifica recursos del sistema (CPU, RAM)."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Calcular score
            cpu_score = max(0, 100 - cpu_percent)
            memory_score = max(0, 100 - memory.percent)
            overall_score = (cpu_score + memory_score) / 2
            
            # Determinar estado
            if overall_score > 70:
                status = ComponentStatus.HEALTHY
            elif overall_score > 50:
                status = ComponentStatus.WARNING
            else:
                status = ComponentStatus.CRITICAL
            
            recommendations = []
            if cpu_percent > self.thresholds["cpu_percent"]:
                recommendations.append("Considerar reducir carga de procesamiento")
            if memory.percent > self.thresholds["memory_percent"]:
                recommendations.append("Liberar memoria o agregar más RAM")
            
            return HealthCheckResult(
                component="system_resources",
                status=status,
                score=overall_score,
                message=f"CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}%",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / (1024**2)
                },
                recommendations=recommendations
            )
        except Exception as e:
            return HealthCheckResult(
                component="system_resources",
                status=ComponentStatus.OFFLINE,
                score=0,
                message=f"Error: {e}"
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Verifica espacio en disco."""
        try:
            disk = psutil.disk_usage('/')
            score = max(0, 100 - disk.percent)
            
            if disk.percent < 70:
                status = ComponentStatus.HEALTHY
            elif disk.percent < 85:
                status = ComponentStatus.WARNING
            else:
                status = ComponentStatus.CRITICAL
            
            recommendations = []
            if disk.percent > self.thresholds["disk_percent"]:
                recommendations.append("Liberar espacio en disco urgentemente")
                recommendations.append("Considerar limpiar logs y backups antiguos")
            
            return HealthCheckResult(
                component="disk_space",
                status=status,
                score=score,
                message=f"Disco: {disk.percent:.1f}% usado",
                details={
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": disk.percent
                },
                recommendations=recommendations
            )
        except Exception as e:
            return HealthCheckResult(
                component="disk_space",
                status=ComponentStatus.OFFLINE,
                score=0,
                message=f"Error: {e}"
            )
    
    async def _check_process_health(self) -> HealthCheckResult:
        """Verifica salud del proceso actual."""
        try:
            import os
            process = psutil.Process(os.getpid())
            
            # Información del proceso
            with process.oneshot():
                cpu_percent = process.cpu_percent(interval=0.5)
                memory_info = process.memory_info()
                num_threads = process.num_threads()
            
            # Score basado en uso de recursos del proceso
            score = 100 - min(cpu_percent, 100)
            
            status = ComponentStatus.HEALTHY if score > 70 else ComponentStatus.WARNING
            
            return HealthCheckResult(
                component="process_health",
                status=status,
                score=score,
                message=f"Proceso saludable: {num_threads} threads",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_info.rss / (1024**2),
                    "num_threads": num_threads
                }
            )
        except Exception as e:
            return HealthCheckResult(
                component="process_health",
                status=ComponentStatus.OFFLINE,
                score=0,
                message=f"Error: {e}"
            )
    
    def get_overall_health_score(self) -> float:
        """Calcula el score general de salud."""
        if not self.health_checks:
            return 100.0
        
        scores = [check.score for check in self.health_checks.values()]
        return sum(scores) / len(scores) if scores else 100.0
    
    def get_health_report(self) -> Dict[str, Any]:
        """Genera reporte de salud completo."""
        overall_score = self.get_overall_health_score()
        
        critical_issues = [
            check for check in self.health_checks.values()
            if check.status == ComponentStatus.CRITICAL
        ]
        
        warnings = [
            check for check in self.health_checks.values()
            if check.status == ComponentStatus.WARNING
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(overall_score, 2),
            "overall_status": self._get_overall_status(overall_score),
            "critical_issues": len(critical_issues),
            "warnings": len(warnings),
            "component_checks": {
                name: {
                    "status": check.status.value,
                    "score": round(check.score, 2),
                    "message": check.message,
                    "recommendations": check.recommendations
                }
                for name, check in self.health_checks.items()
            }
        }
    
    def _get_overall_status(self, score: float) -> str:
        """Determina el estado general basado en el score."""
        if score > 80:
            return "excellent"
        elif score > 60:
            return "good"
        elif score > 40:
            return "fair"
        else:
            return "poor"

__all__ = ['SystemHealthMonitor', 'HealthCheckResult', 'ComponentStatus']
