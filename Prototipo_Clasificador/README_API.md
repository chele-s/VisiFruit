# API REST del Sistema de Prototipo - VisiFruit
==================================================

Esta API REST permite controlar remotamente el sistema de clasificación de frutas del prototipo desde la interfaz web o cualquier cliente HTTP.

## 🌐 Servidor API

- **Puerto**: 8000
- **Host**: 0.0.0.0 (accesible desde la red local)
- **Documentación**: http://localhost:8000/docs (Swagger UI automático)
- **Estado**: Inicia automáticamente con el sistema de prototipo

## 📋 Endpoints Disponibles

### ✅ Sistema y Estado

#### `GET /`
Información básica del sistema.

**Respuesta**:
```json
{
  "system": "VisiFruit Prototipo API",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "status": "/status",
    "belt_control": "/belt/*",
    "docs": "/docs"
  }
}
```

#### `GET /health`
Health check del sistema.

**Respuesta**:
```json
{
  "status": "healthy",
  "system": "VisiFruit Prototipo",
  "version": "1.0.0",
  "state": "running",
  "running": true,
  "timestamp": "2025-10-08T12:15:30.123456"
}
```

#### `GET /status`
Estado completo del sistema con estadísticas.

**Respuesta**:
```json
{
  "state": "running",
  "running": true,
  "stats": {
    "detections_total": 42,
    "labeled_total": 40,
    "classified_total": 38,
    "detections_by_class": {
      "apple": 15,
      "pear": 12,
      "lemon": 15
    }
  },
  "components": {
    "camera": true,
    "ai_detector": true,
    "labeler": true,
    "servos": true,
    "belt": true,
    "sensor": true
  }
}
```

---

### 🎚️ Control de Banda Transportadora

#### `POST /belt/start_forward`
Inicia la banda transportadora hacia adelante.

**Respuesta**:
```json
{
  "status": "success",
  "action": "belt_start_forward",
  "message": "Banda iniciada hacia adelante"
}
```

#### `POST /belt/start_backward`
Inicia la banda en reversa.

**Respuesta**:
```json
{
  "status": "success",
  "action": "belt_start_backward",
  "message": "Banda iniciada hacia atrás"
}
```

#### `POST /belt/stop`
Detiene la banda.

**Respuesta**:
```json
{
  "status": "success",
  "action": "belt_stop",
  "message": "Banda detenida"
}
```

#### `POST /belt/emergency_stop`
Parada de emergencia inmediata.

**Respuesta**:
```json
{
  "status": "success",
  "action": "emergency_stop",
  "message": "Parada de emergencia ejecutada"
}
```

#### `POST /belt/set_speed`
Ajusta la velocidad de la banda (no soportado con relays).

**Parámetros**:
- `speed` (float): Velocidad en porcentaje (0-100)

**Respuesta**:
```json
{
  "status": "success",
  "action": "set_speed",
  "speed": 75.0,
  "message": "Velocidad ajustada a 75.0"
}
```

#### `POST /belt/toggle_enable`
Activa/desactiva la banda.

**Respuesta**:
```json
{
  "status": "success",
  "action": "toggle_enable",
  "enabled": true
}
```

#### `GET /belt/status`
Obtiene el estado actual de la banda.

**Respuesta**:
```json
{
  "available": true,
  "running": true,
  "enabled": true,
  "direction": "forward",
  "speed": 1.0,
  "motor_temperature": 35.0
}
```

---

### 🏷️ Control del Stepper DRV8825 (Etiquetadora)

#### `POST /laser_stepper/toggle`
Activa/desactiva el stepper (siempre activo si está disponible).

**Respuesta**:
```json
{
  "status": "success",
  "enabled": true,
  "message": "Stepper DRV8825 siempre activo"
}
```

#### `POST /laser_stepper/test`
Prueba manual del stepper para aplicar etiqueta.

**Respuesta**:
```json
{
  "status": "success",
  "action": "stepper_test",
  "duration": 0.6,
  "intensity": 80.0,
  "message": "Stepper activado exitosamente"
}
```

**Efecto**: Activa el stepper DRV8825 por 0.6 segundos al 80% de intensidad.

