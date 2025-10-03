# 🏭 VisiFruit - Selector de Modos de Operación

## 📋 Descripción General

El sistema VisiFruit ahora incluye un **selector de modos interactivo** que te permite elegir entre dos configuraciones de hardware al iniciar el sistema:

1. **🏭 Modo Profesional** - Sistema industrial completo con 6 etiquetadoras
2. **🎯 Modo Prototipo** - Sistema de desarrollo con 1 etiquetadora DRV8825

---

## 🚀 Cómo Iniciar el Sistema

### Windows
```bash
# Opción 1: Doble clic en el archivo
start_visifruit_interactive.bat

# Opción 2: Desde PowerShell/CMD
.\start_visifruit_interactive.bat
```

### Linux / Raspberry Pi
```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x start_visifruit_interactive.sh

# Ejecutar
./start_visifruit_interactive.sh
```

### Desde Python directamente
```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Ejecutar
python main_etiquetadora_v4.py
```

---

## 🎯 Modos de Operación

### Opción 1: 🏭 MODO PROFESIONAL

**Hardware requerido:**
- ✅ 6 etiquetadoras automáticas organizadas en 3 grupos:
  - Grupo 🍎 Manzanas: Etiquetadoras 0-1 (Pines 26-27)
  - Grupo 🍐 Peras: Etiquetadoras 2-3 (Pines 28-29)
  - Grupo 🍋 Limones: Etiquetadoras 4-5 (Pines 30-31)
- ✅ Motor DC lineal L298N para posicionamiento automático
  - Pin PWM: GPIO 12
  - Pines de dirección: GPIO 20, 21
  - Pin habilitación: GPIO 16
- ✅ Sistema de desviadores con 2 servomotores MG995:
  - Desviador manzanas: GPIO 18
  - Desviador peras: GPIO 19
- ✅ Banda transportadora con motor L298N
- ✅ Sensor de trigger MH Flying Fish (GPIO 4)
- ✅ Cámara CSI OV5647 o USB
- ✅ IA YOLOv8 avanzada

**Características:**
- 📊 Sistema completo de clasificación y etiquetado
- 🔄 Cambio automático de grupos según detección de IA
- 📦 Clasificación automática en 3 cajas
- 🌐 API REST en puerto 8000
- 📈 Dashboard web en puerto 8001
- 🎨 Interfaz frontend en puerto 3000
- 💾 Base de datos SQLite con métricas
- 🔮 Sistema de optimización predictiva

**Cuando usar:**
- Producción real en planta industrial
- Necesitas etiquetar múltiples categorías simultáneamente
- Requieres alto rendimiento (hasta 120 frutas/min)
- Necesitas clasificación automática por categoría

---

### Opción 2: 🎯 MODO PROTOTIPO

**Hardware requerido:**
- ✅ 1 etiquetadora con driver DRV8825:
  - Motor NEMA 17 para avance de etiquetas
  - Pines: STEP (GPIO 27), DIR (GPIO 22), ENABLE (GPIO 24)
  - Sensor YK0008 para posición (GPIO 19)
- ✅ 3 servomotores MG995 para clasificación:
  - Servo manzanas: GPIO 5
  - Servo peras: GPIO 6
  - Servo limones: GPIO 7
- ✅ Solenoide de etiquetado (GPIO 26)
- ✅ Banda transportadora (opcional)
- ✅ Sensor de trigger MH Flying Fish (GPIO 4)
- ✅ Cámara CSI OV5647 o USB
- ✅ IA YOLOv8 para detección

**Características:**
- 🎯 Sistema simplificado para desarrollo y pruebas
- 🔄 Etiquetado controlado por stepper DRV8825
- 📦 Clasificación con servos MG995 (3 categorías)
- 🤖 Detección con YOLOv8
- 📊 Dashboard básico de monitoreo
- 🧪 Ideal para pruebas y desarrollo

**Cuando usar:**
- Desarrollo y pruebas del sistema
- Validación de algoritmos de IA
- Prototipado de nuevas funcionalidades
- Presupuesto limitado o hardware en construcción
- Aprendizaje del sistema

