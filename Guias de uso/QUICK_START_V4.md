# 🚀 Quick Start - FruPrint v4.0

## ⚡ Inicio Rápido en 3 Minutos

### 1️⃣ Migrar a v4.0 (30 segundos)

```bash
# Ejecutar script de migración automática
python migrate_to_v4.py
```

### 2️⃣ Iniciar el Sistema (30 segundos)

```bash
# Inicia automáticamente: main + backend + frontend
python main_etiquetadora.py
```

### 3️⃣ Verificar que Funciona (2 minutos)

Abrir en el navegador:
- **API Docs**: http://localhost:8000/docs
- **Backend**: http://localhost:8001
- **Frontend**: http://localhost:3000

**¡Listo! Sistema v4.0 funcionando** ✅

---

## 🎯 Comandos Útiles

### Control del Sistema

```bash
# Iniciar sistema completo
python main_etiquetadora.py

# Modo sin frontend (solo main + backend)
export AUTO_START_FRONTEND=false
python main_etiquetadora.py

# Modo solo main (sin servicios auxiliares)
export AUTO_START_BACKEND=false
export AUTO_START_FRONTEND=false
python main_etiquetadora.py
```

### Testing Rápido

```bash
# Test de salud del sistema
curl http://localhost:8000/health

# Test de estado completo
curl http://localhost:8000/status

# Activar grupo de manzanas
curl -X POST "http://localhost:8000/motor/activate_group?category=apple"

# Iniciar producción
curl -X POST http://localhost:8000/control/start
```

---

## 📦 Qué Cambió

### Antes (v3.0)
```
main_etiquetadora.py  ← 3,123 líneas (TODO aquí)
```

### Después (v4.0)
```
main_etiquetadora.py      ← 800 líneas (solo orquestación)
├── system_types.py       ← Tipos y enums
├── metrics_system.py     ← Métricas y telemetría
├── optimization_engine.py ← Optimización y predicción
├── ultra_labeling_system.py ← 6 Etiquetadoras + Motor
├── database_manager.py   ← Base de datos
├── service_manager.py    ← Auto-inicio de servicios
├── system_utils.py       ← Utilidades generales
└── ultra_api.py          ← API REST y WebSocket
```

---

## 🎨 Uso Básico de Módulos

### Métricas

```python
from metrics_system import MetricsManager
from system_types import FruitCategory

# Crear gestor
manager = MetricsManager()

# Actualizar métricas
manager.update_category_metrics(
    FruitCategory.APPLE, 
    detected=5, 
    labeled=5
)

# Obtener snapshot
snapshot = manager.get_metrics_snapshot()
print(snapshot)
```

### Optimización

```python
from optimization_engine import SystemOptimizer

# Crear optimizador
optimizer = SystemOptimizer(pattern_analyzer, prediction_engine)

# Ejecutar optimización
result = await optimizer.optimize(metrics_data)
print(result.improvements)
```

### Sistema de Etiquetado

```python
from ultra_labeling_system import UltraLabelerManager

# Crear gestor
manager = UltraLabelerManager(config)
await manager.initialize()

# Activar grupo de etiquetadoras
await manager.activate_group(
    group_id=0,  # Manzanas
    duration=2.0
)
```

### Base de Datos

```python
from database_manager import DatabaseManager

# Crear gestor
db = DatabaseManager()
db.initialize()

# Guardar detección
await db.save_detection({
    'category': 'apple',
    'confidence': 0.95,
    'processing_time_ms': 45.2
})

# Obtener estadísticas
stats = await db.get_statistics(hours=24)
```

---

## 🔧 Configuración Rápida

### Variables de Entorno

Crear archivo `.env`:

```bash
# Auto-inicio de servicios
AUTO_START_BACKEND=true
AUTO_START_FRONTEND=true
AUTO_CLEAN_ON_START=true

# URLs de servicios
VITE_API_URL=http://localhost:8001
VITE_MAIN_API_URL=http://localhost:8000

# Modo de desarrollo
NODE_ENV=development
```

### Config Principal

