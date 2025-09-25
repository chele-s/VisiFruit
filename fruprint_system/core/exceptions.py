# fruprint_system/core/exceptions.py

class FruPrintException(Exception):
    """Clase base para todas las excepciones personalizadas del sistema."""
    pass

# --- Excepciones de Configuración ---
class ConfigError(FruPrintException):
    """Error relacionado con la carga o validación de la configuración."""
    pass

class PinConfigError(ConfigError):
    """Error específico para una configuración de pin GPIO inválida."""
    pass

# --- Excepciones de Hardware ---
class HardwareException(FruPrintException):
    """Clase base para errores relacionados con el hardware."""
    pass

class CameraError(HardwareException):
    """Error específico de la cámara."""
    pass

class MotorError(HardwareException):
    """Error específico de un motor."""
    pass

class LabelerError(HardwareException):
    """Error específico de una etiquetadora."""
    pass

class SensorError(HardwareException):
    """Error específico de un sensor."""
    pass

# --- Excepciones de Software/Operación ---
class AIError(FruPrintException):
    """Error relacionado con el módulo de Inteligencia Artificial."""
    pass

class InitializationError(FruPrintException):
    """Error ocurrido durante la secuencia de inicialización del sistema."""
    pass

class ShutdownError(FruPrintException):
    """Error ocurrido durante la secuencia de apagado del sistema."""
    pass
