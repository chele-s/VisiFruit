# 🚀 VisiFruit v4.0 - Inicio Rápido

## ⚡ Arranque Rápido en 3 Pasos

### 1️⃣ Activar Entorno Virtual

**Windows (PowerShell/CMD):**
```bash
venv\Scripts\activate
```

**Linux/Mac/Raspberry Pi:**
```bash
source venv/bin/activate
```

### 2️⃣ Ejecutar el Launcher

**Windows:**
```bash
# Doble clic o ejecutar:
.\start_visifruit_interactive.bat
```

**Linux/Raspberry Pi:**
```bash
# Primera vez: dar permisos
chmod +x start_visifruit_interactive.sh

# Ejecutar
./start_visifruit_interactive.sh
```

### 3️⃣ Seleccionar Modo

Verás este menú:

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

**Escoge:**
- `1` para sistema industrial completo
- `2` para prototipo de desarrollo
- `3` para salir

---

## 🎯 ¿Qué Modo Usar?

### Usa **Modo Profesional** (1) si:
- ✅ Tienes todo el hardware industrial instalado
- ✅ Estás en producción real
- ✅ Necesitas alto rendimiento (120 frutas/min)
- ✅ Tienes 6 etiquetadoras + motor DC + desviadores

### Usa **Modo Prototipo** (2) si:
- ✅ Estás desarrollando o probando
- ✅ Tienes hardware limitado o en construcción
- ✅ Solo tienes 1 etiquetadora con DRV8825
- ✅ Estás aprendiendo el sistema
- ✅ Necesitas validar la IA

---

## 🌐 URLs del Sistema

Después de iniciar, el sistema estará disponible en:

### Modo Profesional:
- 🏷️ **API Principal:** http://localhost:8000
- 📊 **Dashboard Backend:** http://localhost:8001
- 🎨 **Interfaz Frontend:** http://localhost:3000

### Modo Prototipo:
- 🏷️ **API Principal:** http://localhost:8002
- 📊 **Dashboard:** Integrado en API

---

## 🛑 Detener el Sistema

Presiona `Ctrl+C` en la terminal donde está corriendo el sistema.

El sistema hará un **shutdown seguro** apagando:
1. IA YOLOv8
2. Etiquetadoras
3. Motores
4. Servos
5. Banda transportadora
6. Base de datos

---

## ❌ Solución Rápida de Problemas

### Error: "TOTAL_LABELERS is not defined"
✅ **SOLUCIONADO** en esta versión

### Sistema se apaga inmediatamente
Posibles causas:
1. ⚠️ Presionaste `Ctrl+C` accidentalmente
2. ⚠️ Error en la configuración
3. ⚠️ Hardware no conectado

**Solución:**
```bash
# Revisar logs
cat logs/backend_ultra.log  # Linux
type logs\backend_ultra.log  # Windows
```

### Cámara no funciona en Windows
⚠️ **Normal** - El sistema continuará en modo simulación
✅ Para usar cámara real, ejecuta en Raspberry Pi

### Frontend no inicia
⚠️ Es opcional - El sistema funciona sin frontend
✅ Para instalarlo:
```bash
cd Interfaz_Usuario/VisiFruit
npm install
npm run dev
```

---

## 📖 Documentación Completa

- 📘 **SELECTOR_MODOS.md** - Guía completa de modos
- 📗 **CAMBIOS_V4.0_SELECTOR_MODOS.md** - Cambios y mejoras
- 📙 **README.md** - Documentación general del proyecto
- 📕 **Guias de uso/** - Guías específicas de cada componente

---

## 🆘 Ayuda Rápida

**Comandos útiles:**

```bash
# Ver estado de puertos
netstat -ano | findstr "8000 8001 3000"  # Windows
lsof -i :8000,8001,3000                  # Linux

# Ver procesos Python
tasklist | findstr python  # Windows
ps aux | grep python       # Linux

# Matar proceso si quedó colgado
taskkill /F /PID <PID>     # Windows
kill -9 <PID>              # Linux
```

---

## ✅ Checklist Pre-Arranque

Antes de ejecutar, verifica:

- [ ] ✅ Entorno virtual activado (`venv`)
- [ ] ✅ Dependencias instaladas
- [ ] ✅ Modelo YOLOv8 en `weights/best.pt`
- [ ] ✅ Configuración correcta según modo:
  - Profesional: `Config_Etiquetadora.json`
  - Prototipo: `Prototipo_Clasificador/Config_Prototipo.json`
- [ ] ✅ Hardware conectado (si no está en Windows para desarrollo)

---

## 🎓 Primeros Pasos para Nuevos Usuarios

1. **Día 1:** Ejecuta en modo prototipo sin hardware (simulación en Windows)
2. **Día 2:** Conecta la cámara y prueba detección de IA
3. **Día 3:** Conecta un servo y prueba clasificación básica
4. **Día 4:** Añade etiquetadora y prueba etiquetado
5. **Día 5:** Sistema completo funcionando

---

**¡Listo para empezar! 🚀**

Si necesitas ayuda, revisa la documentación completa en `SELECTOR_MODOS.md`

