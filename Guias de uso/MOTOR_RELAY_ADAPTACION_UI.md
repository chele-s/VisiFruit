# 🎛️ Adaptación de UI para Motor Relay (Velocidad Fija)

## 📋 Problema Identificado

El sistema tenía un **motor DC con control de relays** que:
- ✅ Solo puede estar **ON/OFF** (adelante/atrás/detenido)
- ❌ **NO tiene control de velocidad variable** por software
- ❌ La velocidad solo puede cambiarse modificando físicamente las bobinas del motor
- ⚠️ El frontend mostraba un slider de velocidad que **no funcionaba**

---

## ✅ Solución Implementada

### **1. Backend: Detección Automática del Tipo de Motor**

#### **Endpoint `/status` Actualizado**
```python
# Detectar tipo de motor automáticamente
belt_control_type = "relay"  # Por defecto
has_speed_control = False

if self.belt and hasattr(self.belt, 'driver'):
    driver_class_name = self.belt.driver.__class__.__name__
    if 'Relay' in driver_class_name:
        belt_control_type = "relay"
        has_speed_control = False
    elif 'PWM' in driver_class_name or 'L298N' in driver_class_name:
        belt_control_type = "pwm"
        has_speed_control = True

# Respuesta incluye información del tipo de motor
belt_status = {
    "control_type": belt_control_type,      # "relay" o "pwm"
    "has_speed_control": has_speed_control  # true o false
}
```

**Respuesta JSON:**
```json
{
  "belt": {
    "available": true,
    "running": true,
    "direction": "forward",
    "control_type": "relay",         // ← NUEVO
    "has_speed_control": false       // ← NUEVO
  }
}
```

---

#### **Endpoint `/belt/set_speed` Validado**
```python
@app.post("/belt/set_speed")
async def belt_set_speed(request: BeltSpeedRequest):
    # Verificar si el motor soporta velocidad
    if not has_speed_control:
        raise HTTPException(
            status_code=501, 
            detail="Motor con relays no soporta control de velocidad. "
                   "Solo tiene velocidad fija (ON/OFF). "
                   "Para cambiar velocidad, debe modificarse físicamente las bobinas."
        )
```

**Respuesta de Error (501):**
```json
{
  "detail": "Motor con relays no soporta control de velocidad. Solo tiene velocidad fija (ON/OFF). Para cambiar velocidad, debe modificarse físicamente las bobinas del motor."
}
```

---

#### **Endpoint `/belt/start_forward` Adaptado**
```python
@app.post("/belt/start_forward")
async def belt_start_forward(request: BeltSpeedRequest = None):
    # Mensaje adaptado al tipo de motor
    if has_speed_control and speed:
        message = f"Banda iniciada hacia adelante a {speed}%"
    else:
        message = "Banda iniciada hacia adelante (velocidad fija)"
    
    response = {
        "control_type": "pwm" if has_speed_control else "relay"
    }
    
    # Solo incluir velocidad si el motor la soporta
    if has_speed_control and speed:
        response["speed_percent"] = speed
```

---

### **2. Frontend: UI Adaptativa Automática**

#### **Interface Actualizada**
```typescript
interface BeltStatus {
  // ... otros campos ...
  controlType?: 'relay' | 'pwm' | 'l298n';  // ← NUEVO
  hasSpeedControl?: boolean;                 // ← NUEVO
}
```

---

#### **Actualización de Estado desde Backend**
```typescript
useEffect(() => {
  if (!externalStatus) return;
  setBeltStatus(prev => ({
    ...prev,
    controlType: externalStatus.controlType ?? prev.controlType,
    hasSpeedControl: externalStatus.hasSpeedControl ?? prev.hasSpeedControl
  }));
}, [externalStatus]);
```

---

#### **Métrica de Velocidad Adaptativa**
```tsx
<Paper>
  <Typography variant="subtitle2">
    {beltStatus.hasSpeedControl ? 'Velocidad' : 'Estado Motor'}
  </Typography>
  
  {beltStatus.hasSpeedControl ? (
    // Motor PWM - Mostrar velocidad variable
    <>
      <Typography variant="h5">
        {beltStatus.currentSpeed.toFixed(1)} m/s
      </Typography>
      <Typography variant="caption">
        Objetivo: {beltStatus.targetSpeed.toFixed(1)} m/s
      </Typography>
    </>
  ) : (
    // Motor Relay - Mostrar estado ON/OFF
    <>
      <Typography variant="h5">
        {beltStatus.isRunning ? 'ENCENDIDO' : 'APAGADO'}
      </Typography>
      <Typography variant="caption">
        Velocidad: Fija (Relay)
      </Typography>
    </>
  )}
</Paper>
```

**Resultado Visual:**

**Motor PWM:**
```
┌─────────────────────┐
│ ⚡ Velocidad        │
│ 1.5 m/s             │
│ Objetivo: 2.0 m/s   │
└─────────────────────┘
```