**Archivo de configuración:**
```
Prototipo_Clasificador/Config_Prototipo.json
```

---

### Opción 3: 🚪 SALIR

Sale del sistema sin ejecutar nada.

---

## ⚙️ Variables de Entorno (Avanzado)

Puedes controlar el modo de operación usando variables de entorno:

### Modo Interactivo (por defecto)
```bash
# Sin variable o con VISIFRUIT_MODE=interactive
python main_etiquetadora_v4.py
```

### Forzar Modo Profesional
```bash
# Windows PowerShell
$env:VISIFRUIT_MODE="professional"
python main_etiquetadora_v4.py

# Linux/Mac
export VISIFRUIT_MODE=professional
python main_etiquetadora_v4.py
```

### Forzar Modo Prototipo
```bash
# Windows PowerShell
$env:VISIFRUIT_MODE="prototype"
python main_etiquetadora_v4.py

# Linux/Mac
export VISIFRUIT_MODE=prototype
python main_etiquetadora_v4.py
```

### Modo Auto-detección
```bash
# Detecta automáticamente según configuración disponible
$env:VISIFRUIT_MODE="auto"
python main_etiquetadora_v4.py
```

---

## 🔧 Solución de Problemas

### Error: "TOTAL_LABELERS is not defined"
✅ **SOLUCIONADO** - Este error ha sido corregido en la versión actual.

### El sistema se apaga automáticamente
- ✅ Verifica que no estés presionando `Ctrl+C` accidentalmente
- ✅ Revisa los logs en `logs/backend_ultra.log`
- ✅ Asegúrate de que el hardware esté conectado correctamente

### La cámara no se inicializa en Windows
- ⚠️ Normal en modo desarrollo - El sistema continuará en modo simulación
- ✅ Para usar cámara real, ejecuta en Raspberry Pi

### Error al iniciar frontend
- ⚠️ El frontend es opcional para el funcionamiento básico
- ✅ Verifica que tengas Node.js instalado si quieres usarlo
- ✅ Navega a `Interfaz_Usuario/VisiFruit` y ejecuta `npm install`

---

## 📊 Comparación de Modos

| Característica | 🏭 Profesional | 🎯 Prototipo |
|----------------|----------------|--------------|
| Etiquetadoras | 6 (3 grupos) | 1 (DRV8825) |
| Motor de posicionamiento | L298N lineal | NEMA 17 stepper |
| Clasificación | 2 servos MG995 | 3 servos MG995 |
| Throughput | Hasta 120/min | Hasta 40/min |
| IA | YOLOv8 dual-worker | YOLOv8 single-worker |
| API REST | ✅ Puerto 8000 | ✅ Puerto 8002 |
| Dashboard | ✅ Puerto 8001 | ✅ Básico |
| Frontend | ✅ Puerto 3000 | ❌ |
| Base de datos | ✅ SQLite completa | ✅ SQLite básica |
| Optimización predictiva | ✅ | ❌ |
| Ideal para | Producción | Desarrollo |

---

## 🆘 Soporte

Si tienes problemas con el selector de modos:

1. **Verifica los logs:**
   ```
   logs/backend_ultra.log
   ```

2. **Revisa la configuración:**
   - Modo Profesional: `Config_Etiquetadora.json`
   - Modo Prototipo: `Prototipo_Clasificador/Config_Prototipo.json`

3. **Contacta a soporte:**
   - Gabriel Calderón
   - Elias Bautista
   - Cristian Hernandez

---

## 📝 Notas Adicionales

- El selector de modos se activa **automáticamente** al ejecutar el script principal
- Puedes cambiar de modo **reiniciando** el sistema
- Ambos modos comparten la misma IA pero con configuraciones optimizadas
- El modo prototipo es **100% funcional** para desarrollo y pruebas
- Puedes migrar de prototipo a profesional sin cambiar el código

---

**Versión:** 4.0.0-MODULAR  
**Fecha:** Octubre 2025  
**Autores:** Gabriel Calderón, Elias Bautista, Cristian Hernandez

