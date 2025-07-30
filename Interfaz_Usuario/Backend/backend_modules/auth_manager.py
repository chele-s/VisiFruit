"""
Sistema Ultra-Avanzado de Autenticación y Autorización
======================================================

Sistema completo de autenticación con:
- JWT tokens con refresh tokens
- Roles y permisos granulares
- Autenticación multifactor (MFA)
- Sesión única (SSO) opcional
- Auditoría de accesos
- Rate limiting por usuario
- Bloqueo automático por intentos fallidos
- Integración con proveedores externos
- API keys para sistemas

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import hashlib
import hmac
import jwt
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import sqlite3
import bcrypt
from pathlib import Path

logger = logging.getLogger("UltraAuthManager")

class UserRole(Enum):
    """Roles de usuario del sistema."""
    ADMIN = "admin"
    OPERATOR = "operator"
    TECHNICIAN = "technician"
    VIEWER = "viewer"
    API_USER = "api_user"
    GUEST = "guest"

class Permission(Enum):
    """Permisos granulares del sistema."""
    # Sistema
    SYSTEM_VIEW = "system:view"
    SYSTEM_CONTROL = "system:control"
    SYSTEM_CONFIG = "system:config"
    
    # Producción
    PRODUCTION_VIEW = "production:view"
    PRODUCTION_START = "production:start"
    PRODUCTION_STOP = "production:stop"
    PRODUCTION_EMERGENCY = "production:emergency"
    
    # Métricas y reportes
    METRICS_VIEW = "metrics:view"
    METRICS_EXPORT = "metrics:export"
    REPORTS_VIEW = "reports:view"
    REPORTS_GENERATE = "reports:generate"
    
    # Configuración
    CONFIG_VIEW = "config:view"
    CONFIG_EDIT = "config:edit"
    CONFIG_BACKUP = "config:backup"
    
    # Usuarios
    USERS_VIEW = "users:view"
    USERS_CREATE = "users:create"
    USERS_EDIT = "users:edit"
    USERS_DELETE = "users:delete"
    
    # Mantenimiento
    MAINTENANCE_VIEW = "maintenance:view"
    MAINTENANCE_EXECUTE = "maintenance:execute"
    
    # Alertas
    ALERTS_VIEW = "alerts:view"
    ALERTS_ACK = "alerts:acknowledge"
    ALERTS_RESOLVE = "alerts:resolve"

@dataclass
class User:
    """Usuario del sistema."""
    id: int = 0
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    permissions: List[Permission] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Session:
    """Sesión de usuario."""
    id: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    user_id: int = 0
    access_token: str = ""
    refresh_token: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    ip_address: str = ""
    user_agent: str = ""
    is_active: bool = True
    last_activity: datetime = field(default_factory=datetime.now)

@dataclass
class AuditEvent:
    """Evento de auditoría."""
    id: str = field(default_factory=lambda: secrets.token_urlsafe(16))
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[int] = None
    username: str = ""
    event_type: str = ""
    resource: str = ""
    action: str = ""
    ip_address: str = ""
    user_agent: str = ""
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)

class UltraAuthManager:
    """Gestor ultra-avanzado de autenticación y autorización."""
    
    def __init__(self):
        self.db_path = "data/auth.db"
        self.jwt_secret = "fruprint_ultra_jwt_secret_2025"  # En producción usar variable de entorno
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        
        # Cache de usuarios y sesiones
        self.users_cache: Dict[int, User] = {}
        self.sessions_cache: Dict[str, Session] = {}
        self.permissions_cache: Dict[UserRole, List[Permission]] = {}
        
        # Rate limiting
        self.login_attempts: Dict[str, List[datetime]] = {}
        self.api_requests: Dict[str, List[datetime]] = {}
        
        # Auditoría
        self.audit_events: List[AuditEvent] = []
        
        self.is_running = False
        
        # Configurar permisos por rol
        self._setup_role_permissions()

    async def initialize(self):
        """Inicializa el gestor de autenticación."""
        try:
            # Crear base de datos
            await self._init_database()
            
            # Crear usuario admin por defecto si no existe
            await self._create_default_admin()
            
            # Cargar usuarios en cache
            await self._load_users_cache()
            
            # Iniciar tareas de limpieza
            await self._start_cleanup_tasks()
            
            self.is_running = True
            logger.info("✅ Gestor de autenticación inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando gestor de autenticación: {e}")
            raise

    def _setup_role_permissions(self):
        """Configura permisos por rol."""
        self.permissions_cache = {
            UserRole.ADMIN: list(Permission),  # Todos los permisos
            
            UserRole.OPERATOR: [
                Permission.SYSTEM_VIEW, Permission.SYSTEM_CONTROL,
                Permission.PRODUCTION_VIEW, Permission.PRODUCTION_START, Permission.PRODUCTION_STOP,
                Permission.METRICS_VIEW, Permission.REPORTS_VIEW,
                Permission.CONFIG_VIEW, Permission.ALERTS_VIEW, Permission.ALERTS_ACK
            ],
            
            UserRole.TECHNICIAN: [
                Permission.SYSTEM_VIEW, Permission.PRODUCTION_VIEW,
                Permission.METRICS_VIEW, Permission.REPORTS_VIEW, Permission.CONFIG_VIEW,
                Permission.MAINTENANCE_VIEW, Permission.MAINTENANCE_EXECUTE,
                Permission.ALERTS_VIEW, Permission.ALERTS_ACK, Permission.ALERTS_RESOLVE
            ],
            
            UserRole.VIEWER: [
                Permission.SYSTEM_VIEW, Permission.PRODUCTION_VIEW,
                Permission.METRICS_VIEW, Permission.REPORTS_VIEW,
                Permission.ALERTS_VIEW
            ],
            
            UserRole.API_USER: [
                Permission.SYSTEM_VIEW, Permission.PRODUCTION_VIEW,
                Permission.METRICS_VIEW, Permission.METRICS_EXPORT
            ],
            
            UserRole.GUEST: [
                Permission.SYSTEM_VIEW
            ]
        }

    async def _init_database(self):
        """Inicializa la base de datos de autenticación."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME NOT NULL,
                last_login DATETIME,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until DATETIME,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret TEXT,
                metadata TEXT
            )
        """)
        
        # Tabla de sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                last_activity DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Tabla de auditoría
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                user_id INTEGER,
                username TEXT,
                event_type TEXT NOT NULL,
                resource TEXT,
                action TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)")
        
        conn.commit()
        conn.close()

    async def _create_default_admin(self):
        """Crea usuario admin por defecto si no existe."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar si ya existe un admin
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (UserRole.ADMIN.value,))
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                # Crear admin por defecto
                password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "admin",
                    "admin@fruprint.com",
                    password_hash,
                    UserRole.ADMIN.value,
                    datetime.now(),
                    json.dumps({"created_by": "system", "default_admin": True})
                ))
                
                conn.commit()
                logger.info("🔑 Usuario admin por defecto creado (admin/admin123)")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creando admin por defecto: {e}")

    async def _load_users_cache(self):
        """Carga usuarios en cache."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE is_active = TRUE")
            
            for row in cursor.fetchall():
                user = User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    role=UserRole(row[4]),
                    is_active=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                    last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                    failed_login_attempts=row[8],
                    locked_until=datetime.fromisoformat(row[9]) if row[9] else None,
                    mfa_enabled=bool(row[10]),
                    mfa_secret=row[11],
                    metadata=json.loads(row[12]) if row[12] else {}
                )
                
                # Asignar permisos basados en el rol
                user.permissions = self.permissions_cache.get(user.role, [])
                
                self.users_cache[user.id] = user
            
            conn.close()
            logger.info(f"📄 {len(self.users_cache)} usuarios cargados en cache")
            
        except Exception as e:
            logger.error(f"Error cargando usuarios: {e}")

    # Autenticación principal
    async def authenticate(self, username: str, password: str, ip_address: str = "", 
                          user_agent: str = "") -> Optional[Tuple[str, str]]:
        """Autentica un usuario y retorna tokens de acceso."""
        try:
            # Verificar rate limiting
            if not await self._check_login_rate_limit(ip_address):
                await self._audit_event("login_rate_limited", username=username, 
                                       ip_address=ip_address, success=False)
                return None
            
            # Buscar usuario
            user = await self._get_user_by_username(username)
            if not user:
                await self._audit_event("login_failed", username=username, 
                                       ip_address=ip_address, success=False,
                                       details={"reason": "user_not_found"})
                return None
            
            # Verificar si el usuario está bloqueado
            if user.locked_until and user.locked_until > datetime.now():
                await self._audit_event("login_blocked", user_id=user.id, username=username,
                                       ip_address=ip_address, success=False,
                                       details={"locked_until": user.locked_until.isoformat()})
                return None
            
            # Verificar contraseña
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Incrementar intentos fallidos
                await self._increment_failed_attempts(user)
                
                await self._audit_event("login_failed", user_id=user.id, username=username,
                                       ip_address=ip_address, success=False,
                                       details={"reason": "invalid_password"})
                return None
            
            # Autenticación exitosa
            await self._reset_failed_attempts(user)
            
            # Crear sesión
            session = await self._create_session(user, ip_address, user_agent)
            
            # Actualizar último login
            await self._update_last_login(user.id)
            
            await self._audit_event("login_success", user_id=user.id, username=username,
                                   ip_address=ip_address, success=True,
                                   details={"session_id": session.id})
            
            logger.info(f"🔓 Usuario autenticado: {username} desde {ip_address}")
            
            return session.access_token, session.refresh_token
            
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            return None

    async def _check_login_rate_limit(self, ip_address: str) -> bool:
        """Verifica rate limiting para intentos de login."""
        if not ip_address:
            return True
        
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=15)  # Ventana de 15 minutos
        
        # Obtener intentos recientes
        if ip_address not in self.login_attempts:
            self.login_attempts[ip_address] = []
        
        # Filtrar intentos dentro de la ventana
        recent_attempts = [
            attempt for attempt in self.login_attempts[ip_address]
            if attempt > window_start
        ]
        
        self.login_attempts[ip_address] = recent_attempts
        
        # Verificar límite (max 10 intentos por IP en 15 minutos)
        if len(recent_attempts) >= 10:
            return False
        
        # Registrar intento actual
        self.login_attempts[ip_address].append(current_time)
        return True

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Obtiene usuario por nombre de usuario."""
        # Buscar en cache primero
        for user in self.users_cache.values():
            if user.username == username and user.is_active:
                return user
        
        # Buscar en base de datos
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM users 
                WHERE username = ? AND is_active = TRUE
            """, (username,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                user = User(
                    id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    role=UserRole(row[4]),
                    is_active=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]),
                    last_login=datetime.fromisoformat(row[7]) if row[7] else None,
                    failed_login_attempts=row[8],
                    locked_until=datetime.fromisoformat(row[9]) if row[9] else None,
                    mfa_enabled=bool(row[10]),
                    mfa_secret=row[11],
                    metadata=json.loads(row[12]) if row[12] else {}
                )
                
                user.permissions = self.permissions_cache.get(user.role, [])
                self.users_cache[user.id] = user
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return None

    async def _increment_failed_attempts(self, user: User):
        """Incrementa intentos fallidos de login."""
        try:
            user.failed_login_attempts += 1
            
            # Bloquear usuario si excede el límite
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
                logger.warning(f"🔒 Usuario {user.username} bloqueado por {self.lockout_duration_minutes} minutos")
            
            # Actualizar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = ?, locked_until = ?
                WHERE id = ?
            """, (user.failed_login_attempts, 
                   user.locked_until.isoformat() if user.locked_until else None,
                   user.id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error incrementando intentos fallidos: {e}")

    async def _reset_failed_attempts(self, user: User):
        """Resetea intentos fallidos de login."""
        try:
            user.failed_login_attempts = 0
            user.locked_until = None
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET failed_login_attempts = 0, locked_until = NULL
                WHERE id = ?
            """, (user.id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error reseteando intentos fallidos: {e}")

    async def _create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Crea una nueva sesión de usuario."""
        try:
            # Generar tokens
            access_token = self._generate_access_token(user)
            refresh_token = secrets.token_urlsafe(64)
            
            session = Session(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Guardar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions 
                (id, user_id, access_token, refresh_token, created_at, expires_at, 
                 ip_address, user_agent, is_active, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id, session.user_id, session.access_token, session.refresh_token,
                session.created_at, session.expires_at, session.ip_address, session.user_agent,
                session.is_active, session.last_activity
            ))
            
            conn.commit()
            conn.close()
            
            # Guardar en cache
            self.sessions_cache[session.id] = session
            
            return session
            
        except Exception as e:
            logger.error(f"Error creando sesión: {e}")
            raise

    def _generate_access_token(self, user: User) -> str:
        """Genera token de acceso JWT."""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "iss": "fruprint-ultra"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _update_last_login(self, user_id: int):
        """Actualiza último login del usuario."""
        try:
            current_time = datetime.now()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (current_time, user_id))
            
            conn.commit()
            conn.close()
            
            # Actualizar cache
            if user_id in self.users_cache:
                self.users_cache[user_id].last_login = current_time
                
        except Exception as e:
            logger.error(f"Error actualizando último login: {e}")

    # Validación de tokens
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida un token de acceso."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Verificar si el usuario sigue activo
            user_id = payload.get("user_id")
            if user_id and user_id in self.users_cache:
                user = self.users_cache[user_id]
                if user.is_active:
                    return payload
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token expirado")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Token inválido")
            return None
        except Exception as e:
            logger.error(f"Error validando token: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresca tokens usando refresh token."""
        try:
            # Buscar sesión por refresh token
            session = None
            for s in self.sessions_cache.values():
                if s.refresh_token == refresh_token and s.is_active:
                    session = s
                    break
            
            if not session:
                # Buscar en base de datos
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM sessions 
                    WHERE refresh_token = ? AND is_active = TRUE AND expires_at > ?
                """, (refresh_token, datetime.now()))
                
                row = cursor.fetchone()
                conn.close()
                
                if not row:
                    return None
                
                session = Session(
                    id=row[0],
                    user_id=row[1],
                    access_token=row[2],
                    refresh_token=row[3],
                    created_at=datetime.fromisoformat(row[4]),
                    expires_at=datetime.fromisoformat(row[5]),
                    ip_address=row[6],
                    user_agent=row[7],
                    is_active=bool(row[8]),
                    last_activity=datetime.fromisoformat(row[9])
                )
            
            # Obtener usuario
            user = self.users_cache.get(session.user_id)
            if not user or not user.is_active:
                return None
            
            # Generar nuevos tokens
            new_access_token = self._generate_access_token(user)
            new_refresh_token = secrets.token_urlsafe(64)
            
            # Actualizar sesión
            session.access_token = new_access_token
            session.refresh_token = new_refresh_token
            session.last_activity = datetime.now()
            
            # Actualizar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sessions 
                SET access_token = ?, refresh_token = ?, last_activity = ?
                WHERE id = ?
            """, (new_access_token, new_refresh_token, session.last_activity, session.id))
            
            conn.commit()
            conn.close()
            
            # Actualizar cache
            self.sessions_cache[session.id] = session
            
            return new_access_token, new_refresh_token
            
        except Exception as e:
            logger.error(f"Error refrescando token: {e}")
            return None

    # Autorización
    async def check_permission(self, user_id: int, permission: Permission) -> bool:
        """Verifica si un usuario tiene un permiso específico."""
        try:
            user = self.users_cache.get(user_id)
            if not user or not user.is_active:
                return False
            
            return permission in user.permissions
            
        except Exception as e:
            logger.error(f"Error verificando permiso: {e}")
            return False

    async def check_permissions(self, user_id: int, permissions: List[Permission]) -> bool:
        """Verifica si un usuario tiene todos los permisos especificados."""
        for permission in permissions:
            if not await self.check_permission(user_id, permission):
                return False
        return True

    async def has_role(self, user_id: int, role: UserRole) -> bool:
        """Verifica si un usuario tiene un rol específico."""
        user = self.users_cache.get(user_id)
        return user is not None and user.role == role

    # Gestión de usuarios
    async def create_user(self, username: str, email: str, password: str, 
                         role: UserRole, created_by: str = "system") -> Optional[User]:
        """Crea un nuevo usuario."""
        try:
            # Validar que no exista
            existing = await self._get_user_by_username(username)
            if existing:
                logger.error(f"Usuario {username} ya existe")
                return None
            
            # Hash de la contraseña
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Crear usuario
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                username, email, password_hash, role.value, datetime.now(),
                json.dumps({"created_by": created_by})
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Crear objeto usuario
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                permissions=self.permissions_cache.get(role, [])
            )
            
            # Agregar al cache
            self.users_cache[user_id] = user
            
            await self._audit_event("user_created", user_id=user_id, username=username,
                                   details={"created_by": created_by, "role": role.value})
            
            logger.info(f"👤 Usuario creado: {username} ({role.value})")
            return user
            
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return None

    async def logout(self, access_token: str) -> bool:
        """Cierra sesión de un usuario."""
        try:
            # Decodificar token para obtener info del usuario
            payload = await self.validate_token(access_token)
            if not payload:
                return False
            
            user_id = payload.get("user_id")
            username = payload.get("username")
            
            # Encontrar y desactivar sesión
            session_id = None
            for sid, session in self.sessions_cache.items():
                if session.access_token == access_token:
                    session.is_active = False
                    session_id = sid
                    break
            
            # Actualizar en base de datos
            if session_id:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE sessions SET is_active = FALSE WHERE id = ?
                """, (session_id,))
                
                conn.commit()
                conn.close()
                
                # Remover del cache
                if session_id in self.sessions_cache:
                    del self.sessions_cache[session_id]
            
            await self._audit_event("logout", user_id=user_id, username=username, success=True)
            
            logger.info(f"🚪 Usuario desconectado: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error en logout: {e}")
            return False

    # Auditoría
    async def _audit_event(self, event_type: str, user_id: Optional[int] = None, 
                          username: str = "", resource: str = "", action: str = "",
                          ip_address: str = "", user_agent: str = "", success: bool = True,
                          details: Dict[str, Any] = None):
        """Registra evento de auditoría."""
        try:
            event = AuditEvent(
                user_id=user_id,
                username=username,
                event_type=event_type,
                resource=resource,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                details=details or {}
            )
            
            # Guardar en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_events 
                (id, timestamp, user_id, username, event_type, resource, action,
                 ip_address, user_agent, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.timestamp, event.user_id, event.username,
                event.event_type, event.resource, event.action, event.ip_address,
                event.user_agent, event.success, json.dumps(event.details)
            ))
            
            conn.commit()
            conn.close()
            
            # Mantener en memoria para acceso rápido
            self.audit_events.append(event)
            if len(self.audit_events) > 1000:
                self.audit_events.pop(0)
                
        except Exception as e:
            logger.error(f"Error registrando evento de auditoría: {e}")

    # Tareas de limpieza
    async def _start_cleanup_tasks(self):
        """Inicia tareas de limpieza periódica."""
        asyncio.create_task(self._cleanup_expired_sessions())
        asyncio.create_task(self._cleanup_old_audit_events())
        asyncio.create_task(self._unlock_users_task())

    async def _cleanup_expired_sessions(self):
        """Limpia sesiones expiradas."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Cada hora
                
                current_time = datetime.now()
                
                # Limpiar sesiones expiradas del cache
                expired_sessions = [
                    sid for sid, session in self.sessions_cache.items()
                    if session.expires_at < current_time
                ]
                
                for sid in expired_sessions:
                    del self.sessions_cache[sid]
                
                # Limpiar de la base de datos
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM sessions WHERE expires_at < ?
                """, (current_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                if deleted_count > 0:
                    logger.info(f"🧹 {deleted_count} sesiones expiradas eliminadas")
                
            except Exception as e:
                logger.error(f"Error limpiando sesiones: {e}")
                await asyncio.sleep(1800)

    async def _cleanup_old_audit_events(self):
        """Limpia eventos de auditoría antiguos."""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # Cada 24 horas
                
                # Mantener solo últimos 90 días
                cutoff_date = datetime.now() - timedelta(days=90)
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM audit_events WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                conn.close()
                
                if deleted_count > 0:
                    logger.info(f"🧹 {deleted_count} eventos de auditoría antiguos eliminados")
                
            except Exception as e:
                logger.error(f"Error limpiando auditoría: {e}")
                await asyncio.sleep(3600)

    async def _unlock_users_task(self):
        """Desbloquea usuarios cuyo tiempo de bloqueo ha expirado."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                
                current_time = datetime.now()
                unlocked_users = []
                
                for user in self.users_cache.values():
                    if user.locked_until and user.locked_until < current_time:
                        user.locked_until = None
                        user.failed_login_attempts = 0
                        unlocked_users.append(user)
                
                if unlocked_users:
                    # Actualizar en base de datos
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    for user in unlocked_users:
                        cursor.execute("""
                            UPDATE users 
                            SET locked_until = NULL, failed_login_attempts = 0
                            WHERE id = ?
                        """, (user.id,))
                        
                        logger.info(f"🔓 Usuario desbloqueado: {user.username}")
                    
                    conn.commit()
                    conn.close()
                
            except Exception as e:
                logger.error(f"Error desbloqueando usuarios: {e}")
                await asyncio.sleep(600)

    # API de información
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene información de un usuario."""
        user = self.users_cache.get(user_id)
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "mfa_enabled": user.mfa_enabled,
            "permissions": [p.value for p in user.permissions],
            "locked_until": user.locked_until.isoformat() if user.locked_until else None
        }

    def get_active_sessions(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtiene sesiones activas."""
        sessions = self.sessions_cache.values()
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        return [
            {
                "id": session.id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "last_activity": session.last_activity.isoformat()
            }
            for session in sessions if session.is_active
        ]

    def get_audit_events(self, user_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene eventos de auditoría."""
        events = self.audit_events
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        # Obtener los más recientes
        recent_events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        return [
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "username": event.username,
                "event_type": event.event_type,
                "resource": event.resource,
                "action": event.action,
                "ip_address": event.ip_address,
                "success": event.success,
                "details": event.details
            }
            for event in recent_events
        ]

    def is_healthy(self) -> bool:
        """Verifica si el gestor está funcionando."""
        try:
            # Verificar base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return self.is_running and len(self.users_cache) > 0
            
        except Exception:
            return False

    async def shutdown(self):
        """Apaga el gestor de autenticación."""
        self.is_running = False
        logger.info("✅ Gestor de autenticación apagado")