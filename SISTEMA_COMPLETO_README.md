# 🚀 VisiFruit Sistema Completo v3.0 ULTRA

## 📋 Guía de Inicio Rápido para Raspberry Pi 5

¡Bienvenido al sistema VisiFruit completo! Esta guía te ayudará a poner en funcionamiento todo el sistema de etiquetado industrial con frontend, backend y controles de banda transportadora.

---

## 🎯 **Lo que se ha configurado automáticamente:**

✅ **Auto-inicio de servicios** - `main_etiquetadora.py` ahora inicia automáticamente:
- 🏷️ Sistema principal de etiquetado (Puerto 8000)
- 📊 Backend dashboard (Puerto 8001) 
- 🎨 Frontend React (Puerto 3000)

✅ **Controles de banda transportadora** - Nuevos controles en el frontend:
- ⬆️ Banda hacia adelante
- ⬇️ Banda hacia atrás
- ⏹️ Parar banda
- 🚨 Parada de emergencia
- ⚙️ Control de velocidad

✅ **Archivo .env configurado** - Todas las variables de entorno listas

✅ **Scripts de gestión** - Scripts para controlar el sistema fácilmente

---

## 🚀 **Inicio Rápido (3 comandos)**

```bash
# 1. Instalar dependencias (solo la primera vez)
./install_and_setup.sh

# 2. Iniciar sistema completo
./start_visifruit_system.sh start

# 3. Ver estado del sistema
./start_visifruit_system.sh status
```

¡Eso es todo! El sistema estará disponible en:
- 🏷️ **Sistema Principal**: http://localhost:8000
- 📊 **Dashboard**: http://localhost:8001  
- 🎨 **Frontend**: http://localhost:3000

---

## 📖 **Guía Completa**

### 1️⃣ **Primera instalación**

Si es la primera vez que usas el sistema:

```bash
# Instalar todas las dependencias automáticamente
./install_and_setup.sh

# O con servicio systemd (opcional)
./install_and_setup.sh --service
```

### 2️⃣ **Uso diario del sistema**

```bash
# Iniciar sistema completo
./start_visifruit_system.sh start

# Ver estado en tiempo real
./start_visifruit_system.sh status

# Ver logs en vivo
./start_visifruit_system.sh logs

# Detener sistema
./start_visifruit_system.sh stop

# Reiniciar sistema
./start_visifruit_system.sh restart
```

### 3️⃣ **Comandos adicionales**

```bash
# Forzar inicio (mata procesos en puertos ocupados)
./start_visifruit_system.sh start --force

# Verificar dependencias
./start_visifruit_system.sh check

# Limpiar logs antiguos
./start_visifruit_system.sh cleanup

# Backup de configuración
./start_visifruit_system.sh backup

# Ver ayuda completa
./start_visifruit_system.sh help
```

---

## 🌐 **URLs del Sistema**

Una vez iniciado el sistema, podrás acceder a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| 🏷️ **Sistema Principal** | http://localhost:8000 | API principal del sistema de etiquetado |
| 📄 **Documentación API** | http://localhost:8000/docs | Documentación interactiva de la API |
| 📊 **Dashboard Backend** | http://localhost:8001 | Backend con métricas avanzadas |
| 🎨 **Frontend React** | http://localhost:3000 | Interfaz principal del usuario |

---

## 🎮 **Nuevos Controles de Banda Transportadora**

### En el Frontend (Pestaña "Controles de Banda"):

- **🔄 Dirección**: Adelante / Atrás / Parado
- **⚡ Velocidad**: Slider de 0.1 a 2.0 m/s
- **🔘 Estado**: Habilitado / Deshabilitado  
- **🚨 Emergencia**: Parada inmediata
- **📊 Monitoreo**: Temperatura del motor, último comando, etc.

### API Endpoints para controlar la banda:

```bash
# Iniciar banda hacia adelante
curl -X POST http://localhost:8000/belt/start_forward

# Iniciar banda hacia atrás
curl -X POST http://localhost:8000/belt/start_backward

# Detener banda
curl -X POST http://localhost:8000/belt/stop

# Parada de emergencia
curl -X POST http://localhost:8000/belt/emergency_stop

# Establecer velocidad
curl -X POST http://localhost:8000/belt/set_speed \
  -H "Content-Type: application/json" \
  -d '{"speed": 1.5}'

# Ver estado de la banda
curl http://localhost:8000/belt/status
```

---

## ⚙️ **Configuración del Sistema**

