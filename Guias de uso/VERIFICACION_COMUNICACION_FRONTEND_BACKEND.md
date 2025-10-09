# 🔗 Verificación de Comunicación Frontend-Backend - VisiFruit

## 📋 Resumen General

Este documento detalla la arquitectura de comunicación completa entre el frontend React/TypeScript y el backend Python/FastAPI, incluyendo todos los componentes del sistema de clasificación de frutas.

**Fecha de actualización:** 2025-01-09
**Versión del sistema:** 4.0 - Prototipo Edition

---

## 🏗️ Arquitectura de Comunicación

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/MUI)                         │
│                         http://localhost:3000                        │
│                                                                      │
│  Components:                                                         │
│  - BeltAdvancedControls.tsx  (Control banda + stepper + diverters)  │
│  - ProductionDashboard.tsx   (Dashboard principal)                  │
│  - SystemMonitor.tsx         (Monitoreo en tiempo real)            │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │ HTTP REST API
                               │ (polling cada 2-5 segundos)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND AUXILIAR (FastAPI)                        │
│                        http://localhost:8001                         │
│                                                                      │
│  Archivos: Interfaz_Usuario/Backend/main.py                        │
│  - Proxy inteligente entre frontend y sistema principal             │
│  - Almacena históricos (belt, stepper, diverters)                  │
│  - Calcula métricas agregadas                                      │
│  - Sistema de alertas                                               │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               │ HTTP REST API
                               │ (conexión directa cada petición)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SISTEMA PRINCIPAL (FastAPI)                        │
│                        http://localhost:8000                         │
│                                                                      │
│  Archivos: Prototipo_Clasificador/smart_classifier_system.py       │
│  - Control directo del hardware                                     │
│  - IA de detección (YOLOv8)                                        │
│  - Gestión de componentes:                                          │
│    • Banda transportadora (RelayMotorDriverPi5)                    │
│    • Stepper DRV8825/NEMA17 (etiquetadora)                         │
│    • Servos MG995 (clasificación)                                  │
│    • Desviadores MG995 (FruitDiverterController)                   │
│    • Sensores (MH Flying Fish)                                      │
│    • Cámara (Raspberry Pi Camera)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📡 Flujo de Datos Completo

### 1. **Banda Transportadora** (Motor DC con 2 Relays)

#### 🔧 Backend Principal (puerto 8000)

**Archivo:** `Prototipo_Clasificador/smart_classifier_system.py`

**Endpoints disponibles:**
```python
GET  /status                    # Estado completo (incluye banda)
POST /belt/start_forward        # Iniciar banda adelante (ON/OFF para relay)
POST /belt/start_backward       # Revertir dirección
POST /belt/stop                 # Detener banda
POST /belt/emergency_stop       # Parada de emergencia
POST /belt/set_speed            # Solo para motores PWM (error para relay)
POST /belt/toggle_enable        # Habilitar/deshabilitar
GET  /belt/status               # Estado detallado de banda
```

**Datos enviados al frontend:**
```typescript
interface BeltStatus {
  available: boolean;           // Si la banda está disponible
  running: boolean;             // Si está corriendo
  isRunning: boolean;           // Alias para compatibilidad
  direction: 'forward' | 'backward' | 'stopped';
  enabled: boolean;
  controlType: 'relay' | 'pwm' | 'l298n';  // ✨ NUEVO
  hasSpeedControl: boolean;     // ✨ NUEVO: false para relay
  currentSpeed: number;         // 0.0 o 1.0 para relay
  targetSpeed: number;
  motorTemperature: number;
  lastAction: string;
  actionTime: string;           // ISO timestamp
  timestamp: number;
}
```

**Detección automática del tipo de motor:**
```python
# En get_system_status:
if hasattr(self.belt, 'driver') and self.belt.driver:
    driver_class_name = self.belt.driver.__class__.__name__
    
    if 'RelayMotor' in driver_class_name:
        belt_control_type = "relay"
        has_speed_control = False
        # 🚀 RelayMotorDriverPi5 detectado (lgpio, Pi5)
    elif 'PWM' in driver_class_name or 'L298N' in driver_class_name:
        belt_control_type = "pwm"
        has_speed_control = True
```

