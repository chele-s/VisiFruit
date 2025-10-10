# 🍓 Configuración de PWM por Hardware en Raspberry Pi 5

Este documento contiene las instrucciones para configurar PWM por hardware en Raspberry Pi 5 para controlar los servomotores MG995.

## ⚠️ Importante: Raspberry Pi 5 y pigpio

**La Raspberry Pi 5 NO es compatible con pigpio** debido a cambios en la arquitectura del chip BCM2712. Por esta razón, hemos migrado a **gpiozero** que sí soporta la Pi 5 y puede usar PWM por hardware.

## 📍 Canales PWM en Raspberry Pi 5

La Raspberry Pi 5 tiene **2 canales de PWM por hardware**:

| Canal | Pines GPIO Disponibles | Uso en VisiFruit |
|-------|------------------------|------------------|
| **PWM0** | GPIO 12, GPIO 18 | **GPIO 18** - Servo Manzanas |
| **PWM1** | GPIO 13, GPIO 19 | **GPIO 19** - Servo Peras |

⚠️ **IMPORTANTE**: No puedes usar dos pines del mismo canal simultáneamente para señales PWM diferentes. Por ejemplo:
- ✅ GPIO 18 (PWM0) + GPIO 19 (PWM1) = **Funciona**
- ❌ GPIO 12 (PWM0) + GPIO 18 (PWM0) = **NO funciona** (mismo canal)

## 🎯 Configuración de Pines para VisiFruit

Hemos configurado los servos de la siguiente manera:

| Fruta | Pin GPIO | Tipo PWM | Canal | Notas |
|-------|----------|----------|-------|-------|
| 🍎 Manzanas | **GPIO 12** | Hardware PWM | PWM0 | Canal hardware |
| 🍐 Peras | **GPIO 13** | Hardware PWM | PWM1 | Canal hardware |
| 🍋 Limones | **GPIO 20** | Software PWM (gpiozero) | - | GPIO 19 ocupado por stepper |

⚠️ **Nota**: GPIO 19 está ocupado por el stepper DRV8825 (laser_stepper), por lo que usamos GPIO 13 para el segundo canal hardware PWM y GPIO 20 para el tercer servo con software PWM.

Esta configuración optimiza el rendimiento usando hardware PWM para 2 servos y software PWM (manejado eficientemente por gpiozero) para el tercero.

---

## 🔧 Paso 1: Instalar Dependencias

Ejecuta estos comandos en tu Raspberry Pi 5:

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar gpiozero y lgpio
sudo apt install python3-gpiozero python3-lgpio -y

# Verificar instalación
python3 -c "import gpiozero; print('gpiozero version:', gpiozero.__version__)"
```

---

## 📝 Paso 2: Configurar /boot/firmware/config.txt

Este es el paso **más importante**. Debes editar el archivo de configuración del sistema para activar los canales PWM por hardware.

### 2.1 Abrir el archivo de configuración:

```bash
sudo nano /boot/firmware/config.txt
```

### 2.2 Agregar la configuración PWM

Ve hasta el final del archivo y agrega estas líneas:

```properties
# ====================================================
# Activar PWM por Hardware para Servos MG995
# ====================================================
# Activa PWM0 en GPIO 12 y PWM1 en GPIO 13
dtoverlay=pwm-2chan

# Nota: La configuraci n por defecto activa autom ticamente:
# - PWM0 en GPIO 12
# - PWM1 en GPIO 13
# Esto es exactamente lo que necesitamos para VisiFruit

```properties
# Ejemplo: Usar GPIO 12 y 13 en lugar de 18 y 19
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

**Para VisiFruit, usa la configuración estándar (pwm-2chan)** que ya está optimizada para nuestros pines.

### 2.4 Guardar y cerrar

- Presiona `Ctrl + O` y luego `Enter` para guardar
- Presiona `Ctrl + X` para salir

---

## 🔄 Paso 3: Reiniciar la Raspberry Pi

Los cambios en `config.txt` requieren un reinicio para aplicarse:

```bash
sudo reboot
```

---

## ✅ Paso 4: Verificar la Configuración

Después del reinicio, verifica que los pines PWM estén activos:

```bash
# Ver dispositivos PWM disponibles
ls /sys/class/pwm/