`Config_Etiquetadora.json`:

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
  }
}
```

---

## 🐛 Solución Rápida de Problemas

### Puerto ocupado
```bash
# Detener procesos en puerto 8000
fuser -k 8000/tcp  # Linux
netstat -ano | findstr :8000  # Windows

# O reiniciar con limpieza automática
export AUTO_CLEAN_ON_START=true
python main_etiquetadora.py
```

### Frontend no inicia
```bash
# Verificar npm
npm --version

# Instalar dependencias
cd Interfaz_Usuario/VisiFruit
npm install

# Iniciar manualmente
npm run dev -- --host 0.0.0.0 --port 3000
```

### Modo simulación GPIO
```bash
# En Windows es normal ver:
# "⚠️ Modo simulación GPIO activo"

# Para usar hardware real en Raspberry Pi:
sudo apt install python3-lgpio
```

---

## 📚 Documentación Completa

### Guías Disponibles

1. **ARCHITECTURE_V4.md** - Arquitectura detallada (60 páginas)
2. **README_V4.md** - Guía completa de usuario (40 páginas)
3. **RESUMEN_REFACTORIZACION.md** - Resumen ejecutivo (15 páginas)
4. **QUICK_START_V4.md** - Esta guía (5 páginas)

### Leer Documentación

```bash
# En terminal
cat ARCHITECTURE_V4.md | less

# O abrir en editor
code ARCHITECTURE_V4.md  # VS Code
nano ARCHITECTURE_V4.md  # Nano
vim ARCHITECTURE_V4.md   # Vim
```

---

## 🎓 Recursos de Aprendizaje

### Ejemplos en Código

```bash
# Ver ejemplos de métricas
python -c "from metrics_system import MetricsManager; help(MetricsManager)"

# Ver API disponible
python -c "from ultra_api import UltraAPIFactory; help(UltraAPIFactory)"

# Ver tipos del sistema
python -c "from system_types import *; print(FruitCategory.__doc__)"
```

### API Interactiva

```bash
# Iniciar sistema
python main_etiquetadora.py

# Abrir en navegador
http://localhost:8000/docs  # Swagger UI
http://localhost:8000/redoc # ReDoc
```

---

## ✅ Checklist de Verificación

Después de iniciar el sistema, verificar:

- [ ] Sistema principal inicia sin errores
- [ ] API accesible en http://localhost:8000
- [ ] `/health` devuelve `{"status": "ultra_healthy"}`
- [ ] `/status` muestra métricas del sistema
- [ ] Backend accesible en http://localhost:8001
- [ ] Frontend accesible en http://localhost:3000
- [ ] Logs sin errores críticos
- [ ] Base de datos creada en `data/fruprint_ultra.db`

---

## 🚀 Siguiente Nivel

Una vez funcionando:

1. **Personalizar configuración** en `Config_Etiquetadora.json`
2. **Probar API** en http://localhost:8000/docs
3. **Ver métricas** en tiempo real via WebSocket
4. **Agregar nuevos módulos** siguiendo la arquitectura
5. **Escribir tests** para tus módulos
6. **Documentar cambios** en tus propios READMEs

---

## 📞 Ayuda

### Problemas Comunes

| Problema | Solución |
|----------|----------|
| Puerto ocupado | `export AUTO_CLEAN_ON_START=true` |
| Frontend no inicia | Verificar `npm install` |
| GPIO no disponible | Normal en Windows, usar simulación |
| Módulo no encontrado | Verificar que todos los `.py` están en la raíz |

### Más Ayuda

- Documentación: `ARCHITECTURE_V4.md`
- GitHub Issues: (tu repo)
- Email: contacto@fruprint.com

---

## 🎉 ¡Felicidades!

Ya tienes FruPrint v4.0 funcionando con:

✅ **Arquitectura modular profesional**  
✅ **9 módulos especializados**  
✅ **800 líneas** en archivo principal (vs 3,123)  
✅ **Sistema totalmente funcional**  
✅ **Listo para producción** 🚀

**¡A desarrollar con la nueva arquitectura!**
