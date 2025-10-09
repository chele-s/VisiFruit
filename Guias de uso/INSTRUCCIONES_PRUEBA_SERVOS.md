# 🧪 Instrucciones para Probar Servos con Nuevos Pines

## ⚡ Inicio Rápido

### 1. Reconectar Hardware

**IMPORTANTE**: Antes de encender, reconecta los servos a los NUEVOS pines:

```
Servo Manzanas 🍎:
  Cable Naranja → GPIO 12 (Pin físico 32)
  Cable Rojo → 5V externo
  Cable Marrón → GND común

Servo Peras 🍐:
  Cable Naranja → GPIO 13 (Pin físico 33)
  Cable Rojo → 5V externo
  Cable Marrón → GND común

Servo Limones 🍋:
  Cable Naranja → GPIO 18 (Pin físico 12)
  Cable Rojo → 5V externo
  Cable Marrón → GND común
```

⚠️ **CRÍTICO**: 
- **NO conectar a GPIO 5, 6, 7** (están dañados)
- **GND común** entre Pi y fuente externa es OBLIGATORIO
- Servos necesitan **5-6V externos** (NO usar 5V de la Pi)

### 2. Iniciar Daemon Pigpio

```bash
cd Prototipo_Clasificador
./start_pigpio_daemon.sh start
```

Verifica que esté corriendo:
```bash
./start_pigpio_daemon.sh status
```

Deberías ver:
```
Estado: CORRIENDO
PID: XXXX
✅ Python puede conectarse al daemon
```

### 3. Ejecutar Diagnóstico

```bash
# Diagnóstico completo (prueba todos los pines)
python3 diagnostico_pines_servos.py

# Probar pin específico
python3 diagnostico_pines_servos.py --pin 12

# Modo interactivo (control manual)
python3 diagnostico_pines_servos.py --interactive
```

### 4. Probar con Script de Test

```bash
cd ..
python3 Demos/test_servos_mg995.py
```

## 🔍 Qué Observar

### ✅ Comportamiento CORRECTO:
- Servo se mueve **suavemente** sin temblores
- Mantiene posición **rígidamente** cuando debe
- Regresa a posición inicial **sin oscilar**
- PWM se desactiva y servo se detiene **completamente**

### ❌ Comportamiento INCORRECTO:
- Servo tiembla o vibra
- No mantiene posición
- No se mueve en absoluto
- Se mueve pero de forma errática

## 🐛 Solución de Problemas

### Problema 1: Servos NO se mueven

**Causas posibles**:

1. **Daemon pigpio no está corriendo**
   ```bash
   sudo pigpiod -s 10
   ```

2. **Sin GND común**
   - Conecta GND de la Pi con GND de la fuente externa
   - **SIN ESTO NO FUNCIONARÁ**

3. **Voltaje insuficiente**
   ```bash
   # Medir con multímetro en VCC del servo
   # Debe ser 5.0-6.0V
   ```

4. **Cables mal conectados**
   - Verificar GPIO 12, 13, 18 (NO 5, 6, 7)
   - Cables firmes, no sueltos

5. **Servo dañado**
   - Probar con servo nuevo
   - Verificar que no esté trabado mecánicamente

### Problema 2: Solo un servo funciona

**Solución**:
- Probar cada pin individualmente:
  ```bash
  python3 diagnostico_pines_servos.py --pin 12
  python3 diagnostico_pines_servos.py --pin 13
  python3 diagnostico_pines_servos.py --pin 18
  ```

- Si un pin no funciona, puede estar también dañado
- Usa pines alternativos disponibles: GPIO 16, 17, 20

### Problema 3: Servos tiemblan/oscilan

**Causas**:
1. **Alimentación inestable**
   - Verificar fuente de 5V estable
   - Agregar capacitor 1000μF si es necesario

2. **Interferencia**
   - Cables de señal alejados de cables de potencia
   - Cables cortos (<30cm idealmente)

