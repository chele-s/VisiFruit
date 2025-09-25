# fruprint_system/config/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional

class GPIOValidator:
    @validator('*', pre=True, allow_reuse=True)
    def valid_pin(cls, v, field):
        if 'pin' in field.name.lower(): # Check if 'pin' is in the field name
            if not (isinstance(v, int) and 0 <= v <= 40):
                raise ValueError(f'El pin GPIO ({v}) para {field.name} debe ser un entero entre 0 y 40.')
        return v

class CameraSettings(BaseModel):
    source: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30

class AIModelSettings(BaseModel):
    model_path: str
    confidence_threshold: float = Field(..., ge=0.0, le=1.0)

class ConveyorBeltSettings(BaseModel, GPIOValidator):
    belt_speed_mps: float = Field(..., gt=0)
    pin_forward_relay: int
    pin_backward_relay: int
    is_active_low: bool = True
    
class LabelerSettings(BaseModel, GPIOValidator):
    pin: int # Pin base para las etiquetadoras
    activation_duration_s: float = Field(..., gt=0)
    distance_camera_to_labeler_m: float = Field(..., gt=0)
    
class SensorSettings(BaseModel, GPIOValidator):
    trigger_pin: int
    echo_pin: Optional[int] = None

class DiverterSettings(BaseModel, GPIOValidator):
    enabled: bool = True
    activation_duration_seconds: float = 2.0
    return_delay_seconds: float = 0.5
    diverters: Dict[int, Dict]

class MotorControllerSettings(BaseModel, GPIOValidator):
    pwm_pin: int
    dir_pin1: int
    dir_pin2: int
    enable_pin: Optional[int] = None
    
class APISettings(BaseModel):
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
class SystemSettings(BaseModel):
    installation_id: str
    system_name: str
    log_level: str = "INFO"

class MainConfig(BaseModel):
    system_settings: SystemSettings
    camera_settings: CameraSettings
    ai_model_settings: AIModelSettings
    conveyor_belt_settings: ConveyorBeltSettings
    labeler_settings: LabelerSettings
    sensor_settings: SensorSettings
    diverter_settings: DiverterSettings
    motor_controller_settings: MotorControllerSettings
    api_settings: APISettings
    
    laser_stepper_settings: Optional[Dict] = None

    @classmethod
    def from_json(cls, file_path: str) -> 'MainConfig':
        import json
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        return cls(**config_data)
