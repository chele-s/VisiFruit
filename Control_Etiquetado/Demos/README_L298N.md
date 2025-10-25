# Driver L298N para Control de Motor DC - VisiFruit System

## Descripción General

Este documento describe la implementación del driver L298N integrado en el sistema VisiFruit para el control preciso de motores DC en la banda transportadora.

## Características del Driver L298N

- **Control bidireccional**: Movimiento hacia adelante y atrás
- **Control de velocidad PWM**: 0-100% con resolución fina
- **Frenado dinámico**: Parada suave y frenado de emergencia
- **Monitoreo en tiempo real**: Estado, velocidad y métricas
- **Recuperación automática**: Manejo inteligente de errores
- **Configuración flexible**: Pins GPIO configurables

## Conexiones Hardware

### Esquema de Conexión

```
Raspberry Pi          L298N Module          Motor DC
============          ============          ========

GPIO 13 (Pin 33) ---> ENA (Velocidad PWM)               
GPIO 20 (Pin 38) ---> IN1 (Dirección 1)               
GPIO 21 (Pin 40) ---> IN2 (Dirección 2)               
GPIO 12 (Pin 32) ---> EN (Habilitación)     
5V (Pin 2)       ---> VCC (Lógica 5V)              
GND (Pin 6)      ---> GND (Tierra común)              
                      OUT1 -----------> Motor (+)
                      OUT2 -----------> Motor (-)
                      VIN <------------ 12V Externa
                      GND <------------ GND Externa
```

### Especificaciones Técnicas

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Tensión lógica | 5V | Alimentación desde Raspberry Pi |
| Tensión motor | 6-12V | Alimentación externa del motor |
| Corriente máxima | 2A por canal | Límite por canal del L298N |
| Frecuencia PWM | 1000 Hz | Frecuencia recomendada |
| Disipación | Hasta 25W | Usar disipador térmico |

## Configuración

### Archivo de Configuración JSON

```json
{
  "conveyor_belt_settings": {
    "control_type": "l298n_motor",
    "motor_pin_bcm": 13,
    "enable_pin_bcm": 12,
    "direction_pin_bcm": 20,
    "direction_pin2_bcm": 21,
    "pwm_frequency_hz": 1000,
    "min_duty_cycle": 30,
    "max_duty_cycle": 100,
    "default_speed_percent": 75,
    "safety_timeout_s": 10.0,
    "recovery_attempts": 3,
    "health_check_interval_s": 1.0
  }
}
```

### Parámetros de Configuración

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `control_type` | string | Debe ser "l298n_motor" |
| `motor_pin_bcm` | int | Pin BCM para ENA (PWM) |
| `enable_pin_bcm` | int | Pin BCM para habilitación (opcional) |
| `direction_pin_bcm` | int | Pin BCM para IN1 |
| `direction_pin2_bcm` | int | Pin BCM para IN2 |
| `pwm_frequency_hz` | int | Frecuencia PWM (100-2000 Hz) |
| `min_duty_cycle` | int | Duty cycle mínimo (20-40%) |
| `max_duty_cycle` | int | Duty cycle máximo (80-100%) |
| `default_speed_percent` | int | Velocidad por defecto (0-100%) |

## Uso del Driver

### Inicialización Básica

```python
from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController

# Crear controlador
controller = ConveyorBeltController('config_l298n.json')

# Inicializar
await controller.initialize()
```

### Control de Motor

```python
# Iniciar motor hacia adelante al 75%
await controller.start_belt(75)

# Cambiar velocidad a 50%
await controller.set_speed(50)

# Detener motor
await controller.stop_belt()

# Parada de emergencia
await controller.emergency_stop()
```

### Control de Dirección (Avanzado)

```python
# Acceso directo al driver L298N
l298n_driver = controller.driver

# Movimiento hacia adelante
await l298n_driver.start_belt(60)

# Cambiar a reversa
await l298n_driver.reverse_direction(40)

# Frenado dinámico
await l298n_driver.emergency_brake()
```

### Monitoreo de Estado

