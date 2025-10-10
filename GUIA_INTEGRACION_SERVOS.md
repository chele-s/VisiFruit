# 📋 Guía de Integración - Control de Servos VisiFruit

## ✅ Respuestas a tus preguntas:

### 1. **¿Dónde aparece el ServoControlPanel en la página web?**

El panel de control de servos ahora está disponible en la interfaz web. Para acceder:

1. **Botón en la barra superior**: Busca el ícono de engranaje (⚙️) en la barra superior junto a los otros íconos de navegación rápida (Dashboard, Production, 3D View)

2. **Acceso directo**: El nuevo botón de "Control de Servos" está ubicado después del botón de vista 3D

3. **Navegación**: Haz clic en el ícono para acceder directamente a la vista de control de servos

---

### 2. **¿El programa principal usa automáticamente rpi5_servo_controller.py?**

**NO**, actualmente el programa principal (`main_etiquetadora_v4.py`) usa:
- `smart_classifier_system.py` → que importa → `mg995_servo_controller.py`
- `mg995_servo_controller.py` usa `gpiozero_servo_driver.py` (NO el nuevo controlador)

Para usar el nuevo controlador optimizado `rpi5_servo_controller.py`, necesitas actualizar `mg995_servo_controller.py`:

```python
# En mg995_servo_controller.py, reemplazar las importaciones:

# ANTES (líneas 38-54):
try:
    from Prototipo_Clasificador.gpiozero_servo_driver import (
        GPIOZeroServoDriver, ServoConfig as GPIOZeroServoConfig,
        check_gpiozero_available
    )
    ...
except ImportError:
    ...

# DESPUÉS:
try:
    from Prototipo_Clasificador.rpi5_servo_controller import (
        RPi5ServoController, 
        RPi5MultiServoController,
        ServoConfig, 
        ServoProfile,
        ServoDirection
    )
    RPI5_CONTROLLER_AVAILABLE = True
except ImportError:
    RPI5_CONTROLLER_AVAILABLE = False
```

---

## 🔧 Para activar el nuevo controlador:

### Opción 1: Actualizar mg995_servo_controller.py (Recomendado)
```python
# En mg995_servo_controller.py, línea ~225:
# Cambiar la creación de drivers para usar el nuevo controlador

# Crear controlador RPI5 en lugar de GPIOZeroServoDriver
from Prototipo_Clasificador.rpi5_servo_controller import (
    RPi5ServoController, ServoConfig, ServoProfile
)

# En el método initialize():
for category, servo in self.servos.items():
    config = ServoConfig(
        pin_bcm=servo.pin_bcm,
        name=servo.name,
        profile=ServoProfile.MG995_STANDARD,
        default_angle=servo.default_angle,
        activation_angle=servo.activation_angle,
        # ... otros parámetros
    )
    controller = RPi5ServoController(config)
    # ... resto del código
```

### Opción 2: Usar directamente en tu código
```python
# En tu código principal:
from Prototipo_Clasificador.rpi5_servo_controller import (
    RPi5MultiServoController, ServoProfile
)

# Crear controlador
controller = RPi5MultiServoController()

# Añadir servos
controller.add_servo(
    "servo1",
    pin=12,  # GPIO 12 - Hardware PWM
    name="Clasificador_1",
    profile=ServoProfile.MG995_STANDARD
)
```

---

## 📌 Estructura actual del sistema:

```
main_etiquetadora_v4.py
    └── smart_classifier_system.py
        └── mg995_servo_controller.py
            ├── gpiozero_servo_driver.py  ← Actualmente usa este
            └── pigpio_servo_driver.py     ← O este como fallback
            
            ❌ NO usa: rpi5_servo_controller.py (el nuevo optimizado)
```

---

## 🚀 Pasos para usar el controlador optimizado:

1. **Prueba primero el controlador nuevo**:
   ```bash
   cd Prototipo_Clasificador
   python3 test_servo_system.py
   ```

2. **Si funciona correctamente**, actualiza mg995_servo_controller.py para usar el nuevo controlador

3. **Verifica en la interfaz web**: El panel de control de servos está en el botón de engranaje en la barra superior

---

## ⚠️ Importante:

- El nuevo controlador `rpi5_servo_controller.py` es **MEJOR** para Raspberry Pi 5
- Usa los pines GPIO 12 y 13 que tienen hardware PWM real
- El controlador antiguo puede funcionar pero no es óptimo para Pi 5
- pigpio NO funciona en Raspberry Pi 5 (incompatibilidad de arquitectura)

---

## 🎮 Para ver el panel en la web:

1. Inicia el frontend:
   ```bash
   cd Interfaz_Usuario/VisiFruit
   npm run dev
   ```

2. Abre el navegador en `http://localhost:5173`

3. Busca el ícono de engranaje (⚙️) en la barra superior

4. Haz clic para acceder al Control de Servos
