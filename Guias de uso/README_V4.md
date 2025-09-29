# 🏭 FruPrint v4.0 - Sistema Industrial de Etiquetado de Frutas

## 🎯 Arquitectura Modular ULTRA

Sistema de etiquetado industrial completamente refactorizado con **arquitectura modular profesional**, reduciendo el código principal de **3100+ líneas a solo 800 líneas** mediante **9 módulos especializados**.

---

## ✨ Nuevas Características v4.0

### 🏗️ Arquitectura Modular
- **9 módulos especializados** en lugar de 1 archivo monolítico
- **74% reducción** en el tamaño del archivo principal
- **Separación clara de responsabilidades**
- **Fácil mantenimiento y testing**

### 🏭 Sistema de Etiquetado Ultra
- **6 Etiquetadoras automáticas** (2 por categoría)
- **Motor DC de posicionamiento** para grupos lineales
- **3 Categorías**: 🍎 Manzanas, 🍐 Peras, 🍋 Limones
- **Sistema de clasificación** con desviadores

### 🤖 Inteligencia Artificial
- **Detector de frutas** con IA avanzada
- **Categorización automática** en tiempo real
- **Sistema de predicción** de throughput
- **Optimización adaptativa** de rendimiento

### 📊 Métricas y Telemetría
- **Sistema de métricas completo** por categoría y etiquetadora
- **OEE (Overall Equipment Effectiveness)**
- **Alertas inteligentes** con auto-resolución
- **Base de datos SQLite** para análisis histórico

### 🌐 API Ultra-Avanzada
- **API REST completa** con FastAPI
- **WebSocket** para dashboard en tiempo real
- **Documentación automática** en `/docs`
- **Control total** de producción, motor, banda y desviadores

### 🚀 Auto-Inicio de Servicios
- **Frontend React** auto-iniciado
- **Backend Dashboard** auto-iniciado
- **Limpieza preventiva** de puertos y procesos
- **Gestión de instancia única**

---

## 📦 Estructura de Módulos

```
FruPrint v4.0/
├── main_etiquetadora.py          # Orquestador principal (800 líneas)
├── system_types.py                # Tipos, enums, constantes
├── metrics_system.py              # Sistema de métricas
├── optimization_engine.py         # Optimización y predicción
├── ultra_labeling_system.py       # 6 Etiquetadoras + Motor DC
├── database_manager.py            # Persistencia de datos
├── service_manager.py             # Auto-inicio de servicios
├── system_utils.py                # Utilidades generales
├── ultra_api.py                   # API REST y WebSocket
├── Control_Etiquetado/            # Módulos de hardware (sin cambios)
│   ├── conveyor_belt_controller.py
│   ├── sensor_interface.py
│   ├── labeler_actuator.py
│   └── fruit_diverter_controller.py
├── IA_Etiquetado/                 # Módulos de IA (sin cambios)
│   └── Fruit_detector.py
├── utils/                         # Utilidades (sin cambios)
│   ├── camera_controller.py
│   ├── config_validator.py
│   └── gpio_wrapper.py
└── Interfaz_Usuario/              # Frontend y Backend (sin cambios)
    ├── VisiFruit/                 # React Frontend
    └── Backend/                   # Dashboard Backend
```

---

## 🚀 Instalación y Migración

### Opción 1: Migración Automática (Recomendada)

```bash
# Ejecutar script de migración
python migrate_to_v4.py
```

El script automáticamente:
1. ✅ Crea backup de tu sistema v3.0
2. ✅ Migra a arquitectura modular v4.0
3. ✅ Verifica que todo funcione
4. ✅ Rollback automático si hay errores

### Opción 2: Migración Manual

```bash
# 1. Crear backup
cp main_etiquetadora.py main_etiquetadora_v3_backup.py

# 2. Renombrar archivos
mv main_etiquetadora.py main_etiquetadora_v3.py
mv main_etiquetadora_v4.py main_etiquetadora.py

# 3. Verificar que todos los módulos estén presentes
ls -1 *.py
```

---

## 🎮 Uso del Sistema

### Inicio Rápido

```bash
# Iniciar el sistema completo (main + frontend + backend)
python main_etiquetadora.py
```

El sistema automáticamente:
- 🧹 Limpia puertos y procesos previos
- 🚀 Inicia el backend dashboard (puerto 8001)
- 🎨 Inicia el frontend React (puerto 3000)
- 🏷️ Inicia el sistema principal (puerto 8000)

### URLs Disponibles

- **Sistema Principal**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Backend Dashboard**: http://localhost:8001
- **Frontend React**: http://localhost:3000

### Configuración

Editar `Config_Etiquetadora.json`:

```json
{
  "system_settings": {
    "installation_id": "FRUPRINT-001",
    "system_name": "FruPrint Ultra v4.0",
    "log_level": "INFO"
  },
  "api_settings": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8000
  },
  ...
}
```

---

## 📡 API Endpoints

### Control de Producción

```bash
# Iniciar producción
POST /control/start

# Detener producción
POST /control/stop

# Parada de emergencia
POST /control/emergency_stop
```