# Debería mostrar:
# pwmchip0  pwmchip2
# pwmchip1  pwmchip3
```

---

## 🧪 Paso 5: Probar los Servos

### 5.1 Probar el driver gpiozero:

```bash
cd /home/pi/VisiFruit/Prototipo_Clasificador
python3 gpiozero_servo_driver.py
```

Esto ejecutará una prueba del servo en GPIO 18.

### 5.2 Probar el controlador completo:

```bash
cd /home/pi/VisiFruit/Prototipo_Clasificador
python3 mg995_servo_controller.py
```

Esto probará los 3 servos en secuencia.

---

## 🔍 Diagnóstico y Solución de Problemas

### Problema: "gpiozero no disponible"

```bash
# Reinstalar gpiozero
sudo apt install --reinstall python3-gpiozero python3-lgpio
```

### Problema: "Pin busy" o conflictos

```bash
# Verificar que pigpio NO esté corriendo
sudo killall pigpiod

# Verificar procesos usando GPIO
### Problema: Jitter o vibraciones

El PWM por hardware elimina el jitter. Si experimentas vibraciones:
- Verifica que la configuración `pwm-2chan` esté activa
- Verifica que los servos estén conectados a la alimentación externa (5-6V, 2A mínimo)
- Asegúrate de que `use_gpiozero: true` en `Config_Prototipo.json`

---

## 📊 Comparación: pigpio vs gpiozero

| Característica | pigpio | gpiozero |
|----------------|--------|----------|
| **Raspberry Pi 5** | ❌ NO compatible | ✅ Compatible |
| **PWM Hardware** | ✅ Sí | ✅ Sí (automático) |
| **Facilidad de uso** | Media | ✅ Alta |
| **Precisión** | Muy alta | ✅ Alta |
| **Daemon requerido** | Sí (pigpiod) | ❌ No |
| **Overhead** | Bajo | ✅ Muy bajo |

---

## 📚 Referencias

- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
- [Raspberry Pi 5 GPIO Pinout](https://pinout.xyz/)
- [Device Tree Overlays Documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#device-trees-overlays-and-parameters)

---

## 🎯 Resumen de Cambios Realizados

### Archivos Modificados:

1. ✅ **Config_Prototipo.json**
   - Actualizado `apple` de GPIO 12 → GPIO 18 (PWM0 hardware)
   - Actualizado `pear` de GPIO 13 → GPIO 19 (PWM1 hardware)
   - Actualizado `lemon` de GPIO 18 → GPIO 13 (Software PWM)
   - Cambiado `use_pigpio: false` y `use_gpiozero: true`

2. ✅ **gpiozero_servo_driver.py** (NUEVO)
   - Driver completo para servos MG995 con gpiozero
   - Soporte automático para hardware/software PWM
   - Compatible con Raspberry Pi 5

3. ✅ **mg995_servo_controller.py**
   - Migrado de pigpio a gpiozero como sistema principal
   - Mantiene pigpio como fallback para retrocompatibilidad
   - Detección automática de pines con hardware PWM

4. ✅ **gpio_wrapper.py**
   - Actualizada protección de pines reservados
   - Soporta tanto gpiozero como pigpio
   - Previene conflictos entre sistemas

---

## 🚀 ¡Listo para Producción!

Una vez completados todos los pasos, tu sistema estará optimizado para Raspberry Pi 5 con:
- ✅ PWM por hardware sin jitter
- ✅ Control preciso de servos MG995
- ✅ Compatibilidad total con Pi 5
- ✅ Rendimiento óptimo

**¡Tu sistema VisiFruit está listo para funcionar perfectamente en Raspberry Pi 5!** 🎉