#### `GET /laser_stepper/status`
Estado del stepper DRV8825.

**Respuesta**:
```json
{
  "available": true,
  "enabled": true,
  "type": "DRV8825",
  "motor": "NEMA 17",
  "state": "idle",
  "config": {
    "step_pin": 19,
    "dir_pin": 26,
    "enable_pin": 21,
    "base_speed_sps": 1500,
    "max_speed_sps": 2000
  }
}
```

---

### 🤖 Control de Servos MG995 (Clasificadores)

#### `GET /servos/status`
Estado de todos los servomotores.

**Respuesta**:
```json
{
  "available": true,
  "servos": {
    "apple": {
      "category": "apple",
      "pin": 5,
      "current_angle": 90.0,
      "default_angle": 90.0,
      "available": true
    },
    "pear": {
      "category": "pear",
      "pin": 6,
      "current_angle": 90.0,
      "default_angle": 90.0,
      "available": true
    },
    "lemon": {
      "category": "lemon",
      "pin": 7,
      "current_angle": 90.0,
      "default_angle": 90.0,
      "available": true
    }
  },
  "total_servos": 3
}
```

#### `POST /servos/test/{category}`
Prueba un servo específico.

**Parámetros de URL**:
- `category`: "apple", "pear", o "lemon"

**Ejemplo**: `POST /servos/test/apple`

**Respuesta**:
```json
{
  "status": "success",
  "category": "apple",
  "message": "Servo apple activado exitosamente"
}
```

**Efecto**: Activa la compuerta del servo para la categoría especificada por 2 segundos.

---

### 📡 Control y Simulación de Sensor

#### `POST /sensor/simulate`
Simula la activación del sensor MH Flying Fish.

**Respuesta**:
```json
{
  "status": "success",
  "message": "Sensor simulado - etiquetadora y captura programadas"
}
```

**Efecto**: 
1. Activa la etiquetadora DRV8825 (0.5s @ 30%)
2. Programa captura de imagen después del delay configurado
3. La IA procesará la imagen y clasificará la fruta detectada

**Uso**: Ideal para probar el sistema sin necesidad de una fruta física pasando por el sensor.

#### `GET /sensor/status`
Estado del sensor de trigger.

**Respuesta**:
```json
{
  "available": true,
  "type": "MH Flying Fish",
  "pin": 4,
  "enabled": true,
  "trigger_level": "falling",
  "config": {
    "pin_bcm": 4,
    "trigger_on_state": "LOW",
    "pull_up_down": "PUD_UP",
    "debounce_time_ms": 50
  }
}
```

---

### ⚙️ Configuración

#### `GET /config/stepper`
Configuración del stepper DRV8825.

**Respuesta**:
```json
{
  "enabled": true,
  "type": "stepper",
  "step_pin_bcm": 19,
  "dir_pin_bcm": 26,
  "enable_pin_bcm": 21,
  "base_speed_sps": 1500,
  "max_speed_sps": 2000,
  "activation_duration_seconds": 0.6
}
```

#### `GET /config/sensor`
Configuración del sensor de trigger.

**Respuesta**:
```json
{
  "trigger_sensor": {
    "enabled": true,
    "type": "mh_flying_fish",
    "pin_bcm": 4,
    "trigger_level": "falling",
    "debounce_time_ms": 50
  }
}
```

#### `GET /config/safety`
Configuración de seguridad.

**Respuesta**:
```json
{
  "emergency_stop_enabled": true,
  "max_continuous_activations": 10,
  "overheat_protection": true,
  "max_temperature_c": 70,
  "watchdog_timeout_s": 30
}
```

#### `GET /config/servos`
Configuración de servos MG995.

**Respuesta**:
```json
{
  "apple": {
    "pin_bcm": 5,
    "default_angle": 90,
    "activation_offset_deg": -45,
    "activation_duration_s": 2.0
  },
  "pear": {...},
  "lemon": {...}
}
```

---

## 🔧 Ejemplos de Uso

### Python

