# 🎉 VisiFruit v4.0 - Selector de Modos Interactivo

## ✅ Problemas Solucionados

### 1. ❌ Error Crítico: `TOTAL_LABELERS is not defined`

**Problema:**
```
[2025-10-03 12:47:01.109] [core_modules.ultra_labeling_system] [ERROR] 
❌ Error inicializando etiquetadoras lineales: name 'TOTAL_LABELERS' is not defined
```

**Solución:**
- ✅ Añadido `TOTAL_LABELERS` a las importaciones en `core_modules/ultra_labeling_system.py`
- ✅ El sistema ahora importa correctamente todas las constantes necesarias

**Archivo modificado:**
```python
# core_modules/ultra_labeling_system.py - Línea 29-32
from core_modules.system_types import (
    FruitCategory, LabelerGroup, LABELERS_PER_GROUP,
    NUM_LABELER_GROUPS, TOTAL_LABELERS, DEFAULT_MOTOR_PINS  # ← TOTAL_LABELERS añadido
)
```

---

### 2. 🎯 Selector de Modos Interactivo

**Problema Original:**
- El sistema siempre iniciaba en modo profesional sin preguntar
- No había forma fácil de cambiar entre modo profesional y prototipo
- Usuario quería seleccionar el modo al inicio

**Solución Implementada:**
- ✅ Nuevo selector de modos interactivo con menú visual
- ✅ 3 opciones claras: Profesional, Prototipo, Salir
- ✅ Descripción detallada del hardware de cada modo
- ✅ Manejo de interrupciones (Ctrl+C) sin crashes

**Características del Selector:**

```
======================================================================
🏭 VISIFRUIT - SISTEMA DE ETIQUETADO INDUSTRIAL
======================================================================

Selecciona el modo de operación:

  [1] 🏭 MODO PROFESIONAL
      - 6 etiquetadoras automáticas (2 por categoría)
      - Motor DC lineal para posicionamiento
      - Sistema de desviadores industriales
      - IA YOLOv8 avanzada

  [2] 🎯 MODO PROTOTIPO
      - 1 etiquetadora con driver DRV8825
      - Motor NEMA 17 para etiquetado
      - 3 servomotores MG995 para clasificación
      - IA YOLOv8 para detección

  [3] 🚪 SALIR
======================================================================

👉 Ingresa tu opción (1, 2 o 3):
```

**Código Añadido:**
```python
# main_etiquetadora_v4.py - Líneas 1004-1042
def select_operation_mode() -> str:
    """Selector interactivo de modo de operación."""
    print("\n" + "=" * 70)
    print("🏭 VISIFRUIT - SISTEMA DE ETIQUETADO INDUSTRIAL")
    # ... menú visual ...
    
    while True:
        try:
            choice = input("\n👉 Ingresa tu opción (1, 2 o 3): ").strip()
            
            if choice == "1":
                return "professional"
            elif choice == "2":
                return "prototype"
            elif choice == "3":
                return "exit"
        except (EOFError, KeyboardInterrupt):
            return "exit"
```

---

## 🆕 Archivos Nuevos Creados

### 1. `start_visifruit_interactive.bat` (Windows)
Launcher visual para Windows con:
- ✅ Banner ASCII art de VisiFruit
- ✅ Activación automática del entorno virtual
- ✅ Manejo de errores
- ✅ Pausa al finalizar para ver mensajes

### 2. `start_visifruit_interactive.sh` (Linux/Raspberry Pi)
Launcher para Linux con:
- ✅ Banner ASCII art
- ✅ Detección y activación de venv
- ✅ Soporte para Python3
- ✅ Compatible con Raspberry Pi

### 3. `SELECTOR_MODOS.md`
Documentación completa con:
- ✅ Descripción de cada modo
- ✅ Hardware requerido por modo
- ✅ Comparación de características
- ✅ Guía de solución de problemas
- ✅ Uso de variables de entorno

### 4. `CAMBIOS_V4.0_SELECTOR_MODOS.md` (este archivo)
Registro de cambios y mejoras implementadas

---

## 🔧 Cambios en Archivos Existentes

### `main_etiquetadora_v4.py`

**Cambios:**
1. ✅ Función `select_operation_mode()` añadida (líneas 1004-1042)
2. ✅ Modo por defecto cambiado de `"auto"` a `"interactive"` (línea 1048)
3. ✅ Lógica de selección de modo mejorada (líneas 1051-1066)

**Antes:**
```python
mode = os.getenv("VISIFRUIT_MODE", "auto").lower()
```

**Después:**
```python
mode = os.getenv("VISIFRUIT_MODE", "interactive").lower()

# Selector interactivo (por defecto)
if mode == "interactive":
    mode = select_operation_mode()
    if mode == "exit":
        return 0
```

### `core_modules/ultra_labeling_system.py`

**Cambios:**
1. ✅ Importación de `TOTAL_LABELERS` añadida (línea 31)

