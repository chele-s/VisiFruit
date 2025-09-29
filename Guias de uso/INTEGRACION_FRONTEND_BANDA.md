# 🎯 Guía de Integración Frontend - Control de Banda
## VisiFruit - Sistema Profesional y Prototipo

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura de Componentes](#arquitectura-de-componentes)
3. [Configuración de URLs y Puertos](#configuración-de-urls-y-puertos)
4. [Componentes Frontend](#componentes-frontend)
5. [Endpoints del Backend](#endpoints-del-backend)
6. [Configuración del Motor NEMA 17](#configuración-del-motor-nema-17)
7. [Flujo de Integración](#flujo-de-integración)
8. [Solución de Problemas](#solución-de-problemas)

---

## 🎬 Visión General

El sistema VisiFruit cuenta con **dos componentes de control de banda** en el frontend que funcionan con **ambas versiones del sistema**:

- ✅ **Versión Profesional**: Sistema completo con 12 etiquetadoras (`main_etiquetadora_v4.py`)
- ✅ **Versión Prototipo**: Sistema simplificado con clasificador (`smart_classifier_system.py`)

### Características Principales

- 🔄 **Conexión Dual**: Soporte simultáneo para sistema principal y demo
- 🎮 **Control Avanzado**: Control completo de banda + motor NEMA 17 (DRV8825)
- 📊 **Monitoreo en Tiempo Real**: Temperatura, velocidad, estado del sistema
- 💾 **Configuración Persistente**: Guardado automático en localStorage
- 🚨 **Seguridad**: Parada de emergencia integrada

---

## 🏗️ Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + TypeScript)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           BeltControlView.tsx (Vista Principal)           │  │
│  │  • Gestiona conexiones duales (main + demo)               │  │
│  │  • Coordina acciones entre sistemas                       │  │
│  │  • Maneja configuración de URLs                           │  │
│  └──────────────────┬────────────────────────────────────────┘  │
│                     │                                             │
│     ┌───────────────┴────────────────┐                           │
│     │                                │                           │
│  ┌──▼──────────────────┐  ┌──────────▼──────────────┐           │
│  │  BeltAdvancedControls│  │    BeltControls.tsx     │           │
│  │  • Control NEMA 17   │  │  • Controles básicos    │           │
│  │  • Config avanzada   │  │  • Interfaz simple      │           │
│  │  • Métricas completas│  │  • Estado esencial      │           │
│  └──────────────────────┘  └─────────────────────────┘           │
│                                                                   │
└───────────────────────┬───────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼────────┐
│   Sistema    │ │   Sistema   │ │  Backend UI  │
│  Principal   │ │    Demo     │ │  (Puerto     │
│ (Puerto 8000)│ │(Puerto 8002)│ │   8001)      │
└──────────────┘ └─────────────┘ └──────────────┘
```

---

## 🌐 Configuración de URLs y Puertos

### Puertos por Defecto

| Sistema | Puerto | Script | Descripción |
|---------|--------|--------|-------------|
| **Sistema Principal** | 8000 | `main_etiquetadora_v4.py` | Versión profesional con 12 etiquetadoras |
| **Backend UI** | 8001 | `Interfaz_Usuario/Backend/main.py` | API centralizada del frontend |
| **Sistema Demo** | 8002 | `demo_sistema_web_server.py` | Sistema de demostración |
| **Frontend** | 5173 | Vite Dev Server | Interfaz React |

### Configuración en `constants.ts`

```typescript
// Interfaz_Usuario/VisiFruit/src/config/constants.ts

export const APP_CONFIG = {
  api: {
    // Backend principal de la UI
    baseUrl: 'http://localhost:8001',
    
    // Sistema principal (main_etiquetadora.py)
    mainSystemUrl: 'http://localhost:8000',
    
    // Demo system (demo_sistema_web_server.py)  
    demoSystemUrl: 'http://localhost:8002',
    
    timeout: 10000,
  },
  // ... resto de configuración
}
```

### Variables de Entorno (`.env`)

```bash
# Backend UI principal
VITE_API_URL=http://localhost:8001

# Sistema principal (profesional)
VITE_MAIN_API_URL=http://localhost:8000

# Sistema demo (prototipo)
VITE_DEMO_API_URL=http://localhost:8002

# WebSocket
VITE_WS_URL=ws://localhost:8001/ws/realtime
```

---

## 🎨 Componentes Frontend

### 1. `BeltControlView.tsx` - Vista Principal

**Ubicación**: `Interfaz_Usuario/VisiFruit/src/components/views/BeltControlView.tsx`

**Responsabilidades**:
- ✅ Gestión de conexiones duales
- ✅ Coordinación de acciones entre sistemas
- ✅ Prueba automática de conectividad
- ✅ Manejo de errores y fallbacks
- ✅ Configuración de URLs

**Características**:

```typescript
interface ConnectionConfig {
  type: 'main' | 'demo' | 'both';  // Tipo de conexión
  mainUrl: string;                  // URL del sistema principal
  demoUrl: string;                  // URL del sistema demo
  autoConnect: boolean;             // Conexión automática
}

// Las acciones se ejecutan en paralelo cuando type='both'
await handleBeltAction('start_forward', { 
  connectionType: 'both'  // Envía a ambos sistemas
});
```

**Mapeo de Acciones**:

| Acción Frontend | Endpoint Main | Endpoint Demo |
|----------------|---------------|---------------|
| `start_forward` | `/belt/start_forward` | `/belt/start_forward` |
| `start_backward` | `/belt/start_backward` | `/belt/start_backward` |
| `stop` | `/belt/stop` | `/belt/stop` |
| `emergency_stop` | `/belt/emergency_stop` | `/belt/emergency_stop` |
| `set_speed` | `/belt/set_speed` | `/belt/set_speed` |
| `toggle_enable` | `/belt/toggle_enable` | `/belt/toggle_enable` |
| `stepper_manual_activation` | `/laser_stepper/test` | `/laser_stepper/test` |
| `stepper_sensor_trigger` | `/laser_stepper/test` | `/laser_stepper/test` |

---

### 2. `BeltAdvancedControls.tsx` - Control Avanzado

**Ubicación**: `Interfaz_Usuario/VisiFruit/src/components/production/BeltAdvancedControls.tsx`

**Características Principales**:

#### 🎛️ Control de Banda
- Dirección: Adelante / Atrás / Detener
- Control de velocidad: 0.1 - 2.5 m/s
- Parada de emergencia
- Habilitación/deshabilitación del sistema

#### ⚡ Control Motor NEMA 17 (DRV8825)
- **Activación manual**: Control directo desde UI
- **Activación por sensor**: Simulación de sensor MH Flying Fish
- **Configuración de potencia**: 10% - 100%
- **Duración configurable**: 0.1s - 5.0s
- **Velocidad de pasos**: 100 - 3000 pasos/segundo

#### 📊 Monitoreo en Tiempo Real
- Temperatura del motor
- Consumo de potencia
- Vibración
- Tiempo total de funcionamiento
- Temperatura del driver DRV8825
- Estadísticas de activaciones

#### Estructura de Configuración

```typescript
interface BeltConfiguration {
  defaultSpeed: number;                    // 0.1 - 2.5 m/s
  sensorActivationSpeed: number;           // Velocidad al detectar sensor
  accelerationRate: number;                // Tasa de aceleración
  decelerationRate: number;                // Tasa de desaceleración
  autoStartOnSensor: boolean;              // Auto-inicio por sensor
  emergencyStopEnabled: boolean;           // Habilitar parada emergencia
  maintenanceMode: boolean;                // Modo mantenimiento
  maxTemperature: number;                  // Temperatura máxima (°C)
  name: string;                            // Nombre de la banda
  description: string;                     // Descripción
  
  stepperConfig: {
    powerIntensity: number;                // 0-100% potencia al driver
    manualActivationDuration: number;      // Duración activación manual (s)
    sensorActivationDuration: number;      // Duración por sensor (s)
    enableAutoActivation: boolean;         // Activación automática
    minIntervalBetweenActivations: number; // Intervalo mínimo (s)
    currentStepSpeed: number;              // Velocidad en pasos/seg
    maxStepSpeed: number;                  // Velocidad máxima pasos/seg
  };
}
```

#### Estado del Sistema

```typescript
interface BeltStatus {
  isRunning: boolean;
  direction: 'forward' | 'backward' | 'stopped';
  currentSpeed: number;
  targetSpeed: number;
  motorTemperature: number;
  enabled: boolean;
  lastAction: string;
  actionTime: Date;
  powerConsumption: number;
  vibrationLevel: number;
  totalRuntime: number;
  isConnected: boolean;
  firmwareVersion: string;
  
  stepperStatus: {
    isActive: boolean;                     // Estado del stepper
    currentPower: number;                  // Potencia actual (0-100%)
    activationCount: number;               // Número de activaciones
    lastActivation: Date | null;           // Timestamp última activación
    activationDuration: number;            // Duración última activación
    totalActiveTime: number;               // Tiempo total activo (s)
    sensorTriggers: number;                // Triggers por sensor
    manualActivations: number;             // Activaciones manuales
    driverTemperature: number;             // Temperatura driver DRV8825
    currentStepRate: number;               // Velocidad actual pasos/seg
  };
}
```

---

### 3. `BeltControls.tsx` - Control Básico

**Ubicación**: `Interfaz_Usuario/VisiFruit/src/components/production/BeltControls.tsx`

**Características**:
- Controles básicos de dirección
- Control de velocidad simplificado
- Indicadores de estado esenciales
- Interfaz minimalista

**Uso**:
```typescript
<BeltControls
  onBeltAction={(action, params) => handleAction(action, params)}
  isConnected={true}
  disabled={false}
/>
```

---

## 🔌 Endpoints del Backend

### Sistema Principal (Puerto 8000)

**Archivo**: `main_etiquetadora_v4.py`, `ultra_api.py`

#### Control de Banda

```python
# POST /belt/start_forward
# Inicia la banda hacia adelante
Response: {
  "success": true,
  "message": "Banda iniciada hacia adelante",
  "direction": "forward",
  "timestamp": "2025-09-29T10:30:00"
}

# POST /belt/start_backward
# Inicia la banda hacia atrás
Response: {
  "success": true,
  "message": "Banda iniciada hacia atrás",
  "direction": "backward",
  "timestamp": "2025-09-29T10:30:00"
}

# POST /belt/stop
# Detiene la banda
Response: {
  "success": true,
  "message": "Banda detenida",
  "direction": "stopped",
  "timestamp": "2025-09-29T10:30:00"
}

# POST /belt/emergency_stop
# Parada de emergencia
Response: {
  "success": true,
  "message": "PARADA DE EMERGENCIA EJECUTADA",
  "direction": "emergency_stopped",
  "system_disabled": true,
  "timestamp": "2025-09-29T10:30:00"
}

# POST /belt/set_speed
Body: { "speed": 1.5 }  // m/s
Response: {
  "success": true,
  "message": "Velocidad establecida a 1.5 m/s",
  "speed_ms": 1.5,
  "speed_percent": 75.0,
  "timestamp": "2025-09-29T10:30:00"
}

# GET /belt/status
# Obtiene el estado de la banda
Response: {
  "isRunning": true,
  "direction": "forward",
  "speed": 1.0,
  "temperature": 42.5,
  "timestamp": "2025-09-29T10:30:00"
}
```

#### Control Motor NEMA 17 (DRV8825)

```python
# POST /laser_stepper/toggle
Body: { "enabled": true }
Response: {
  "success": true,
  "enabled": true,
  "message": "Stepper habilitado"
}

# POST /laser_stepper/test
Body: {
  "duration": 0.6,      // segundos
  "intensity": 80.0     // porcentaje
}
Response: {
  "success": true,
  "duration": 0.6,
  "intensity": 80.0,
  "message": "Stepper activado por 0.6s"
}
```

---

### Sistema Demo (Puerto 8002)

**Archivo**: `Control_Etiquetado/demo_sistema_web_server.py`

**Endpoints**: Mismos que el sistema principal

**Diferencias**:
- Incluye modo simulación cuando no hay hardware
- Response incluye campo `"simulation": true/false`
- Logging más verboso para debugging

**Ejemplo**:
```python
# POST /belt/start_forward (en modo simulación)
Response: {
  "success": true,
  "message": "Banda iniciada hacia adelante (simulación)",
  "direction": "forward",
  "simulation": true,  // ← Indica modo simulación
  "timestamp": "2025-09-29T10:30:00"
}
```

---

### Backend UI (Puerto 8001)

**Archivo**: `Interfaz_Usuario/Backend/main.py`

**Función**: API centralizada que puede comunicarse con los otros sistemas si es necesario.

---

## ⚙️ Configuración del Motor NEMA 17

### Configuración en el Backend

#### Sistema Profesional (`Config_Etiquetadora.json`)

```json
{
  "laser_stepper_settings": {
    "enabled": true,
    "name": "LabelApplicatorStepper",
    "type": "stepper",
    "step_pin_bcm": 19,
    "dir_pin_bcm": 26,
    "enable_pin_bcm": 21,
    "enable_active_low": true,
    "base_speed_sps": 1500,
    "max_speed_sps": 3000,
    "min_speed_sps": 100,
    "step_pulse_us": 4,
    "activation_on_laser": {
      "enabled": true,
      "activation_duration_seconds": 0.6,
      "intensity_percent": 80.0,
      "min_interval_seconds": 0.15
    }
  }
}
```

#### Sistema Prototipo (`Config_Prototipo.json`)

```json
{
  "laser_stepper_settings": {
    "enabled": true,
    "type": "stepper",
    "name": "Stepper_Laser",
    "step_pin_bcm": 19,
    "dir_pin_bcm": 26,
    "enable_pin_bcm": 21,
    "enable_active_low": true,
    "base_speed_sps": 1500,
    "max_speed_sps": 2000,
    "acceleration_sps2": 500,
    "step_pulse_us": 4,
    "activation_duration_seconds": 0.6,
    "steps_per_revolution": 200,
    "microsteps": 1
  }
}
```

### Configuración en el Frontend

**localStorage**: `visifruit_belt_config`

```json
{
  "stepperConfig": {
    "powerIntensity": 80,
    "manualActivationDuration": 0.6,
    "sensorActivationDuration": 0.6,
    "enableAutoActivation": true,
    "minIntervalBetweenActivations": 0.15,
    "currentStepSpeed": 1500,
    "maxStepSpeed": 3000
  }
}
```

### Parámetros Recomendados

| Parámetro | Valor Mínimo | Valor Máximo | Recomendado | Descripción |
|-----------|--------------|--------------|-------------|-------------|
| **Potencia** | 10% | 100% | 80% | Potencia enviada al driver DRV8825 |
| **Duración Manual** | 0.1s | 5.0s | 0.6s | Tiempo de activación manual |
| **Duración Sensor** | 0.1s | 5.0s | 0.6s | Tiempo de activación por sensor |
| **Velocidad Pasos** | 100 sps | 3000 sps | 1500 sps | Velocidad en pasos por segundo |
| **Intervalo Mínimo** | 50ms | 1000ms | 150ms | Tiempo mínimo entre activaciones |

---

## 🔄 Flujo de Integración

### Caso 1: Iniciar Banda en Ambos Sistemas

```typescript
// Usuario hace clic en "Iniciar Adelante"
// Frontend: BeltAdvancedControls.tsx
handleBeltAction('start_forward') 
  ↓
// Frontend: BeltControlView.tsx
handleBeltAction('start_forward', { connectionType: 'both' })
  ↓
// Ejecuta en paralelo:
Promise.allSettled([
  callMainSystemAPI('start_forward'),      // → http://localhost:8000/belt/start_forward
  callDemoSystemAPI('start_forward')       // → http://localhost:8002/belt/start_forward
])
  ↓
// Actualiza estado local del frontend
setBeltStatus({ isRunning: true, direction: 'forward', ... })
  ↓
// Muestra alerta de éxito
showAlert('Banda iniciada hacia adelante')
```

### Caso 2: Activación Manual del Motor NEMA 17

```typescript
// Usuario hace clic en "Activar Demo Manual"
// Frontend: BeltAdvancedControls.tsx
handleBeltAction('stepper_manual_activation')
  ↓
// Actualiza estado local inmediatamente (UI responsiva)
setBeltStatus(prev => ({
  ...prev,
  stepperStatus: {
    isActive: true,
    currentPower: configuration.stepperConfig.powerIntensity,
    manualActivations: prev.stepperStatus.manualActivations + 1,
    currentStepRate: configuration.stepperConfig.currentStepSpeed,
    ...
  }
}))
  ↓
// Llama API del backend
callDemoSystemAPI('stepper_manual_activation', {
  duration: 0.6,
  intensity: 80.0
})
  ↓
// Backend ejecuta activación física
await laser_stepper.activate_for_duration(0.6, 80.0)
  ↓
// Después de la duración, frontend desactiva automáticamente
setTimeout(() => {
  setBeltStatus(prev => ({
    ...prev,
    stepperStatus: {
      ...prev.stepperStatus,
      isActive: false,
      currentPower: 0,
      totalActiveTime: prev.stepperStatus.totalActiveTime + 0.6
    }
  }))
}, 600)  // 0.6 segundos
```

### Caso 3: Cambio de Configuración

```typescript
// Usuario cambia configuración y guarda
// Frontend: BeltAdvancedControls.tsx - Dialog de configuración
handleConfigSave()
  ↓
// Guarda en localStorage
localStorage.setItem('visifruit_belt_config', JSON.stringify(configuration))
  ↓
// Callback opcional al componente padre
if (onConfigChange) {
  onConfigChange(configuration)
}
  ↓
// El backend lee su propia configuración de Config_*.json
// No es necesario sincronizar con el backend en este caso
// ya que cada sistema tiene su configuración independiente
```

---

## 🚨 Solución de Problemas

### Problema 1: "Sistema desconectado o deshabilitado"

**Síntomas**:
- Botones deshabilitados
- Alerta de error al intentar acciones

**Solución**:
1. Verificar que los servicios backend estén ejecutándose:
   ```bash
   # Terminal 1: Sistema Principal
   python main_etiquetadora_v4.py
   
   # Terminal 2: Sistema Demo
   python Control_Etiquetado/demo_sistema_web_server.py
   ```

2. Verificar las URLs en el frontend:
   - Abrir DevTools → Console
   - Buscar errores de `fetch` o `CORS`
   
3. Probar conectividad manualmente:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8002/health
   ```

4. Verificar configuración en `constants.ts`

---

### Problema 2: Motor NEMA 17 no responde

**Síntomas**:
- Botones de activación manual no hacen nada
- No hay respuesta física del motor

**Solución**:

1. **Verificar hardware**:
   ```bash
   # En la Raspberry Pi
   python Control_Etiquetado/demo_laser_stepper.py
   ```

2. **Verificar configuración GPIO**:
   - Revisar `Config_Prototipo.json` o `Config_Etiquetadora.json`
   - Confirmar pines BCM correctos:
     - `step_pin_bcm: 19`
     - `dir_pin_bcm: 26`
     - `enable_pin_bcm: 21`

3. **Verificar driver DRV8825**:
   - Alimentación correcta (8-35V)
   - Microstepping configurado
   - Enable activo (LOW si `enable_active_low: true`)

4. **Ver logs del backend**:
   ```bash
   tail -f logs/prototipo_clasificador.log
   ```

---

### Problema 3: Configuración no se guarda

**Síntomas**:
- Cambios en diálogo de configuración no persisten
- Al recargar página, vuelve a valores anteriores

**Solución**:

1. **Verificar localStorage**:
   ```javascript
   // En DevTools Console
   console.log(localStorage.getItem('visifruit_belt_config'));
   console.log(localStorage.getItem('visifruit_stepper_config'));
   ```

2. **Limpiar localStorage corrupto**:
   ```javascript
   // En DevTools Console
   localStorage.removeItem('visifruit_belt_config');
   localStorage.removeItem('visifruit_stepper_config');
   // Recargar página
   ```

3. **Verificar permisos del navegador**:
   - Asegurarse de que no esté en modo incógnito
   - Verificar que el sitio tenga permisos de almacenamiento

---

### Problema 4: "No hay sistemas conectados para ejecutar la acción"

**Síntomas**:
- Error al intentar cualquier acción
- Todos los sistemas muestran "Desconectado"

**Solución**:

1. **Verificar modo de conexión**:
   - Ir a la sección "Configuración" en la UI
   - Cambiar entre "Principal", "Demo", "Ambos"
   - Click en "Probar Conexiones"

2. **Verificar CORS**:
   - En `Config_Etiquetadora.json`:
   ```json
   "api_settings": {
     "enable_cors": true,
     "cors_origins": [
       "http://localhost:3000",
       "http://localhost:5173"
     ]
   }
   ```

3. **Verificar firewall**:
   ```bash
   # Linux
   sudo ufw allow 8000
   sudo ufw allow 8002
   ```

---

### Problema 5: Valores de configuración incorrectos

**Síntomas**:
- Sliders no responden
- Valores fuera de rango
- `TypeError` en console

**Solución**:

1. **Verificar validación de rangos** en `BeltAdvancedControls.tsx`:
   ```typescript
   // Potencia: 10-100%
   min={10} max={100} step={5}
   
   // Duración: 0.1-5.0s
   min={0.1} max={5.0} step={0.1}
   
   // Velocidad: 100-3000 sps
   min={100} max={configuration.stepperConfig.maxStepSpeed} step={100}
   ```

2. **Reset a valores por defecto**:
   ```javascript
   // DevTools Console
   localStorage.removeItem('visifruit_belt_config');
   location.reload();
   ```

---

## ✅ Checklist de Integración

### Backend

- [ ] `main_etiquetadora_v4.py` ejecutándose en puerto 8000
- [ ] `demo_sistema_web_server.py` ejecutándose en puerto 8002
- [ ] Endpoints de banda respondiendo correctamente
- [ ] Endpoints de stepper respondiendo correctamente
- [ ] CORS configurado para frontend
- [ ] Hardware conectado (si aplica)

### Frontend

- [ ] `constants.ts` con URLs correctas
- [ ] Componentes `BeltControls` y `BeltAdvancedControls` importados
- [ ] `BeltControlView` montado en ruta `/belt-control`
- [ ] localStorage funcionando
- [ ] Conexión a WebSocket (opcional)
- [ ] Manejo de errores implementado

### Configuración

- [ ] `Config_Etiquetadora.json` o `Config_Prototipo.json` configurado
- [ ] Pines GPIO correctos
- [ ] Parámetros de stepper validados
- [ ] Configuración de banda validada
- [ ] Variables de entorno establecidas

---

## 📚 Referencias Adicionales

### Documentos Relacionados

- `CAMBIOS_PINES_Y_SERVOS.md` - Configuración de hardware
- `QUICK_START_V4.md` - Inicio rápido del sistema
- `README_V4.md` - Documentación general v4
- `BELT_CONTROL_README.md` - Guía específica del control de banda

### Archivos de Configuración

- `Config_Etiquetadora.json` - Sistema profesional
- `Prototipo_Clasificador/Config_Prototipo.json` - Sistema prototipo
- `Interfaz_Usuario/VisiFruit/src/config/constants.ts` - Frontend

### Componentes Clave

- `Interfaz_Usuario/VisiFruit/src/components/views/BeltControlView.tsx`
- `Interfaz_Usuario/VisiFruit/src/components/production/BeltAdvancedControls.tsx`
- `Interfaz_Usuario/VisiFruit/src/components/production/BeltControls.tsx`

---

## 🎓 Mejores Prácticas

### 1. Manejo de Errores

```typescript
try {
  await handleBeltAction('start_forward');
} catch (error) {
  console.error('Error:', error);
  showAlert('Error al ejecutar acción', 'error');
  // Revertir estado local si es necesario
  setBeltStatus(prev => ({ ...prev, isRunning: false }));
}
```

### 2. Validación de Parámetros

```typescript
// Antes de enviar al backend
if (speed < 0.1 || speed > 2.5) {
  showAlert('Velocidad debe estar entre 0.1 y 2.5 m/s', 'warning');
  return;
}
```

### 3. Feedback al Usuario

```typescript
// Mostrar inmediatamente en UI
setBeltStatus({ isRunning: true, direction: 'forward' });
showAlert('Banda iniciada hacia adelante', 'success');

// Luego ejecutar acción en backend
await onBeltAction('start_forward');
```

### 4. Configuración Persistente

```typescript
// Guardar automáticamente al cambiar
useEffect(() => {
  localStorage.setItem('visifruit_belt_config', JSON.stringify(configuration));
  if (onConfigChange) {
    onConfigChange(configuration);
  }
}, [configuration]);
```

### 5. Timeouts y Reintentos

```typescript
const response = await fetch(`${url}/belt/start_forward`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  signal: AbortSignal.timeout(10000),  // 10 segundos timeout
});
```

---

## 🎯 Conclusión

Con esta guía, ambos sistemas (Profesional y Prototipo) están completamente integrados con el frontend. Los componentes `BeltControls` y `BeltAdvancedControls` funcionan perfectamente con:

✅ **Sistema Profesional** (`main_etiquetadora_v4.py`)
✅ **Sistema Prototipo** (`smart_classifier_system.py` + `demo_sistema_web_server.py`)
✅ **Modo Dual** (ambos sistemas simultáneamente)
✅ **Configuración Persistente** (localStorage)
✅ **Control Motor NEMA 17** (DRV8825)
✅ **Monitoreo en Tiempo Real**

¡Tu sistema está listo para producción y desarrollo! 🚀

---

**Última actualización**: 29 de septiembre de 2025  
**Versión**: 1.0.0  
**Autores**: Gabriel Calderón, Elias Bautista, Cristian Hernandez
