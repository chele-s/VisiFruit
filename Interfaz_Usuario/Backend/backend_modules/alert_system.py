"""
Sistema Ultra-Avanzado de Alertas Multinivel
==========================================

Sistema completo de gestión de alertas con:
- Alertas multinivel (INFO, WARNING, ERROR, CRITICAL, EMERGENCY)
- Escalado automático de alertas
- Notificaciones en tiempo real vía WebSocket
- Agregación inteligente de alertas similares
- Sistema de ACK y resolución
- Integración con sistemas externos (email, Slack, etc.)
- Dashboard de alertas en tiempo real
- Análisis de patrones de alertas

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import sqlite3
import hashlib
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger("UltraAlertSystem")

class AlertLevel(Enum):
    """Niveles de alerta del sistema."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    """Estados de una alerta."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class AlertCategory(Enum):
    """Categorías de alertas."""
    SYSTEM = "system"
    PRODUCTION = "production"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER = "user"

@dataclass
class UltraAlert:
    """Alerta ultra-avanzada del sistema."""
    id: str = field(default_factory=lambda: hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12])
    timestamp: datetime = field(default_factory=datetime.now)
    level: AlertLevel = AlertLevel.INFO
    category: AlertCategory = AlertCategory.SYSTEM
    component: str = ""
    title: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    count: int = 1
    first_occurrence: datetime = field(default_factory=datetime.now)
    last_occurrence: datetime = field(default_factory=datetime.now)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    escalated: bool = False
    escalation_count: int = 0
    tags: List[str] = field(default_factory=list)
    related_alerts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la alerta a diccionario."""
        data = asdict(self)
        # Convertir enums a strings
        data['level'] = self.level.value
        data['category'] = self.category.value
        data['status'] = self.status.value
        # Convertir datetimes a ISO format
        data['timestamp'] = self.timestamp.isoformat()
        data['first_occurrence'] = self.first_occurrence.isoformat()
        data['last_occurrence'] = self.last_occurrence.isoformat()
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

@dataclass
class AlertRule:
    """Regla de alerta configurable."""
    name: str
    condition: str  # Expresión que se evalúa
    level: AlertLevel
    category: AlertCategory
    message_template: str
    cooldown_minutes: int = 5
    escalation_minutes: int = 30
    enabled: bool = True
    tags: List[str] = field(default_factory=list)

class UltraAlertSystem:
    """Sistema ultra-avanzado de gestión de alertas."""
    
    def __init__(self):
        self.alerts = {}  # ID -> UltraAlert
        self.alert_history = deque(maxlen=10000)
        self.alert_rules = {}
        self.notification_channels = {}
        self.escalation_rules = {}
        self.aggregation_rules = {}
        self.db_path = "data/alerts.db"
        self.is_running = False
        
        # Callbacks para notificaciones
        self.alert_callbacks: List[Callable] = []
        self.websocket_callbacks: List[Callable] = []
        
        # Configuración de notificaciones
        self.email_config = {
            "enabled": False,
            "smtp_server": "",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_email": ""
        }
        
        # Estadísticas en tiempo real
        self.stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "alerts_by_level": defaultdict(int),
            "alerts_by_category": defaultdict(int),
            "top_components": defaultdict(int),
            "resolution_time_avg": 0.0
        }
        
        # Buffer para agregación de alertas similares
        self.aggregation_buffer = defaultdict(list)
        self.last_cleanup = time.time()

    async def initialize(self):
        """Inicializa el sistema de alertas."""
        try:
            # Crear base de datos
            await self._init_database()
            
            # Cargar reglas de alerta
            await self._load_alert_rules()
            
            # Cargar configuración de notificaciones
            await self._load_notification_config()
            
            # Cargar alertas activas
            await self._load_active_alerts()
            
            # Iniciar tareas de background
            await self._start_background_tasks()
            
            self.is_running = True
            logger.info("✅ Sistema de alertas inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema de alertas: {e}")
            raise

    async def _init_database(self):
        """Inicializa la base de datos de alertas."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla principal de alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                level TEXT,
                category TEXT,
                component TEXT,
                title TEXT,
                message TEXT,
                details TEXT,
                status TEXT,
                count INTEGER,
                first_occurrence DATETIME,
                last_occurrence DATETIME,
                acknowledged_by TEXT,
                acknowledged_at DATETIME,
                resolved_by TEXT,
                resolved_at DATETIME,
                escalated BOOLEAN,
                escalation_count INTEGER,
                tags TEXT,
                related_alerts TEXT
            )
        """)
        
        # Tabla de reglas de alerta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                name TEXT PRIMARY KEY,
                condition_expr TEXT,
                level TEXT,
                category TEXT,
                message_template TEXT,
                cooldown_minutes INTEGER,
                escalation_minutes INTEGER,
                enabled BOOLEAN,
                tags TEXT
            )
        """)
        
        # Tabla de notificaciones enviadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT,
                channel TEXT,
                timestamp DATETIME,
                status TEXT,
                details TEXT,
                FOREIGN KEY (alert_id) REFERENCES alerts (id)
            )
        """)
        
        # Índices para rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_category ON alerts(category)")
        
        conn.commit()
        conn.close()

    async def _load_alert_rules(self):
        """Carga reglas de alerta desde la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM alert_rules WHERE enabled = 1")
            
            for row in cursor.fetchall():
                rule = AlertRule(
                    name=row[0],
                    condition=row[1],
                    level=AlertLevel(row[2]),
                    category=AlertCategory(row[3]),
                    message_template=row[4],
                    cooldown_minutes=row[5],
                    escalation_minutes=row[6],
                    enabled=bool(row[7]),
                    tags=json.loads(row[8]) if row[8] else []
                )
                self.alert_rules[rule.name] = rule
            
            conn.close()
            logger.info(f"Cargadas {len(self.alert_rules)} reglas de alerta")
            
        except Exception as e:
            logger.error(f"Error cargando reglas de alerta: {e}")

    async def _load_notification_config(self):
        """Carga configuración de notificaciones."""
        try:
            with open("data/notification_config.json", "r") as f:
                config = json.load(f)
                self.email_config.update(config.get("email", {}))
                
        except FileNotFoundError:
            logger.info("No se encontró configuración de notificaciones")

    async def _load_active_alerts(self):
        """Carga alertas activas desde la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM alerts 
                WHERE status IN ('active', 'acknowledged')
                ORDER BY timestamp DESC
            """)
            
            for row in cursor.fetchall():
                alert = UltraAlert(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    level=AlertLevel(row[2]),
                    category=AlertCategory(row[3]),
                    component=row[4],
                    title=row[5],
                    message=row[6],
                    details=json.loads(row[7]) if row[7] else {},
                    status=AlertStatus(row[8]),
                    count=row[9],
                    first_occurrence=datetime.fromisoformat(row[10]),
                    last_occurrence=datetime.fromisoformat(row[11]),
                    acknowledged_by=row[12],
                    acknowledged_at=datetime.fromisoformat(row[13]) if row[13] else None,
                    resolved_by=row[14],
                    resolved_at=datetime.fromisoformat(row[15]) if row[15] else None,
                    escalated=bool(row[16]),
                    escalation_count=row[17],
                    tags=json.loads(row[18]) if row[18] else [],
                    related_alerts=json.loads(row[19]) if row[19] else []
                )
                self.alerts[alert.id] = alert
            
            conn.close()
            logger.info(f"Cargadas {len(self.alerts)} alertas activas")
            
        except Exception as e:
            logger.error(f"Error cargando alertas activas: {e}")

    async def _start_background_tasks(self):
        """Inicia tareas de background."""
        asyncio.create_task(self._escalation_monitor())
        asyncio.create_task(self._aggregation_processor())
        asyncio.create_task(self._stats_updater())
        asyncio.create_task(self._cleanup_task())

    async def create_alert(self, component: str, alert_type: str, message: str, 
                         details: Optional[Dict[str, Any]] = None,
                         level: AlertLevel = AlertLevel.INFO,
                         category: AlertCategory = AlertCategory.SYSTEM) -> UltraAlert:
        """Crea una nueva alerta."""
        try:
            # Verificar si es una alerta duplicada reciente
            alert_key = f"{component}:{alert_type}:{message}"
            existing_alert = await self._find_similar_alert(alert_key, 300)  # 5 minutos
            
            if existing_alert:
                # Incrementar contador y actualizar timestamp
                existing_alert.count += 1
                existing_alert.last_occurrence = datetime.now()
                await self._save_alert(existing_alert)
                return existing_alert
            
            # Crear nueva alerta
            alert = UltraAlert(
                level=level,
                category=category,
                component=component,
                title=alert_type.replace("_", " ").title(),
                message=message,
                details=details or {},
                tags=[component, alert_type]
            )
            
            # Guardar en memoria y base de datos
            self.alerts[alert.id] = alert
            await self._save_alert(alert)
            
            # Añadir al historial
            self.alert_history.append(alert)
            
            # Procesar notificaciones
            await self._process_notifications(alert)
            
            # Actualizar estadísticas
            await self._update_stats(alert)
            
            # Notificar a callbacks
            await self._notify_callbacks(alert)
            
            logger.info(f"🚨 Nueva alerta {level.value}: {component} - {message}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creando alerta: {e}")
            raise

    async def _find_similar_alert(self, alert_key: str, window_seconds: int) -> Optional[UltraAlert]:
        """Busca alertas similares en la ventana de tiempo especificada."""
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        
        for alert in self.alerts.values():
            if (alert.status == AlertStatus.ACTIVE and 
                alert.last_occurrence >= cutoff_time):
                
                existing_key = f"{alert.component}:{alert.title.lower().replace(' ', '_')}:{alert.message}"
                if existing_key == alert_key:
                    return alert
        
        return None

    async def _save_alert(self, alert: UltraAlert):
        """Guarda una alerta en la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO alerts 
                (id, timestamp, level, category, component, title, message, details,
                 status, count, first_occurrence, last_occurrence, acknowledged_by,
                 acknowledged_at, resolved_by, resolved_at, escalated, escalation_count,
                 tags, related_alerts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.timestamp.isoformat(),
                alert.level.value,
                alert.category.value,
                alert.component,
                alert.title,
                alert.message,
                json.dumps(alert.details),
                alert.status.value,
                alert.count,
                alert.first_occurrence.isoformat(),
                alert.last_occurrence.isoformat(),
                alert.acknowledged_by,
                alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                alert.resolved_by,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                alert.escalated,
                alert.escalation_count,
                json.dumps(alert.tags),
                json.dumps(alert.related_alerts)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Confirma recepción de una alerta."""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            
            await self._save_alert(alert)
            await self._notify_callbacks(alert)
            
            logger.info(f"✅ Alerta {alert_id} confirmada por {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirmando alerta: {e}")
            return False

    async def resolve_alert(self, alert_id: str, resolved_by: str, resolution_note: str = "") -> bool:
        """Resuelve una alerta."""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_by = resolved_by
            alert.resolved_at = datetime.now()
            
            if resolution_note:
                alert.details["resolution_note"] = resolution_note
            
            await self._save_alert(alert)
            await self._notify_callbacks(alert)
            
            # Remover de alertas activas
            del self.alerts[alert_id]
            
            logger.info(f"✅ Alerta {alert_id} resuelta por {resolved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolviendo alerta: {e}")
            return False

    async def _process_notifications(self, alert: UltraAlert):
        """Procesa notificaciones para una alerta."""
        try:
            # Notificación por email para alertas críticas
            if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                await self._send_email_notification(alert)
            
            # Notificación WebSocket en tiempo real
            await self._send_websocket_notification(alert)
            
            # Log de la notificación
            await self._log_notification(alert.id, "processed", "all_channels")
            
        except Exception as e:
            logger.error(f"Error procesando notificaciones: {e}")

    async def _send_email_notification(self, alert: UltraAlert):
        """Envía notificación por email."""
        if not self.email_config["enabled"]:
            return
        
        try:
            # Crear mensaje
            msg = MimeMultipart()
            msg['From'] = self.email_config["from_email"]
            msg['To'] = "admin@fruprint.com"  # Configurar destinatarios
            msg['Subject'] = f"🚨 ALERTA {alert.level.value.upper()}: {alert.title}"
            
            body = f"""
            <h2>Alerta del Sistema FruPrint</h2>
            <p><strong>Nivel:</strong> {alert.level.value.upper()}</p>
            <p><strong>Componente:</strong> {alert.component}</p>
            <p><strong>Mensaje:</strong> {alert.message}</p>
            <p><strong>Timestamp:</strong> {alert.timestamp.isoformat()}</p>
            <p><strong>Detalles:</strong></p>
            <pre>{json.dumps(alert.details, indent=2)}</pre>
            """
            
            msg.attach(MimeText(body, 'html'))
            
            # Enviar email
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)
            
            await self._log_notification(alert.id, "email", "sent")
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            await self._log_notification(alert.id, "email", f"error: {e}")

    async def _send_websocket_notification(self, alert: UltraAlert):
        """Envía notificación vía WebSocket."""
        try:
            for callback in self.websocket_callbacks:
                await callback({
                    "type": "alert",
                    "data": alert.to_dict()
                })
        except Exception as e:
            logger.error(f"Error enviando notificación WebSocket: {e}")

    async def _log_notification(self, alert_id: str, channel: str, status: str):
        """Registra una notificación enviada."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO notifications (alert_id, channel, timestamp, status, details)
                VALUES (?, ?, ?, ?, ?)
            """, (alert_id, channel, datetime.now(), status, ""))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error registrando notificación: {e}")

    async def _notify_callbacks(self, alert: UltraAlert):
        """Notifica a callbacks registrados."""
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error en callback de alerta: {e}")

    async def _update_stats(self, alert: UltraAlert):
        """Actualiza estadísticas de alertas."""
        self.stats["total_alerts"] += 1
        self.stats["alerts_by_level"][alert.level.value] += 1
        self.stats["alerts_by_category"][alert.category.value] += 1
        self.stats["top_components"][alert.component] += 1
        
        # Contar alertas activas
        self.stats["active_alerts"] = len([
            a for a in self.alerts.values() 
            if a.status == AlertStatus.ACTIVE
        ])

    async def get_active_alerts(self, level: Optional[AlertLevel] = None, 
                              category: Optional[AlertCategory] = None) -> List[UltraAlert]:
        """Obtiene alertas activas con filtros opcionales."""
        alerts = [alert for alert in self.alerts.values() if alert.status == AlertStatus.ACTIVE]
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        if category:
            alerts = [alert for alert in alerts if alert.category == category]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene alertas recientes."""
        recent = list(self.alert_history)[-limit:]
        return [alert.to_dict() for alert in reversed(recent)]

    async def get_alert_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de alertas."""
        return {
            "timestamp": datetime.now().isoformat(),
            **self.stats,
            "avg_resolution_time_hours": self._calculate_avg_resolution_time()
        }

    def _calculate_avg_resolution_time(self) -> float:
        """Calcula tiempo promedio de resolución."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT first_occurrence, resolved_at
                FROM alerts
                WHERE status = 'resolved' AND resolved_at IS NOT NULL
                ORDER BY resolved_at DESC
                LIMIT 100
            """)
            
            resolution_times = []
            for row in cursor.fetchall():
                start = datetime.fromisoformat(row[0])
                end = datetime.fromisoformat(row[1])
                resolution_times.append((end - start).total_seconds() / 3600)  # Horas
            
            conn.close()
            
            return sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
            
        except Exception:
            return 0.0

    async def get_active_count(self) -> int:
        """Obtiene el número de alertas activas."""
        return len([a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE])

    # Tareas de background
    async def _escalation_monitor(self):
        """Monitor de escalado de alertas."""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                for alert in self.alerts.values():
                    if (alert.status == AlertStatus.ACTIVE and 
                        not alert.escalated and
                        alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]):
                        
                        # Verificar si debe escalarse
                        time_since_creation = (current_time - alert.timestamp).total_seconds() / 60
                        if time_since_creation > 30:  # 30 minutos
                            await self._escalate_alert(alert)
                
                await asyncio.sleep(60)  # Cada minuto
                
            except Exception as e:
                logger.error(f"Error en monitor de escalado: {e}")
                await asyncio.sleep(120)

    async def _escalate_alert(self, alert: UltraAlert):
        """Escala una alerta."""
        try:
            alert.escalated = True
            alert.escalation_count += 1
            
            # Incrementar nivel si es posible
            if alert.level == AlertLevel.ERROR:
                alert.level = AlertLevel.CRITICAL
            elif alert.level == AlertLevel.CRITICAL:
                alert.level = AlertLevel.EMERGENCY
            
            await self._save_alert(alert)
            await self._process_notifications(alert)
            
            logger.warning(f"⬆️ Alerta {alert.id} escalada a {alert.level.value}")
            
        except Exception as e:
            logger.error(f"Error escalando alerta: {e}")

    async def _aggregation_processor(self):
        """Procesador de agregación de alertas similares."""
        while self.is_running:
            try:
                # Procesar buffer de agregación cada 30 segundos
                await asyncio.sleep(30)
                
                # TODO: Implementar lógica de agregación
                # Por ahora solo limpiamos buffers antiguos
                current_time = time.time()
                for key in list(self.aggregation_buffer.keys()):
                    self.aggregation_buffer[key] = [
                        item for item in self.aggregation_buffer[key]
                        if current_time - item["timestamp"] < 300  # 5 minutos
                    ]
                    
                    if not self.aggregation_buffer[key]:
                        del self.aggregation_buffer[key]
                
            except Exception as e:
                logger.error(f"Error en agregación: {e}")
                await asyncio.sleep(60)

    async def _stats_updater(self):
        """Actualizador de estadísticas."""
        while self.is_running:
            try:
                # Actualizar estadísticas cada 5 minutos
                await asyncio.sleep(300)
                
                # Recalcular alertas activas
                self.stats["active_alerts"] = len([
                    a for a in self.alerts.values() 
                    if a.status == AlertStatus.ACTIVE
                ])
                
                # Recalcular tiempo promedio de resolución
                self.stats["resolution_time_avg"] = self._calculate_avg_resolution_time()
                
            except Exception as e:
                logger.error(f"Error actualizando estadísticas: {e}")
                await asyncio.sleep(600)

    async def _cleanup_task(self):
        """Tarea de limpieza periódica."""
        while self.is_running:
            try:
                # Limpiar cada hora
                await asyncio.sleep(3600)
                
                # Limpiar alertas resueltas antiguas (más de 7 días)
                cutoff_date = datetime.now() - timedelta(days=7)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM alerts 
                    WHERE status = 'resolved' AND resolved_at < ?
                """, (cutoff_date,))
                
                cursor.execute("""
                    DELETE FROM notifications 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                conn.commit()
                conn.close()
                
                logger.info("✅ Limpieza de alertas completada")
                
            except Exception as e:
                logger.error(f"Error en limpieza: {e}")
                await asyncio.sleep(7200)  # Reintentar en 2 horas

    def register_alert_callback(self, callback: Callable):
        """Registra un callback para alertas."""
        self.alert_callbacks.append(callback)

    def register_websocket_callback(self, callback: Callable):
        """Registra un callback para WebSocket."""
        self.websocket_callbacks.append(callback)

    def is_healthy(self) -> bool:
        """Verifica si el sistema de alertas está funcionando."""
        try:
            # Verificar base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return self.is_running
            
        except Exception:
            return False

    async def shutdown(self):
        """Apaga el sistema de alertas."""
        self.is_running = False
        logger.info("✅ Sistema de alertas apagado")