# 🤖 Sistema de 3 Servos MG995 - Actualización VisiFruit Prototipo

## 📋 Resumen de Cambios

Se ha actualizado el sistema de servos para soportar **3 servomotores MG995** con ángulos específicos para clasificación de frutas.

---

## 🔧 Configuración de Servos

### **Servo 1 - Clasificador de Manzanas (GPIO 12)**
- **Pin BCM**: 12 (Hardware PWM0)
- **Ángulo de Reposo**: 180° (posición normal sin detector)
- **Ángulo de Actuación**: 90° (cuando detecta frutas)
- **Categoría**: `apple`

### **Servo 2 - Clasificador de Peras (GPIO 13)**
- **Pin BCM**: 13 (Hardware PWM1)
- **Ángulo de Reposo**: 150° (cuando no detecta nada)
- **Ángulo de Actuación**: 100° (cuando detecta frutas)
- **Categoría**: `pear`

### **Servo 3 - Clasificador de Limones (GPIO 20)**
- **Pin BCM**: 20 (Software PWM)
- **Ángulo de Reposo**: 90° (posición de reposo)
- **Ángulo de Actuación**: 10° (cuando detecta frutas)
- **Categoría**: `lemon`

---

## 📂 Archivos Modificados

### 1. `test_servo_system.py` ✅
**Mejoras implementadas:**
- ✅ Soporte completo para 3 servos (GPIO 12, 13, 20)
- ✅ Configuración de ángulos específicos por servo
- ✅ Modo DEMO: Solo usa ángulos de reposo
- ✅ Modo interactivo mejorado con opciones para:
  - Mover servos individualmente
  - Mover todos a posición de REPOSO
  - Mover todos a posición de ACTUACIÓN
  - Ver estado detallado con ángulos configurados

### 2. `Config_Prototipo.json` ✅
**Actualizado con:**
```json
"servo_settings": {
  "apple": {
    "pin_bcm": 12,
    "default_angle": 180,      // Reposo
    "activation_angle": 90,    // Actuación
    ...
  },
  "pear": {
    "pin_bcm": 13,
    "default_angle": 150,      // Reposo
    "activation_angle": 100,   // Actuación
    ...
  },
  "lemon": {
    "pin_bcm": 20,
    "default_angle": 90,       // Reposo
    "activation_angle": 10,    // Actuación
    ...
  }
}
```

### 3. `mg995_servo_controller.py` ✅
**Ya compatible con:**
- Modo `"activation_mode": "absolute"` → usa `activation_angle` directamente
- Modo `"activation_mode": "relative"` → calcula desde `activation_offset_deg`
- Soporte completo para los 3 servos

---

## 🎮 Modos de Operación

### 🧪 **MODO DEMO** (`test_servo_system.py`)
**Propósito**: Pruebas y calibración sin riesgo

**Comportamiento**:
- ✅ Solo utiliza ángulos de **REPOSO**
- ✅ Prueba movimientos seguros alrededor de la posición de reposo
- ✅ No activa los servos a posición de actuación automáticamente
- ✅ Ideal para verificar conexiones y funcionamiento mecánico

**Uso**:
```bash
cd Prototipo_Clasificador
python test_servo_system.py
```

**Opciones del menú**:
1. Ejecutar todas las pruebas automáticas
2. Modo interactivo (control manual)
3. Salir

### 🏭 **MODO PRODUCCIÓN** (`main_etiquetadora_v4.py`)
**Propósito**: Operación real con detección de IA

**Comportamiento**:
- ✅ Los servos inician en posición de **REPOSO**
- ✅ Cuando la IA detecta una fruta, el servo correspondiente se mueve a posición de **ACTUACIÓN**
- ✅ El servo mantiene la posición durante `hold_duration_s` (1.5s)
- ✅ Luego regresa suavemente a posición de **REPOSO**

**Flujo de Operación**:
1. Sistema en reposo → Servos en ángulos de reposo (180°, 150°, 90°)
2. Sensor detecta objeto → Cámara captura frame
3. IA detecta "apple" → Servo 1 actúa (180° → 90°)
4. Mantiene posición 1.5s → Fruta cae en contenedor
5. Regresa a reposo → Servo 1 vuelve a 180°

---

## 🚀 Guía de Uso Rápida

### **Paso 1: Probar Servos (DEMO)**
```bash
cd /home/pi/VisiFruit/Prototipo_Clasificador
python test_servo_system.py
```

**Selecciona opción 1** para pruebas automáticas o **opción 2** para control manual.

### **Paso 2: Verificar Conexiones**
En el modo interactivo:
- Opción 6: Mover todos a REPOSO → Verifica posiciones normales
- Opción 1-3: Mover servos individuales → Prueba cada uno
- Opción 8: Ver estado → Confirma ángulos actuales

### **Paso 3: Calibración Fina**
Si los ángulos necesitan ajuste:
1. Edita `Config_Prototipo.json`
2. Modifica `default_angle` (reposo) o `activation_angle` (actuación)
3. Guarda y prueba nuevamente

### **Paso 4: Ejecutar Sistema Real**
```bash
cd /home/pi/VisiFruit
python main_etiquetadora_v4.py
```

---

## ⚙️ Configuración en `Config_Prototipo.json`

### Parámetros Importantes

