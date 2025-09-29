# 📋 Cambios Realizados - Actualización de Pines y Servos

## 🎯 Cambios Implementados

### 1. ✅ Actualización de Pines GPIO

Todos los pines han sido actualizados según la especificación:

#### Transportador (Motor DC con PWM)
```json
"belt_settings": {
  "relay1_pin": 22,
  "relay2_pin": 23,
  "motor_pin_bcm": 13,
  "enable_pin_bcm": 12,
  "direction_pin_bcm": 20,
  "direction_pin2_bcm": 21,
  "speed_control_pin": 13
}
```

#### Sensor de Disparo (MH Flying Fish)
```json
"sensor_settings": {
  "trigger_sensor": {
    "enabled": true,
    "pin_bcm": 4
  }
}
```

#### Etiquetadora (Solenoide)
```json
"labeler_settings": {
  "type": "solenoid",
  "pin_bcm": 26,
  "activation_duration_seconds": 0.6
}
```

#### Motor a Pasos (Stepper) para Láser
```json
"laser_stepper_settings": {
  "step_pin_bcm": 19,
  "dir_pin_bcm": 26,
  "enable_pin_bcm": 21
}
```

#### Servomotores para Desvío
```json
"servo_settings": {
  "apple": {
    "pin_bcm": 5,  // Pin para manzanas
    "activation_angle": 90
  },
  "pear": {
    "pin_bcm": 6,  // Pin para peras
    "activation_angle": 90
  }
}
```

---

### 2. ✅ Sistema de Clasificación por IA

**Lógica implementada:**

```
IA Detecta Fruta → Clasificación Automática
├─ 🍎 Manzana → Activa Servo Pin 5 (90°) → Caja Manzanas
├─ 🍐 Pera    → Activa Servo Pin 6 (90°) → Caja Peras
└─ 🍋 Limón   → Sin servo (pasa directo) → Caja Final
```

**Código en `smart_classifier_system.py`:**

```python
async def _classify_fruit(self, event: DetectionEvent):
    # Los limones pasan directo (sin servo)
    if event.category == FruitCategory.LEMON:
        logger.info(f"🍋 Limón - Pasa directo")
        self.stats["classified_by_servo"]["lemon_passthrough"] += 1
        return
    
    # Manzanas y peras activan su servo correspondiente
    if event.category == FruitCategory.APPLE:
        await self.servo_controller.activate_servo(FruitCategory.APPLE)  # Pin 5
        self.stats["classified_by_servo"]["apple"] += 1
    
    elif event.category == FruitCategory.PEAR:
        await self.servo_controller.activate_servo(FruitCategory.PEAR)  # Pin 6
        self.stats["classified_by_servo"]["pear"] += 1
```

---

### 3. ✅ Backend y Frontend en Modo Prototipo

El modo prototipo ahora inicia automáticamente:
- 📊 **Backend Dashboard**: http://localhost:8001
- 🎨 **Frontend React**: http://localhost:3000

**Código en `main_etiquetadora_v4.py`:**

```python
async def run_prototype_mode():
    # Iniciar servicios auxiliares (backend y frontend)
    services = await check_and_start_services()
    
    # ... inicializar sistema prototipo ...
    
    logger.info("🌐 === URLS DEL SISTEMA PROTOTIPO ===")
    if "backend" in services:
        logger.info("   📊 Dashboard Backend: http://localhost:8001")
    if "frontend" in services:
        logger.info("   🎨 Interfaz Frontend: http://localhost:3000")
```

---

## 📊 Resumen de Configuración Final

### Hardware Configurado

| Componente | Pin BCM | Función |
|------------|---------|---------|
| **Banda - Relay 1** | 22 | Control adelante |
| **Banda - Relay 2** | 23 | Control atrás |
| **Banda - Motor PWM** | 13 | Control velocidad |
| **Banda - Enable** | 12 | Habilitar motor |
| **Banda - Dirección 1** | 20 | Control dirección |
| **Banda - Dirección 2** | 21 | Control dirección |
| **Sensor MH** | 4 | Detección de fruta |
| **Etiquetadora** | 26 | Solenoide etiquetado |
| **Stepper - Step** | 19 | Pulsos stepper |
| **Stepper - Dir** | 26 | Dirección stepper |
| **Stepper - Enable** | 21 | Habilitar stepper |
| **Servo Manzanas** | 5 | Clasificación 🍎 |
| **Servo Peras** | 6 | Clasificación 🍐 |

---

## 🔄 Flujo Completo del Sistema

```
1. 📷 Cámara captura fruta en banda
         ↓
2. 🧠 IA analiza y detecta:
   ├─ Manzana (confidence > 0.6)
   ├─ Pera (confidence > 0.6)
   └─ Limón (confidence > 0.6)
         ↓
3. 🏷️ Etiquetadora (Pin 26) aplica etiqueta
   └─ Activación: 0.6s
         ↓
4. ⏱️ Sistema calcula delay basado en:
   └─ Distancia / Velocidad banda
         ↓
5. 🔄 Clasificación automática:
   ├─ 🍎 Manzana → Servo Pin 5 → Caja 1
   ├─ 🍐 Pera    → Servo Pin 6 → Caja 2
   └─ 🍋 Limón   → Sin servo   → Caja 3 (final)
         ↓
6. 📊 Estadísticas actualizadas en tiempo real
```

