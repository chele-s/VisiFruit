"""
Sistema Ultra-Avanzado de Gestión de Configuración
=================================================

Gestor completo de configuración del sistema con:
- Configuración dinámica sin reinicio
- Validación automática de parámetros
- Historial de cambios y rollback
- Configuración por entorno (dev, test, prod)
- Templates de configuración
- Sincronización distribuida
- Backup automático de configuraciones
- API REST para gestión remota
- Notificaciones de cambios

Autor: Gabriel Calderón, Elias Bautista, Cristian Hernandez
"""

import asyncio
import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import shutil
import yaml

logger = logging.getLogger("UltraConfigManager")

class ConfigScope(Enum):
    """Ámbitos de configuración."""
    SYSTEM = "system"
    PRODUCTION = "production"
    LABELERS = "labelers"
    MOTOR = "motor"
    IA = "ia"
    API = "api"
    DATABASE = "database"
    ALERTS = "alerts"
    REPORTS = "reports"
    USER = "user"

class ConfigType(Enum):
    """Tipos de configuración."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    PASSWORD = "password"
    FILE_PATH = "file_path"
    URL = "url"
    EMAIL = "email"

@dataclass
class ConfigParameter:
    """Definición de un parámetro de configuración."""
    key: str
    value: Any
    type: ConfigType
    scope: ConfigScope
    description: str = ""
    default_value: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    requires_restart: bool = False
    sensitive: bool = False
    validation_regex: Optional[str] = None
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: str = "system"

@dataclass
class ConfigChange:
    """Registro de cambio de configuración."""
    id: str = field(default_factory=lambda: hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12])
    parameter_key: str = ""
    old_value: Any = None
    new_value: Any = None
    changed_by: str = "system"
    changed_at: datetime = field(default_factory=datetime.now)
    reason: str = ""
    applied: bool = False
    rollback_id: Optional[str] = None

class UltraConfigManager:
    """Gestor ultra-avanzado de configuración del sistema."""
    
    def __init__(self):
        self.config_file = Path("Config_Etiquetadora.json")
        self.config_backup_dir = Path("data/config_backups")
        self.config_templates_dir = Path("config_templates")
        self.environment = "production"  # dev, test, production
        
        # Configuración actual
        self.current_config: Dict[str, Any] = {}
        self.config_parameters: Dict[str, ConfigParameter] = {}
        self.config_schemas: Dict[ConfigScope, Dict[str, Any]] = {}
        
        # Historial de cambios
        self.config_history: List[ConfigChange] = []
        self.change_callbacks: List[Callable] = []
        
        # Cache de configuración
        self.config_cache = {}
        self.cache_ttl = 60  # 1 minuto
        self.last_cache_update = 0
        
        self.is_running = False

    async def initialize(self):
        """Inicializa el gestor de configuración."""
        try:
            # Crear directorios
            self.config_backup_dir.mkdir(parents=True, exist_ok=True)
            self.config_templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Detectar entorno
            self._detect_environment()
            
            # Cargar esquemas de configuración
            await self._load_config_schemas()
            
            # Cargar configuración actual
            await self._load_current_config()
            
            # Validar configuración
            await self._validate_all_config()
            
            # Crear backup inicial
            await self._backup_config("initialization")
            
            # Iniciar tareas de monitoreo
            await self._start_monitoring_tasks()
            
            self.is_running = True
            logger.info("✅ Gestor de configuración inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando gestor de configuración: {e}")
            raise

    def _detect_environment(self):
        """Detecta el entorno de ejecución."""
        # Verificar variables de entorno
        import os
        env = os.getenv("FRUPRINT_ENV", "production").lower()
        
        if env in ["dev", "development"]:
            self.environment = "development"
        elif env in ["test", "testing"]:
            self.environment = "testing"
        else:
            self.environment = "production"
        
        logger.info(f"🌍 Entorno detectado: {self.environment}")

    async def _load_config_schemas(self):
        """Carga esquemas de configuración."""
        # Esquema para configuración del sistema
        self.config_schemas[ConfigScope.SYSTEM] = {
            "installation_id": {"type": ConfigType.STRING, "required": True},
            "system_name": {"type": ConfigType.STRING, "required": True},
            "log_level": {"type": ConfigType.STRING, "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR"]},
            "max_workers": {"type": ConfigType.INTEGER, "min_value": 1, "max_value": 16},
            "debug_mode": {"type": ConfigType.BOOLEAN, "requires_restart": True}
        }
        
        # Esquema para configuración de producción
        self.config_schemas[ConfigScope.PRODUCTION] = {
            "auto_start": {"type": ConfigType.BOOLEAN},
            "max_production_rate": {"type": ConfigType.FLOAT, "min_value": 1.0, "max_value": 1000.0},
            "quality_threshold": {"type": ConfigType.FLOAT, "min_value": 0.0, "max_value": 1.0},
            "enable_statistics": {"type": ConfigType.BOOLEAN}
        }
        
        # Esquema para etiquetadoras
        self.config_schemas[ConfigScope.LABELERS] = {
            "total_labelers": {"type": ConfigType.INTEGER, "min_value": 1, "max_value": 20},
            "labeler_timeout": {"type": ConfigType.FLOAT, "min_value": 0.1, "max_value": 10.0},
            "retry_attempts": {"type": ConfigType.INTEGER, "min_value": 0, "max_value": 5},
            "maintenance_mode": {"type": ConfigType.BOOLEAN}
        }
        
        # Esquema para motor DC
        self.config_schemas[ConfigScope.MOTOR] = {
            "calibration_required": {"type": ConfigType.BOOLEAN, "requires_restart": True},
            "positioning_speed": {"type": ConfigType.FLOAT, "min_value": 0.1, "max_value": 5.0},
            "max_current": {"type": ConfigType.FLOAT, "min_value": 0.5, "max_value": 3.0},
            "emergency_stop_enabled": {"type": ConfigType.BOOLEAN}
        }
        
        # Esquema para IA
        self.config_schemas[ConfigScope.IA] = {
            "model_path": {"type": ConfigType.FILE_PATH, "required": True},
            "confidence_threshold": {"type": ConfigType.FLOAT, "min_value": 0.0, "max_value": 1.0},
            "gpu_enabled": {"type": ConfigType.BOOLEAN, "requires_restart": True},
            "batch_size": {"type": ConfigType.INTEGER, "min_value": 1, "max_value": 32}
        }
        
        # Esquema para API
        self.config_schemas[ConfigScope.API] = {
            "enabled": {"type": ConfigType.BOOLEAN, "requires_restart": True},
            "host": {"type": ConfigType.STRING},
            "port": {"type": ConfigType.INTEGER, "min_value": 1000, "max_value": 65535},
            "cors_enabled": {"type": ConfigType.BOOLEAN},
            "rate_limit": {"type": ConfigType.INTEGER, "min_value": 10, "max_value": 1000}
        }

    async def _load_current_config(self):
        """Carga la configuración actual desde el archivo."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.current_config = json.load(f)
                logger.info(f"📄 Configuración cargada desde {self.config_file}")
            else:
                # Crear configuración por defecto
                await self._create_default_config()
            
            # Convertir a objetos ConfigParameter
            await self._populate_config_parameters()
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            raise

    async def _create_default_config(self):
        """Crea configuración por defecto."""
        default_config = {
            "system_settings": {
                "installation_id": f"fruprint_{int(time.time())}",
                "system_name": "FruPrint Ultra System",
                "log_level": "INFO",
                "max_workers": 4,
                "debug_mode": self.environment != "production"
            },
            "production_settings": {
                "auto_start": False,
                "max_production_rate": 100.0,
                "quality_threshold": 0.85,
                "enable_statistics": True
            },
            "labeler_settings": {
                "total_labelers": 12,
                "labeler_timeout": 5.0,
                "retry_attempts": 3,
                "maintenance_mode": False
            },
            "motor_controller_settings": {
                "calibration_required": True,
                "positioning_speed": 1.0,
                "max_current": 2.0,
                "emergency_stop_enabled": True
            },
            "ia_settings": {
                "model_path": "IA_Etiquetado/Models/best.pt",
                "confidence_threshold": 0.8,
                "gpu_enabled": False,
                "batch_size": 1
            },
            "api_settings": {
                "enabled": True,
                "host": "0.0.0.0",
                "port": 8001,
                "cors_enabled": True,
                "rate_limit": 100
            }
        }
        
        self.current_config = default_config
        await self._save_config()
        logger.info("🆕 Configuración por defecto creada")

    async def _populate_config_parameters(self):
        """Convierte la configuración a objetos ConfigParameter."""
        self.config_parameters.clear()
        
        for section_name, section_data in self.current_config.items():
            # Determinar scope basado en el nombre de la sección
            scope = self._get_scope_from_section(section_name)
            
            for key, value in section_data.items():
                full_key = f"{section_name}.{key}"
                
                # Obtener esquema si existe
                schema_info = {}
                if scope in self.config_schemas and key in self.config_schemas[scope]:
                    schema_info = self.config_schemas[scope][key]
                
                # Crear parámetro
                param = ConfigParameter(
                    key=full_key,
                    value=value,
                    type=schema_info.get("type", self._infer_type(value)),
                    scope=scope,
                    description=schema_info.get("description", ""),
                    default_value=schema_info.get("default", value),
                    min_value=schema_info.get("min_value"),
                    max_value=schema_info.get("max_value"),
                    allowed_values=schema_info.get("allowed_values"),
                    requires_restart=schema_info.get("requires_restart", False),
                    sensitive=schema_info.get("sensitive", False)
                )
                
                self.config_parameters[full_key] = param

    def _get_scope_from_section(self, section_name: str) -> ConfigScope:
        """Determina el scope basado en el nombre de la sección."""
        section_lower = section_name.lower()
        
        if "system" in section_lower:
            return ConfigScope.SYSTEM
        elif "production" in section_lower:
            return ConfigScope.PRODUCTION
        elif "labeler" in section_lower:
            return ConfigScope.LABELERS
        elif "motor" in section_lower:
            return ConfigScope.MOTOR
        elif "ia" in section_lower or "ai" in section_lower:
            return ConfigScope.IA
        elif "api" in section_lower:
            return ConfigScope.API
        elif "database" in section_lower or "db" in section_lower:
            return ConfigScope.DATABASE
        elif "alert" in section_lower:
            return ConfigScope.ALERTS
        elif "report" in section_lower:
            return ConfigScope.REPORTS
        else:
            return ConfigScope.SYSTEM

    def _infer_type(self, value: Any) -> ConfigType:
        """Infiere el tipo de configuración basado en el valor."""
        if isinstance(value, bool):
            return ConfigType.BOOLEAN
        elif isinstance(value, int):
            return ConfigType.INTEGER
        elif isinstance(value, float):
            return ConfigType.FLOAT
        elif isinstance(value, list):
            return ConfigType.ARRAY
        elif isinstance(value, dict):
            return ConfigType.OBJECT
        else:
            return ConfigType.STRING

    async def _validate_all_config(self):
        """Valida toda la configuración actual."""
        errors = []
        
        for param in self.config_parameters.values():
            error = await self._validate_parameter(param)
            if error:
                errors.append(f"{param.key}: {error}")
        
        if errors:
            logger.warning(f"⚠️ Errores de validación encontrados: {'; '.join(errors)}")
        else:
            logger.info("✅ Configuración validada correctamente")

    async def _validate_parameter(self, param: ConfigParameter) -> Optional[str]:
        """Valida un parámetro individual."""
        try:
            value = param.value
            
            # Validar tipo
            if param.type == ConfigType.INTEGER and not isinstance(value, int):
                return f"Debe ser un entero, recibido: {type(value)}"
            elif param.type == ConfigType.FLOAT and not isinstance(value, (int, float)):
                return f"Debe ser un número, recibido: {type(value)}"
            elif param.type == ConfigType.BOOLEAN and not isinstance(value, bool):
                return f"Debe ser booleano, recibido: {type(value)}"
            
            # Validar rangos
            if param.min_value is not None and isinstance(value, (int, float)):
                if value < param.min_value:
                    return f"Valor {value} menor que el mínimo {param.min_value}"
            
            if param.max_value is not None and isinstance(value, (int, float)):
                if value > param.max_value:
                    return f"Valor {value} mayor que el máximo {param.max_value}"
            
            # Validar valores permitidos
            if param.allowed_values and value not in param.allowed_values:
                return f"Valor {value} no está en valores permitidos: {param.allowed_values}"
            
            # Validar archivos
            if param.type == ConfigType.FILE_PATH and isinstance(value, str):
                if not Path(value).exists():
                    return f"Archivo no encontrado: {value}"
            
            return None
            
        except Exception as e:
            return f"Error de validación: {e}"

    # API principal de gestión de configuración
    async def get_config(self, key: Optional[str] = None, scope: Optional[ConfigScope] = None) -> Dict[str, Any]:
        """Obtiene configuración por clave o scope."""
        # Usar cache si está vigente
        cache_key = f"{key}_{scope.value if scope else 'all'}"
        current_time = time.time()
        
        if (cache_key in self.config_cache and 
            current_time - self.last_cache_update < self.cache_ttl):
            return self.config_cache[cache_key]
        
        # Obtener configuración
        if key:
            # Configuración específica
            if key in self.config_parameters:
                result = asdict(self.config_parameters[key])
            else:
                # Buscar en configuración anidada
                result = self._get_nested_config(key)
        elif scope:
            # Configuración por scope
            result = {
                k: asdict(v) for k, v in self.config_parameters.items()
                if v.scope == scope
            }
        else:
            # Toda la configuración
            result = self.current_config.copy()
        
        # Actualizar cache
        self.config_cache[cache_key] = result
        self.last_cache_update = current_time
        
        return result

    def _get_nested_config(self, key: str) -> Any:
        """Obtiene configuración anidada usando notación punto."""
        keys = key.split('.')
        current = self.current_config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current

    async def set_config(self, key: str, value: Any, changed_by: str = "system", 
                        reason: str = "", apply_immediately: bool = True) -> bool:
        """Establece un valor de configuración."""
        try:
            # Validar el nuevo valor
            if key in self.config_parameters:
                param = self.config_parameters[key]
                param_copy = ConfigParameter(
                    key=param.key,
                    value=value,
                    type=param.type,
                    scope=param.scope,
                    min_value=param.min_value,
                    max_value=param.max_value,
                    allowed_values=param.allowed_values
                )
                
                error = await self._validate_parameter(param_copy)
                if error:
                    logger.error(f"Error de validación para {key}: {error}")
                    return False
            
            # Obtener valor anterior
            old_value = self._get_nested_config(key)
            
            # Crear registro de cambio
            change = ConfigChange(
                parameter_key=key,
                old_value=old_value,
                new_value=value,
                changed_by=changed_by,
                reason=reason
            )
            
            if apply_immediately:
                # Aplicar cambio
                success = await self._apply_config_change(change)
                if success:
                    change.applied = True
                    self.config_history.append(change)
                    
                    # Notificar callbacks
                    await self._notify_config_change(change)
                    
                    logger.info(f"🔧 Configuración actualizada: {key} = {value}")
                    return True
                else:
                    return False
            else:
                # Guardar cambio pendiente
                self.config_history.append(change)
                logger.info(f"📝 Cambio de configuración programado: {key} = {value}")
                return True
                
        except Exception as e:
            logger.error(f"Error estableciendo configuración {key}: {e}")
            return False

    async def _apply_config_change(self, change: ConfigChange) -> bool:
        """Aplica un cambio de configuración."""
        try:
            # Actualizar configuración anidada
            keys = change.parameter_key.split('.')
            current = self.current_config
            
            # Navegar hasta el penúltimo nivel
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Establecer el valor final
            current[keys[-1]] = change.new_value
            
            # Actualizar parámetro si existe
            if change.parameter_key in self.config_parameters:
                self.config_parameters[change.parameter_key].value = change.new_value
                self.config_parameters[change.parameter_key].updated_at = datetime.now()
                self.config_parameters[change.parameter_key].updated_by = change.changed_by
            
            # Guardar configuración
            await self._save_config()
            
            # Limpiar cache
            self.config_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando cambio de configuración: {e}")
            return False

    async def _save_config(self):
        """Guarda la configuración actual al archivo."""
        try:
            # Crear backup antes de guardar
            if self.config_file.exists():
                backup_name = f"config_backup_{int(time.time())}.json"
                backup_path = self.config_backup_dir / backup_name
                shutil.copy2(self.config_file, backup_path)
            
            # Guardar configuración
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Configuración guardada en {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            raise

    async def rollback_config(self, change_id: Optional[str] = None) -> bool:
        """Revierte cambios de configuración."""
        try:
            if change_id:
                # Rollback específico
                change = next((c for c in self.config_history if c.id == change_id), None)
                if not change:
                    logger.error(f"Cambio {change_id} no encontrado")
                    return False
                
                # Crear cambio inverso
                rollback_change = ConfigChange(
                    parameter_key=change.parameter_key,
                    old_value=change.new_value,
                    new_value=change.old_value,
                    changed_by="rollback_system",
                    reason=f"Rollback de cambio {change_id}",
                    rollback_id=change.id
                )
                
                success = await self._apply_config_change(rollback_change)
                if success:
                    rollback_change.applied = True
                    self.config_history.append(rollback_change)
                    logger.info(f"🔄 Rollback aplicado para cambio {change_id}")
                    return True
            else:
                # Rollback del último cambio aplicado
                last_change = next((c for c in reversed(self.config_history) if c.applied), None)
                if last_change:
                    return await self.rollback_config(last_change.id)
                else:
                    logger.warning("No hay cambios para revertir")
                    return False
                    
        except Exception as e:
            logger.error(f"Error en rollback: {e}")
            return False

    async def _backup_config(self, reason: str = "manual"):
        """Crea backup de la configuración actual."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_{reason}_{timestamp}.json"
            backup_path = self.config_backup_dir / backup_name
            
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "environment": self.environment,
                "config": self.current_config.copy()
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Backup creado: {backup_name}")
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")

    async def restore_from_backup(self, backup_file: str) -> bool:
        """Restaura configuración desde un backup."""
        try:
            backup_path = self.config_backup_dir / backup_file
            
            if not backup_path.exists():
                logger.error(f"Backup no encontrado: {backup_file}")
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validar backup
            if "config" not in backup_data:
                logger.error("Backup inválido: falta sección 'config'")
                return False
            
            # Crear backup de la configuración actual
            await self._backup_config("before_restore")
            
            # Restaurar configuración
            self.current_config = backup_data["config"]
            await self._populate_config_parameters()
            await self._save_config()
            
            logger.info(f"🔄 Configuración restaurada desde {backup_file}")
            
            # Notificar cambio masivo
            change = ConfigChange(
                parameter_key="*",
                old_value="current_config",
                new_value="restored_config",
                changed_by="restore_system",
                reason=f"Restored from {backup_file}",
                applied=True
            )
            
            self.config_history.append(change)
            await self._notify_config_change(change)
            
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False

    async def export_config(self, format: str = "json", include_sensitive: bool = False) -> str:
        """Exporta configuración a diferentes formatos."""
        try:
            # Preparar datos para exportación
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "environment": self.environment,
                    "version": "3.0.0"
                },
                "configuration": {}
            }
            
            # Filtrar datos sensibles si es necesario
            for key, param in self.config_parameters.items():
                if param.sensitive and not include_sensitive:
                    continue
                
                export_data["configuration"][key] = {
                    "value": param.value if not param.sensitive else "***HIDDEN***",
                    "type": param.type.value,
                    "scope": param.scope.value,
                    "description": param.description
                }
            
            # Generar archivo según formato
            timestamp = int(time.time())
            
            if format.lower() == "json":
                filename = f"config_export_{timestamp}.json"
                filepath = self.config_backup_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
            elif format.lower() == "yaml":
                filename = f"config_export_{timestamp}.yaml"
                filepath = self.config_backup_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
                    
            else:
                raise ValueError(f"Formato no soportado: {format}")
            
            logger.info(f"📤 Configuración exportada: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exportando configuración: {e}")
            raise

    # Callbacks y notificaciones
    def register_change_callback(self, callback: Callable):
        """Registra callback para cambios de configuración."""
        self.change_callbacks.append(callback)

    async def _notify_config_change(self, change: ConfigChange):
        """Notifica cambios a callbacks registrados."""
        for callback in self.change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change)
                else:
                    callback(change)
            except Exception as e:
                logger.error(f"Error en callback de configuración: {e}")

    # Tareas de monitoreo
    async def _start_monitoring_tasks(self):
        """Inicia tareas de monitoreo."""
        asyncio.create_task(self._config_file_watcher())
        asyncio.create_task(self._periodic_backup_task())
        asyncio.create_task(self._cleanup_old_backups_task())

    async def _config_file_watcher(self):
        """Monitorea cambios en el archivo de configuración."""
        last_modified = 0
        
        while self.is_running:
            try:
                if self.config_file.exists():
                    current_modified = self.config_file.stat().st_mtime
                    
                    if current_modified > last_modified and last_modified > 0:
                        logger.info("📁 Archivo de configuración modificado externamente")
                        await self._load_current_config()
                        await self._validate_all_config()
                        
                        # Notificar cambio externo
                        change = ConfigChange(
                            parameter_key="*",
                            old_value="previous_config",
                            new_value="reloaded_config",
                            changed_by="external_file_change",
                            reason="File modified externally",
                            applied=True
                        )
                        
                        self.config_history.append(change)
                        await self._notify_config_change(change)
                    
                    last_modified = current_modified
                
                await asyncio.sleep(5)  # Verificar cada 5 segundos
                
            except Exception as e:
                logger.error(f"Error en watcher de configuración: {e}")
                await asyncio.sleep(10)

    async def _periodic_backup_task(self):
        """Tarea de backup periódico."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Cada hora
                await self._backup_config("periodic")
                
            except Exception as e:
                logger.error(f"Error en backup periódico: {e}")
                await asyncio.sleep(1800)  # Reintentar en 30 minutos

    async def _cleanup_old_backups_task(self):
        """Limpia backups antiguos."""
        while self.is_running:
            try:
                await asyncio.sleep(86400)  # Cada 24 horas
                
                # Mantener solo los últimos 30 backups
                backup_files = sorted(
                    self.config_backup_dir.glob("config_*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )
                
                for backup in backup_files[30:]:
                    backup.unlink()
                    logger.info(f"🗑️ Backup antiguo eliminado: {backup.name}")
                
            except Exception as e:
                logger.error(f"Error limpiando backups: {e}")
                await asyncio.sleep(3600)

    # API de información
    def get_config_parameters(self, scope: Optional[ConfigScope] = None) -> List[Dict[str, Any]]:
        """Obtiene lista de parámetros de configuración."""
        params = self.config_parameters.values()
        
        if scope:
            params = [p for p in params if p.scope == scope]
        
        return [
            {
                "key": p.key,
                "value": p.value if not p.sensitive else "***HIDDEN***",
                "type": p.type.value,
                "scope": p.scope.value,
                "description": p.description,
                "requires_restart": p.requires_restart,
                "updated_at": p.updated_at.isoformat()
            }
            for p in params
        ]

    def get_config_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene historial de cambios."""
        recent_changes = list(reversed(self.config_history))[:limit]
        
        return [
            {
                "id": c.id,
                "parameter_key": c.parameter_key,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "changed_by": c.changed_by,
                "changed_at": c.changed_at.isoformat(),
                "reason": c.reason,
                "applied": c.applied,
                "rollback_id": c.rollback_id
            }
            for c in recent_changes
        ]

    def get_config_templates(self) -> List[str]:
        """Obtiene lista de templates disponibles."""
        try:
            return [f.name for f in self.config_templates_dir.glob("*.json")]
        except:
            return []

    def get_backup_files(self) -> List[Dict[str, Any]]:
        """Obtiene lista de archivos de backup."""
        try:
            backups = []
            for backup_file in self.config_backup_dir.glob("config_*.json"):
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return sorted(backups, key=lambda x: x["modified_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo backups: {e}")
            return []

    def is_healthy(self) -> bool:
        """Verifica si el gestor está funcionando correctamente."""
        return (
            self.is_running and 
            self.config_file.exists() and 
            bool(self.config_parameters)
        )

    async def shutdown(self):
        """Apaga el gestor de configuración."""
        logger.info("Apagando gestor de configuración...")
        
        self.is_running = False
        
        # Crear backup final
        try:
            await self._backup_config("shutdown")
        except:
            pass
        
        logger.info("✅ Gestor de configuración apagado")