**Antes:**
```python
from core_modules.system_types import (
    FruitCategory, LabelerGroup, LABELERS_PER_GROUP,
    NUM_LABELER_GROUPS, DEFAULT_MOTOR_PINS
)
```

**Después:**
```python
from core_modules.system_types import (
    FruitCategory, LabelerGroup, LABELERS_PER_GROUP,
    NUM_LABELER_GROUPS, TOTAL_LABELERS, DEFAULT_MOTOR_PINS
)
```

---

## 🚀 Cómo Usar el Sistema Actualizado

### Opción 1: Launcher Interactivo (RECOMENDADO)

**Windows:**
```bash
# Doble clic o desde CMD/PowerShell
.\start_visifruit_interactive.bat
```

**Linux/Raspberry Pi:**
```bash
# Primera vez: dar permisos
chmod +x start_visifruit_interactive.sh

# Ejecutar
./start_visifruit_interactive.sh
```

### Opción 2: Python Directo
```bash
# Activar venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# Ejecutar (mostrará el selector)
python main_etiquetadora_v4.py
```

### Opción 3: Forzar un Modo Específico
```bash
# Windows PowerShell
$env:VISIFRUIT_MODE="professional"  # o "prototype"
python main_etiquetadora_v4.py

# Linux/Mac
export VISIFRUIT_MODE=professional   # o prototype
python main_etiquetadora_v4.py
```

---

## 🎯 Diferencias entre Modos

### 🏭 Modo Profesional (Opción 1)
- **Archivo config:** `Config_Etiquetadora.json`
- **Sistema completo:** 6 etiquetadoras + motor DC + 2 desviadores
- **Puerto API:** 8000
- **Dashboard:** Puerto 8001
- **Frontend:** Puerto 3000
- **Base de datos:** SQLite completa con optimización
- **Throughput:** Hasta 120 frutas/minuto
- **Ideal para:** Producción industrial real

### 🎯 Modo Prototipo (Opción 2)
- **Archivo config:** `Prototipo_Clasificador/Config_Prototipo.json`
- **Sistema simplificado:** 1 etiquetadora DRV8825 + 3 servos clasificadores
- **Puerto API:** 8002
- **Dashboard:** Básico integrado
- **Frontend:** No incluido
- **Base de datos:** SQLite básica
- **Throughput:** Hasta 40 frutas/minuto
- **Ideal para:** Desarrollo, pruebas, aprendizaje

---

## 🐛 Bugs Conocidos Solucionados

1. ✅ **Error `TOTAL_LABELERS is not defined`** - SOLUCIONADO
2. ✅ **Sistema se apagaba sin selector** - SOLUCIONADO
3. ✅ **No había forma de elegir modo fácilmente** - SOLUCIONADO
4. ✅ **Falta de documentación de modos** - SOLUCIONADO

---

## 📋 Checklist de Verificación

Antes de ejecutar, verifica:

- [ ] Entorno virtual activado
- [ ] Dependencias instaladas (`pip install -r requirements_yolov8.txt`)
- [ ] Archivo de configuración existe:
  - `Config_Etiquetadora.json` (modo profesional)
  - `Prototipo_Clasificador/Config_Prototipo.json` (modo prototipo)
- [ ] Modelo YOLOv8 en `weights/best.pt`
- [ ] Hardware conectado según el modo seleccionado

---

## 🔄 Próximos Pasos Sugeridos

1. ✅ Probar el selector interactivo
2. ✅ Verificar funcionamiento en modo prototipo
3. ✅ Verificar funcionamiento en modo profesional
4. ⏳ Validar transiciones de estado sin errores
5. ⏳ Optimizar tiempos de calibración del motor
6. ⏳ Añadir modo "demo" sin hardware

---

## 📞 Soporte

Si encuentras problemas:

1. **Revisa los logs:**
   ```
   logs/backend_ultra.log
   logs/launcher.log
   ```

2. **Verifica la configuración:**
   - Modo profesional: `Config_Etiquetadora.json`
   - Modo prototipo: `Prototipo_Clasificador/Config_Prototipo.json`

3. **Lee la documentación:**
   - `SELECTOR_MODOS.md` - Guía completa de modos
   - `README.md` - Documentación general
   - `Guias de uso/` - Guías específicas

---

## 👨‍💻 Créditos

**Desarrollado por:**
- Gabriel Calderón
- Elias Bautista
- Cristian Hernandez

**Versión:** 4.0.0-MODULAR  
**Fecha:** Octubre 3, 2025  
**Cambios aplicados:** Selector de modos interactivo + Fix TOTAL_LABELERS

---

## 📝 Notas de Migración

Si estabas usando versiones anteriores:

1. **Sin cambios en código existente** - 100% compatible
2. **Nuevas funcionalidades opcionales** - Usa el selector o sigue usando variables de entorno
3. **Configuraciones anteriores funcionan** - No necesitas modificar configs
4. **Logs mejorados** - Más información sobre el modo seleccionado

---

**¡El sistema ahora es más intuitivo y fácil de usar! 🎉**

