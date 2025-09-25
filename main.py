# main.py (punto de entrada final)
import asyncio
import sys
from fruprint_system.core.controller import SystemController
from fruprint_system.core.logging_config import setup_logging, get_logger
from fruprint_system.core.exceptions import ConfigError

# Configuración inicial de logging
setup_logging()
logger = get_logger(__name__)

async def main():
    """Punto de entrada principal de la aplicación."""
    logger.info("==========================================================")
    logger.info("=== Iniciando VisiFruit System v4.1 (State Machine) ===")
    logger.info("==========================================================")
    
    controller = None
    try:
        config_file = "Config_Etiquetadora.json"
        controller = SystemController(config_file)
        
        log_level = controller.config.system_settings.log_level.upper()
        setup_logging(log_level)

        loop = asyncio.get_event_loop()
        stop_event = asyncio.Event()

        def handle_signal():
            logger.warning("Señal de apagado recibida. Iniciando cierre ordenado...")
            if controller:
                # Disparamos el evento de shutdown en la máquina de estados
                loop.create_task(controller.shutdown_system())
            if not stop_event.is_set():
                loop.call_soon_threadsafe(stop_event.set)
        
        # ... (signal handler setup)
        
        # Usamos el nuevo método para iniciar el sistema
        if not await controller.initialize_system():
            logger.critical("Fallo en la inicialización del sistema. Abortando.")
            return 1
            
        logger.info("🚀 Sistema corriendo. Presiona Ctrl+C para detener. 🚀")
        await stop_event.wait()

    except ConfigError as e:
        logger.critical("Error de configuración. No se puede iniciar el sistema.", error=str(e))
        return 1
    except Exception as e:
        logger.exception(f"Error no manejado en el nivel superior: {e}")
        return 1
    finally:
        if controller and controller.state != 'offline':
            logger.info("Asegurando apagado final del sistema...")
            await controller.shutdown_system()
        
        logger.info("==========================================================")
        logger.info("===            Sistema FruPrint detenido             ===")
        logger.info("==========================================================")

    return 0

if __name__ == "__main__":
    import signal

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida forzosamente.")
        sys.exit(1)