3. **Daemon con parámetros incorrectos**
   ```bash
   sudo killall pigpiod
   sudo pigpiod -s 10  # -s 10 es CRÍTICO para precisión
   ```

## 📊 Checklist Pre-Prueba

Antes de probar, verifica:

- [ ] Daemon pigpio corriendo (`./start_pigpio_daemon.sh status`)
- [ ] Servos conectados a GPIO 12, 13, 18 (NO 5, 6, 7)
- [ ] Alimentación 5V externa conectada a servos
- [ ] GND común entre Pi y fuente externa
- [ ] Voltaje medido: 5.0-6.0V en VCC de servos
- [ ] `Config_Prototipo.json` actualizado con nuevos pines
- [ ] Servos físicamente en buen estado

## 🎯 Secuencia de Prueba Recomendada

### Paso 1: Verificación Individual
```bash
# Probar cada pin uno por uno
python3 diagnostico_pines_servos.py --pin 12
python3 diagnostico_pines_servos.py --pin 13
python3 diagnostico_pines_servos.py --pin 18
```

### Paso 2: Prueba Completa
```bash
# Todos los servos en secuencia
python3 diagnostico_pines_servos.py
```

### Paso 3: Test del Sistema
```bash
# Script de test completo
cd ..
python3 Demos/test_servos_mg995.py
```

### Paso 4: Sistema Real
```bash
# Si todo funciona, ejecutar sistema completo
cd Prototipo_Clasificador
python3 smart_classifier_system.py
```

## 📝 Registro de Resultados

Anota los resultados de las pruebas:

| Pin  | Servo     | Funciona | Observaciones |
|------|-----------|----------|---------------|
| 12   | Manzanas  | ☐ Sí ☐ No |               |
| 13   | Peras     | ☐ Sí ☐ No |               |
| 18   | Limones   | ☐ Sí ☐ No |               |

## 🔄 Si Pines También Están Dañados

Si GPIO 12, 13 o 18 tampoco funcionan, usa estos **pines alternativos**:

**Opción 1 (GPIO estándar)**:
- GPIO 16 → Servo Manzanas
- GPIO 17 → Servo Peras
- GPIO 20 → Servo Limones

**Opción 2 (otros PWM)**:
- GPIO 24 → Servo Manzanas
- GPIO 25 → Servo Peras
- GPIO 8 → Servo Limones

Para cambiarlos, edita `Config_Prototipo.json`:
```json
{
  "servo_settings": {
    "apple": { "pin_bcm": 16, ... },
    "pear": { "pin_bcm": 17, ... },
    "lemon": { "pin_bcm": 20, ... }
  }
}
```

Y actualiza `utils/gpio_wrapper.py`:
```python
PIGPIO_RESERVED_PINS = {16, 17, 20}
```

## ✅ Confirmación de Éxito

Si todo funciona bien, deberías ver:

```
🧪 Probando: Servo Manzanas 🍎 (GPIO 12 - PWM0)
✅ Pin 12 configurado correctamente

Moviendo servo a diferentes posiciones...
  → 90° - Centro (pulso: 1500μs)
  → 0° - Mínimo (pulso: 1000μs)
  → 180° - Máximo (pulso: 2000μs)
  → 90° - Centro (pulso: 1500μs)
  → 45° - Intermedio (pulso: 1250μs)
  → 135° - Intermedio (pulso: 1750μs)
  → 90° - Centro final (pulso: 1500μs)

✅ Prueba completada
¿El servo se movió correctamente? (s/n): s
✅ Pin 12 FUNCIONAL
```

## 📞 Soporte

Si después de seguir todos los pasos los servos no funcionan:

1. Revisa `CAMBIO_PINES_SERVOS.md` para detalles técnicos
2. Verifica pinout en diagrama (Raspberry Pi 5)
3. Considera reemplazo de hardware dañado
4. Usa multímetro para verificar continuidad de pines

---

**Última actualización**: Enero 2025  
**Pines nuevos**: GPIO 12, 13, 18  
**Pines dañados**: GPIO 5, 6, 7 (NO USAR)

