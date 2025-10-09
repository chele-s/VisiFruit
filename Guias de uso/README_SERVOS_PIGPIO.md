# 🎯 Control de Servos MG995 con Pigpio - VisiFruit

## 📋 Resumen

Sistema de control ultra-preciso para servomotores MG995 usando **pigpio daemon** exclusivamente. Esta solución resuelve los problemas de temblores, movimientos erráticos y conflictos entre lgpio y pigpio.

## ⚡ Características

- ✅ PWM ultra-preciso con pigpio (hardware-timed, sin jitter)
- ✅ Control independiente de 3 servos MG995
- ✅ Sin conflictos con lgpio (separación de hardware)
- ✅ Posiciones suaves y estables
- ✅ Sistema de hold rígido y retorno suave

## 🔧 Instalación

### 1. Instalar pigpio

```bash
sudo apt update
sudo apt install -y pigpio python3-pigpio
```

### 2. Iniciar daemon pigpio

```bash
# Método 1: Script automático (recomendado)
cd Prototipo_Clasificador
./start_pigpio_daemon.sh start

# Método 2: Manual
sudo pigpiod -s 10  # -s 10: sample rate 10μs para mejor precisión
```

### 3. Verificar daemon

```bash
# Con el script
./start_pigpio_daemon.sh status

# Manual
pgrep pigpiod  # Debe mostrar un PID
```

## 📌 Configuración de Pines

Los servos están configurados en (ACTUALIZADOS - Enero 2025):

- **GPIO 12**: Servo Manzanas 🍎 (MG995 - PWM0 hardware)
- **GPIO 13**: Servo Peras 🍐 (MG995 - PWM1 hardware)
- **GPIO 18**: Servo Limones 🍋 (MG995 - PWM0 alt hardware)

⚠️ **IMPORTANTE**: 
- Estos pines están **reservados para pigpio**. lgpio NO los reclamará automáticamente para evitar conflictos.
- Los pines GPIO 5, 6, 7 anteriores están **DAÑADOS** - NO usar
- Ver `CAMBIO_PINES_SERVOS.md` para detalles del cambio

## 🚀 Uso

### Inicio del sistema

```bash
# Desde el directorio raíz del proyecto
cd Prototipo_Clasificador

# 1. Iniciar daemon pigpio
./start_pigpio_daemon.sh start

# 2. Ejecutar el sistema
python3 smart_classifier_system.py
```

### Comandos del daemon

```bash
# Iniciar daemon
./start_pigpio_daemon.sh start

# Detener daemon
./start_pigpio_daemon.sh stop

# Reiniciar daemon
./start_pigpio_daemon.sh restart

# Ver estado
./start_pigpio_daemon.sh status
```

## 🔍 Solución de Problemas

### Problema: Servos no se mueven

1. **Verificar daemon pigpio**:
   ```bash
   ./start_pigpio_daemon.sh status
   ```

2. **Si no está corriendo, iniciarlo**:
   ```bash
   sudo pigpiod -s 10
   ```

3. **Verificar conectividad Python**:
   ```python
   import pigpio
   pi = pigpio.pi()
   print("Conectado:", pi.connected)
   pi.stop()
   ```

### Problema: Error "GPIO busy"

Esto indica conflicto entre lgpio y pigpio.

**Solución**:
```bash
# Detener pigpio temporalmente
sudo killall pigpiod

# O reiniciar el sistema
sudo reboot
```

### Problema: Servos tiemblan o se mueven erráticos

Esto ocurría con lgpio. Con pigpio **NO debe ocurrir**.

Si sigue ocurriendo:
1. Verificar voltaje de alimentación (4.8-7.2V)
2. Verificar que el daemon pigpio esté corriendo
3. Revisar conexiones físicas

### Problema: "pigpio no disponible"

```bash
# Instalar pigpio
sudo apt update
sudo apt install -y pigpio python3-pigpio

# Verificar instalación
python3 -c "import pigpio; print('OK')"
```

## 🔒 Protección contra Conflictos

El sistema incluye protección automática:

1. **gpio_wrapper.py** detecta si pigpio está activo
2. Si pigpio está corriendo, lgpio **NO reclamará** los pines 5, 6, 7
3. Advertencias claras en los logs si hay conflicto

### Logs de protección

```
⚠️ Daemon pigpio detectado - Pines {5, 6, 7} reservados para servos
   lgpio NO reclamará estos pines para evitar conflictos
```

## 📊 Configuración (Config_Prototipo.json)

Los servos se configuran en `servo_settings`:

```json
{
  "servo_settings": {
    "apple": {
      "pin_bcm": 5,
      "name": "Servo_Manzanas",
      "min_pulse_us": 1000,
      "max_pulse_us": 2000,
      "default_angle": 90,
      "activation_mode": "relative",
      "activation_offset_deg": -45,
      "hold_duration_s": 1.5,
      "return_smoothly": true
    },
    "pear": {
      "pin_bcm": 6,
      "name": "Servo_Peras",
      "min_pulse_us": 1000,
      "max_pulse_us": 2000,
      "default_angle": 90,
      "activation_mode": "relative",
      "activation_offset_deg": 90,
      "hold_duration_s": 1.5,
      "invert": true
    },
    "lemon": {
      "pin_bcm": 7,
      "name": "Servo_Limones",
      "min_pulse_us": 1000,
      "max_pulse_us": 2000,
      "default_angle": 90,
      "activation_mode": "relative",
      "activation_offset_deg": -80,
      "hold_duration_s": 1.5
    }
  },
  "advanced": {
    "use_pigpio": true
  }
}
```

## 🧪 Pruebas

### Probar driver pigpio individualmente

```bash
cd Prototipo_Clasificador
python3 pigpio_servo_driver.py
```

### Probar controlador MG995

```bash
python3 mg995_servo_controller.py
```

## ⚙️ Parámetros Técnicos

### Servomotor MG995
- Voltaje: 4.8-7.2V
- Torque: 9.4-11 kg·cm
- Velocidad: 0.2s/60° (4.8V)
- Pulso: 1000-2000μs
- Frecuencia: 50Hz

### Daemon pigpio
- Sample rate: 10μs (-s 10)
- PWM hardware-timed
- Sin jitter de software
- Precisión sub-microsegundo

## 📝 Notas Importantes

1. **NO mezclar lgpio y pigpio en los mismos pines**
2. **Siempre iniciar pigpiod ANTES del sistema**
3. **Los servos requieren alimentación externa estable**
4. **Verificar estado del daemon con `./start_pigpio_daemon.sh status`**

## 🔗 Referencias

- [Documentación pigpio](http://abyz.me.uk/rpi/pigpio/)
- [MG995 Datasheet](https://www.towerpro.com.tw/product/mg995/)
- [Raspberry Pi 5 GPIO](https://www.raspberrypi.com/documentation/computers/raspberry-pi-5.html)

## 🆘 Soporte

Si tienes problemas:

1. Verifica logs del sistema
2. Comprueba estado del daemon: `./start_pigpio_daemon.sh status`
3. Revisa voltaje de alimentación de servos
4. Asegúrate de que `use_pigpio: true` en config

---

**Autores**: Gabriel Calderón, Elias Bautista, Cristian Hernandez  
**Versión**: 1.0 - Enero 2025

