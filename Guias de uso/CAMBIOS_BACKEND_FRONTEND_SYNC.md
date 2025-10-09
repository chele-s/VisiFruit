# 🚀 Mejoras en Sincronización Backend ↔ Frontend

## 📋 Resumen de Cambios

Se ha mejorado completamente la sincronización de datos entre el backend (Python) y el frontend (React/TypeScript) para resolver problemas de:

1. ✅ Motor DC con 2 relays arrancando automáticamente
2. ✅ Sensor Flying Fish MH no mostrando activaciones en frontend
3. ✅ Datos históricos no mostrándose correctamente
4. ✅ Detección correcta de tipo de motor (relay vs PWM)

---

## 🔧 Cambios en Backend Principal (smart_classifier_system.py)

### 1. Detección Mejorada de Tipo de Motor

**ANTES:**
```python
# No distinguía correctamente entre relay y PWM
belt_control_type = "relay"
```

**AHORA:**
```python
# Detecta correctamente SimpleBeltController (tu motor de 2 relays)
belt_class_name = self.belt.__class__.__name__

if 'SimpleBeltController' in belt_class_name:
    belt_control_type = "relay"  # ✅ Motor DC con 2 relays (ON/OFF)
    has_speed_control = False
    logger.debug("🔌 Motor DC con 2 relays detectado (ON/OFF, sin velocidad variable)")
```

### 2. Endpoint /status Mejorado

**Datos nuevos enviados:**
```python
{
    "belt": {
        "running": True/False,           # Estado real del motor
        "isRunning": True/False,         # Alias para compatibilidad
        "direction": "forward/stopped",  # Dirección actual
        "controlType": "relay",          # 🔑 IMPORTANTE: tipo de motor
        "hasSpeedControl": False,        # 🔑 NO tiene velocidad variable
        "currentSpeed": 1.0 o 0.0,       # Para relay: 1.0=ON, 0.0=OFF
        "timestamp": 1234567890.123      # Timestamp para sincronización
    },
    "stepper": {
        "isActive": True/False,                    # Si está activo AHORA
        "currentPower": 80,                        # Potencia aplicada (0-100)
        "sensorTriggers": 45,                      # ✅ Contador de activaciones por sensor
        "manualActivations": 12,                   # ✅ Contador de activaciones manuales
        "lastActivation": "2025-10-09T...",       # ✅ Timestamp de última activación
        "lastActivationTimestamp": 1234567890.123, # Unix timestamp
        "activationDuration": 0.6,                 # Duración configurada
        "currentStepRate": 1500,                   # Pasos/segundo cuando activo
        "timestamp": 1234567890.123
    },
    "timestamp": 1234567890.123,  # Timestamp global
    "system_running": True,       # Si el sistema está corriendo
    "system_state": "running"     # Estado del sistema
}
```

### 3. Endpoint /belt/start_forward Mejorado

**Para tu motor relay de 2 contactos:**
```python
# ✅ NO intenta establecer velocidad
if 'SimpleBeltController' in belt_class_name:
    await self.belt.start()  # Solo enciende el relay
    logger.info("✅ Banda relay iniciada (relay adelante = HIGH)")
    
response = {
    "message": "Banda RELAY iniciada (ON - velocidad fija física)",
    "control_type": "relay",
    "has_speed_control": False  # ✅ Indica que NO tiene control de velocidad
}
```

---

## 🌐 Cambios en Backend Auxiliar (main.py)

### 1. Proxy Mejorado al Sistema Principal

```python
# Conecta al puerto 8000 (sistema principal)
async with session.get('http://localhost:8000/status') as resp:
    main_system_status = await resp.json()
    main_connected = True
```

### 2. Persistencia de Datos Históricos

**Nuevo sistema de caché histórico:**
```python
# Guarda histórico de banda
self._belt_history.append({
    "timestamp": current_time,
    "running": belt_running,
    "direction": belt_direction
})

# Guarda histórico de stepper
self._stepper_history.append({
    "timestamp": current_time,
    "isActive": stepper_is_active,
    "sensorTriggers": sensor_triggers,  # ✅ Contador de sensor
    "manualActivations": manual_acts     # ✅ Contador manual
})
```