#### 🔄 Backend Auxiliar (puerto 8001)

**Archivo:** `Interfaz_Usuario/Backend/main.py`

**Proceso:**
1. Conecta a `http://localhost:8000/status` cada 2 segundos
2. Extrae y enriquece datos de banda
3. Almacena histórico en `_belt_history` (últimas 1000 muestras)
4. Calcula métricas:
   - `belt_uptime_percent`: % de tiempo que la banda estuvo activa

**Datos adicionales agregados:**
```python
{
  "belt": {
    ...status_from_main_system,
    "totalRuntime": current_time - self.start_time,
    "timestamp": current_time
  },
  "historical": {
    "belt_uptime_percent": 85.5,  # Calculado de histórico
    "data_points": {
      "belt": 1000  # Muestras almacenadas
    }
  }
}
```

#### 🖥️ Frontend (React)

**Componente:** `BeltAdvancedControls.tsx`

**Sincronización con backend:**
```typescript
// Effect que actualiza estado desde externalStatus
useEffect(() => {
  if (!externalStatus) return;
  
  setBeltStatus(prev => ({
    ...prev,
    isRunning: externalStatus.isRunning ?? externalStatus.running,
    direction: externalStatus.direction,
    controlType: externalStatus.controlType ?? externalStatus.control_type,
    hasSpeedControl: externalStatus.hasSpeedControl ?? externalStatus.has_speed_control,
    // ... más campos
  }));
}, [externalStatus]);
```

**Visualización adaptativa:**
```typescript
// Mostrar control de velocidad SOLO si el motor lo soporta
{beltStatus.hasSpeedControl ? (
  <Slider value={beltStatus.targetSpeed} onChange={handleSpeedChange} />
) : (
  <Typography>Motor ON/OFF (sin control de velocidad)</Typography>
)}
```

---

### 2. **Stepper Motor DRV8825/NEMA17** (Etiquetadora)

#### 🔧 Backend Principal (puerto 8000)

**Endpoints disponibles:**
```python
POST /laser_stepper/toggle      # Habilitar/deshabilitar
POST /laser_stepper/test        # Activación manual de prueba
GET  /laser_stepper/status      # Estado del stepper
```

**Datos enviados:**
```typescript
interface StepperStatus {
  available: boolean;
  enabled: boolean;
  isActive: boolean;              // Si está actualmente activo
  currentPower: number;           // 0-100%
  activationCount: number;        // Total de activaciones
  lastActivation: string | null;  // ISO timestamp
  lastActivationTimestamp: number | null;
  sensorTriggers: number;         // ✨ NUEVO: Activaciones por sensor
  manualActivations: number;      // ✨ NUEVO: Activaciones manuales
  activationDuration: number;     // Duración en segundos
  driverTemperature: number;
  currentStepRate: number;        // Pasos por segundo
  timestamp: number;
}
```

**Lógica de detección de actividad:**
```python
# En get_system_status:
stepper_is_active = False
history = getattr(self.labeler, 'activation_history', [])
if history:
    stepper_last_activation_ts = history[-1]
    stepper_last_activation = datetime.fromtimestamp(history[-1]).isoformat()
    # Considerar activo si la última activación fue hace <= 1.5s
    if (current_time - history[-1]) <= 1.5:
        stepper_is_active = True
        stepper_power = 80
```

**Contadores separados:**
```python
# Incrementar en sensor_callback:
self.stats["stepper_sensor_triggers"] += 1

# Incrementar en /laser_stepper/test:
self.stats["stepper_manual_activations"] += 1
```

#### 🔄 Backend Auxiliar (puerto 8001)

**Persistencia histórica:**
```python
if main_system_status and "stepper" in main_system_status:
    stepper_status.update(main_system_status["stepper"])
    
    # Persistir histórico
    self._stepper_history.append({
        "timestamp": current_time,
        "isActive": stepper_status.get("isActive", False),
        "sensorTriggers": stepper_status.get("sensorTriggers", 0),
        "manualActivations": stepper_status.get("manualActivations", 0)
    })
```

**Métricas calculadas:**
```python
"stepper_activation_rate": 12.5  # % de tiempo activo
```

#### 🖥️ Frontend