```python
# Obtener estado completo
status = controller.get_status()
print(f"Ejecutándose: {status['status']['is_running']}")
print(f"Velocidad: {status['status']['speed_percent']}%")
print(f"Dirección: {status['status']['direction']}")

# Obtener métricas
metrics = controller.get_metrics()
print(f"Tiempo funcionamiento: {metrics['performance']['total_runtime_hours']}h")
print(f"Velocidad promedio: {metrics['performance']['avg_speed_percent']}%")
```

## Estados del Motor L298N

### Tabla de Verdad

| ENA | IN1 | IN2 | Estado del Motor |
|-----|-----|-----|------------------|
| PWM | HIGH | LOW | Giro hacia adelante |
| PWM | LOW | HIGH | Giro hacia atrás |
| PWM | LOW | LOW | Parado (libre) |
| PWM | HIGH | HIGH | Frenado dinámico |
| 0 | X | X | Parado (sin energía) |

### Estados del Driver

- **IDLE**: Motor detenido, listo para arrancar
- **RUNNING**: Motor en funcionamiento
- **STOPPING**: Motor deteniéndose
- **ERROR**: Error en el sistema
- **MAINTENANCE**: Modo mantenimiento

## API Específica del L298N

### Métodos Adicionales

```python
# Cambiar dirección manteniendo velocidad
await driver.reverse_direction(speed_percent)

# Frenado de emergencia con frenado dinámico
await driver.emergency_brake()

# Configurar dirección específica
await driver._set_direction("forward")  # "forward", "backward", "stop", "brake"
```

### Propiedades de Estado

```python
# Estado actual de dirección
direction = driver.current_direction  # "forward", "backward", "stop"

# Estado del motor
is_running = driver.motor_running  # True/False

# Duty cycle actual
duty_cycle = driver.current_duty_cycle  # 0.0-100.0
```

## Diagnóstico y Solución de Problemas

### Problemas Comunes

| Problema | Causa Posible | Solución |
|----------|---------------|----------|
| Motor no arranca | Duty cycle muy bajo | Aumentar `min_duty_cycle` a 30-40% |
| Motor muy lento | Tensión insuficiente | Verificar alimentación 12V |
| L298N se calienta | Corriente alta | Usar disipador, verificar motor |
| Dirección incorrecta | Cables invertidos | Intercambiar OUT1 y OUT2 |
| PWM irregular | Frecuencia muy alta | Reducir `pwm_frequency_hz` |

### Comandos de Diagnóstico

```python
# Verificar estado del driver
status = await driver.get_status()
if status.get("error"):
    print(f"Error: {status['error']}")

# Verificar configuración de pins
pins = status.get("pins", {})
print(f"ENA (PWM): GPIO {pins['ena_pwm']}")
print(f"IN1: GPIO {pins['in1']}")
print(f"IN2: GPIO {pins['in2']}")
```

## Mantenimiento y Cuidado

### Recomendaciones

1. **Disipador térmico**: Instalar en el L298N para operación continua
2. **Alimentación estable**: Usar fuente regulada de 12V/3A mínimo
3. **Conexiones firmes**: Verificar conexiones periódicamente
4. **Monitoreo**: Revisar métricas de temperatura y corriente

### Limpieza y Finalización

```python
# Siempre limpiar recursos al finalizar
await controller.cleanup()

# O usando context manager
async with ConveyorBeltController('config.json') as controller:
    await controller.initialize()
    # ... usar controlador ...
    # cleanup automático al salir
```

## Ejemplo Completo

Ver archivo `l298n_example.py` para ejemplos completos de uso incluyendo:

- Configuración automática
- Pruebas básicas y avanzadas
- Control de dirección
- Manejo de errores
- Diagrama de conexiones

## Integración con VisiFruit

El driver L298N se integra perfectamente con el sistema VisiFruit:

- **API unificada**: Misma interfaz que otros drivers
- **Monitoreo**: Métricas integradas en el dashboard
- **Configuración**: Via archivo JSON centralizado
- **Recuperación**: Sistema automático de recuperación de errores
- **Logging**: Registro detallado de eventos

## Soporte y Documentación

Para más información:
- Ver código fuente en `conveyor_belt_controller.py`
- Ejecutar ejemplos en `l298n_example.py`
- Consultar logs del sistema para diagnóstico
- Revisar métricas de rendimiento en tiempo real