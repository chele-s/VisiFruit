# fruprint_system/metrics/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY
import asyncio

from fruprint_system.core.logging_config import get_logger

logger = get_logger(__name__)

# --- Definición de Métricas ---

FRUITS_PROCESSED = Counter(
    'fruits_processed_total',
    'Total de frutas procesadas por el sistema',
    ['category']
)

DETECTION_CONFIDENCE = Histogram(
    'detection_confidence_ratio',
    'Distribución de la confianza de detección de la IA'
)

PROCESSING_TIME = Histogram(
    'processing_duration_seconds',
    'Tiempo que toma procesar un frame (detección + etiquetado)'
)

SYSTEM_STATE = Gauge(
    'system_state_info',
    'Estado actual de la máquina de estados del sistema',
    ['state']
)

COMPONENT_HEALTH = Gauge(
    'component_health_status',
    'Estado de salud de un componente individual (1=healthy, 0=unhealthy)',
    ['component']
)

class MetricsCollector:
    """Clase para encapsular la lógica de las métricas de Prometheus."""
    
    def __init__(self, port: int = 9090, enabled: bool = True):
        self.port = port
        self.enabled = enabled
        self._server_started = False

    async def start_server(self):
        """Inicia el servidor HTTP de Prometheus en un hilo separado."""
        if not self.enabled or self._server_started:
            return
        
        try:
            # Limpiar registros previos si existen
            for collector in list(REGISTRY._collector_to_names.keys()):
                if collector is not self:
                    REGISTRY.unregister(collector)

            await asyncio.to_thread(start_http_server, self.port)
            logger.info(f"Servidor de métricas Prometheus iniciado en el puerto {self.port}")
            self._server_started = True
        except Exception as e:
            logger.error(f"No se pudo iniciar el servidor de Prometheus: {e}")
            self.enabled = False

    def record_fruit_processed(self, category: str):
        if self.enabled:
            FRUITS_PROCESSED.labels(category=category).inc()

    def record_detection_confidence(self, confidence: float):
        if self.enabled:
            DETECTION_CONFIDENCE.observe(confidence)

    def record_processing_time(self, duration_seconds: float):
        if self.enabled:
            PROCESSING_TIME.observe(duration_seconds)

    def set_system_state(self, state: str):
        if self.enabled:
            # Asegura que solo un estado esté activo a la vez
            for s in ['offline', 'initializing', 'idle', 'running', 'stopping', 'error', 'emergency_stop']:
                SYSTEM_STATE.labels(state=s).set(1 if s == state else 0)

    def set_component_health(self, component: str, is_healthy: bool):
        if self.enabled:
            COMPONENT_HEALTH.labels(component=component).set(1 if is_healthy else 0)