**Visualización en tiempo real:**
```typescript
// Estado del stepper actualizado desde externalStatus
stepperStatus: {
  isActive: externalStatus.stepperStatus?.isActive ?? false,
  currentPower: externalStatus.stepperStatus?.currentPower ?? 0,
  sensorTriggers: externalStatus.stepperStatus?.sensorTriggers ?? 0,
  manualActivations: externalStatus.stepperStatus?.manualActivations ?? 0,
  lastActivation: new Date(externalStatus.stepperStatus.lastActivation),
}
```

**Indicadores visuales:**
- 🟢 LED verde cuando `isActive: true`
- 📊 Gráfico de activaciones (sensor vs manual)
- 🕐 Tiempo desde última activación

---

### 3. **Desviadores (FruitDiverterController)** ✨ NUEVO

#### 🔧 Backend Principal (puerto 8000)

**Endpoints disponibles:**
```python
GET  /diverters/status          # Estado de todos los desviadores
POST /diverters/test            # Prueba manual de desviador
POST /diverters/classify/{category}  # Clasificar fruta manualmente
```

**Modelo de datos:**
```python
class DiverterTestRequest(BaseModel):
    category: str  # "apple", "pear", "lemon"
    delay: float = 0.0  # Delay en segundos
```

**Respuesta de estado:**
```typescript
interface DiversStatus {
  available: boolean;
  enabled: boolean;
  initialized: boolean;
  diverters_count: number;
  active_diverters: string[];  // IDs de desviadores activos
  diverters: {
    apple: {
      id: number;
      pin: number;
      current_position: 'straight' | 'diverted';
      activations: number;
    };
    pear: { ... };
    lemon: { ... };
  };
  classification_flow: {
    apple: "Desviador 0 → Caja manzanas";
    pear: "Desviador 1 → Caja peras";
    lemon: "Sin desviador → Caja final";
  };
  timestamp: string;
}
```

**Flujo de clasificación:**
```
🍎 Manzanas → Desviador 0 (GPIO Pin X) → Caja manzanas
🍐 Peras    → Desviador 1 (GPIO Pin Y) → Caja peras
🍋 Limones  → Sin desviador           → Caja final
```

#### 🔄 Backend Auxiliar (puerto 8001)

**Sincronización:**
```python
# Estado de los desviadores CON DATOS REALES O FALLBACK
diverters_status = {
    "available": False,
    "enabled": True,
    "initialized": False,
    "diverters_count": 0,
    "active_diverters": [],
    "diverters": {},
    "timestamp": current_time
}

if main_system_status and "diverters" in main_system_status:
    diverters_status.update(main_system_status["diverters"])
    
    # Persistir histórico
    self._diverters_history.append({
        "timestamp": current_time,
        "initialized": diverters_status.get("initialized", False),
        "active_count": len(diverters_status.get("active_diverters", []))
    })
```

**Métricas:**
```python
"diverters_usage_rate": 8.3  # % de tiempo con desviadores activos
```

---

## 🔍 Verificación de Comunicación

### ✅ Checklist de Funcionamiento

#### 1. Verificar Backend Principal (puerto 8000)
```bash
# Desde navegador o curl:
curl http://localhost:8000/health
# Respuesta esperada:
{
  "status": "healthy",
  "system": "VisiFruit Prototipo",
  "version": "1.0.0",
  "state": "idle",
  "running": false
}

# Estado completo:
curl http://localhost:8000/status
# Debe contener: belt, stepper, diverters
```

#### 2. Verificar Backend Auxiliar (puerto 8001)
```bash
curl http://localhost:8001/api/system/ultra-status
# Respuesta debe incluir:
{
  "belt": { ... },
  "stepper": { ... },
  "diverters": { ... },
  "historical": {
    "belt_uptime_percent": ...,
    "stepper_activation_rate": ...,
    "diverters_usage_rate": ...
  }
}
```

#### 3. Verificar Frontend (puerto 3000)
1. **Abrir:** http://localhost:3000
2. **Verificar componentes:**
   - ✅ BeltAdvancedControls muestra estado de banda
   - ✅ Muestra "ENCENDIDO/APAGADO" para motor relay
   - ✅ Oculta slider de velocidad si `hasSpeedControl: false`
   - ✅ Muestra estado del stepper con contadores separados
   - ✅ Muestra estado de desviadores (si configurados)

