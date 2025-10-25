# 🔧 Corrección de Jitter en Servos MG995 - Raspberry Pi 5

## ⚠️ Problema Principal

### Hardware PWM en Raspberry Pi 5
- **Solo GPIO 12 y 13** tienen hardware PWM real
- **GPIO 20** usa software PWM → siempre tendrá algo de jitter
- El test funciona mejor porque usa directamente lgpio tx_pwm

## ✅ Soluciones Implementadas

### 1. Optimización de Parámetros de Movimiento
```python
# Ajustado en mg995_servo_controller.py
movement_speed=0.5    # Reducido de 0.7 para movimientos más controlados
smooth_steps=15       # Reducido de 30 para menos cambios abruptos
```

### 2. Aumento del Delay Entre Pasos
```python
# Ajustado en rpi5_servo_controller.py
delay_ms = (1.0 - movement_speed) * 30 + 10  # Aumentado de 10+5 a 30+10
# Con speed=0.5: delay = 25ms entre pasos (antes ~8ms)
```

### 3. Optimización de Software PWM para GPIO 20
- LGPIOFactory configurado especialmente para pines sin hardware PWM
- Reducción del jitter mediante frecuencia PWM optimizada

## 📊 Comparación de Rendimiento

| Servo | GPIO | PWM Type | Calidad |
|-------|------|----------|---------|
| Manzanas | 12 | Hardware (lgpio tx_pwm) | ✅ Excelente |
| Peras | 13 | Hardware (lgpio tx_pwm) | ✅ Excelente |
| Limones | 20 | Software (gpiozero) | ⚠️ Aceptable |

## 🚀 Solución ÓPTIMA Recomendada

### Opción A: Cambiar Pines (MEJOR)
Si es posible en tu hardware, considera esta reconfiguración:

```json
// Config_Prototipo.json - CONFIGURACIÓN IDEAL
"servo_settings": {
    "apple": {
        "pin_bcm": 12,  // ✅ Hardware PWM
        // ...
    },
    "pear": {
        "pin_bcm": 13,  // ✅ Hardware PWM
        // ...
    },
    "lemon": {
        "pin_bcm": 18,  // ⚠️ Cambiar de 20 a 18 (PWM2 en algunos casos)
        // ...
    }
}
```

**Nota**: GPIO 18 puede tener PWM en Raspberry Pi 5 con configuración especial en `/boot/firmware/config.txt`:
```bash
# Agregar para habilitar PWM en GPIO 18
dtoverlay=pwm,pin=18,func=2
```

### Opción B: Configuración Actual Optimizada
Si no puedes cambiar los pines, los ajustes realizados minimizan el jitter:

```python
# Configuración optimizada para GPIO 20 (sin hardware PWM)
{
    "pin_bcm": 20,
    "movement_speed": 0.3,  # Más lento para software PWM
    "smooth_steps": 10,     # Menos pasos para reducir jitter
    "hold_duration_s": 10.0 # Mantener posición estable
}
```

## 🧪 Pruebas y Verificación

### Test Rápido
```bash
cd ~/VisiFruit/Prototipo_Clasificador
python3 test_servo_system.py
```

### Monitoreo en Producción
```bash
cd ~/VisiFruit
python3 main_etiquetadora_v4.py
```

## 📈 Resultados Esperados

### Con Hardware PWM (GPIO 12, 13)
- ✅ Movimiento ultra-suave
- ✅ Posicionamiento exacto
- ✅ Sin vibraciones

### Con Software PWM (GPIO 20)
- ⚠️ Movimiento aceptable
- ⚠️ Pequeñas vibraciones mínimas
- ⚠️ Funcional para producción

## 🔄 Configuración de Emergencia

Si el jitter persiste en GPIO 20, prueba:

```python
# En rpi5_servo_controller.py, línea 367
delay_ms = 40  # Fijo en 40ms para máxima estabilidad
```

## 💡 Recomendaciones Finales

1. **IDEAL**: Usa solo GPIO 12 y 13 para servos críticos
2. **ACEPTABLE**: GPIO 20 con configuración optimizada
3. **EVITAR**: Movimientos rápidos en pines sin hardware PWM
4. **CONSIDERAR**: Usar un controlador de servos externo (PCA9685) para múltiples servos con PWM de alta calidad

## 📋 Checklist de Verificación

- [x] movement_speed reducido a 0.5
- [x] smooth_steps reducido a 15
- [x] delay_ms aumentado a 25ms
- [x] hold_duration_s aumentado a 10s
- [ ] Considerar cambio de GPIO 20 a GPIO 18
- [ ] Verificar ausencia de jitter en producción

## Autor

Sistema VisiFruit - Enero 2025
