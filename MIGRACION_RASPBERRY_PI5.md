# 🚀 Migración a Raspberry Pi 5 - GPIO lgpio

## Resumen de la Migración

¡Felicidades! Tu proyecto VisiFruit ha sido completamente migrado para funcionar con **Raspberry Pi 5** y su nueva arquitectura GPIO. La migración incluye el reemplazo de `RPi.GPIO` por `lgpio` y compatibilidad universal.

## ✅ ¿Qué se ha migrado?

### 📁 Archivos modificados:
- ✅ `main_etiquetadora.py` - Sistema principal
- ✅ `Control_Etiquetado/relay_motor_controller.py` - Control de relays
- ✅ `Control_Etiquetado/conveyor_belt_controller.py` - Control de banda
- ✅ `Control_Etiquetado/fruit_diverter_controller.py` - Desviadores
- ✅ `Control_Etiquetado/labeler_actuator.py` - Etiquetadoras
- ✅ `Control_Etiquetado/sensor_interface.py` - Sensores
- ✅ `Requirements.txt` - Dependencias actualizadas

### 🆕 Archivos nuevos:
- ✅ `utils/gpio_wrapper.py` - **Wrapper GPIO universal**
- ✅ `install_raspberry_pi5.sh` - **Script de instalación automática**
- ✅ `MIGRACION_RASPBERRY_PI5.md` - Esta documentación

## 🔧 Características del Nuevo Sistema

### 🎯 Detección Automática de Hardware
El sistema detecta automáticamente tu hardware y usa:

- **🍓 Raspberry Pi 5**: `lgpio` (nueva arquitectura BCM2712)
- **📟 Raspberry Pi < 5**: `RPi.GPIO` (arquitectura legacy)
- **🖥️ Windows/Desarrollo**: Simulación GPIO completa

### 🌟 Ventajas del Nuevo Sistema

1. **✅ Compatibilidad Universal**: Funciona en cualquier entorno
2. **🚀 Raspberry Pi 5 Nativo**: Soporte completo para nueva arquitectura
3. **🔄 Fallback Automático**: Si lgpio no está disponible, usa alternativas
4. **💻 Desarrollo Fácil**: Simulación completa en Windows
5. **🐛 Debug Mejorado**: Logs detallados del sistema GPIO usado

## 📦 Instalación en Raspberry Pi 5

### Opción 1: Script Automático (Recomendado)
```bash
# Hacer ejecutable el script
chmod +x install_raspberry_pi5.sh

# Ejecutar instalación automática
bash install_raspberry_pi5.sh
```

### Opción 2: Manual
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar lgpio
sudo apt install -y python3-lgpio python3-rpi-lgpio
pip install lgpio

# Instalar dependencias
pip install -r Requirements.txt
```

## 🖥️ Desarrollo en Windows

**¡No necesitas cambiar nada!** El sistema automáticamente:

1. **Detecta Windows** y activa modo simulación
2. **Muestra logs** de todas las operaciones GPIO simuladas
3. **Mantiene compatibilidad** completa con tu código existente

### Ejemplo de salida en Windows:
```
🔧 Sistema GPIO: SimulatedGPIO (simulation)
⚠️ Modo simulación GPIO activo - Ideal para desarrollo en Windows
🏷️ Etiquetadoras: Modo simulación activo (ideal para desarrollo)
📡 Sensores: Modo simulación activo (ideal para desarrollo)
```

## 🔍 Verificación del Sistema

### Comprobar qué sistema GPIO está usando:
```python
from utils.gpio_wrapper import get_gpio_info, is_raspberry_pi5, is_simulation_mode

# Información del sistema
info = get_gpio_info()
print(f"Modo GPIO: {info['mode']}")
print(f"Tipo GPIO: {info['gpio_type']}")
print(f"Plataforma: {info['platform']}")

