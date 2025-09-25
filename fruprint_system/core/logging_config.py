# fruprint_system/core/logging_config.py
import logging
import sys
import structlog
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """
    Configura structlog para un logging estructurado y avanzado.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "fruprint_system_structured.log"

    # Configuración de procesadores para structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # El último procesador renderiza el log.
            # Para la consola, usamos un formato legible.
            # Para el archivo, usamos JSON.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configuración del handler para el archivo (JSON)
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(json_formatter)
    
    # Configuración del handler para la consola (formato de texto)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level.upper())

    logger = structlog.get_logger("logging_setup")
    logger.info("Sistema de logging estructurado (structlog) configurado.", log_file=str(log_file))

# Para facilitar la obtención de loggers en otros módulos
def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name)
