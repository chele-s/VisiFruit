# Arquitectura FruPrint v4.0 - Modular Edition

## 🎯 Resumen de la Refactorización

El sistema ha sido completamente refactorizado de un archivo monolítico de **3100+ líneas** a una arquitectura modular profesional con **8 módulos especializados** y un archivo principal de solo **800 líneas**.

## 📦 Estructura de Módulos

### 1. `system_types.py` (160 líneas)
**Propósito**: Tipos, enums y constantes del sistema

**Contenido**:
- `SystemState`: Estados del sistema
- `AlertLevel`: Niveles de alerta
- `FruitCategory`: Categorías de frutas (🍎🍐🍋)
- `LabelerGroup`: Grupos de etiquetadoras
- `ProcessingPriority`, `OptimizationMode`
- Constantes globales del sistema

**Uso**:
```python
from system_types import FruitCategory, SystemState, TOTAL_LABELERS
```

### 2. `metrics_system.py` (280 líneas)
**Propósito**: Sistema de métricas y telemetría

**Contenido**:
- `UltraSystemMetrics`: Métricas generales
- `UltraCategoryMetrics`: Métricas por categoría
- `LabelerMetrics`: Métricas por etiquetadora
- `MetricsManager`: Gestor centralizado de métricas

**Características**:
- Thread-safe con locks
- Actualización automática de métricas
- Sistema de alertas
- Cálculo de OEE (Overall Equipment Effectiveness)

**Uso**:
```python
from metrics_system import MetricsManager

manager = MetricsManager()
manager.update_category_metrics(FruitCategory.APPLE, detected=5)
```

### 3. `optimization_engine.py` (270 líneas)
**Propósito**: Optimización y predicción

**Contenido**:
- `UltraPatternAnalyzer`: Análisis de patrones
- `UltraPredictionEngine`: Predicción de throughput
- `SystemOptimizer`: Optimizador con 4 estrategias

**Estrategias de Optimización**:
1. **Speed**: Velocidad máxima
2. **Accuracy**: Precisión máxima
3. **Efficiency**: Eficiencia energética
4. **Adaptive**: Adaptativo basado en patrones

**Uso**:
```python
from optimization_engine import SystemOptimizer

optimizer = SystemOptimizer(pattern_analyzer, prediction_engine)
result = await optimizer.optimize(metrics_data)
```

### 4. `ultra_labeling_system.py` (270 líneas)
**Propósito**: Sistema de 6 etiquetadoras con motor DC

**Contenido**:
- `UltraLinearMotorController`: Control del motor DC
- `UltraLabelerManager`: Gestión de las 6 etiquetadoras

**Arquitectura del Sistema**:
```
Grupo 0 (🍎 Manzanas): Etiquetadoras 0-1
Grupo 1 (🍐 Peras):     Etiquetadoras 2-3
Grupo 2 (🍋 Limones):   Etiquetadoras 4-5
```

**Uso**:
```python
from ultra_labeling_system import UltraLabelerManager

manager = UltraLabelerManager(config)
await manager.initialize()
await manager.activate_group(group_id=0, duration=2.0)
```

### 5. `database_manager.py` (300 líneas)
**Propósito**: Persistencia de datos

**Contenido**:
- `DatabaseManager`: Gestor de SQLite
- Tablas: detections, labelings, metrics, alerts, classifications
- Operaciones asíncronas con `asyncio.to_thread()`

**Uso**:
```python
from database_manager import DatabaseManager

db = DatabaseManager()
db.initialize()
await db.save_detection(detection_data)
await db.save_metrics(metrics)
```

### 6. `service_manager.py` (280 líneas)
**Propósito**: Auto-inicio de servicios auxiliares

**Contenido**:
- Auto-inicio de frontend React
- Auto-inicio de backend dashboard
- Limpieza preventiva de puertos/procesos
- Gestión de instancia única

**Uso**:
```python
from service_manager import check_and_start_services, cleanup_services

services = await check_and_start_services()
# ... trabajo ...
await cleanup_services(services)
```

### 7. `system_utils.py` (370 líneas)
**Propósito**: Utilidades generales

**Contenido**:
- Logging ultra-avanzado
- Cache inteligente con TTL
- Medidor de performance
- Rate limiter
- Retry mechanism
- Helpers (format_bytes, format_duration, etc.)

**Decoradores Útiles**:
```python
from system_utils import intelligent_cache, measure_performance, retry_on_failure

@intelligent_cache(ttl_seconds=300)
@measure_performance
async def expensive_operation():
    # ...
    pass

@retry_on_failure(max_attempts=3, delay=1.0)
async def unreliable_operation():
    # ...
    pass
```

### 8. `ultra_api.py` (550 líneas)
**Propósito**: API REST y WebSocket

**Contenido**:
- `UltraAPIFactory`: Factory para crear FastAPI app
- Rutas organizadas por dominio:
  - Basic: `/health`, `/status`
  - Control: `/control/start`, `/control/stop`, `/control/emergency_stop`
  - Motor: `/motor/activate_group`, `/motor/status`
  - Belt: `/belt/start_forward`, `/belt/stop`, `/belt/set_speed`
  - Diverters: `/diverters/status`, `/diverters/classify`
  - Metrics: `/metrics/categories`, `/metrics/predictions`
  - WebSocket: `/ws/ultra_dashboard`

**Uso**:
```python
from ultra_api import UltraAPIFactory, start_api_server

factory = UltraAPIFactory(system_instance)
app = factory.create_app()
server_task = await start_api_server(app, host="0.0.0.0", port=8000)
```

### 9. `main_etiquetadora_v4.py` (800 líneas)
**Propósito**: Orquestador principal

**Contenido**:
- `UltraIndustrialFruitLabelingSystem`: Clase principal
- Inicialización de componentes
- Bucles de procesamiento
- Control de producción
- Punto de entrada `main()`