### Control de Motor

```bash
# Activar grupo de etiquetadoras
POST /motor/activate_group?category=apple

# Estado del motor
GET /motor/status
```

### Control de Banda

```bash
# Iniciar banda hacia adelante
POST /belt/start_forward

# Detener banda
POST /belt/stop

# Establecer velocidad
POST /belt/set_speed
Body: {"speed": 0.5}

# Estado de la banda
GET /belt/status
```

### Métricas

```bash
# Métricas por categoría
GET /metrics/categories

# Predicciones
GET /metrics/predictions
```

### WebSocket

```javascript
// Conectar a dashboard en tiempo real
const ws = new WebSocket('ws://localhost:8000/ws/ultra_dashboard');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Métricas en tiempo real:', data);
};
```

---

## 🧪 Testing

### Test de Módulos

```python
# Test del sistema de métricas
from metrics_system import MetricsManager

manager = MetricsManager()
manager.update_category_metrics(FruitCategory.APPLE, detected=5)
print(manager.get_metrics_snapshot())
```

### Test de API

```bash
# Test de salud
curl http://localhost:8000/health

# Test de estado
curl http://localhost:8000/status

# Test de activación de grupo
curl -X POST http://localhost:8000/motor/activate_group?category=apple
```

---

## 🔧 Desarrollo

### Agregar Nuevo Módulo

1. **Crear módulo**:
```python
# my_new_module.py
class MyNewFeature:
    def __init__(self, config):
        self.config = config
    
    async def initialize(self):
        # Inicialización
        pass
```

2. **Importar en main**:
```python
from my_new_module import MyNewFeature

class UltraIndustrialFruitLabelingSystem:
    def __init__(self, config_path):
        self.my_feature = MyNewFeature(self.config)
```

3. **Inicializar**:
```python
async def initialize(self):
    await self.my_feature.initialize()
```

### Decoradores Útiles

```python
from system_utils import intelligent_cache, measure_performance, retry_on_failure

@intelligent_cache(ttl_seconds=300)  # Cache con TTL
@measure_performance                  # Medición automática
@retry_on_failure(max_attempts=3)   # Reintentos automáticos
async def my_function():
    # Tu código aquí
    pass
```

---

## 📊 Comparación v3.0 vs v4.0

| Característica | v3.0 | v4.0 |
|----------------|------|------|
| **Archivo Principal** | 3123 líneas | 800 líneas |
| **Módulos** | 1 monolítico | 9 especializados |
| **Mantenibilidad** | ⚠️ Difícil | ✅ Excelente |
| **Testabilidad** | ⚠️ Baja | ✅ Alta |
| **Documentación** | ⚠️ Inline | ✅ Modular |
| **Escalabilidad** | ⚠️ Limitada | ✅ Excelente |

---

## 🐛 Troubleshooting

### Error: "Otra instancia ya está en ejecución"
```bash
# Permitir múltiples instancias
export ALLOW_MULTIPLE_INSTANCES=true
python main_etiquetadora.py
```

### Error: "Frontend no se inicia"
```bash
# Verificar npm
npm --version

# Instalar dependencias manualmente
cd Interfaz_Usuario/VisiFruit
npm install
npm run dev
```

### Error: "GPIO no disponible"
- ✅ **Normal en Windows**: Modo simulación activo
- ⚠️ **En Raspberry Pi**: Instalar `lgpio`
```bash
sudo apt install python3-lgpio
```

---

## 📚 Documentación Adicional

- **Arquitectura**: `ARCHITECTURE_V4.md` - Guía completa de la arquitectura
- **Control de Banda**: `BELT_CONTROL_README.md` - Documentación de banda
- **Demos**: `Control_Etiquetado/README_DEMOS.md` - Scripts de demostración

---

## 🤝 Contribuir

### Guía de Estilo

1. **Un módulo = Una responsabilidad**
2. **Type hints** en todas las funciones públicas
3. **Docstrings** en formato Google/NumPy
4. **Logging** en lugar de `print()`
5. **Async/await** para I/O

### Pull Requests

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Abre un Pull Request

---

## 📝 Changelog

### v4.0.0 - Septiembre 2025
- ✨ **Arquitectura modular completa**
- 🏭 **9 módulos especializados**
- 📊 **Sistema de métricas avanzado**
- 🤖 **Optimización predictiva**
- 🌐 **API ultra-avanzada**
- 🚀 **Auto-inicio de servicios**
- 📖 **Documentación completa**

### v3.0.0 - Julio 2025
- 🏭 6 Etiquetadoras con motor DC
- 🤖 IA de categorización
- 📊 Telemetría avanzada
- 🌐 Dashboard 3D

---

## 👥 Autores

- **Gabriel Calderón** - Desarrollo principal
- **Elias Bautista** - Hardware y control
- **Cristian Hernandez** - IA y optimización

---

## 📄 Licencia

Este proyecto es propiedad de FruPrint Industries.

---

## 🎉 ¡Gracias por usar FruPrint v4.0!

Para soporte: contacto@fruprint.com

**🚀 Disfruta la nueva arquitectura modular!**
