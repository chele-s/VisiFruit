# 🚀 VisiFruit v3.0 RT-DETR - Instalador para Raspberry Pi 5

<p align="center">
<img src="Others/Images/VisiFruit Logo Github.png" alt="Logo de VisiFruit" width="200">
</p>

<p align="center">
<strong>Instalador Completo y Automatizado para Raspberry Pi 5</strong><br>
<em>Sistema Industrial de Etiquetado de Frutas con RT-DETR</em>
</p>

---

## 📦 Archivos del Instalador

Este instalador está compuesto por varios scripts especializados que trabajan en conjunto para configurar completamente VisiFruit en tu Raspberry Pi 5:

### 🔧 Scripts Principales

| Script | Propósito | Descripción |
|--------|-----------|-------------|
| **`install_visifruit_complete.sh`** | 🎯 **SCRIPT MAESTRO** | Ejecuta toda la instalación automáticamente |
| **`raspberry_pi5_installer.sh`** | 📦 Instalación Base | Sistema operativo, dependencias, usuarios, servicios |
| **`install_rtdetr_pi5.sh`** | 🤖 RT-DETR Específico | PyTorch, Transformers, RT-DETR optimizado |
| **`raspberry_pi5_camera_setup.sh`** | 📷 Configuración de Cámaras | Detección, calibración, optimización cámaras |
| **`raspberry_pi5_optimizer.sh`** | ⚡ Optimización Pi 5 | CPU, GPU, memoria, rendimiento específico |

### 📚 Documentación

| Archivo | Contenido |
|---------|-----------|
| **`README_INSTALACION_PI5.md`** | 📖 Guía completa de instalación paso a paso |
| **`INSTALADOR_PI5_README.md`** | 📋 Este archivo - resumen del instalador |

---

## 🚀 Instalación Rápida (Recomendada)

### Opción 1: Instalación Automática Completa

```bash
# 1. Clonar o copiar el proyecto VisiFruit a tu Pi 5
git clone https://github.com/tu-usuario/VisiFruit.git
cd VisiFruit

# 2. Ejecutar instalador completo (30-60 minutos)
sudo ./install_visifruit_complete.sh
```

**¡Eso es todo!** El script maestro se encarga de ejecutar todos los componentes automáticamente.

### Opción 2: Instalación Paso a Paso (Avanzada)

```bash
# 1. Instalación base del sistema
sudo ./raspberry_pi5_installer.sh

# 2. Configuración específica de RT-DETR
sudo ./install_rtdetr_pi5.sh

# 3. Configuración de cámaras (opcional)
sudo ./raspberry_pi5_camera_setup.sh

# 4. Optimizaciones específicas (opcional)
sudo ./raspberry_pi5_optimizer.sh
```

---

## ⚙️ Características del Instalador

### ✅ Lo Que Incluye

- **🔧 Configuración Completa del Sistema**
  - Usuario dedicado `visifruit` con permisos adecuados
  - Dependencias del sistema Debian/Ubuntu
  - Configuración de hardware (GPIO, I2C, SPI, cámara)
  - Servicios systemd para auto-inicio

- **🤖 Instalación Optimizada de RT-DETR**
  - PyTorch optimizado para ARM64
  - Transformers y HuggingFace libraries
  - PaddlePaddle (si disponible) + PyTorch backends
  - YOLO como fallback automático
  - Variables de entorno optimizadas

- **📷 Configuración Inteligente de Cámaras**
  - Auto-detección de cámaras USB y CSI
  - Herramientas de calibración incluidas
  - Optimizaciones de rendimiento de video
  - Scripts de prueba y diagnóstico

- **⚡ Optimizaciones Específicas para Pi 5**
  - Configuración de CPU/GPU optimizada
  - Gestión térmica avanzada
  - Optimizaciones de memoria y I/O
  - Herramientas de monitoreo incluidas

- **🌐 Interfaz Web Lista para Usar**
  - Frontend React compilado automáticamente
  - Backend FastAPI configurado
  - Nginx como proxy reverso
  - Acceso web inmediato tras instalación

### 🛠️ Herramientas Incluidas