**Motor Relay:**
```
┌─────────────────────┐
│ ⚡ Estado Motor     │
│ ENCENDIDO           │
│ Velocidad: Fija     │
│ (Relay)             │
└─────────────────────┘
```

---

#### **Control de Velocidad Adaptativo**
```tsx
<Box>
  <Typography variant="h6">
    {beltStatus.hasSpeedControl 
      ? 'Control de Velocidad Inteligente' 
      : 'Información de Velocidad'
    }
  </Typography>
  
  {beltStatus.hasSpeedControl ? (
    // Motor PWM - Mostrar slider interactivo
    <Slider
      value={beltStatus.targetSpeed}
      onChange={(_, value) => handleBeltAction('set_speed', { speed: value })}
      min={0.1}
      max={2.5}
      step={0.1}
      marks={[...]}
    />
  ) : (
    // Motor Relay - Mostrar alerta informativa
    <Alert severity="info" icon={<Speed />}>
      <Typography variant="body2" fontWeight={600}>
        Motor DC con Control de Relays (Velocidad Fija)
      </Typography>
      <Typography variant="body2">
        Este motor funciona solo con ON/OFF (adelante/atrás/detenido). 
        No tiene control de velocidad variable por software.
      </Typography>
      <Typography variant="caption">
        💡 Para cambiar la velocidad, debe modificarse físicamente 
        las bobinas del motor.
      </Typography>
      <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
        <Chip label="Tipo: RELAY" color="info" />
        <Chip label="Velocidad: Fija" color="default" />
      </Box>
    </Alert>
  )}
</Box>
```

**Resultado Visual Motor Relay:**
```
┌────────────────────────────────────────────────────────┐
│ ℹ️ Motor DC con Control de Relays (Velocidad Fija)    │
│                                                         │
│ Este motor funciona solo con ON/OFF (adelante/atrás/   │
│ detenido). No tiene control de velocidad variable por  │
│ software.                                               │
│                                                         │
│ 💡 Para cambiar la velocidad, debe modificarse         │
│    físicamente las bobinas del motor.                  │
│                                                         │
│ [Tipo: RELAY]  [Velocidad: Fija]                      │
└────────────────────────────────────────────────────────┘
```

**Resultado Visual Motor PWM:**
```
┌────────────────────────────────────────────────────────┐
│ ⚡ Control de Velocidad Inteligente                    │
│                                                         │
│ ├───●─────────────────────────────────┤               │
│ 0.5   1.0    1.5    2.0    2.5 m/s                    │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 Flujo de Detección

```
┌────────────────────────────────────────────────┐
│           INICIO DEL SISTEMA                   │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│  Backend: Detectar tipo de driver              │
│  - RelayMotorDriver → relay (sin velocidad)    │
│  - PWMDriver → pwm (con velocidad)             │
│  - L298NDriver → l298n (con velocidad)         │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│  Endpoint /status devuelve:                    │
│  {                                              │
│    "belt": {                                    │
│      "control_type": "relay",                  │
│      "has_speed_control": false                │
│    }                                            │
│  }                                              │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│  Frontend: Recibe estado del backend           │
│  - Actualiza beltStatus.hasSpeedControl        │
│  - Actualiza beltStatus.controlType            │
└──────────────────┬─────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────┐
│  UI se adapta automáticamente:                 │
│                                                 │
│  SI hasSpeedControl === false:                 │
│  ✅ Ocultar slider de velocidad                │
│  ✅ Mostrar "ENCENDIDO/APAGADO"                │
│  ✅ Mostrar alerta informativa                 │
│  ✅ Mostrar chips "RELAY" y "Velocidad Fija"   │
│                                                 │
│  SI hasSpeedControl === true:                  │
│  ✅ Mostrar slider interactivo                 │
│  ✅ Mostrar velocidad en m/s                   │
│  ✅ Permitir ajuste de velocidad               │
└─────────────────────────────────────────────────┘
```

---

## 📊 Comparación: Antes vs Después

### **Antes** ❌
```
- Slider de velocidad siempre visible
- Usuario intenta cambiar velocidad
- Nada sucede (motor relay no responde)
- Confusión: "¿Por qué no funciona?"
- Sin información sobre el tipo de motor
```

### **Después** ✅
```
- UI detecta automáticamente tipo de motor
- Motor relay: Slider oculto, mensaje informativo
- Motor PWM: Slider visible y funcional
- Usuario entiende las capacidades del sistema
- Información clara sobre velocidad fija
```

---

## 🧪 Testing

### **1. Con Motor Relay (Sin Velocidad)**
```bash
# Backend responde:
{
  "belt": {
    "control_type": "relay",
    "has_speed_control": false,
    "running": true,
    "direction": "forward"
  }
}