### Archivo `.env` (Variables de entorno):

El archivo `.env` ya está configurado con valores óptimos para Raspberry Pi 5. Los principales parámetros son:

```env
# Puertos
BACKEND_PORT=8000
DASHBOARD_PORT=8001  
FRONTEND_PORT=3000

# Auto-inicio de servicios
AUTO_START_FRONTEND=true
AUTO_START_BACKEND=true

# Hardware GPIO (Raspberry Pi 5)
RELAY1_PIN_BCM=18      # Relay adelante
RELAY2_PIN_BCM=19      # Relay atrás
ENABLE_PIN_BCM=26      # Pin de habilitación
MOTOR_ACTIVE_STATE=LOW # Activación con nivel bajo

# Configuración de banda
BELT_SPEED_MPS=0.5     # Velocidad por defecto
ENABLE_BELT_CONTROL=true
```

### Configuración avanzada:

Puedes editar el archivo `.env` para personalizar:
- Pines GPIO utilizados
- Puertos de red
- Configuración de hardware
- Niveles de logging
- Y mucho más

---

## 🔧 **Solución de Problemas**

### Problema: "Puerto ocupado"
```bash
# Solución: Usar --force para liberar puertos
./start_visifruit_system.sh start --force
```

### Problema: "Dependencias faltantes"
```bash
# Solución: Reinstalar dependencias
./install_and_setup.sh
```

### Problema: "Error de permisos GPIO"
```bash
# Solución: Configurar permisos
sudo usermod -a -G gpio $USER
# Luego reiniciar sesión
```

### Problema: "Frontend no carga"
```bash
# Verificar Node.js
node --version
npm --version

# Reinstalar dependencias del frontend
cd Interfaz_Usuario/VisiFruit
npm install
```

### Ver logs detallados:
```bash
# Logs del sistema principal
./start_visifruit_system.sh logs main_system

# Logs en archivos
tail -f logs/main_system.log
tail -f logs/backend_ultra.log
```

---

## 📁 **Estructura del Proyecto**

```
VisiFruit/
├── 🚀 start_visifruit_system.sh     # Script principal de control
├── 🛠️ install_and_setup.sh         # Instalador automático
├── 📄 .env                          # Configuración del sistema
├── 🏷️ main_etiquetadora.py         # Sistema principal (con auto-inicio)
├── 📁 Interfaz_Usuario/
│   ├── 📊 Backend/                  # Backend dashboard (Puerto 8001)
│   └── 🎨 VisiFruit/               # Frontend React (Puerto 3000)
├── 📁 Control_Etiquetado/          # Controladores de hardware
├── 📁 IA_Etiquetado/               # Sistema de IA
├── 📁 logs/                        # Archivos de log
└── 📁 data/                        # Base de datos y datos
```

---

## 🎛️ **Caracteristicas del Hardware Soportado**

### GPIO Raspberry Pi 5:
- ✅ **lgpio** - Soporte nativo para Pi 5
- ✅ **Relays de 12V** - Control bidireccional de motor DC
- ✅ **Sensores** - Detección de frutas
- ✅ **Servomotores** - Sistema de desviadores
- ✅ **Cámaras** - Captura para IA

### Sistema de Banda Transportadora:
- **Motor DC** controlado por 2 relays
- **Dirección bidireccional** (adelante/atrás)
- **Control de velocidad** mediante PWM
- **Parada de emergencia** instantánea
- **Monitoreo de temperatura** del motor

---

## 📞 **Soporte y Contacto**

- **Autores**: Gabriel Calderón, Elias Bautista, Cristian Hernandez
- **Versión**: 3.0.0-ULTRA
- **Fecha**: Julio 2025

### Comandos útiles para diagnóstico:
```bash
# Estado completo del sistema
./start_visifruit_system.sh status

# Verificar dependencias
./start_visifruit_system.sh check

# Ver logs en tiempo real
./start_visifruit_system.sh logs

# Información del sistema
uname -a
python3 --version
node --version
```

---

## 🎉 **¡Listo para Producir!**

El sistema VisiFruit v3.0 ULTRA está completamente configurado y listo para usar. 

**Para iniciar todo el sistema:**
```bash
./start_visifruit_system.sh start
```

**Para acceder a la interfaz:**
Ve a http://localhost:3000 y navega a la pestaña "Controles de Banda" para probar los nuevos controles.

¡Disfruta de tu sistema de etiquetado industrial ultra-avanzado! 🚀