Después de la instalación, tendrás disponibles estos comandos:

```bash
# Gestión principal del sistema
visifruit {start|stop|restart|status|logs|update}

# Información y monitoreo
visifruit-info                    # Info completa del sistema
visifruit-monitor [continuous]    # Monitor en tiempo real

# Gestión de cámaras
visifruit-camera detect           # Detectar cámaras
visifruit-camera test [id]        # Probar cámara específica
visifruit-camera calibrate [id]   # Calibrar cámara
visifruit-camera info             # Info del sistema de cámaras

# Gestión de RT-DETR
visifruit-rtdetr test             # Probar instalación RT-DETR
visifruit-rtdetr info             # Info de componentes IA
visifruit-rtdetr benchmark        # Benchmark de rendimiento

# Optimización de rendimiento
visifruit-tune max-performance    # Máximo rendimiento
visifruit-tune balanced           # Modo balanceado
visifruit-tune power-save         # Ahorro de energía
visifruit-tune status             # Estado actual
```

---

## 🎯 Requisitos del Sistema

### 📱 Hardware Mínimo

| Componente | Mínimo | Recomendado |
|------------|---------|-------------|
| **Raspberry Pi** | Pi 5 (4GB RAM) | Pi 5 (8GB RAM) |
| **Almacenamiento** | MicroSD 32GB Clase 10 | SSD USB 3.0 128GB+ |
| **Alimentación** | 5V/3A | 5V/5A oficial Pi 5 |
| **Cámara** | USB 2.0 webcam | USB 3.0 industrial |

### 🐧 Software

| Requisito | Versión |
|-----------|---------|
| **OS** | Raspberry Pi OS (64-bit) Bookworm | 
| **Python** | 3.11+ (incluido) |
| **Node.js** | 18+ (instalado automáticamente) |
| **Espacio Libre** | 8GB mínimo |

### 🌐 Red

- Conexión a internet durante la instalación
- Acceso SSH (opcional, para instalación remota)

---

## 📊 Proceso de Instalación

### Fases de la Instalación Automática

```
FASE 1: Instalación Base (15-25 min)
├── Configuración de usuario del sistema
├── Actualización del sistema operativo  
├── Instalación de dependencias del sistema
├── Configuración de hardware (GPIO, I2C, SPI, cámara)
└── Instalación del proyecto VisiFruit

FASE 2: Entorno Python y IA (10-20 min)
├── Configuración de entorno virtual Python
├── Instalación de PyTorch optimizado para ARM64
├── Instalación de RT-DETR (PaddlePaddle + PyTorch)
├── Instalación de dependencias de IA y visión
└── Configuración de modelos RT-DETR

FASE 3: Configuración Avanzada (5-10 min)
├── Detección y configuración automática de cámaras
├── Optimizaciones específicas para Pi 5
├── Configuración de servicios systemd
├── Construcción del frontend web
└── Configuración de nginx

FASE 4: Finalización (2-5 min)
├── Creación de herramientas de gestión
├── Configuración de monitoreo
├── Pruebas del sistema
└── Verificación final
```

### ⏱️ Tiempos Esperados

| Hardware | Tiempo Total |
|----------|--------------|
| **Pi 5 (8GB) + SSD** | 25-35 minutos |
| **Pi 5 (4GB) + microSD rápida** | 35-50 minutos |
| **Pi 5 (4GB) + microSD lenta** | 50-80 minutos |

---

## 🔍 Verificación Post-Instalación

### Comandos de Verificación

```bash
# Verificar servicios principales
visifruit status

# Verificar RT-DETR
visifruit-rtdetr test

# Verificar cámaras
visifruit-camera detect

# Monitor completo del sistema
visifruit-monitor

# Información detallada
visifruit-info
```

### Acceso Web

Después de la instalación, accede a:
- **URL Local**: `http://localhost` (desde la Pi)
- **URL Red**: `http://[IP-de-tu-Pi]` (desde otros dispositivos)

Para encontrar la IP de tu Pi:
```bash
hostname -I
```

---

## 🛠️ Personalización y Configuración

### Archivos de Configuración Principales