# Verificaciones específicas
print(f"¿Es Raspberry Pi 5?: {is_raspberry_pi5()}")
print(f"¿Modo simulación?: {is_simulation_mode()}")
```

### Ejemplo de salida en Raspberry Pi 5:
```python
{
    'mode': 'lgpio',
    'available': True, 
    'platform': 'linux',
    'gpio_type': 'LGPIOWrapper'
}
```

## 🎮 Uso del GPIO Wrapper

El nuevo wrapper mantiene **100% compatibilidad** con el código existente:

```python
from utils.gpio_wrapper import GPIO

# ¡Tu código existente funciona sin cambios!
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)

# PWM también funciona
pwm = GPIO.PWM(18, 1000)  # Pin 18, 1000Hz
pwm.start(50)  # 50% duty cycle
pwm.ChangeDutyCycle(75)
pwm.stop()

GPIO.cleanup()
```

## 🚨 Resolución de Problemas

### Error: "lgpio no disponible"
```bash
# Instalar lgpio manualmente
sudo apt install python3-lgpio python3-rpi-lgpio
pip install lgpio
```

### Error: "GPIO wrapper no disponible"
```bash
# Verificar estructura de directorios
ls -la utils/gpio_wrapper.py

# Si no existe, verificar que estés en el directorio correcto
pwd
```

### Problemas de permisos GPIO
```bash
# Añadir usuario a grupos GPIO
sudo usermod -a -G gpio $USER
sudo usermod -a -G dialout $USER

# Reiniciar sesión
logout
```

## 📊 Comparación: Antes vs Después

| Aspecto | Antes (RPi.GPIO) | Después (lgpio wrapper) |
|---------|------------------|-------------------------|
| **Raspberry Pi 5** | ❌ No compatible | ✅ Totalmente compatible |
| **Raspberry Pi < 5** | ✅ Funciona | ✅ Mantiene compatibilidad |
| **Windows Dev** | ❌ Errores | ✅ Simulación completa |
| **Detección Auto** | ❌ Manual | ✅ Automática |
| **Fallbacks** | ❌ Ninguno | ✅ Múltiples niveles |
| **Debugging** | ⚠️ Básico | ✅ Avanzado |

## 🔮 Código Migrado Automáticamente

El sistema migró automáticamente:

### Importaciones:
```python
# ANTES:
import RPi.GPIO as GPIO

# DESPUÉS:
from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, is_simulation_mode
```

### Detección de hardware:
```python
# ANTES:
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

# DESPUÉS:
try:
    from utils.gpio_wrapper import GPIO, GPIO_AVAILABLE, get_gpio_info
    gpio_info = get_gpio_info()
    print(f"🔧 Sistema GPIO: {gpio_info['gpio_type']} ({gpio_info['mode']})")
except ImportError:
    GPIO_AVAILABLE = False
```

## 🎯 Próximos Pasos

1. **✅ Completo**: La migración está lista
2. **🧪 Probar**: Ejecuta tu sistema en Windows (simulación)
3. **🍓 Desplegar**: Usa el script de instalación en Raspberry Pi 5
4. **🔧 Configurar**: Ajusta `Config_Etiquetadora.json` según necesites
5. **🚀 Producir**: ¡Tu sistema está listo para producción!

## 📞 Soporte

Si encuentras algún problema:

1. **Verifica la detección**: Ejecuta `python -c "from utils.gpio_wrapper import get_gpio_info; print(get_gpio_info())"`
2. **Revisa los logs**: El sistema muestra información detallada del GPIO usado
3. **Modo simulación**: En Windows, todo debería funcionar automáticamente
4. **Hardware real**: En Raspberry Pi 5, usa el script de instalación

---

## 🎉 ¡Migración Completada!

Tu proyecto VisiFruit ahora es **totalmente compatible** con:
- ✅ **Raspberry Pi 5** (arquitectura BCM2712)
- ✅ **Raspberry Pi anteriores** (compatibility mode)
- ✅ **Windows** (desarrollo y testing)
- ✅ **Linux genérico** (simulación)

**¡El futuro de VisiFruit es ahora! 🚀🍓**
