# 🎮 Sistema de Control de Servos MG995 - VisiFruit
## Raspberry Pi 5 - Hardware PWM Optimizado

---

## 📋 Descripción General

Sistema completo de control de servos MG995 optimizado específicamente para Raspberry Pi 5, usando los únicos pines con hardware PWM real (GPIO 12 y 13). Incluye control desde interfaz web, configuración dinámica y calibración avanzada.

## ⚠️ Información CRÍTICA para Raspberry Pi 5

### Pines Hardware PWM en Raspberry Pi 5:
- **GPIO 12** - PWM0 (Hardware PWM Canal 0)
- **GPIO 13** - PWM1 (Hardware PWM Canal 1)

**IMPORTANTE**: GPIO 18 y 19 NO tienen hardware PWM en Raspberry Pi 5 (cambio de arquitectura del BCM2712)

### Incompatibilidades conocidas:
- ❌ **pigpio**: NO compatible con Raspberry Pi 5
- ❌ **lgpio**: Problemas con PWM
- ✅ **gpiozero + LGPIOFactory**: MEJOR opción para Pi 5

---

## 🚀 Instalación

### 1. Requisitos del Sistema

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3-gpiozero python3-lgpio python3-pip

# Instalar dependencias Python
pip3 install gpiozero asyncio
```

### 2. Configuración Hardware

Editar `/boot/firmware/config.txt`:

```bash
sudo nano /boot/firmware/config.txt
```

Añadir al final:

```
# Hardware PWM para Raspberry Pi 5
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Reiniciar:

```bash
sudo reboot
```

### 3. Conexión de Servos MG995

```
MG995 Servo 1:
- Cable Marrón (GND) → GPIO GND
- Cable Rojo (5V) → Fuente Externa 5V
- Cable Naranja (PWM) → GPIO 12

MG995 Servo 2:
- Cable Marrón (GND) → GPIO GND
- Cable Rojo (5V) → Fuente Externa 5V
- Cable Naranja (PWM) → GPIO 13

⚡ IMPORTANTE: Usar fuente de alimentación externa para los servos (5V, mínimo 2A)
```

---

## 📁 Estructura de Archivos

```
VisiFruit/
├── Prototipo_Clasificador/
│   ├── rpi5_servo_controller.py     # Controlador optimizado para Pi 5
│   ├── gpiozero_servo_driver.py     # Driver base con gpiozero
│   ├── mg995_servo_controller.py    # Controlador principal
│   └── Config_Prototipo.json        # Configuración del sistema
│
├── Interfaz_Usuario/
│   ├── Backend/
│   │   └── backend_modules/
│   │       └── servo_control_module.py  # Módulo backend para API
│   └── VisiFruit/
│       └── src/components/production/
│           └── ServoControlPanel.tsx     # Componente React
```

---

## 🔧 Configuración

### Configuración Básica (Config_Prototipo.json)

```json
{
  "servo_settings": {
    "apple": {
      "pin_bcm": 12,              // GPIO 12 - Hardware PWM
      "name": "Servo_Manzanas",
      "min_pulse_us": 1000,       // Pulso mínimo (0°)
      "max_pulse_us": 2000,       // Pulso máximo (180°)
      "default_angle": 90,        // Posición inicial
      "activation_angle": 45,     // Posición de activación
      "direction": "forward",     // forward o reverse
      "smooth_movement": true,    // Movimiento suave
      "movement_speed": 0.8       // Velocidad (0.1-1.0)
    },
    "pear": {
      "pin_bcm": 13,              // GPIO 13 - Hardware PWM
      "name": "Servo_Peras",
      // ... configuración similar
    }
  }
}
```

### Perfiles Predefinidos

- **MG995 Standard**: 1.0-2.0ms, 0-180°
- **MG995 Extended**: 0.5-2.5ms, 0-180°
- **MG996R**: 0.8-2.2ms, 0-180°
- **Custom**: Configuración personalizada

---

## 💻 Uso del Controlador

### Python - Uso Básico

```python
import asyncio
from Prototipo_Clasificador.rpi5_servo_controller import (
    RPi5ServoController, ServoConfig, ServoProfile, ServoDirection
)

# Configurar servo
config = ServoConfig(
    pin_bcm=12,                        # GPIO 12 (Hardware PWM)
    name="Servo_1",
    profile=ServoProfile.MG995_STANDARD,
    default_angle=90,
    activation_angle=0,
    direction=ServoDirection.FORWARD,
    smooth_movement=True,
    movement_speed=0.8
)

# Crear controlador
controller = RPi5ServoController(config)

# Mover servo
async def main():
    # Movimiento suave a 45°
    await controller.set_angle_async(45, smooth=True)
    await asyncio.sleep(1)
    
    # Activación
    await controller.move_to_activation()
    await asyncio.sleep(1)
    
    # Regresar a default
    await controller.move_to_default()

asyncio.run(main())
```

### Control Múltiple

```python
from Prototipo_Clasificador.rpi5_servo_controller import RPi5MultiServoController

controller = RPi5MultiServoController()

# Añadir servos
controller.add_servo(
    "servo1", 
    pin=12,
    name="Clasificador_1",
    default_angle=90,
    activation_angle=0
)

controller.add_servo(
    "servo2",
    pin=13, 
    name="Clasificador_2",
    default_angle=90,
    activation_angle=180,
    direction=ServoDirection.REVERSE
)

# Mover todos
await controller.move_all(90, smooth=True)
```