```
/home/visifruit/VisiFruit/
├── Config_Etiquetadora.json          # Configuración principal
├── config/
│   ├── camera_config.json            # Configuración de cámara
│   └── rtdetr/
│       └── environment.sh             # Variables de entorno RT-DETR
├── models/                           # Modelos RT-DETR
└── logs/                            # Logs del sistema
```

### Personalizar Modelo RT-DETR

1. **Copiar tu modelo entrenado:**
```bash
sudo cp tu_modelo_rtdetr.pth /home/visifruit/VisiFruit/models/
```

2. **Editar configuración:**
```bash
sudo nano /home/visifruit/VisiFruit/Config_Etiquetadora.json
```

3. **Ejemplo de configuración:**
```json
{
  "ai_model_settings": {
    "model_type": "rtdetr",
    "model_path": "/home/visifruit/VisiFruit/models/tu_modelo_rtdetr.pth",
    "confidence_threshold": 0.5,
    "class_names": ["apple", "pear", "lemon", "orange"]
  }
}
```

---

## 🔧 Resolución de Problemas

### Problemas Comunes

#### ❌ "Error: Sin conexión a internet"
```bash
# Verificar conectividad
ping google.com

# Configurar WiFi
sudo raspi-config
```

#### ❌ "Error: Espacio insuficiente"
```bash
# Verificar espacio
df -h

# Limpiar espacio si es necesario
sudo apt clean
sudo apt autoremove
```

#### ❌ "Error: No se puede abrir la cámara"
```bash
# Verificar detección
visifruit-camera detect

# Verificar permisos
sudo usermod -a -G video visifruit
```

#### ❌ "Error: RT-DETR no funciona"
```bash
# Ejecutar diagnóstico completo
visifruit-rtdetr test

# Verificar logs
journalctl -u visifruit -f
```

### Logs del Sistema

```bash
# Logs principales
sudo journalctl -u visifruit -f
sudo journalctl -u visifruit-backend -f

# Logs específicos
tail -f /home/visifruit/VisiFruit/logs/backend_ultra.log
tail -f /tmp/visifruit_install.log
```

### Reinstalación

Si necesitas reinstalar:

```bash
# Limpiar instalación previa
sudo systemctl stop visifruit visifruit-backend nginx
sudo userdel -r visifruit 2>/dev/null || true
sudo rm -rf /home/visifruit

# Ejecutar instalador nuevamente
sudo ./install_visifruit_complete.sh
```

---

## 📞 Soporte y Recursos

### Documentación Adicional

- **📖 Guía Completa**: `README_INSTALACION_PI5.md` - Manual detallado
- **🔄 Migración RT-DETR**: `MIGRACION_RT-DETR.md` - Detalles técnicos
- **🎮 Control del Sistema**: `README_LAUNCHER.md` - Interfaz de usuario

### Archivos de Log

- **📝 Instalación**: `/tmp/visifruit_install.log`
- **📝 Sistema**: `/home/visifruit/VisiFruit/logs/`
- **📝 Servicios**: `journalctl -u visifruit`

### Comandos de Ayuda

```bash
visifruit --help
visifruit-camera --help
visifruit-rtdetr --help
visifruit-tune --help
```

---

## 🎉 ¡Listo para Producción!

Una vez completada la instalación, tendrás:

- ✅ **Sistema VisiFruit completamente funcional**
- ✅ **RT-DETR optimizado para Pi 5**
- ✅ **Interfaz web accesible**
- ✅ **Herramientas de gestión completas**
- ✅ **Monitoreo en tiempo real**
- ✅ **Servicios auto-iniciables**

### Próximos Pasos

1. **Acceder a la interfaz web**: `http://[IP-de-tu-Pi]`
2. **Calibrar cámaras**: `visifruit-camera calibrate`
3. **Cargar modelo personalizado** (si tienes uno)
4. **Configurar parámetros** según tus necesidades
5. **¡Comenzar a detectar frutas!** 🍎🍊🍋

---

<p align="center">
<strong>🍓 ¡Tu sistema VisiFruit v3.0 RT-DETR está listo! 🚀</strong>
</p>