### 3. Datos Históricos Calculados

**Nuevas métricas disponibles:**
```python
{
    "historical": {
        "belt_uptime_percent": 85.3,        # % del tiempo que ha estado encendida
        "stepper_activation_rate": 12.4,    # % del tiempo activo
        "data_points": {
            "belt": 500,      # Número de muestras guardadas
            "stepper": 500    # Número de muestras guardadas
        }
    }
}
```

---

## 🎨 Cambios en Frontend (BeltAdvancedControls.tsx)

### 1. Sincronización Mejorada con externalStatus

**ANTES:**
```typescript
// Sincronización básica
setBeltStatus(prev => ({
    ...prev,
    isRunning: externalStatus.isRunning
}))
```

**AHORA:**
```typescript
// Sincronización completa con logs de depuración
console.debug('Actualizando desde externalStatus:', {
    running: externalStatus.isRunning,
    controlType: externalStatus.controlType,  // ✅ Detecta tipo de motor
    hasSpeedControl: externalStatus.hasSpeedControl,
    stepperActive: externalStatus.stepperStatus?.isActive,
    sensorTriggers: externalStatus.stepperStatus?.sensorTriggers  // ✅ Muestra contador
})

setBeltStatus(prev => ({
    ...prev,
    isRunning: externalStatus.isRunning ?? externalStatus.running,
    controlType: externalStatus.controlType ?? 'relay',  // ✅ Tipo de motor
    hasSpeedControl: externalStatus.hasSpeedControl ?? false,
    stepperStatus: {
        sensorTriggers: externalStatus.stepperStatus?.sensorTriggers,  // ✅ Sincroniza contador
        manualActivations: externalStatus.stepperStatus?.manualActivations,
        lastActivation: new Date(externalStatus.stepperStatus?.lastActivation)
    }
}))
```

### 2. Visualización Adaptativa según Tipo de Motor

**Para motor RELAY (tu caso):**
```tsx
{beltStatus.hasSpeedControl ? (
    // Motor PWM - muestra velocidad
    <Typography variant="h5">{beltStatus.currentSpeed.toFixed(1)} m/s</Typography>
) : (
    // Motor RELAY - muestra ON/OFF
    <Typography variant="h5">
        {beltStatus.isRunning ? 'ENCENDIDO ✅' : 'APAGADO ⭕'}
    </Typography>
)}
```

---

## 🎯 Problemas Resueltos

### ✅ 1. Motor arrancando automáticamente

**Problema:** Al iniciar el sistema, el motor se activaba solo.

**Solución:**
- Detección correcta de `SimpleBeltController`
- No envía comandos de velocidad innecesarios
- Respeta el estado inicial configurado

### ✅ 2. Sensor Flying Fish no mostrando activaciones

**Problema:** El sensor activaba el stepper físicamente pero no se veía en UI.

**Solución:**
- Campo `sensorTriggers` se sincroniza en tiempo real
- Campo `manualActivations` separado para distinguir origen
- Timestamp `lastActivation` muestra cuándo fue la última vez
- Estado `isActive` se detecta correctamente (activo si última activación < 1.5s)

### ✅ 3. Datos históricos vacíos

**Problema:** La UI mostraba que nunca se había encendido el sistema.

**Solución:**
- Backend guarda histórico en `_belt_history` y `_stepper_history`
- Calcula métricas: `belt_uptime_percent` y `stepper_activation_rate`
- Persiste datos entre llamadas a `/status`
- Frontend recibe y muestra correctamente `totalRuntime`

---

## 📊 Flujo de Datos Mejorado