# Frontend muestra:
✅ "Estado Motor: ENCENDIDO"
✅ "Velocidad: Fija (Relay)"
✅ Alerta informativa
✅ Sin slider de velocidad
```

### **2. Con Motor PWM (Con Velocidad)**
```bash
# Backend responde:
{
  "belt": {
    "control_type": "pwm",
    "has_speed_control": true,
    "running": true,
    "direction": "forward",
    "speed": 75.0
  }
}

# Frontend muestra:
✅ "Velocidad: 1.5 m/s"
✅ "Objetivo: 2.0 m/s"
✅ Slider interactivo visible
✅ Control de velocidad funcional
```

### **3. Intentar Cambiar Velocidad con Motor Relay**
```bash
# Request:
POST /belt/set_speed
{"speed_percent": 75.0}

# Response (501 Not Implemented):
{
  "detail": "Motor con relays no soporta control de velocidad. Solo tiene velocidad fija (ON/OFF). Para cambiar velocidad, debe modificarse físicamente las bobinas del motor."
}
```

---

## 📁 Archivos Modificados

### **Backend**
1. ✅ `Prototipo_Clasificador/smart_classifier_system.py`
   - Detección automática de tipo de motor
   - Endpoint `/status` con `control_type` y `has_speed_control`
   - Endpoint `/belt/set_speed` con validación
   - Endpoint `/belt/start_forward` adaptado

### **Frontend**
1. ✅ `Interfaz_Usuario/VisiFruit/src/components/production/BeltAdvancedControls.tsx`
   - Interface `BeltStatus` actualizada
   - Métrica de velocidad adaptativa
   - Control de velocidad condicional
   - Alerta informativa para motor relay

---

## 🎨 Screenshots Conceptuales

### **Motor Relay (Tu Caso)**
```
╔══════════════════════════════════════════════════════╗
║  🎚️ Control Avanzado de Banda                       ║
║                                                       ║
║  ┌─────────────────────┐ ┌─────────────────────┐   ║
║  │ ⚡ Estado Motor     │ │ 🌡️ Temperatura      │   ║
║  │ ENCENDIDO           │ │ 35.2°C              │   ║
║  │ Velocidad: Fija     │ │ ████░░░░ 54%        │   ║
║  │ (Relay)             │ │                      │   ║
║  └─────────────────────┘ └─────────────────────┘   ║
║                                                       ║
║  [▶️ ADELANTE]  [⏹️ STOP]  [◀️ ATRÁS]              ║
║                                                       ║
║  ℹ️ Motor DC con Control de Relays (Velocidad Fija) ║
║     Este motor funciona solo con ON/OFF.            ║
║     💡 Para cambiar velocidad, modificar bobinas.   ║
║     [Tipo: RELAY] [Velocidad: Fija]                 ║
╚══════════════════════════════════════════════════════╝
```

### **Motor PWM (Futuro/Otros Usuarios)**
```
╔══════════════════════════════════════════════════════╗
║  🎚️ Control Avanzado de Banda                       ║
║                                                       ║
║  ┌─────────────────────┐ ┌─────────────────────┐   ║
║  │ ⚡ Velocidad        │ │ 🌡️ Temperatura      │   ║
║  │ 1.5 m/s             │ │ 42.8°C              │   ║
║  │ Objetivo: 2.0 m/s   │ │ ████████░ 78%       │   ║
║  └─────────────────────┘ └─────────────────────┘   ║
║                                                       ║
║  [▶️ ADELANTE]  [⏹️ STOP]  [◀️ ATRÁS]              ║
║                                                       ║
║  ⚡ Control de Velocidad Inteligente                ║
║  ├────────●──────────────────┤                      ║
║  0.5    1.0   1.5   2.0  2.5 m/s                   ║
╚══════════════════════════════════════════════════════╝
```

---

## ✅ Beneficios

1. **UI Adaptativa Automática**
   - No requiere configuración manual
   - Se adapta al hardware real del sistema

2. **Experiencia de Usuario Clara**
   - Usuario entiende inmediatamente las capacidades
   - No hay confusión sobre controles que no funcionan

3. **Mensajes Informativos**
   - Explica por qué no hay control de velocidad
   - Indica cómo cambiar velocidad (modificar bobinas)

4. **Escalable**
   - Funciona con motor relay actual
   - Automáticamente habilitará slider si cambias a PWM/L298N

5. **Manejo de Errores Robusto**
   - Backend rechaza intentos de cambiar velocidad en relay
   - Frontend no muestra controles no funcionales

---

## 🚀 Resultado Final

✅ **Backend detecta tipo de motor automáticamente**  
✅ **Frontend adapta UI según capacidades reales**  
✅ **Motor relay: UI simple ON/OFF con mensaje informativo**  
✅ **Motor PWM: UI completa con slider de velocidad**  
✅ **Sin confusión para el usuario**  
✅ **Sistema listo para cualquier tipo de motor**

---

**Fecha**: 2025-01-09  
**Versión**: 2.1 - Motor Relay UI Adaptation  
**Estado**: ✅ Completado y testeado

