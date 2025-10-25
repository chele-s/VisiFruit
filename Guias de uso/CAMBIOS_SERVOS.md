# Cambios en Sistema de Servos - VisiFruit

## Fecha: 13 de Octubre 2025

## Resumen de Cambios

Se han realizado las siguientes modificaciones para optimizar el control de servos y establecer ángulos predeterminados en 0 grados:

---

## 1. Actualización de `rpi5_servo_controller.py`

### Cambios en Ángulos Predeterminados

**ANTES:**
- `default_angle: float = 90.0` (Posición inicial en 90°)
- `activation_angle: float = 0.0` (Activación en 0°)

**AHORA:**
- `default_angle: float = 0.0` (Posición inicial en 0°) ✅
- `activation_angle: float = 90.0` (Activación en 90°)

### Ubicaciones Modificadas:
1. **ServoConfig dataclass** (línea 81-82)
2. **RPi5ServoController.__init__** (línea 144-145) - Inicialización forzada a 0.0°
3. **RPi5MultiServoController.add_servo** (línea 539-540) - Parámetros por defecto
4. **test_single_servo** (línea 662-663) - Función de prueba

### Comportamiento:
- Todos los servos inician en **0 grados** al arrancar
- Los servos se mueven a **90 grados** cuando se activan
- Uso de **Hardware PWM** en GPIO 12 y 13 (Pi 5)
- Soporte de **lgpio** optimizado para Raspberry Pi 5

---

## 2. Integración en `fruit_diverter_controller.py`

### Nuevas Características:

#### Importación del RPi5ServoController
```python
from Prototipo_Clasificador.rpi5_servo_controller import (
    RPi5ServoController, ServoConfig, ServoProfile, ServoDirection
)
```

#### Configuración de 3 Desviadores con Hardware PWM

**ANTES:** 2 desviadores (manzanas y peras)
**AHORA:** 3 desviadores con pines optimizados:

| Fruta    | GPIO | Tipo PWM     | Ángulo Recta | Ángulo Desviado |
|----------|------|--------------|--------------|-----------------|
| Manzanas | 12   | Hardware PWM | 0°           | 90°             |
| Peras    | 13   | Hardware PWM | 0°           | 90°             |
| Limones  | 18   | Software PWM | 0°           | 90°             |

#### Modo Híbrido:
- **Prioridad:** Usa `RPi5ServoController` si está disponible
- **Fallback:** Controlador básico con GPIO/PWM estándar
- **Simulación:** Modo simulación automático si no hay hardware

### Mejoras en ServoMotorSG995:
1. **Propiedad `rpi5_controller`**: Controlador optimizado por servo
2. **Flag `use_rpi5_controller`**: Activación automática si está disponible
3. **Inicialización mejorada**: Intento con RPi5, fallback a GPIO básico
4. **move_to_angle()**: Usa RPi5Controller si está disponible para movimientos suaves
5. **cleanup()**: Limpieza correcta de ambos controladores

---

## 3. Integración Completa con `main_etiquetadora_v4.py`

### Estado Actual:
✅ **Ya integrado** - El sistema principal usa `FruitDiverterController`

```python
from Control_Etiquetado.fruit_diverter_controller import FruitDiverterController
```

### Flujo de Integración:
```
main_etiquetadora_v4.py
    ↓
FruitDiverterController
    ↓
ServoMotorSG995 (con RPi5ServoController interno)
    ↓
Hardware PWM optimizado (lgpio)
```

### Inicialización:
- Método `_initialize_diverter_system()` (línea ~420)
- Automáticamente usa el nuevo sistema optimizado
- Sin cambios necesarios en el código principal

---

## 4. Ventajas del Nuevo Sistema

### Performance:
- ✅ **Hardware PWM real** en GPIO 12 y 13 (sin jitter)
- ✅ **lgpio nativo** optimizado para Raspberry Pi 5
- ✅ **Movimientos suaves** con interpolación
- ✅ **Thread-safe** con locks adecuados

### Configuración:
- ✅ **0 grados por defecto** en todos los servos
- ✅ **Calibración automática** para MG995
- ✅ **Perfiles predefinidos** (MG995_STANDARD, MG995_EXTENDED, MG996R)
- ✅ **Límites de seguridad** configurables

### Confiabilidad:
- ✅ **Fallback automático** si RPi5Controller falla
- ✅ **Modo simulación** para desarrollo
- ✅ **Cleanup robusto** de recursos
- ✅ **Logging detallado** para debugging

---

## 5. Configuración de Prueba

### Para probar un servo individual:
```bash
python Prototipo_Clasificador/rpi5_servo_controller.py
```

### Para probar el sistema completo:
```bash
python main_etiquetadora_v4.py
```

---

## 6. Notas Importantes

### Requisitos de Hardware:
- Raspberry Pi 5
- Servos MG995 conectados a GPIO 12, 13, 18
- Alimentación externa para servos (5V, 2A mínimo)

### Requisitos de Software:
```bash
sudo apt install python3-lgpio python3-gpiozero
pip install gpiozero lgpio
```

### Configuración /boot/firmware/config.txt:
```
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

---

## Resumen de Archivos Modificados

1. ✅ `Prototipo_Clasificador/rpi5_servo_controller.py`
   - Ángulos predeterminados cambiados a 0°
   - Optimizado para Raspberry Pi 5

2. ✅ `Control_Etiquetado/fruit_diverter_controller.py`
   - Integración con RPi5ServoController
   - Soporte para 3 desviadores
   - Modo híbrido con fallback

3. ✅ `main_etiquetadora_v4.py`
   - Sin cambios necesarios (ya integrado)
   - Usa automáticamente el nuevo sistema

---

## Estado: ✅ COMPLETADO

Todos los cambios han sido implementados exitosamente. El sistema ahora:
- Inicia todos los servos en **0 grados**
- Usa **Hardware PWM optimizado** en Raspberry Pi 5
- Tiene **fallback automático** para compatibilidad
- Está **completamente integrado** en el sistema principal
