# fruprint_system/core/state_machine.py
from transitions import Machine
from fruprint_system.core.logging_config import get_logger

logger = get_logger(__name__)

class SystemStateMachine:
    """
    Gestiona el estado del SystemController usando una máquina de estados formal.
    Esto asegura que las transiciones de estado sean válidas y predecibles.
    """
    
    STATES = [
        'offline',        # El sistema está completamente apagado.
        'initializing',   # Arrancando componentes.
        'idle',           # Componentes listos, esperando comando de inicio.
        'starting',       # Activando la producción (ej. encendiendo cinta).
        'running',        # Producción activa, procesando objetos.
        'stopping',       # Deteniendo la producción de forma ordenada.
        'error',          # Un error crítico ha ocurrido.
        'emergency_stop'  # Parada de emergencia activada.
    ]

    TRANSITIONS = [
        # Flujo de vida normal
        {'trigger': 'initialize', 'source': 'offline', 'dest': 'initializing', 'after': '_log_transition'},
        {'trigger': 'initialization_complete', 'source': 'initializing', 'dest': 'idle', 'after': '_log_transition'},
        {'trigger': 'start_production', 'source': 'idle', 'dest': 'starting', 'after': '_log_transition'},
        {'trigger': 'production_started', 'source': 'starting', 'dest': 'running', 'after': '_log_transition'},
        {'trigger': 'stop_production', 'source': 'running', 'dest': 'stopping', 'after': '_log_transition'},
        {'trigger': 'production_stopped', 'source': 'stopping', 'dest': 'idle', 'after': '_log_transition'},
        
        # Flujo de apagado
        {'trigger': 'shutdown', 'source': '*', 'dest': 'offline', 'after': '_log_transition'},
        
        # Flujos de error
        {'trigger': 'encounter_error', 'source': '*', 'dest': 'error', 'after': '_log_transition'},
        {'trigger': 'emergency', 'source': '*', 'dest': 'emergency_stop', 'after': '_log_transition'},
        {'trigger': 'reset_error', 'source': ['error', 'emergency_stop'], 'dest': 'idle', 'after': '_log_transition'}
    ]

    def __init__(self, controller):
        self.machine = Machine(
            model=controller,  # La máquina de estados opera sobre el propio SystemController
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial='offline',
            send_event=True,    # Pasa los kwargs de los triggers a los callbacks
            auto_transitions=False # No queremos transiciones automáticas
        )

    def _log_transition(self, event):
        """Callback que se ejecuta después de cada transición para loguear el cambio."""
        logger.info(
            "Transición de estado completada",
            trigger=event.event.name,
            source=event.transition.source,
            destination=event.transition.dest,
        )