#### 4. Pruebas de Integración

**Test 1: Iniciar Banda**
```bash
curl -X POST http://localhost:8000/belt/start_forward
# Frontend debe actualizar:
# - isRunning: true
# - direction: "forward"
# - Mostrar LED verde
```

**Test 2: Activar Stepper Manualmente**
```bash
curl -X POST http://localhost:8000/laser_stepper/test \
  -H "Content-Type: application/json" \
  -d '{"duration": 0.6, "intensity": 80.0}'
# Frontend debe:
# - Incrementar manualActivations
# - Actualizar lastActivation
# - Mostrar LED de actividad
```

**Test 3: Probar Desviador**
```bash
curl -X POST http://localhost:8000/diverters/test \
  -H "Content-Type: application/json" \
  -d '{"category": "apple", "delay": 0.0}'
# Frontend debe:
# - Actualizar estado del desviador de manzanas
# - Incrementar contador de activaciones
```

---

## 🐛 Debugging y Solución de Problemas

### Problema: Frontend no recibe datos

**Diagnóstico:**
```javascript
// En DevTools > Console:
console.log('Estado recibido:', externalStatus);
```

**Soluciones:**
1. Verificar que backend auxiliar esté corriendo (puerto 8001)
2. Verificar que sistema principal esté corriendo (puerto 8000)
3. Revisar logs del backend:
   ```bash
   # Logs del sistema principal:
   tail -f logs/smart_classifier_system.log
   
   # Logs del backend auxiliar:
   tail -f Interfaz_Usuario/Backend/logs/backend.log
   ```

### Problema: Datos desincronizados

**Causa común:** Formato de datos incompatible (camelCase vs snake_case)

**Solución implementada:**
```typescript
// En BeltAdvancedControls.tsx:
controlType: externalStatus.controlType ?? externalStatus.control_type,
hasSpeedControl: externalStatus.hasSpeedControl ?? externalStatus.has_speed_control,
// Fallback para compatibilidad con ambos formatos
```

### Problema: Stepper no muestra actividad reciente

**Causa:** Window de detección muy corta

**Solución:**
```python
# En smart_classifier_system.py:
# Considerar activo si última activación <= 1.5s
if (current_time - history[-1]) <= 1.5:
    stepper_is_active = True
```

---

## 📊 Métricas y Monitoreo

### Datos Históricos Disponibles

**Belt (Banda):**
- Historial de running/stopped (últimas 1000 muestras)
- Uptime percentage
- Cambios de dirección

**Stepper:**
- Activaciones (sensor vs manual)
- Tasa de activación
- Historial de timestamps

**Diverters:**
- Uso por categoría (apple, pear, lemon)
- Tasa de utilización
- Historial de activaciones

### Endpoints de Métricas

```python
GET /config/stepper     # Configuración del stepper
GET /config/sensor      # Configuración del sensor
GET /config/safety      # Configuración de seguridad
GET /config/servos      # Configuración de servos
```

---

## 🚀 Próximas Mejoras

- [ ] WebSocket para datos en tiempo real (eliminar polling)
- [ ] Gráficos históricos en tiempo real (Chart.js)
- [ ] Alertas proactivas al frontend
- [ ] Exportar métricas a CSV/JSON
- [ ] Dashboard de análisis predictivo

---

## 📝 Notas Técnicas

### Compatibilidad de Tipos
- Backend usa `snake_case` (Python)
- Frontend usa `camelCase` (TypeScript)
- Se implementan aliases para compatibilidad:
  ```python
  "isRunning": belt_running,
  "running": belt_running,  # Alias
  ```

### Timeouts y Reintentos
- Frontend: polling cada 2-5 segundos
- Backend auxiliar: timeout de 2 segundos para main system
- Reintentos automáticos con backoff exponencial

### Seguridad
- CORS habilitado para desarrollo
- Para producción: configurar origins específicos
- Validación de datos con Pydantic en backend
- Sanitización de inputs en frontend

---

**Autor:** Gabriel Calderón, Elias Bautista, Cristian Hernandez  
**Última actualización:** 2025-01-09  
**Sistema:** VisiFruit v4.0 - Prototipo Edition