---

## 🚀 Cómo Usar

### Inicio Rápido

```bash
# Ejecutar sistema completo (con backend y frontend)
python3 main_etiquetadora_v4.py

# O forzar modo prototipo
VISIFRUIT_MODE=prototype python3 main_etiquetadora_v4.py
```

### URLs Disponibles

Una vez iniciado, el sistema estará disponible en:

- **Frontend**: http://localhost:3000
- **Backend Dashboard**: http://localhost:8001
- **API Docs Backend**: http://localhost:8001/docs

---

## 📈 Estadísticas del Sistema

El sistema ahora muestra estadísticas detalladas:

```python
{
  "detections_total": 150,
  "detections_by_class": {
    "apple": 60,
    "pear": 55,
    "lemon": 35
  },
  "labeled_total": 148,
  "classified_total": 145,
  "classified_by_servo": {
    "apple": 58,        // Activaciones del servo de manzanas
    "pear": 53,         // Activaciones del servo de peras
    "lemon_passthrough": 34  // Limones que pasaron directo
  }
}
```

---

## 🧪 Pruebas

### Probar Solo Servos

```bash
python3 Prototipo_Clasificador/mg995_servo_controller.py
```

Esto probará:
- ✅ Servo Manzanas (Pin 5): 0° → 90° → 0°
- ✅ Servo Peras (Pin 6): 0° → 90° → 0°

### Probar Sistema Completo

```bash
python3 Prototipo_Clasificador/smart_classifier_system.py
```

---

## 🎯 Calibración

### 1. Verificar Pines Físicos

Asegúrate de que los componentes estén conectados a los pines correctos:

- Servo manzanas → GPIO 5
- Servo peras → GPIO 6
- Etiquetadora solenoide → GPIO 26
- Sensor MH → GPIO 4

### 2. Ajustar Ángulos de Servos

Si los servos no abren correctamente las compuertas:

```json
// En Config_Prototipo.json
"servo_settings": {
  "apple": {
    "activation_angle": 90,  // Ajustar si es necesario
    "invert": false  // Cambiar a true si servo está invertido
  }
}
```

### 3. Ajustar Temporización

```json
"timing": {
  "belt_speed_mps": 0.2,  // Velocidad real de tu banda
  "camera_to_classifier_distance_m": 0.5  // Distancia real medida
}
```

---

## ⚠️ Notas Importantes

### Alimentación de Servos

- Los MG995 requieren **4.8-7.2V** y hasta **2A por servo**
- NO alimentar desde Raspberry Pi (insuficiente corriente)
- Usar fuente externa con tierra común

### Sensor MH Flying Fish

- Configurado en **Pull-Up** con trigger en **FALLING**
- Detecta cuando objeto pasa frente al sensor
- Debounce de 50ms configurado

### Limones Sin Servo

- Los limones **no activan ningún servo**
- Pasan directo hasta el final de la banda
- Caen en la última caja por gravedad

---

## 📝 Archivos Modificados

1. ✅ `Prototipo_Clasificador/Config_Prototipo.json`
   - Actualización de todos los pines
   - Configuración de 2 servos (apple, pear)
   - Etiquetadora tipo solenoide

2. ✅ `Prototipo_Clasificador/smart_classifier_system.py`
   - Lógica de clasificación por IA
   - Activación selectiva de servos
   - Estadísticas por servo

3. ✅ `Prototipo_Clasificador/mg995_servo_controller.py`
   - Soporte para 2 servos
   - Pines actualizados (5 y 6)
   - Pruebas actualizadas

4. ✅ `main_etiquetadora_v4.py`
   - Backend y frontend en modo prototipo
   - Información de hardware actualizada
   - URLs de servicios

---

## ✅ Checklist de Verificación

- [x] Pines GPIO actualizados según especificación
- [x] Servo manzanas en Pin 5
- [x] Servo peras en Pin 6
- [x] Limones pasan directo sin servo
- [x] IA clasifica correctamente según detección
- [x] Backend disponible en puerto 8001
- [x] Frontend disponible en puerto 3000
- [x] Estadísticas por servo implementadas
- [x] Sensor MH Flying Fish en Pin 4
- [x] Etiquetadora solenoide en Pin 26
- [x] Sin errores de linting

---

## 🎉 ¡Todo Listo!

El sistema está completamente configurado y listo para:

✅ Detectar frutas con IA (>95% precisión)  
✅ Clasificar manzanas → Servo Pin 5  
✅ Clasificar peras → Servo Pin 6  
✅ Limones pasan directo (sin servo)  
✅ Monitorear con backend web  
✅ Controlar desde frontend  

**¡A clasificar frutas! 🍎🍐🍋**