## 🔄 Comparación v3.0 vs v4.0

| Aspecto | v3.0 | v4.0 |
|---------|------|------|
| **Archivo Principal** | 3123 líneas | 800 líneas (-74%) |
| **Módulos** | 1 monolítico | 9 especializados |
| **Mantenibilidad** | Difícil | Excelente |
| **Testabilidad** | Baja | Alta |
| **Reutilización** | Baja | Alta |
| **Documentación** | Inline | Modular + README |
| **Separación de Concerns** | No | Sí |

## 🚀 Beneficios de la Nueva Arquitectura

### 1. **Mantenibilidad**
- Cada módulo tiene una responsabilidad clara
- Fácil localizar y corregir bugs
- Cambios localizados no afectan todo el sistema

### 2. **Testabilidad**
- Módulos independientes son fáciles de testear
- Mock de dependencias simplificado
- Tests unitarios por módulo

### 3. **Escalabilidad**
- Fácil agregar nuevas características
- Módulos pueden evolucionar independientemente
- Plugins y extensiones sencillos

### 4. **Colaboración**
- Múltiples desarrolladores pueden trabajar en paralelo
- Menos conflictos de merge
- Code reviews más enfocados

### 5. **Reusabilidad**
- Módulos pueden usarse en otros proyectos
- Sistema de métricas reutilizable
- API factory puede generar múltiples APIs

## 📊 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                  main_etiquetadora_v4.py                    │
│              (Orquestador Principal - 800 líneas)           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ system_types │    │metrics_system│    │ultra_api     │
│   (Tipos)    │    │ (Telemetría) │    │   (API)      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│optimization_ │    │ultra_labeling│    │database_     │
│   engine     │    │   _system    │    │  manager     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│system_utils  │    │service_      │    │Control_      │
│ (Utilidades) │    │  manager     │    │ Etiquetado/  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 🔧 Migración de v3.0 a v4.0

### Paso 1: Backup
```bash
cp main_etiquetadora.py main_etiquetadora_v3_backup.py
```

### Paso 2: Copiar Módulos
Todos los archivos nuevos ya están en la raíz del proyecto:
- `system_types.py`
- `metrics_system.py`
- `optimization_engine.py`
- `ultra_labeling_system.py`
- `database_manager.py`
- `service_manager.py`
- `system_utils.py`
- `ultra_api.py`
- `main_etiquetadora_v4.py`

### Paso 3: Renombrar y Probar
```bash
# Renombrar el nuevo archivo como principal
mv main_etiquetadora.py main_etiquetadora_v3.py
mv main_etiquetadora_v4.py main_etiquetadora.py

# Probar el sistema
python main_etiquetadora.py
```

### Paso 4: Verificar Funcionalidad
1. Verificar que todos los servicios inicien correctamente
2. Probar endpoints de API
3. Verificar métricas y telemetría
4. Probar sistema de etiquetado
5. Verificar base de datos

## 📝 Notas de Desarrollo

### Agregar Nueva Funcionalidad

**Ejemplo: Agregar un nuevo tipo de sensor**

1. **Definir tipo en `system_types.py`**:
```python
class SensorType(Enum):
    LASER = "laser"
    PROXIMITY = "proximity"
    NEW_SENSOR = "new_sensor"  # ← Agregar aquí
```

2. **Implementar lógica en módulo apropiado**:
```python
# En sensor_module.py (nuevo o existente)
class NewSensorHandler:
    async def initialize(self):
        # ...
        pass
```

3. **Integrar en `main_etiquetadora.py`**:
```python
async def _initialize_new_sensor(self):
    self.new_sensor = NewSensorHandler(self.config)
    await self.new_sensor.initialize()
```

### Debugging

**Logs organizados por dominio**:
```python
logger = logging.getLogger("FruPrintUltra.Metrics")
logger = logging.getLogger("FruPrintUltra.Optimization")
logger = logging.getLogger("FruPrintUltra.API")
```

**Logs de performance**:
```python
@measure_performance
async def my_function():
    # Automáticamente logea "PERF: my_function ejecutado en Xms"
    pass
```

## 🎓 Mejores Prácticas

1. **Un módulo = Una responsabilidad**
2. **Imports explícitos**: `from module import SpecificClass`
3. **Type hints** en todas las funciones públicas
4. **Docstrings** en formato Google/NumPy
5. **Logging** en lugar de `print()`
6. **Async/await** para operaciones I/O
7. **Context managers** para recursos
8. **Dataclasses** en lugar de dicts para datos estructurados

## 🔮 Roadmap Futuro

### v4.1 - Testing Suite
- [ ] Tests unitarios por módulo
- [ ] Tests de integración
- [ ] CI/CD pipeline

### v4.2 - Performance
- [ ] Profiling y optimización
- [ ] Reducción de latencia
- [ ] Mejora de throughput

### v4.3 - Features
- [ ] Machine Learning integrado
- [ ] Dashboard 3D en tiempo real
- [ ] Sistema de redundancia activa

### v5.0 - Microservicios
- [ ] Separación en microservicios
- [ ] Message queue (RabbitMQ/Redis)
- [ ] Kubernetes deployment

## 📞 Soporte

Para preguntas sobre la arquitectura:
- Documentación inline en cada módulo
- Este documento (ARCHITECTURE_V4.md)
- Comments en código crítico

## ✨ Conclusión

La arquitectura v4.0 es una **mejora sustancial** sobre v3.0:
- **74% menos código** en archivo principal
- **9 módulos especializados** vs 1 monolítico
- **Infinitamente más mantenible**
- **Listo para crecer** sin volverse inmanejable

¡Disfruta desarrollando con la nueva arquitectura! 🚀
