# utils/config_validator.py
"""
Sistema de Validación de Configuración Industrial - FruPrint
==========================================================

Módulo avanzado para validación, normalización y gestión de configuraciones:
- Validación de esquemas con Pydantic
- Validación de hardware y conectividad
- Migración automática de configuraciones
- Generación de configuraciones optimizadas
- Sistema de profiles de configuración
- Validación de seguridad y cumplimiento

Autor(es): Gabriel Calderón, Elias Bautista, Cristian Hernandez
Fecha: Julio 2025
Versión: 2.0 - Edición Industrial
"""

import json
import logging
import os
import shutil
import time
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

import jsonschema
from pydantic import BaseModel, Field, validator, ValidationError

logger = logging.getLogger(__name__)

class ConfigProfile(Enum):
    """Perfiles de configuración predefinidos."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high_performance"
    ENERGY_EFFICIENT = "energy_efficient"
    SAFETY_CRITICAL = "safety_critical"

class ValidationLevel(Enum):
    """Niveles de validación."""
    BASIC = auto()
    STANDARD = auto()
    STRICT = auto()
    INDUSTRIAL = auto()

class SystemSettings(BaseModel):
    """Configuración del sistema."""
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    debug_mode: bool = False
    performance_mode: str = Field("balanced", pattern="^(low_power|balanced|high_performance)$")
    enable_telemetry: bool = True
    system_name: str = Field(..., min_length=3, max_length=50)
    installation_id: str = Field(..., pattern="^[A-Z0-9-]+$")
    timezone: str = "UTC"

class SecuritySettings(BaseModel):
    """Configuración de seguridad."""
    enable_authentication: bool = True
    session_timeout_minutes: int = Field(30, ge=5, le=480)
    max_failed_attempts: int = Field(5, ge=1, le=20)
    lockout_duration_minutes: int = Field(15, ge=1, le=1440)
    enable_audit_log: bool = True
    enable_encryption: bool = True

class CameraSettings(BaseModel):
    """Configuración de cámara."""
    type: str = Field("usb_webcam", pattern="^(usb_webcam|csi_camera|ip_camera|mock)$")
    device_id: int = Field(0, ge=0, le=10)
    frame_width: int = Field(1280, ge=320, le=4096)
    frame_height: int = Field(720, ge=240, le=2160)
    fps: int = Field(30, ge=1, le=120)
    buffer_size: int = Field(10, ge=1, le=100)
    
    @validator('frame_width', 'frame_height')
    def validate_resolution(cls, v):
        if v % 8 != 0:  # Múltiplo de 8 para mejor compatibilidad
            raise ValueError("Resolución debe ser múltiplo de 8")
        return v

class AIModelSettings(BaseModel):
    """Configuración del modelo de IA."""
    model_path: str = Field(..., min_length=5)
    confidence_threshold: float = Field(0.65, ge=0.1, le=1.0)
    iou_threshold: float = Field(0.45, ge=0.1, le=1.0)
    num_workers: int = Field(2, ge=1, le=16)
    request_timeout_seconds: float = Field(10.0, ge=1.0, le=300.0)

class ConveyorBeltSettings(BaseModel):
    """Configuración de banda transportadora."""
    type: str = Field("dc_motor_pwm", pattern="^(dc_motor_pwm|stepper|servo)$")
    belt_speed_mps: float = Field(0.15, ge=0.01, le=2.0)
    max_speed_mps: float = Field(0.5, ge=0.1, le=5.0)
    enable_speed_control: bool = True
    
    @validator('max_speed_mps')
    def validate_max_speed(cls, v, values):
        if 'belt_speed_mps' in values and v <= values['belt_speed_mps']:
            raise ValueError("max_speed_mps debe ser mayor que belt_speed_mps")
        return v

class SensorSettings(BaseModel):
    """Configuración de sensores."""
    trigger_sensor: Dict[str, Any]
    secondary_sensors: List[Dict[str, Any]] = []
    environmental_sensors: Dict[str, Any] = {}

class LabelerSettings(BaseModel):
    """Configuración del etiquetador."""
    type: str = Field("solenoid", pattern="^(solenoid|servo|stepper|pneumatic)$")
    pin: int = Field(26, ge=1, le=40)
    max_activation_time_seconds: float = Field(60.0, ge=0.1, le=300.0)
    distance_camera_to_labeler_m: float = Field(0.5, ge=0.1, le=5.0)
    fruit_avg_width_m: float = Field(0.08, ge=0.01, le=0.5)

class FruPrintConfig(BaseModel):
    """Configuración principal del sistema FruPrint."""
    system_metadata: Dict[str, Any]
    system_settings: SystemSettings
    security_settings: SecuritySettings
    camera_settings: CameraSettings
    ai_model_settings: AIModelSettings
    conveyor_belt_settings: ConveyorBeltSettings
    sensor_settings: SensorSettings
    labeler_settings: LabelerSettings
    api_settings: Dict[str, Any] = {}
    monitoring_settings: Dict[str, Any] = {}
    performance_settings: Dict[str, Any] = {}

class ConfigValidator:
    """
    Validador avanzado de configuraciones con características industriales.
    
    Características:
    - Validación de esquemas con Pydantic
    - Validación de hardware
    - Migración automática
    - Optimización de configuraciones
    - Perfiles predefinidos
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.error_history: List[Dict] = []
        self.validation_cache = {}
        
        # Esquema JSON para validación adicional
        self.json_schema = self._load_json_schema()
        
        logger.info(f"ConfigValidator inicializado (nivel: {validation_level.name})")
    
    def _load_json_schema(self) -> Dict:
        """Carga el esquema JSON para validación."""
        return {
            "type": "object",
            "required": [
                "system_metadata",
                "system_settings", 
                "camera_settings",
                "ai_model_settings",
                "conveyor_belt_settings",
                "sensor_settings",
                "labeler_settings"
            ],
            "properties": {
                "system_metadata": {
                    "type": "object",
                    "required": ["config_version"]
                },
                "system_settings": {
                    "type": "object",
                    "required": ["system_name", "installation_id"]
                }
            }
        }
    
    def validate_config_file(self, config_path: Union[str, Path]) -> Tuple[bool, List[str]]:
        """
        Valida un archivo de configuración completo.
        
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        try:
            config_path = Path(config_path)
            
            # Verificar que el archivo existe
            if not config_path.exists():
                return False, [f"Archivo de configuración no encontrado: {config_path}"]
            
            # Cargar JSON
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return self.validate_config_dict(config_data)
            
        except json.JSONDecodeError as e:
            error_msg = f"Error de sintaxis JSON: {e}"
            self._record_error("json_syntax", error_msg)
            return False, [error_msg]
        
        except Exception as e:
            error_msg = f"Error inesperado validando configuración: {e}"
            self._record_error("validation_error", error_msg)
            return False, [error_msg]
    
    def validate_config_dict(self, config_data: Dict) -> Tuple[bool, List[str]]:
        """Valida un diccionario de configuración."""
        errors = []
        
        try:
            # Validación de esquema JSON
            jsonschema.validate(config_data, self.json_schema)
            
            # Validación con Pydantic
            try:
                validated_config = FruPrintConfig(**config_data)
                
                # Validaciones adicionales según el nivel
                if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.INDUSTRIAL]:
                    additional_errors = self._perform_advanced_validation(validated_config)
                    errors.extend(additional_errors)
                
                # Validación de hardware si es necesario
                if self.validation_level == ValidationLevel.INDUSTRIAL:
                    hardware_errors = self._validate_hardware_compatibility(validated_config)
                    errors.extend(hardware_errors)
                
            except ValidationError as e:
                for error in e.errors():
                    field = " -> ".join(str(x) for x in error['loc'])
                    message = error['msg']
                    errors.append(f"Campo '{field}': {message}")
            
        except jsonschema.ValidationError as e:
            errors.append(f"Error de esquema JSON: {e.message}")
        
        # Registrar errores
        if errors:
            self._record_error("validation_failed", f"{len(errors)} errores encontrados")
        
        return len(errors) == 0, errors
    
    def _perform_advanced_validation(self, config: FruPrintConfig) -> List[str]:
        """Realiza validaciones avanzadas específicas."""
        errors = []
        
        # Validar compatibilidad entre componentes
        belt_speed = config.conveyor_belt_settings.belt_speed_mps
        camera_fps = config.camera_settings.fps
        
        # Verificar que la velocidad de la banda es compatible con el FPS de la cámara
        max_recommended_speed = camera_fps * 0.01  # 1cm por frame máximo
        if belt_speed > max_recommended_speed:
            errors.append(
                f"Velocidad de banda ({belt_speed} m/s) muy alta para FPS de cámara ({camera_fps}). "
                f"Máximo recomendado: {max_recommended_speed:.3f} m/s"
            )
        
        # Validar distancia cámara-etiquetador vs velocidad
        distance = config.labeler_settings.distance_camera_to_labeler_m
        min_processing_time = 0.1  # 100ms mínimo para procesamiento
        min_distance = belt_speed * min_processing_time
        
        if distance < min_distance:
            errors.append(
                f"Distancia cámara-etiquetador ({distance}m) muy corta para velocidad actual. "
                f"Mínimo recomendado: {min_distance:.3f}m"
            )
        
        # Validar configuración de pines GPIO (no duplicados)
        used_pins = []
        
        # Recopilar pines usados
        if hasattr(config.conveyor_belt_settings, 'enable_pin'):
            used_pins.append(config.conveyor_belt_settings.enable_pin)
        
        used_pins.append(config.labeler_settings.pin)
        
        if 'pin' in config.sensor_settings.trigger_sensor:
            used_pins.append(config.sensor_settings.trigger_sensor['pin'])
        
        # Verificar duplicados
        duplicate_pins = [pin for pin in set(used_pins) if used_pins.count(pin) > 1]
        if duplicate_pins:
            errors.append(f"Pines GPIO duplicados detectados: {duplicate_pins}")
        
        return errors
    
    def _validate_hardware_compatibility(self, config: FruPrintConfig) -> List[str]:
        """Valida compatibilidad con hardware específico."""
        errors = []
        
        # Verificar que el modelo de IA existe
        model_path = Path(config.ai_model_settings.model_path)
        if not model_path.exists():
            errors.append(f"Modelo de IA no encontrado: {model_path}")
        
        # Verificar capacidad de resolución vs recursos
        resolution = config.camera_settings.frame_width * config.camera_settings.frame_height
        fps = config.camera_settings.fps
        
        # Estimación de ancho de banda requerido (aproximado)
        bandwidth_mbps = (resolution * fps * 3 * 8) / (1024 * 1024)  # RGB, 8 bits por canal
        
        if bandwidth_mbps > 100:  # Límite aproximado para USB 2.0
            errors.append(
                f"Configuración de video requiere {bandwidth_mbps:.1f} Mbps. "
                "Puede ser incompatible con USB 2.0"
            )
        
        return errors
    
    def _record_error(self, error_type: str, message: str):
        """Registra error en el historial."""
        self.error_history.append({
            'timestamp': datetime.now(),
            'type': error_type,
            'message': message
        })
        
        # Mantener solo los últimos 100 errores
        if len(self.error_history) > 100:
            self.error_history.pop(0)
    
    def create_config_from_profile(self, profile: ConfigProfile, 
                                 installation_id: str = "FRUPRINT-001") -> Dict:
        """Crea configuración basada en un perfil predefinido."""
        
        base_config = {
            "system_metadata": {
                "config_version": "2.0.0",
                "last_updated": datetime.now().isoformat(),
                "created_by": f"ConfigValidator - Profile {profile.value}",
                "description": f"Configuración generada automáticamente para perfil {profile.value}",
                "hardware_profile": "raspberry_pi_5_industrial",
                "deployment_environment": profile.value
            },
            "system_settings": {
                "system_name": f"FruPrint-{profile.value.title()}",
                "installation_id": installation_id,
                "log_level": "DEBUG" if profile == ConfigProfile.DEVELOPMENT else "INFO",
                "debug_mode": profile == ConfigProfile.DEVELOPMENT,
                "enable_telemetry": profile != ConfigProfile.DEVELOPMENT,
                "performance_mode": self._get_performance_mode(profile),
                "timezone": "UTC"
            }
        }
        
        # Configuraciones específicas por perfil
        if profile == ConfigProfile.HIGH_PERFORMANCE:
            base_config.update(self._get_high_performance_config())
        elif profile == ConfigProfile.ENERGY_EFFICIENT:
            base_config.update(self._get_energy_efficient_config())
        elif profile == ConfigProfile.SAFETY_CRITICAL:
            base_config.update(self._get_safety_critical_config())
        else:
            base_config.update(self._get_standard_config())
        
        return base_config
    
    def _get_performance_mode(self, profile: ConfigProfile) -> str:
        """Obtiene el modo de rendimiento según el perfil."""
        performance_map = {
            ConfigProfile.DEVELOPMENT: "balanced",
            ConfigProfile.TESTING: "balanced", 
            ConfigProfile.STAGING: "high_performance",
            ConfigProfile.PRODUCTION: "high_performance",
            ConfigProfile.HIGH_PERFORMANCE: "high_performance",
            ConfigProfile.ENERGY_EFFICIENT: "low_power",
            ConfigProfile.SAFETY_CRITICAL: "balanced"
        }
        return performance_map.get(profile, "balanced")
    
    def _get_high_performance_config(self) -> Dict:
        """Configuración optimizada para alto rendimiento."""
        return {
            "camera_settings": {
                "type": "usb_webcam",
                "frame_width": 1920,
                "frame_height": 1080,
                "fps": 60,
                "buffer_size": 20
            },
            "ai_model_settings": {
                "num_workers": 8,
                "enable_auto_scaling": True,
                "max_workers": 16,
                "confidence_threshold": 0.7
            },
            "conveyor_belt_settings": {
                "belt_speed_mps": 0.25,
                "max_speed_mps": 0.8
            }
        }
    
    def _get_energy_efficient_config(self) -> Dict:
        """Configuración optimizada para eficiencia energética."""
        return {
            "camera_settings": {
                "type": "usb_webcam",
                "frame_width": 1280,
                "frame_height": 720,
                "fps": 15,
                "buffer_size": 5
            },
            "ai_model_settings": {
                "num_workers": 2,
                "enable_auto_scaling": False,
                "confidence_threshold": 0.65
            },
            "conveyor_belt_settings": {
                "belt_speed_mps": 0.1,
                "max_speed_mps": 0.3
            }
        }
    
    def _get_safety_critical_config(self) -> Dict:
        """Configuración con máxima seguridad y redundancia."""
        return {
            "camera_settings": {
                "type": "usb_webcam",
                "frame_width": 1920,
                "frame_height": 1080,
                "fps": 30,
                "buffer_size": 15
            },
            "security_settings": {
                "enable_authentication": True,
                "session_timeout_minutes": 15,
                "max_failed_attempts": 3,
                "enable_audit_log": True,
                "enable_encryption": True
            },
            "monitoring_settings": {
                "enable_prometheus_metrics": True,
                "enable_email_alerts": True,
                "enable_webhook_alerts": True
            }
        }
    
    def _get_standard_config(self) -> Dict:
        """Configuración estándar balanceada."""
        return {
            "camera_settings": {
                "type": "usb_webcam",
                "device_id": 0,
                "frame_width": 1280,
                "frame_height": 720,
                "fps": 30,
                "buffer_size": 10
            },
            "ai_model_settings": {
                "model_path": "IA_Etiquetado/Models/best_fruit_model.pt",
                "confidence_threshold": 0.65,
                "num_workers": 4,
                "request_timeout_seconds": 10.0
            },
            "conveyor_belt_settings": {
                "type": "dc_motor_pwm",
                "belt_speed_mps": 0.15,
                "max_speed_mps": 0.5,
                "enable_speed_control": True
            },
            "sensor_settings": {
                "trigger_sensor": {
                    "type": "infrared",
                    "pin": 16,
                    "debounce_time_ms": 50
                }
            },
            "labeler_settings": {
                "type": "solenoid",
                "pin": 26,
                "distance_camera_to_labeler_m": 0.5,
                "fruit_avg_width_m": 0.08,
                "max_activation_time_seconds": 60.0
            }
        }
    
    def migrate_config(self, old_config_path: Union[str, Path], 
                      backup: bool = True) -> Tuple[bool, str]:
        """
        Migra configuración antigua a nueva versión.
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            old_config_path = Path(old_config_path)
            
            if not old_config_path.exists():
                return False, f"Archivo no encontrado: {old_config_path}"
            
            # Crear backup si se solicita
            if backup:
                backup_path = old_config_path.with_suffix(f'.backup.{int(time.time())}')
                shutil.copy2(old_config_path, backup_path)
                logger.info(f"Backup creado: {backup_path}")
            
            # Cargar configuración antigua
            with open(old_config_path, 'r') as f:
                old_config = json.load(f)
            
            # Detectar versión
            version = old_config.get('system_metadata', {}).get('config_version', '1.0.0')
            
            # Migrar según la versión
            if version.startswith('1.'):
                migrated_config = self._migrate_from_v1(old_config)
            else:
                return False, f"Versión no soportada para migración: {version}"
            
            # Validar configuración migrada
            is_valid, errors = self.validate_config_dict(migrated_config)
            
            if not is_valid:
                return False, f"Configuración migrada inválida: {'; '.join(errors)}"
            
            # Guardar configuración migrada
            with open(old_config_path, 'w') as f:
                json.dump(migrated_config, f, indent=2)
            
            return True, "Migración completada exitosamente"
            
        except Exception as e:
            error_msg = f"Error durante migración: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _migrate_from_v1(self, old_config: Dict) -> Dict:
        """Migra configuración desde versión 1.x."""
        
        # Crear estructura base v2
        migrated = {
            "system_metadata": {
                "config_version": "2.0.0",
                "last_updated": datetime.now().isoformat(),
                "created_by": "ConfigValidator Migration",
                "description": "Configuración migrada desde v1.x",
                "hardware_profile": "raspberry_pi_5_industrial",
                "deployment_environment": "production"
            }
        }
        
        # Migrar configuraciones conocidas
        if 'system_settings' in old_config:
            migrated['system_settings'] = old_config['system_settings']
            
        if 'camera_settings' in old_config:
            camera_config = old_config['camera_settings'].copy()
            # Agregar campos nuevos con valores por defecto
            camera_config.setdefault('buffer_size', 10)
            camera_config.setdefault('auto_optimize', True)
            migrated['camera_settings'] = camera_config
        
        # Continuar con otros componentes...
        # [Lógica de migración específica para cada sección]
        
        return migrated
    
    def optimize_config_for_hardware(self, config_data: Dict, 
                                   hardware_info: Dict) -> Dict:
        """Optimiza configuración para hardware específico."""
        
        optimized = config_data.copy()
        
        # Optimizar según CPU
        cpu_cores = hardware_info.get('cpu_cores', 4)
        ram_gb = hardware_info.get('ram_gb', 4)
        
        # Ajustar número de workers de IA
        optimal_workers = min(cpu_cores, max(2, cpu_cores // 2))
        optimized['ai_model_settings']['num_workers'] = optimal_workers
        
        # Ajustar resolución según RAM
        if ram_gb < 2:
            optimized['camera_settings']['frame_width'] = 640
            optimized['camera_settings']['frame_height'] = 480
        elif ram_gb < 4:
            optimized['camera_settings']['frame_width'] = 1280
            optimized['camera_settings']['frame_height'] = 720
        
        # Ajustar buffer según RAM
        buffer_size = min(20, max(5, int(ram_gb * 2.5)))
        optimized['camera_settings']['buffer_size'] = buffer_size
        
        logger.info(f"Configuración optimizada para {cpu_cores} cores, {ram_gb}GB RAM")
        
        return optimized
    
    def get_validation_report(self) -> Dict:
        """Genera reporte de validación."""
        
        error_types = {}
        for error in self.error_history:
            error_type = error['type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_validations': len(self.validation_cache),
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'validation_level': self.validation_level.name,
            'last_error': self.error_history[-1] if self.error_history else None
        }

# --- Funciones de utilidad ---

def validate_config(config_path: str, level: ValidationLevel = ValidationLevel.STANDARD) -> bool:
    """Función de conveniencia para validar configuración."""
    validator = ConfigValidator(level)
    is_valid, errors = validator.validate_config_file(config_path)
    
    if not is_valid:
        logger.error(f"Configuración inválida: {'; '.join(errors)}")
    
    return is_valid

def create_default_config(profile: ConfigProfile = ConfigProfile.PRODUCTION, 
                         output_path: str = "Config_Etiquetadora_Generated.json") -> bool:
    """Crea configuración por defecto."""
    try:
        validator = ConfigValidator()
        config = validator.create_config_from_profile(profile)
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuración creada: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creando configuración: {e}")
        return False

# --- Punto de entrada principal ---

if __name__ == "__main__":
    """Script de prueba para validación de configuración."""
    
    # Crear validador
    validator = ConfigValidator(ValidationLevel.INDUSTRIAL)
    
    # Probar validación
    config_file = "Config_Etiquetadora.json"
    
    print(f"=== Validando {config_file} ===")
    
    is_valid, errors = validator.validate_config_file(config_file)
    
    if is_valid:
        print("✓ Configuración válida")
    else:
        print("✗ Configuración inválida:")
        for error in errors:
            print(f"  - {error}")
    
    # Generar reporte
    report = validator.get_validation_report()
    print(f"\nReporte: {report}")
    
    print("=== Validación Completada ===")