| Parámetro | Descripción | Valores |
|-----------|-------------|---------|
| `pin_bcm` | Pin GPIO BCM | 12, 13, 20 |
| `default_angle` | Ángulo de reposo | 0-180° |
| `activation_angle` | Ángulo de actuación | 0-180° |
| `activation_duration_s` | Duración total del ciclo | 2.0s |
| `hold_duration_s` | Tiempo en posición actuada | 1.5s |
| `return_smoothly` | Retorno suave a reposo | true/false |
| `min_pulse_us` | Pulso mínimo PWM | 1000µs |
| `max_pulse_us` | Pulso máximo PWM | 2000µs |

### Ejemplo de Ajuste Manual
Para cambiar el ángulo de actuación del servo de manzanas:
```json
"apple": {
  "pin_bcm": 12,
  "default_angle": 180,        // ← Posición sin fruta
  "activation_angle": 85,      // ← Cambiar aquí (era 90°)
  ...
}
```

---

## 🔌 Conexiones Hardware

```
Raspberry Pi 5          MG995 Servos
GPIO 12 (PWM0)    ───→  Servo 1 (Manzanas)    [Cable Naranja/Amarillo]
GPIO 13 (PWM1)    ───→  Servo 2 (Peras)       [Cable Naranja/Amarillo]
GPIO 20           ───→  Servo 3 (Limones)     [Cable Naranja/Amarillo]

5V                ───→  Cable Rojo (VCC) de los 3 servos
GND               ───→  Cable Marrón/Negro (GND) de los 3 servos
```

### ⚠️ Consideraciones Eléctricas
- **Alimentación**: Usa fuente externa 5V-6V para los 3 servos (mínimo 3A)
- **No alimentes** los servos directamente desde el pin 5V de la Pi
- **GPIO 12 y 13**: Hardware PWM (mejor rendimiento)
- **GPIO 20**: Software PWM (funcional, puede tener ligero jitter)

---

## 🐛 Solución de Problemas

### **Servo no se mueve**
1. Verifica conexiones (señal, VCC, GND)
2. Confirma que el pin está configurado correctamente
3. Revisa logs: `python test_servo_system.py` y observa errores

### **Servo tiembla o vibra**
1. Ajusta `min_pulse_us` y `max_pulse_us` en Config_Prototipo.json
2. Típicos MG995: 1000-2000µs (prueba 500-2500µs si es necesario)
3. Asegura alimentación estable (fuente externa, no desde Pi)

### **Ángulos incorrectos**
1. Usa modo interactivo para probar ángulos manualmente
2. Ajusta `default_angle` o `activation_angle` según comportamiento real
3. Si está invertido, cambia `"invert": true` en la configuración

### **GPIO 20 no funciona**
- GPIO 20 usa Software PWM (lgpio)
- Verifica que no esté ocupado por otro dispositivo
- Si persiste, considera usar GPIO 18 (también tiene hardware PWM)

---

## 📊 Verificación del Sistema

### Comando de Estado Rápido
```python
# En modo interactivo, opción 8
# Muestra:
# - Pin BCM de cada servo
# - Ángulo actual
# - Ángulos configurados (reposo/actuación)
# - Estado de Hardware PWM
```

### Indicadores de Éxito ✅
- ✅ Los 3 servos inicializan sin errores
- ✅ Hardware PWM activo en GPIO 12 y 13
- ✅ Servos responden a comandos en modo interactivo
- ✅ Movimiento suave entre posiciones

---

## 📝 Notas Técnicas

### **Hardware PWM vs Software PWM**
- **GPIO 12, 13**: Hardware PWM nativo (lgpio tx_pwm) - Sin jitter, ultra preciso
- **GPIO 20**: Software PWM (gpiozero) - Funcional, puede tener ligero jitter bajo carga

### **Timing del Sistema**
```
Detección → Actuación → Hold → Retorno → Reposo
   0ms        200ms      1.5s    500ms     ∞
```

### **Flujo en Producción**
```python
# En main_etiquetadora_v4.py, cuando detecta "apple":
servo_controller.activate_servo(FruitCategory.APPLE)
# Automáticamente:
# 1. Mueve de 180° → 90° (actuación)
# 2. Mantiene 1.5s (hold)
# 3. Regresa 90° → 180° (reposo)
```

---

## 🎯 Próximos Pasos

1. **Prueba los servos en modo DEMO**
   - Ejecuta `test_servo_system.py`
   - Verifica que los 3 servos funcionan correctamente
   
2. **Ajusta ángulos si es necesario**
   - Usa modo interactivo para encontrar ángulos óptimos
   - Actualiza `Config_Prototipo.json`

3. **Ejecuta el sistema completo**
   - `main_etiquetadora_v4.py` usará los ángulos de actuación
   - Verifica que la clasificación funciona correctamente

4. **Optimización**
   - Ajusta `hold_duration_s` según tiempo de caída de fruta
   - Modifica `return_smoothly` si necesitas retorno más rápido

---

## 📚 Referencias

- **Especificaciones MG995**: Torque 9.4-11 kg·cm, Velocidad 0.2s/60°
- **Raspberry Pi 5 PWM**: GPIO 12, 13 (Hardware), GPIO 18, 19 (Hardware)
- **Controlador usado**: `rpi5_servo_controller.py` (RPi5ServoController)

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs del sistema
2. Ejecuta modo DEMO para aislar el problema
3. Verifica conexiones físicas y alimentación
4. Consulta este README para soluciones comunes

**¡Sistema actualizado y listo para operar con 3 servos! 🚀**
