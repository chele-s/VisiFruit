"""
Sistema Ultra-Avanzado de Gestión de WebSockets
==============================================

Gestiona todas las conexiones WebSocket del sistema con:
- Múltiples canales especializados (realtime, dashboard, alerts, etc.)
- Autenticación y autorización de conexiones
- Broadcasting inteligente por grupos
- Compresión automática de mensajes grandes
- Heartbeat y reconexión automática
- Rate limiting por conexión
- Métricas de conexiones en tiempo real
- Buffer de mensajes para clientes desconectados

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import json
import logging
import time
import gzip
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid
import jwt
from fastapi import WebSocket, WebSocketDisconnect
import os
try:
    import redis
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

logger = logging.getLogger("UltraWebSocketManager")

class ConnectionState(Enum):
    """Estados de conexión WebSocket."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class MessageType(Enum):
    """Tipos de mensaje WebSocket."""
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    DATA = "data"
    ERROR = "error"
    STATUS = "status"

@dataclass
class WebSocketConnection:
    """Representación de una conexión WebSocket."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    websocket: WebSocket = None
    state: ConnectionState = ConnectionState.CONNECTING
    channels: Set[str] = field(default_factory=set)
    user_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)
    last_pong: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    rate_limit_count: int = 0
    rate_limit_reset: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChannelInfo:
    """Información de un canal WebSocket."""
    name: str
    description: str
    max_connections: int = 1000
    rate_limit_per_minute: int = 100
    compression_enabled: bool = True
    auth_required: bool = False
    message_buffer_size: int = 100

@dataclass
class BroadcastMessage:
    """Mensaje para broadcasting."""
    channel: str
    message_type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    compression: bool = False
    target_users: Optional[List[str]] = None
    exclude_users: Optional[List[str]] = None

class UltraWebSocketManager:
    """Gestor ultra-avanzado de conexiones WebSocket."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.channels: Dict[str, ChannelInfo] = {}
        self.channel_connections: Dict[str, Set[str]] = defaultdict(set)
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.message_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.broadcast_queue = asyncio.Queue()
        self.is_running = False
        
        # Callbacks para eventos
        self.connection_callbacks: List[Callable] = []
        self.disconnect_callbacks: List[Callable] = []
        self.message_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Configuración
        self.jwt_secret = "fruprint_ultra_secret_2025"  # En producción usar variable de entorno
        self.ping_interval = 30  # segundos
        self.pong_timeout = 10   # segundos
        self.rate_limit_window = 60  # segundos
        
        # Métricas
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_transferred": 0,
            "channels_active": 0,
            "disconnections": 0,
            "errors": 0
        }
        
        # Redis para sincronización entre instancias (opcional)
        self.redis_client = None
        self.redis_enabled = os.environ.get("VISIFRUIT_REDIS_ENABLED", "0").lower() in ("1", "true", "yes", "y")
        if self.redis_enabled and REDIS_AVAILABLE:
            try:
                redis_host = os.environ.get("VISIFRUIT_REDIS_HOST", "localhost")
                redis_port = int(os.environ.get("VISIFRUIT_REDIS_PORT", "6379"))
                redis_db = int(os.environ.get("VISIFRUIT_REDIS_DB_WS", "1"))

                self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
                self.redis_client.ping()
                logger.info("Redis conectado para sincronización WebSocket")
            except Exception:
                logger.info("Redis no disponible - modo standalone")
                self.redis_client = None
        else:
            if not self.redis_enabled:
                logger.info("Redis desactivado por configuración (VISIFRUIT_REDIS_ENABLED=0) - modo standalone")
            else:
                logger.info("Redis no instalado - modo standalone")

    async def initialize(self):
        """Inicializa el gestor de WebSockets."""
        try:
            # Configurar canales predefinidos
            await self._setup_default_channels()
            
            # Iniciar tareas de background
            await self._start_background_tasks()
            
            self.is_running = True
            logger.info("✅ Gestor de WebSockets inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando WebSocket manager: {e}")
            raise

    async def _setup_default_channels(self):
        """Configura canales predefinidos."""
        default_channels = [
            ChannelInfo(
                name="realtime",
                description="Datos del sistema en tiempo real",
                max_connections=500,
                rate_limit_per_minute=60,
                compression_enabled=True,
                auth_required=False
            ),
            ChannelInfo(
                name="dashboard",
                description="Dashboard 3D del sistema",
                max_connections=100,
                rate_limit_per_minute=30,
                compression_enabled=True,
                auth_required=True
            ),
            ChannelInfo(
                name="alerts",
                description="Alertas del sistema",
                max_connections=200,
                rate_limit_per_minute=120,
                compression_enabled=False,
                auth_required=True
            ),
            ChannelInfo(
                name="metrics",
                description="Métricas del sistema",
                max_connections=300,
                rate_limit_per_minute=90,
                compression_enabled=True,
                auth_required=False
            ),
            ChannelInfo(
                name="production",
                description="Datos de producción",
                max_connections=150,
                rate_limit_per_minute=120,
                compression_enabled=True,
                auth_required=True
            ),
            ChannelInfo(
                name="maintenance",
                description="Información de mantenimiento",
                max_connections=50,
                rate_limit_per_minute=30,
                compression_enabled=False,
                auth_required=True
            )
        ]
        
        for channel in default_channels:
            self.channels[channel.name] = channel
            logger.info(f"Canal configurado: {channel.name}")

    async def _start_background_tasks(self):
        """Inicia tareas de background."""
        asyncio.create_task(self._heartbeat_monitor())
        asyncio.create_task(self._broadcast_processor())
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._metrics_collector())
        asyncio.create_task(self._rate_limit_resetter())

    async def handle_connection(self, websocket: WebSocket, channel: str = "default"):
        """Maneja una nueva conexión WebSocket."""
        connection_id = str(uuid.uuid4())[:12]
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTING
        )
        
        try:
            # Aceptar conexión
            await websocket.accept()
            connection.state = ConnectionState.CONNECTED
            
            # Registrar conexión
            self.connections[connection_id] = connection
            self.metrics["total_connections"] += 1
            self.metrics["active_connections"] += 1
            
            logger.info(f"🔗 Nueva conexión WebSocket: {connection_id} en canal {channel}")
            
            # Suscribir al canal por defecto si es válido
            if channel in self.channels:
                await self._subscribe_to_channel(connection, channel)
            
            # Enviar mensaje de bienvenida
            await self._send_to_connection(connection, {
                "type": MessageType.STATUS.value,
                "data": {
                    "connection_id": connection_id,
                    "status": "connected",
                    "channels_available": list(self.channels.keys()),
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Notificar callbacks
            await self._notify_connection_callbacks(connection, "connected")
            
            # Bucle principal de mensajes
            await self._message_loop(connection)
            
        except WebSocketDisconnect:
            logger.info(f"🔌 Conexión {connection_id} desconectada normalmente")
        except Exception as e:
            logger.error(f"❌ Error en conexión {connection_id}: {e}")
            connection.state = ConnectionState.ERROR
            self.metrics["errors"] += 1
        finally:
            await self._cleanup_connection(connection)

    async def _message_loop(self, connection: WebSocketConnection):
        """Bucle principal para procesar mensajes de una conexión."""
        while connection.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
            try:
                # Recibir mensaje
                message = await connection.websocket.receive_text()
                connection.message_count += 1
                connection.bytes_received += len(message.encode())
                self.metrics["messages_received"] += 1
                
                # Verificar rate limiting
                if not await self._check_rate_limit(connection):
                    await self._send_error(connection, "rate_limit_exceeded", 
                                         "Too many messages. Please slow down.")
                    continue
                
                # Parsear mensaje
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    await self._send_error(connection, "invalid_json", "Invalid JSON format")
                    continue
                
                # Procesar mensaje
                await self._process_message(connection, data)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error procesando mensaje de {connection.id}: {e}")
                await self._send_error(connection, "processing_error", str(e))

    async def _process_message(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """Procesa un mensaje recibido."""
        message_type = data.get("type")
        
        if message_type == MessageType.PING.value:
            await self._handle_ping(connection, data)
        elif message_type == MessageType.AUTH.value:
            await self._handle_auth(connection, data)
        elif message_type == MessageType.SUBSCRIBE.value:
            await self._handle_subscribe(connection, data)
        elif message_type == MessageType.UNSUBSCRIBE.value:
            await self._handle_unsubscribe(connection, data)
        else:
            # Notificar callbacks específicos del tipo de mensaje
            await self._notify_message_callbacks(message_type, connection, data)

    async def _handle_ping(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """Maneja mensaje PING."""
        connection.last_ping = datetime.now()
        await self._send_to_connection(connection, {
            "type": MessageType.PONG.value,
            "data": {"timestamp": datetime.now().isoformat()}
        })

    async def _handle_auth(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """Maneja autenticación."""
        try:
            token = data.get("token")
            if not token:
                await self._send_error(connection, "missing_token", "Token required")
                return
            
            # Verificar JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload.get("user_id")
            
            if user_id:
                connection.user_id = user_id
                connection.state = ConnectionState.AUTHENTICATED
                self.user_connections[user_id].add(connection.id)
                
                await self._send_to_connection(connection, {
                    "type": MessageType.STATUS.value,
                    "data": {
                        "authenticated": True,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
                logger.info(f"🔐 Usuario {user_id} autenticado en conexión {connection.id}")
            else:
                await self._send_error(connection, "invalid_token", "Invalid token payload")
                
        except jwt.InvalidTokenError:
            await self._send_error(connection, "invalid_token", "Token verification failed")

    async def _handle_subscribe(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """Maneja suscripción a canal."""
        channel = data.get("channel")
        
        if not channel or channel not in self.channels:
            await self._send_error(connection, "invalid_channel", f"Channel '{channel}' not found")
            return
        
        channel_info = self.channels[channel]
        
        # Verificar autenticación si es requerida
        if channel_info.auth_required and connection.state != ConnectionState.AUTHENTICATED:
            await self._send_error(connection, "auth_required", f"Channel '{channel}' requires authentication")
            return
        
        # Verificar límite de conexiones
        if len(self.channel_connections[channel]) >= channel_info.max_connections:
            await self._send_error(connection, "channel_full", f"Channel '{channel}' is full")
            return
        
        await self._subscribe_to_channel(connection, channel)

    async def _subscribe_to_channel(self, connection: WebSocketConnection, channel: str):
        """Suscribe una conexión a un canal."""
        connection.channels.add(channel)
        self.channel_connections[channel].add(connection.id)
        
        await self._send_to_connection(connection, {
            "type": MessageType.STATUS.value,
            "data": {
                "subscribed": True,
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Enviar mensajes en buffer si los hay
        if channel in self.message_buffer:
            for buffered_message in list(self.message_buffer[channel]):
                await self._send_to_connection(connection, buffered_message)
        
        logger.info(f"📢 Conexión {connection.id} suscrita al canal {channel}")

    async def _handle_unsubscribe(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """Maneja desuscripción de canal."""
        channel = data.get("channel")
        
        if channel in connection.channels:
            connection.channels.remove(channel)
            self.channel_connections[channel].discard(connection.id)
            
            await self._send_to_connection(connection, {
                "type": MessageType.STATUS.value,
                "data": {
                    "unsubscribed": True,
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            logger.info(f"📭 Conexión {connection.id} desuscrita del canal {channel}")

    async def _send_to_connection(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """Envía un mensaje a una conexión específica."""
        try:
            # Preparar mensaje
            message_str = json.dumps(message)
            
            # Comprimir si es necesario
            if len(message_str) > 1024:  # Comprimir mensajes grandes
                compressed = gzip.compress(message_str.encode())
                if len(compressed) < len(message_str):
                    await connection.websocket.send_bytes(compressed)
                    connection.bytes_sent += len(compressed)
                else:
                    await connection.websocket.send_text(message_str)
                    connection.bytes_sent += len(message_str)
            else:
                await connection.websocket.send_text(message_str)
                connection.bytes_sent += len(message_str)
            
            self.metrics["messages_sent"] += 1
            self.metrics["bytes_transferred"] += connection.bytes_sent
            
        except Exception as e:
            logger.error(f"Error enviando mensaje a {connection.id}: {e}")
            connection.state = ConnectionState.ERROR

    async def _send_error(self, connection: WebSocketConnection, error_code: str, message: str):
        """Envía un mensaje de error."""
        await self._send_to_connection(connection, {
            "type": MessageType.ERROR.value,
            "data": {
                "error_code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        })

    async def _check_rate_limit(self, connection: WebSocketConnection) -> bool:
        """Verifica rate limiting para una conexión."""
        now = datetime.now()
        
        # Resetear contador si ha pasado la ventana
        if now > connection.rate_limit_reset:
            connection.rate_limit_count = 0
            connection.rate_limit_reset = now + timedelta(seconds=self.rate_limit_window)
        
        connection.rate_limit_count += 1
        
        # Buscar límite del canal más restrictivo
        max_limit = 100  # Límite por defecto
        for channel in connection.channels:
            if channel in self.channels:
                max_limit = min(max_limit, self.channels[channel].rate_limit_per_minute)
        
        return connection.rate_limit_count <= max_limit

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any], 
                                 target_users: Optional[List[str]] = None,
                                 exclude_users: Optional[List[str]] = None):
        """Envía un mensaje a todos los suscriptores de un canal."""
        broadcast_msg = BroadcastMessage(
            channel=channel,
            message_type=MessageType.DATA,
            data=message,
            target_users=target_users,
            exclude_users=exclude_users
        )
        
        await self.broadcast_queue.put(broadcast_msg)

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Envía un mensaje a todas las conexiones de un usuario."""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.connections:
                    connection = self.connections[connection_id]
                    await self._send_to_connection(connection, {
                        "type": MessageType.DATA.value,
                        "data": message
                    })

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Envía un mensaje a todas las conexiones activas."""
        for connection in self.connections.values():
            if connection.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
                await self._send_to_connection(connection, {
                    "type": MessageType.DATA.value,
                    "data": message
                })

    # Tareas de background
    async def _heartbeat_monitor(self):
        """Monitor de heartbeat para detectar conexiones muertas."""
        while self.is_running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(seconds=self.ping_interval + self.pong_timeout)
                
                dead_connections = []
                for connection in self.connections.values():
                    if connection.last_pong < timeout_threshold:
                        dead_connections.append(connection)
                
                # Limpiar conexiones muertas
                for connection in dead_connections:
                    logger.info(f"💀 Conexión {connection.id} detectada como muerta")
                    await self._cleanup_connection(connection)
                
                await asyncio.sleep(self.ping_interval)
                
            except Exception as e:
                logger.error(f"Error en monitor de heartbeat: {e}")
                await asyncio.sleep(30)

    async def _broadcast_processor(self):
        """Procesador de mensajes de broadcasting."""
        while self.is_running:
            try:
                broadcast_msg = await self.broadcast_queue.get()
                
                # Obtener conexiones del canal
                channel_connections = self.channel_connections.get(broadcast_msg.channel, set())
                
                # Filtrar conexiones por usuarios target/exclude
                target_connections = []
                for connection_id in channel_connections:
                    if connection_id not in self.connections:
                        continue
                    
                    connection = self.connections[connection_id]
                    
                    # Verificar target users
                    if broadcast_msg.target_users:
                        if connection.user_id not in broadcast_msg.target_users:
                            continue
                    
                    # Verificar exclude users
                    if broadcast_msg.exclude_users:
                        if connection.user_id in broadcast_msg.exclude_users:
                            continue
                    
                    target_connections.append(connection)
                
                # Enviar mensaje a conexiones filtradas
                message = {
                    "type": broadcast_msg.message_type.value,
                    "channel": broadcast_msg.channel,
                    "data": broadcast_msg.data,
                    "timestamp": broadcast_msg.timestamp.isoformat()
                }
                
                for connection in target_connections:
                    await self._send_to_connection(connection, message)
                
                # Guardar en buffer para nuevas conexiones
                if broadcast_msg.channel in self.channels:
                    self.message_buffer[broadcast_msg.channel].append(message)
                
            except Exception as e:
                logger.error(f"Error en broadcast processor: {e}")
                await asyncio.sleep(1)

    async def _cleanup_task(self):
        """Tarea de limpieza periódica."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                
                # Limpiar buffers de mensajes antiguos
                current_time = datetime.now()
                for channel, buffer in self.message_buffer.items():
                    # Mantener solo mensajes de los últimos 10 minutos
                    cutoff_time = current_time - timedelta(minutes=10)
                    
                    while buffer and datetime.fromisoformat(buffer[0]["timestamp"]) < cutoff_time:
                        buffer.popleft()
                
                # Actualizar métricas de canales activos
                self.metrics["channels_active"] = len([
                    channel for channel, connections in self.channel_connections.items()
                    if connections
                ])
                
            except Exception as e:
                logger.error(f"Error en tarea de limpieza: {e}")
                await asyncio.sleep(600)

    async def _metrics_collector(self):
        """Recolector de métricas."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Cada minuto
                
                # Actualizar métricas de conexiones activas
                active_count = len([
                    conn for conn in self.connections.values()
                    if conn.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]
                ])
                
                self.metrics["active_connections"] = active_count
                
                # Log de métricas
                # Usar logging sin emojis para evitar errores de codificación
                logger.info(f"[METRICS] WebSocket Metrics: {active_count} conexiones activas, "
                          f"{self.metrics['messages_sent']} mensajes enviados")
                
            except Exception as e:
                logger.error(f"Error recolectando métricas: {e}")
                await asyncio.sleep(120)

    async def _rate_limit_resetter(self):
        """Resetea contadores de rate limit."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Cada minuto
                
                current_time = datetime.now()
                for connection in self.connections.values():
                    if current_time > connection.rate_limit_reset:
                        connection.rate_limit_count = 0
                        connection.rate_limit_reset = current_time + timedelta(seconds=self.rate_limit_window)
                
            except Exception as e:
                logger.error(f"Error reseteando rate limits: {e}")
                await asyncio.sleep(120)

    async def _cleanup_connection(self, connection: WebSocketConnection):
        """Limpia una conexión desconectada."""
        try:
            # Remover de conexiones activas
            if connection.id in self.connections:
                del self.connections[connection.id]
            
            # Remover de canales
            for channel in connection.channels:
                self.channel_connections[channel].discard(connection.id)
            
            # Remover de usuarios
            if connection.user_id:
                self.user_connections[connection.user_id].discard(connection.id)
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]
            
            # Actualizar métricas
            self.metrics["active_connections"] = max(0, self.metrics["active_connections"] - 1)
            self.metrics["disconnections"] += 1
            
            # Notificar callbacks
            await self._notify_connection_callbacks(connection, "disconnected")
            
            logger.info(f"🧹 Conexión {connection.id} limpiada")
            
        except Exception as e:
            logger.error(f"Error limpiando conexión: {e}")

    async def _notify_connection_callbacks(self, connection: WebSocketConnection, event: str):
        """Notifica callbacks de eventos de conexión."""
        callbacks = self.connection_callbacks if event == "connected" else self.disconnect_callbacks
        
        for callback in callbacks:
            try:
                await callback(connection, event)
            except Exception as e:
                logger.error(f"Error en callback de conexión: {e}")

    async def _notify_message_callbacks(self, message_type: str, connection: WebSocketConnection, data: Dict[str, Any]):
        """Notifica callbacks de mensajes."""
        for callback in self.message_callbacks.get(message_type, []):
            try:
                await callback(connection, data)
            except Exception as e:
                logger.error(f"Error en callback de mensaje: {e}")

    # API pública
    def register_connection_callback(self, callback: Callable):
        """Registra callback para eventos de conexión."""
        self.connection_callbacks.append(callback)

    def register_disconnect_callback(self, callback: Callable):
        """Registra callback para eventos de desconexión."""
        self.disconnect_callbacks.append(callback)

    def register_message_callback(self, message_type: str, callback: Callable):
        """Registra callback para tipos específicos de mensaje."""
        self.message_callbacks[message_type].append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del gestor."""
        return {
            **self.metrics,
            "timestamp": datetime.now().isoformat(),
            "channels": {
                name: {
                    "connections": len(self.channel_connections.get(name, set())),
                    "max_connections": info.max_connections,
                    "rate_limit": info.rate_limit_per_minute
                }
                for name, info in self.channels.items()
            }
        }

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una conexión específica."""
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        return {
            "id": connection.id,
            "state": connection.state.value,
            "channels": list(connection.channels),
            "user_id": connection.user_id,
            "connected_at": connection.connected_at.isoformat(),
            "message_count": connection.message_count,
            "bytes_sent": connection.bytes_sent,
            "bytes_received": connection.bytes_received,
            "last_ping": connection.last_ping.isoformat(),
            "metadata": connection.metadata
        }

    def is_healthy(self) -> bool:
        """Verifica si el gestor está funcionando correctamente."""
        return self.is_running and len(self.connections) >= 0

    async def shutdown(self):
        """Apaga el gestor de WebSockets."""
        logger.info("Apagando gestor de WebSockets...")
        
        self.is_running = False
        
        # Cerrar todas las conexiones
        for connection in list(self.connections.values()):
            try:
                await connection.websocket.close()
            except:
                pass
        
        self.connections.clear()
        self.channel_connections.clear()
        self.user_connections.clear()
        
        logger.info("✅ Gestor de WebSockets apagado")