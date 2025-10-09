# 🔄 Cambio de Pines de Servos MG995

## ⚠️ Problema Detectado

Los pines GPIO **5, 6, 7** se dañaron cuando se quemó la bobina del motor DC.

**Síntomas**:
- Servos no se mueven en absoluto
- Antes funcionaban de forma errática
- Daño ocurrió junto con falla del motor DC

## ✅ Solución: Nuevos Pines Seguros

Se han cambiado los servos a **pines PWM hardware disponibles y seguros**:

### Mapeo de Pines ANTERIOR (DAÑADOS ❌)
```
GPIO 5  → Servo Manzanas 🍎  [DAÑADO]
GPIO 6  → Servo Peras 🍐     [DAÑADO]
GPIO 7  → Servo Limones 🍋   [DAÑADO]
```

### Mapeo de Pines NUEVO (SEGUROS ✅)
```
GPIO 12 → Servo Manzanas 🍎  [PWM0 - Hardware PWM]
GPIO 13 → Servo Peras 🍐     [PWM1 - Hardware PWM]
GPIO 18 → Servo Limones 🍋   [PWM0 alt - Hardware PWM]
```

## 🔌 Conexiones Físicas

### Reconectar los servos:

**Servo de Manzanas (MG995)**
- Cable Naranja (señal) → GPIO 12
- Cable Rojo (VCC) → 5V externo
- Cable Marrón (GND) → GND común

**Servo de Peras (MG995)**
- Cable Naranja (señal) → GPIO 13
- Cable Rojo (VCC) → 5V externo
- Cable Marrón (GND) → GND común

**Servo de Limones (MG995)**
- Cable Naranja (señal) → GPIO 18
- Cable Rojo (VCC) → 5V externo
- Cable Marrón (GND) → GND común

⚠️ **IMPORTANTE**: 
- Asegúrate de tener un **GND común** entre Raspberry Pi y la fuente de 5V de los servos
- Los servos MG995 necesitan **5-6V y hasta 1.5A** por servo
- NO alimentes los servos desde los 5V de la Raspberry (insuficiente corriente)

## 📋 Resumen de Pines en Uso

### Pines OCUPADOS (NO usar):
- **GPIO 4**: Sensor MH Flying Fish
- **GPIO 19**: Stepper STEP
- **GPIO 21**: Stepper ENABLE
- **GPIO 22, 23, 27**: Banda transportadora (relay motor)
- **GPIO 26**: Stepper DIR
- **GPIO 5, 6, 7**: ⚠️ DAÑADOS - NO USAR

### Pines SERVOS (actualizados):
- **GPIO 12**: Servo Manzanas ✅
- **GPIO 13**: Servo Peras ✅
- **GPIO 18**: Servo Limones ✅

### Pines DISPONIBLES (reserva):
- GPIO 16, 17, 20, 24, 25 (disponibles para futuro uso)

## 🔧 Archivos Actualizados

Se han actualizado automáticamente:

1. **Config_Prototipo.json**
   - `servo_settings.apple.pin_bcm`: 5 → **12**
   - `servo_settings.pear.pin_bcm`: 6 → **13**
   - `servo_settings.lemon.pin_bcm`: 7 → **18**

2. **utils/gpio_wrapper.py**
   - `PIGPIO_RESERVED_PINS`: {5, 6, 7} → **{12, 13, 18}**

3. **README_SERVOS_PIGPIO.md** (actualizado)

## 🧪 Verificación

### 1. Verificar daemon pigpio
```bash
cd Prototipo_Clasificador
./start_pigpio_daemon.sh status
```

### 2. Probar servos individualmente
```bash
# Usar script de diagnóstico
python3 diagnostico_pines_servos.py

# O probar con el test normal
python3 ../Demos/test_servos_mg995.py
```

### 3. Verificar conexiones
- [ ] Cables de señal conectados a GPIO 12, 13, 18
- [ ] Alimentación 5V externa conectada
- [ ] GND común entre Pi y fuente externa
- [ ] Servos reciben 5-6V estables

## 🐛 Diagnóstico de Problemas

### Si los servos aún no se mueven:

1. **Verificar alimentación**:
   ```bash
   # Medir voltaje con multímetro
   # Debe ser 5.0-6.0V en VCC del servo
   ```

2. **Verificar tierra común**:
   ```bash
   # Conectar GND de la Pi con GND de la fuente externa
   # Sin esto, los servos NO funcionarán
   ```

3. **Probar pin individual**:
   ```python
   # Usar diagnostico_pines_servos.py para probar un pin a la vez
   python3 diagnostico_pines_servos.py --pin 12
   ```

4. **Verificar servo físicamente**:
   - Cambiar servo por uno nuevo
   - Probar con servo conocido que funcione
   - Verificar que el servo no esté trabado mecánicamente

### Si el daemon pigpio no conecta:

```bash
# Reiniciar daemon
sudo killall pigpiod
sudo pigpiod -s 10

# Verificar
./start_pigpio_daemon.sh status
```

## ✅ Ventajas de los Nuevos Pines

1. **PWM Hardware**: GPIO 12, 13, 18 son pines PWM hardware
   - Mejor precisión con pigpio
   - Menos jitter
   - Más estables

2. **Separados de zona dañada**: 
   - Alejados de GPIO 5, 6, 7 (dañados)
   - No comparten circuitos internos

3. **Compatible con pigpio**:
   - Pigpio usa excelente estos pines PWM
   - Sin conflictos con otros periféricos

## 📊 Pinout Raspberry Pi 5 (Referencia)

```
     3.3V  [ 1] [ 2]  5V
    GPIO2  [ 3] [ 4]  5V
    GPIO3  [ 5] [ 6]  GND
    GPIO4  [ 7] [ 8]  GPIO14
      GND  [ 9] [10]  GPIO15
   GPIO17  [11] [12]  GPIO18  ← SERVO LIMONES ✅
   GPIO27  [13] [14]  GND
   GPIO22  [15] [16]  GPIO23
     3.3V  [17] [18]  GPIO24
   GPIO10  [19] [20]  GND
    GPIO9  [21] [22]  GPIO25
   GPIO11  [23] [24]  GPIO8
      GND  [25] [26]  GPIO7   ← DAÑADO ❌
    GPIO0  [27] [28]  GPIO1
    GPIO5  [29] [30]  GND     ← DAÑADO ❌
    GPIO6  [31] [32]  GPIO12  ← SERVO MANZANAS ✅
   GPIO13  [33] [34]  GND     ← SERVO PERAS ✅
   GPIO19  [35] [36]  GPIO16
   GPIO26  [37] [38]  GPIO20
      GND  [39] [40]  GPIO21
```

## 🚀 Próximos Pasos

1. **Reconectar físicamente**:
   - Mover cables de servos a GPIO 12, 13, 18
   - Verificar GND común
   - Verificar alimentación 5V externa

2. **Probar**:
   ```bash
   cd Prototipo_Clasificador
   python3 diagnostico_pines_servos.py
   ```

3. **Si funciona**:
   - Ejecutar sistema completo
   - Calibrar ángulos si es necesario

4. **Si NO funciona**:
   - Revisar conexiones físicas
   - Probar con servo nuevo
   - Verificar voltaje de alimentación

---

**Fecha del cambio**: Enero 2025  
**Razón**: Daño de pines GPIO 5, 6, 7 tras falla de motor DC  
**Nuevos pines**: GPIO 12, 13, 18 (PWM hardware)