```python
import requests

BASE_URL = "http://192.168.1.150:8000"  # IP de tu Raspberry Pi

# Iniciar banda
response = requests.post(f"{BASE_URL}/belt/start_forward")
print(response.json())

# Simular sensor (prueba de etiquetado)
response = requests.post(f"{BASE_URL}/sensor/simulate")
print(response.json())

# Probar servo de manzanas
response = requests.post(f"{BASE_URL}/servos/test/apple")
print(response.json())

# Obtener estado del sistema
response = requests.get(f"{BASE_URL}/status")
print(response.json())

# Detener banda
response = requests.post(f"{BASE_URL}/belt/stop")
print(response.json())
```

### JavaScript/TypeScript (Frontend)

```typescript
const API_URL = 'http://192.168.1.150:8000';

// Iniciar banda
async function startBelt() {
  const response = await fetch(`${API_URL}/belt/start_forward`, {
    method: 'POST'
  });
  const data = await response.json();
  console.log(data);
}

// Simular sensor
async function simulateSensor() {
  const response = await fetch(`${API_URL}/sensor/simulate`, {
    method: 'POST'
  });
  const data = await response.json();
  console.log(data);
}

// Probar stepper
async function testStepper() {
  const response = await fetch(`${API_URL}/laser_stepper/test`, {
    method: 'POST'
  });
  const data = await response.json();
  console.log(data);
}
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Iniciar banda
curl -X POST http://localhost:8000/belt/start_forward

# Simular sensor
curl -X POST http://localhost:8000/sensor/simulate

# Probar stepper
curl -X POST http://localhost:8000/laser_stepper/test

# Estado del sistema
curl http://localhost:8000/status

# Detener banda
curl -X POST http://localhost:8000/belt/stop
```

---

## 🌐 Acceso desde la Red Local

Si quieres acceder a la API desde otra computadora en la misma red:

1. **En la Raspberry Pi**, encuentra tu IP:
```bash
hostname -I
```

2. **Desde otra computadora**, usa esa IP:
```bash
curl http://192.168.1.150:8000/health
```

3. **En el frontend** (opcional), configura `.env.local`:
```bash
VITE_MAIN_API_URL=http://192.168.1.150:8000
```

---

## 📚 Documentación Interactiva

FastAPI genera automáticamente documentación interactiva:

### Swagger UI
Accede a: `http://localhost:8000/docs`

Características:
- Prueba endpoints directamente desde el navegador
- Ve todos los parámetros y respuestas
- Ejecuta peticiones de prueba

### ReDoc
Accede a: `http://localhost:8000/redoc`

Características:
- Documentación más detallada
- Mejor para leer y entender la API
- Exportable a PDF

---

## ⚠️ Notas Importantes

1. **Reversa del Motor**: Solo funciona con controladores que soporten cambio de dirección (L298N, Relays con 2 canales). Los relays simples solo permiten ON/OFF.

2. **Simulación de Sensor**: Usa esto para probar el sistema sin hardware. Activará todo el flujo: etiquetadora → captura → IA → clasificación.

3. **Control de Velocidad**: Los relays no soportan control de velocidad variable. Solo ON/OFF a velocidad máxima.

4. **Seguridad**: La parada de emergencia (`/belt/emergency_stop`) detiene inmediatamente todos los componentes.

5. **Estado Inicial**: Cuando el sistema inicia, la banda arranca automáticamente en modo FORWARD. Esto se refleja correctamente en `/belt/status`.

---

## 🐛 Solución de Problemas

### API no responde

```bash
# Verifica que el sistema esté corriendo
ps aux | grep smart_classifier

# Verifica el puerto
netstat -tulpn | grep 8000
```

### Error 503 (Service Unavailable)

Significa que el componente no está disponible:
- `Banda no disponible`: Error en inicialización del controlador de banda
- `Etiquetadora no disponible`: Error en DRV8825
- `Servos no disponibles`: Error en servos MG995

**Solución**: Revisa los logs del sistema para detalles del error.

### Error 501 (Not Implemented)

Significa que la funcionalidad no está soportada por el hardware actual:
- `Reversa no soportada`: Tu controlador de banda no permite cambio de dirección
- `Control de velocidad no soportado`: Estás usando relays simples

---

**Última actualización**: Octubre 2025  
**Versión API**: 1.0.0  
**Sistema**: VisiFruit Prototipo