### Actualización Dinámica

```python
# Cambiar configuración en tiempo real
controller.update_config(
    direction=ServoDirection.REVERSE,
    movement_speed=0.5,
    smooth_steps=30
)

# Guardar configuración
controller.save_config()

# Cargar configuración
controller = RPi5ServoController.load_config(Path("servo_config.json"))
```

---

## 🌐 Control desde Interfaz Web

### Backend API

El módulo `servo_control_module.py` proporciona endpoints REST:

```python
# Endpoints disponibles
POST /api/servo/move
POST /api/servo/activate
POST /api/servo/reset
POST /api/servo/config
GET  /api/servo/status
GET  /api/servo/statistics
```

### Frontend React

Importar el componente:

```typescript
import ServoControlPanel from './components/production/ServoControlPanel';

// En tu componente
<ServoControlPanel
  servos={servoConfigs}
  onServoAction={handleServoAction}
  onConfigUpdate={handleConfigUpdate}
  isConnected={true}
  disabled={false}
/>
```

---

## 🧪 Pruebas y Diagnóstico

### Test de Hardware PWM

```bash
# Verificar que los overlays estén cargados
sudo dtoverlay -l

# Debe mostrar:
# 0:  pwm-2chan  pin=12 func=4 pin2=13 func2=4
```

### Test de Servo Individual

```bash
cd VisiFruit/Prototipo_Clasificador
python3 rpi5_servo_controller.py
```

### Test del Sistema Completo

```bash
cd VisiFruit/Interfaz_Usuario/Backend
python3 -c "from backend_modules import servo_control_module; import asyncio; asyncio.run(servo_control_module.test_module())"
```

### Diagnóstico de Problemas Comunes

#### Servo vibrando o con jitter:
- Verificar que uses GPIO 12 o 13 (hardware PWM)
- Revisar fuente de alimentación (mínimo 2A)
- Verificar configuración en `/boot/firmware/config.txt`

#### Servo no responde:
```python
# Test básico de gpiozero
from gpiozero import Servo
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device

Device.pin_factory = LGPIOFactory()
servo = Servo(12)
servo.mid()  # Debería mover a 90°
```

#### Error "pigpio daemon not running":
- NO uses pigpio con Raspberry Pi 5
- Usa el controlador `rpi5_servo_controller.py`

---

## 📊 Monitoreo y Estadísticas

El sistema incluye monitoreo en tiempo real:

```python
# Obtener estado
status = controller.get_status()
print(f"Ángulo actual: {status['current_angle']}°")
print(f"Hardware PWM: {status['hardware_pwm']}")

# Estadísticas del sistema
stats = await module.get_statistics()
print(f"Movimientos totales: {stats['total_movements']}")
print(f"Activaciones: {stats['total_activations']}")
```

---

## 🔄 Integración con el Sistema Principal

### En main_etiquetadora_v4.py:

```python
# Importar controlador optimizado
from Prototipo_Clasificador.rpi5_servo_controller import RPi5MultiServoController

# En la inicialización
self.servo_controller = RPi5MultiServoController()
self.servo_controller.add_servo("apple", pin=12, ...)
self.servo_controller.add_servo("pear", pin=13, ...)

# En detección de fruta
if detected_class == "apple":
    await self.servo_controller.get_servo("apple").move_to_activation()
```

---

## 🛠️ Mantenimiento

### Calibración de Servos

```python
# Calibración personalizada
calibration = ServoCalibration(
    min_pulse_ms=0.9,    # Ajustar según tu servo
    max_pulse_ms=2.1,
    min_angle=0,
    max_angle=180,
    center_pulse_ms=1.5,
    deadband_ms=0.01
)

config.calibration = calibration
controller.update_config(calibration=calibration)
```

### Límites de Seguridad

```python
# Establecer límites seguros
config.min_safe_angle = 10    # No ir por debajo de 10°
config.max_safe_angle = 170    # No ir por encima de 170°
```

---

## 📝 Notas Importantes

1. **Alimentación**: SIEMPRE usar fuente externa para servos (5V, 2A mínimo)
2. **Hardware PWM**: Solo GPIO 12 y 13 en Raspberry Pi 5
3. **No mezclar**: No usar pigpio o lgpio directamente
4. **Thread-safe**: El controlador es thread-safe, úsalo con asyncio
5. **Configuración**: Guarda cambios con `save_config()` para persistencia

---

## 🆘 Soporte

Si encuentras problemas:

1. Verifica configuración hardware (`/boot/firmware/config.txt`)
2. Revisa logs: `tail -f logs/prototipo_clasificador.log`
3. Ejecuta diagnósticos: `python3 rpi5_servo_controller.py`
4. Verifica permisos GPIO: `sudo usermod -a -G gpio $USER`

---

## 📚 Referencias

- [Raspberry Pi 5 GPIO](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
- [MG995 Datasheet](http://www.towerpro.com.tw/product/mg995/)

---

**Última actualización**: Enero 2025  
**Versión**: 2.0 - Raspberry Pi 5 Optimized
