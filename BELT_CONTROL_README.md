# 🎛️ Control Avanzado de Banda Transportadora - VisiFruit

## 📋 Descripción

Página especializada para el control avanzado de la banda transportadora del sistema VisiFruit, con soporte dual para conexión tanto con `main_etiquetadora.py` como con `demo_sistema_web_server.py`.

## ✨ Características Principales

### 🚀 Control Inteligente
- **Start/Stop avanzado**: Controles de dirección con animaciones fluidas
- **Control de velocidad**: Slider inteligente con configuración persistente (0.1 - 2.5 m/s)
- **Parada de emergencia**: Botón de emergencia con confirmación visual
- **Auto-habilitación**: Sistema de habilitación/deshabilitación automático

### ⚙️ Configuración Persistente
- **Velocidad por defecto**: Se guarda en localStorage y persiste entre sesiones
- **Velocidad de sensor**: Configuración específica para activación automática
- **Configuración de conexión**: Dual, Principal, o Demo

### 🔗 Conexión Dual
- **Sistema Principal**: `main_etiquetadora.py` (puerto 8000)
- **Sistema Demo**: `demo_sistema_web_server.py` (puerto 8002)
- **Fallback automático**: Si un sistema no está disponible, continúa con el otro
- **Indicadores visuales**: Estado de conexión en tiempo real

## 🚀 Instalación y Configuración

### 1. Frontend (React + TypeScript)

```bash
cd Interfaz_Usuario/VisiFruit
npm install
npm run dev
```

### 2. Sistema Principal (main_etiquetadora.py)

```bash
# Desde la raíz del proyecto
python main_etiquetadora.py
```

**Puerto**: 8000  
**Endpoints**: `/belt/*`, `/laser_stepper/*`, `/health`, `/status`

### 3. Demo Web Server (NUEVO)

```bash
# Instalar dependencias web si no están disponibles
pip install fastapi uvicorn

# Ejecutar demo web server
python Control_Etiquetado/demo_sistema_web_server.py
```

**Puerto**: 8002  
**Endpoints**: Compatibles con main_etiquetadora.py

## 🌐 URLs del Sistema Completo

Una vez que todos los servicios estén funcionando:

- **🎨 Frontend React**: http://localhost:3000
- **📊 Dashboard Backend**: http://localhost:8001  
- **🏷️ Sistema Principal**: http://localhost:8000
- **🔧 Demo Web Server**: http://localhost:8002

### Documentación de APIs:
- **Principal**: http://localhost:8000/docs
- **Demo**: http://localhost:8002/docs

## 🎮 Uso de la Página de Control de Banda

### Acceso
1. Abrir el frontend: http://localhost:3000
2. En la barra lateral, hacer clic en **"Control de Banda"** 🎛️
3. La página detectará automáticamente los sistemas disponibles

### Configuración de Conexión

**Pestaña "Configuración de Conexión"**:
- **Dual**: Conecta a ambos sistemas (recomendado)
- **Principal**: Solo sistema principal
- **Demo**: Solo demo web server

### Controles Disponibles

#### 🎢 Control de Banda
- **▶️ ADELANTE**: Inicia la banda hacia adelante
- **◀️ ATRÁS**: Inicia la banda hacia atrás  
- **⏹️ PARAR**: Detiene la banda
- **🚨 EMERGENCIA**: Parada de emergencia

#### ⚙️ Configuración
- **Slider de Velocidad**: 0.1 - 2.5 m/s
- **Toggle Enable**: Habilitar/deshabilitar sistema
- **Velocidad por Defecto**: Se guarda automáticamente

#### 📊 Estado en Tiempo Real
- **Indicadores de conexión**: Verde = conectado, Rojo = desconectado
- **Estado de banda**: Funcionando, Parada, Error
- **Velocidad actual**: Muestra la velocidad configurada
- **Estadísticas**: Tiempo de funcionamiento, activaciones

## 📡 Endpoints de API

### Sistema Principal (puerto 8000)
```
POST /belt/start_forward     - Iniciar banda adelante
POST /belt/start_backward    - Iniciar banda atrás
POST /belt/stop              - Parar banda
POST /belt/emergency_stop    - Parada de emergencia
POST /belt/set_speed         - Establecer velocidad
POST /belt/toggle_enable     - Habilitar/deshabilitar
GET  /belt/status            - Estado de banda
POST /laser_stepper/toggle   - Toggle stepper
POST /laser_stepper/test     - Prueba stepper
GET  /health                 - Estado del sistema
GET  /status                 - Estado detallado
```

### Demo Web Server (puerto 8002)
Mismos endpoints que el sistema principal, completamente compatibles.

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# URLs de los sistemas
VITE_MAIN_API_URL=http://localhost:8000
VITE_DEMO_API_URL=http://localhost:8002
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws/realtime

# Auto-inicio de servicios
AUTO_START_FRONTEND=true
AUTO_START_BACKEND=true
AUTO_CLEAN_ON_START=true
```

### Personalización

El componente `BeltAdvancedControls.tsx` puede ser personalizado:

- **Colores**: Modificar el tema en `src/config/constants.ts`
- **Velocidades**: Ajustar rangos en el componente
- **Animaciones**: Configurar en la sección de animaciones
- **Intervalos de actualización**: Configurar polling rates

## 🛠️ Troubleshooting

### Demo Web Server No Inicia
```bash
# Verificar dependencias
pip install fastapi uvicorn

# Verificar puerto disponible
lsof -i :8002

# Ejecutar con logs detallados
python Control_Etiquetado/demo_sistema_web_server.py
```

### Frontend No Se Conecta
1. Verificar que todos los servicios estén funcionando
2. Revisar la consola del navegador para errores CORS
3. Confirmar que las URLs en `.env` son correctas

### Sistema Principal No Responde
1. Verificar que `main_etiquetadora.py` esté ejecutándose
2. Comprobar el puerto 8000 en http://localhost:8000/health
3. Revisar logs del sistema principal

## 🧪 Testing

### Prueba de Conectividad
```bash
# Probar sistema principal
curl http://localhost:8000/health

# Probar demo web server  
curl http://localhost:8002/health

# Probar backend dashboard
curl http://localhost:8001/health
```

### Prueba de Banda
```bash
# Iniciar banda adelante (sistema principal)
curl -X POST http://localhost:8000/belt/start_forward

# Iniciar banda adelante (demo)
curl -X POST http://localhost:8002/belt/start_forward

# Parar banda
curl -X POST http://localhost:8000/belt/stop
curl -X POST http://localhost:8002/belt/stop
```

## 📝 Notas Técnicas

- **Arquitectura**: Microservicios con APIs REST
- **Comunicación**: HTTP/WebSocket
- **Persistencia**: localStorage para configuraciones
- **Fallback**: Simulación automática si hardware no disponible
- **Compatibilidad**: Los endpoints del demo son 100% compatibles con el sistema principal

## 🎯 Características de Producción

- ✅ **Control dual simultáneo**
- ✅ **Persistencia de configuración**  
- ✅ **Fallback automático**
- ✅ **Indicadores visuales de estado**
- ✅ **Validación de velocidades**
- ✅ **Parada de emergencia**
- ✅ **Control de habilitación**
- ✅ **Estadísticas en tiempo real**

---

**Desarrollado para VisiFruit v3.0 - Sistema Ultra-Industrial**  
*Gabriel Calderón, Elias Bautista, Cristian Hernandez*