```
┌─────────────────────────────────────────────────┐
│  HARDWARE (Raspberry Pi 5)                      │
│  - Motor DC (2 relays: pins 22, 23)            │
│  - NEMA 17 + DRV8825                            │
│  - Sensor Flying Fish MH (pin 4)               │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  BACKEND PRINCIPAL (Puerto 8000)                │
│  smart_classifier_system.py                     │
│                                                  │
│  ✅ Detecta SimpleBeltController → relay        │
│  ✅ Incrementa sensorTriggers al activar       │
│  ✅ Guarda timestamp de última activación      │
│  ✅ No envía comandos de velocidad a relay     │
└────────────────┬────────────────────────────────┘
                 │ GET /status cada 2s
                 ▼
┌─────────────────────────────────────────────────┐
│  BACKEND AUXILIAR (Puerto 8001)                 │
│  main.py                                        │
│                                                  │
│  ✅ Hace proxy a puerto 8000                   │
│  ✅ Guarda histórico en _belt_history          │
│  ✅ Guarda histórico en _stepper_history       │
│  ✅ Calcula métricas agregadas                 │
└────────────────┬────────────────────────────────┘
                 │ GET /api/status/ultra cada 2s
                 ▼
┌─────────────────────────────────────────────────┐
│  FRONTEND (Puerto 3000)                         │
│  BeltAdvancedControls.tsx                       │
│                                                  │
│  ✅ Detecta hasSpeedControl = false            │
│  ✅ Muestra ON/OFF en vez de velocidad         │
│  ✅ Muestra sensorTriggers en tiempo real      │
│  ✅ Muestra datos históricos correctos         │
└─────────────────────────────────────────────────┘
```

---

## 🧪 Cómo Probar las Mejoras

### 1. Verificar detección de motor relay

```bash
# Iniciar sistema
python main_etiquetadora_v4.py

# Buscar en logs:
# "🔌 Motor DC con 2 relays detectado (ON/OFF, sin velocidad variable)"
```

### 2. Verificar contador de sensor

```bash
# En el frontend, observar panel de stepper
# Debe mostrar:
# - "Activaciones por sensor: X"
# - "Activaciones manuales: Y"
# - "Última activación: hace 2s" (actualizado en tiempo real)
```

### 3. Verificar datos históricos

```bash
# Dejar el sistema corriendo 5 minutos
# En el frontend, debe mostrar:
# - "Tiempo total encendido: 5m 32s"
# - "% tiempo activo: 78.5%"
```

---

## 📝 Configuración Recomendada

**Para tu motor DC de 2 relays, asegúrate de tener en `Config_Prototipo.json`:**

```json
{
    "belt_settings": {
        "use_advanced_controller": false,
        "control_type": "relay_motor",
        "relay1_pin": 22,
        "relay2_pin": 23,
        "enable_pin": 27,
        "active_state_on": "LOW",
        "default_speed_percent": 100
    }
}
```

---

## 🐛 Debugging

Si algo no funciona, revisa los logs de consola del navegador:

```javascript
// Deberías ver:
"BeltAdvancedControls: Actualizando desde externalStatus: {
    running: true,
    controlType: 'relay',
    hasSpeedControl: false,
    stepperActive: true,
    sensorTriggers: 45
}"
```

---

## ✨ Resumen de Mejoras

| Componente | Mejora | Estado |
|------------|--------|--------|
| Backend Principal | Detección correcta de tipo de motor | ✅ |
| Backend Principal | No envía velocidad a motor relay | ✅ |
| Backend Principal | Contador de activaciones por sensor | ✅ |
| Backend Principal | Timestamp de última activación | ✅ |
| Backend Auxiliar | Proxy mejorado a puerto 8000 | ✅ |
| Backend Auxiliar | Persistencia de datos históricos | ✅ |
| Frontend | Sincronización en tiempo real | ✅ |
| Frontend | Visualización adaptativa relay/PWM | ✅ |
| Frontend | Muestra contadores de sensor | ✅ |
| Frontend | Muestra datos históricos | ✅ |

---

**Fecha de actualización:** 9 de Octubre, 2025  
**Versión:** 1.0.0  
**Autores:** Gabriel Calderón, Elias Bautista, Cristian Hernandez

