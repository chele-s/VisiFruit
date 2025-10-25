# Control de Motor DC con Relays de 12V - Raspberry Pi 5

## Descripción General

Este documento describe la implementación del control de motor DC usando 2 relays de 12V con Raspberry Pi 5 para el sistema VisiFruit. Esta configuración es ideal para motores de banda transportadora que requieren control bidireccional simple y robusto.

## Características del Sistema

- ✅ **Compatible con Raspberry Pi 5**
- ✅ **Control bidireccional** (adelante/atrás)
- ✅ **Relays de 12V** para alta corriente
- ✅ **Protección contra cortocircuitos**
- ✅ **Timeout de seguridad**
- ✅ **Monitoreo en tiempo real**
- ✅ **Recuperación automática de errores**

## Esquema de Conexiones

### Diagrama Físico

```
                     RASPBERRY PI 5
                     ==============
                     │            │
         GPIO 18 ────┤ Pin 12     │
         GPIO 19 ────┤ Pin 35     │
         GPIO 26 ────┤ Pin 37     │ (Opcional)
              5V ────┤ Pin 2      │
             GND ────┤ Pin 6      │
                     │            │
                     └────────────┘
                           │
                           │ 5V/GND/Señales
                           │
                  ┌────────▼────────┐
                  │  MÓDULO RELAYS  │
                  │   2 CANALES     │
                  │                 │
                  │ VCC     Relay1  │────┐
                  │ GND     Relay2  │────┤
                  │ IN1             │    │
                  │ IN2             │    │
                  └─────────────────┘    │
                                         │
    ┌──────────────────────────────────────┘
    │
    │        RELAY 1 (ADELANTE)    RELAY 2 (ATRÁS)
    │        ================    ================
    │        │NC  COM   NO │    │NC  COM   NO │
    │        │ │   │    │  │    │ │   │    │  │
    └────────┤ └───┼────┘  │    │ └───┼────┘  │
             │     │       │    │     │       │
        12V+ ┴─────┘       │    │     └───────┴ 12V+
                           │    │
                    MOTOR  │    │  MOTOR
                      (+)──┘    └──(-)
                           
                    MOTOR DC 12V
                    ============
```

### Tabla de Conexiones

| Componente | Pin/Terminal | Conectar a | Función |
|------------|--------------|------------|---------|
| **Raspberry Pi 5** ||||
| GPIO 18 | Pin 12 | Relay IN1 | Control Relay 1 (Adelante) |
| GPIO 19 | Pin 35 | Relay IN2 | Control Relay 2 (Atrás) |
| GPIO 26 | Pin 37 | Enable | Habilitación (Opcional) |
| 5V | Pin 2 | Relay VCC | Alimentación lógica |
| GND | Pin 6 | Relay GND | Tierra común |
| **Módulo Relays** ||||
| Relay 1 NC | Terminal | 12V+ | Alimentación motor |
| Relay 1 COM | Terminal | Motor (+) | Terminal positivo motor |
| Relay 2 NC | Terminal | 12V+ | Alimentación motor |
| Relay 2 COM | Terminal | Motor (-) | Terminal negativo motor |
| **Fuente 12V** ||||
| 12V+ | Cable rojo | NC de ambos relays | Alimentación motor |
| 12V- | Cable negro | Motor GND/Chasis | Tierra motor |

## Principio de Funcionamiento

### Estados del Motor

| Relay 1 | Relay 2 | Estado Motor | Descripción |
|---------|---------|--------------|-------------|
| OFF | OFF | **PARADO** | Motor sin alimentación |
| ON | OFF | **ADELANTE** | Motor gira hacia adelante |
| OFF | ON | **ATRÁS** | Motor gira hacia atrás |
| ON | ON | **PROHIBIDO** | ⚠️ CORTOCIRCUITO |

### Lógica de Control

```python
# Adelante: Solo Relay 1 activo
GPIO.output(relay1_pin, GPIO.LOW)  # Relay 1 ON (activo bajo)
GPIO.output(relay2_pin, GPIO.HIGH) # Relay 2 OFF

# Atrás: Solo Relay 2 activo  
GPIO.output(relay1_pin, GPIO.HIGH) # Relay 1 OFF
GPIO.output(relay2_pin, GPIO.LOW)  # Relay 2 ON (activo bajo)

# Parado: Ambos relays OFF
GPIO.output(relay1_pin, GPIO.HIGH) # Relay 1 OFF
GPIO.output(relay2_pin, GPIO.HIGH) # Relay 2 OFF
```

## Configuración del Sistema

### Archivo de Configuración

```json
{
  "conveyor_belt_settings": {
    "control_type": "relay_motor",
    "relay1_pin_bcm": 18,
    "relay2_pin_bcm": 19, 
    "enable_pin_bcm": 26,
    "active_state_on": "LOW",
    "safety_timeout_s": 10.0,
    "direction_change_delay_s": 0.5
  }
}
```

### Parámetros de Configuración

| Parámetro | Tipo | Valor Recomendado | Descripción |
|-----------|------|-------------------|-------------|
| `relay1_pin_bcm` | int | 18 | Pin BCM para relay 1 (adelante) |
| `relay2_pin_bcm` | int | 19 | Pin BCM para relay 2 (atrás) |
| `enable_pin_bcm` | int | 26 | Pin de habilitación (opcional) |
| `active_state_on` | string | "LOW" | Lógica de activación de relays |
| `safety_timeout_s` | float | 10.0 | Timeout automático de seguridad |
| `direction_change_delay_s` | float | 0.5 | Delay entre cambios de dirección |

## Implementación de Código

### Uso Básico

```python
from Control_Etiquetado.relay_motor_controller import create_relay_motor_driver

# Crear driver
driver = create_relay_motor_driver(
    relay1_pin=18,  # Adelante
    relay2_pin=19,  # Atrás
    enable_pin=26   # Habilitación
)

# Inicializar
await driver.initialize()

# Usar motor
await driver.start_belt()        # Adelante
await asyncio.sleep(3)
await driver.reverse_direction() # Atrás 
await asyncio.sleep(3)
await driver.stop_belt()         # Parar

# Limpiar
await driver.cleanup()
```

### Integración con VisiFruit

```python
from Control_Etiquetado.conveyor_belt_controller import ConveyorBeltController

# Usar archivo de configuración
controller = ConveyorBeltController('config_relay_motor.json')
await controller.initialize()

# Control a través de la API estándar
await controller.start_belt()
await controller.stop_belt()
```

### Control Manual Avanzado

```python
# Acceso directo al driver de relays
relay_driver = controller.driver

# Control específico de relays
await relay_driver._set_relay_direction("forward")
await relay_driver._set_relay_direction("backward") 
await relay_driver._set_relay_direction("stop")

# Obtener estado de relays
status = await relay_driver.get_status()
print(f"Estado Relay 1: {status['relay_states']['relay1']}")
print(f"Estado Relay 2: {status['relay_states']['relay2']}")
```

## Características de Seguridad

### Protecciones Implementadas

1. **Anti-cortocircuito**: Nunca activa ambos relays simultáneamente
2. **Delay entre cambios**: Pausa de 0.5s entre cambios de dirección
3. **Timeout automático**: Para el motor después de 10s por defecto
4. **Estado seguro**: En caso de error, desactiva todos los relays
5. **Monitoreo**: Verifica estado de relays constantemente

### Funciones de Emergencia

```python
# Parada de emergencia inmediata
await driver.emergency_brake()

# Desactivar todos los relays
await driver._emergency_stop_relays()

# Verificar estado seguro
status = await driver.get_status()
assert not status['running']
```

## Especificaciones Técnicas

### Requisitos de Hardware

| Componente | Especificación | Recomendación |
|------------|----------------|---------------|
| **Raspberry Pi** | Pi 5 (compatible con Pi 4/3) | Pi 5 con 4GB RAM |
| **Módulo Relays** | 2 canales, 5V lógica | SRD-05VDC-SL-C |
| **Motor DC** | 12V, hasta 5A | 12V/60W máximo |
| **Fuente Motor** | 12V/5A mínimo | 12V/7A recomendado |
| **Fusible** | 7A para protección | Fusible rápido |

### Características Relays

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Tensión bobina | 5V DC | Alimentado desde RPi |
| Corriente bobina | 70mA | Por relay |
| Contactos | SPDT (1NO + 1NC) | Uso solo NC |
| Capacidad contactos | 10A/250VAC | 7A/30VDC recomendado |
| Tiempo conmutación | 10ms | Típico |
| Aislamiento | 4000V | Optoacoplado |

## Instalación y Puesta en Marcha

### 1. Preparación del Hardware

```bash
# Verificar GPIO de Raspberry Pi 5
gpio readall

# Instalar dependencias Python
pip install RPi.GPIO asyncio
```

### 2. Conexiones Físicas

1. **Conectar módulo de relays** según el diagrama
2. **Verificar alimentación** 5V para relays, 12V para motor
3. **Instalar fusible** de 7A en línea positiva del motor
4. **Verificar conexiones** antes de energizar

### 3. Prueba Inicial

```python
# Ejecutar prueba básica
python Control_Etiquetado/relay_motor_controller.py
```

### 4. Integración Completa

```python
# Usar con sistema VisiFruit completo
python main_etiquetadora.py --config config_relay_motor.json
```

## Diagnóstico y Solución de Problemas

### Problemas Comunes

| Problema | Causa Posible | Solución |
|----------|---------------|----------|
| Motor no responde | Conexiones flojas | Verificar todas las conexiones |
| Solo funciona una dirección | Relay defectuoso | Probar relays individualmente |
| RPi se reinicia | Sobrecarga 5V | Usar fuente RPi de 3A mínimo |
| Motor muy lento | Tensión baja | Verificar fuente 12V/5A |
| Relays no conmutan | GPIO mal configurado | Verificar pins BCM |

### Comandos de Diagnóstico

```python
# Verificar estado del sistema
status = await driver.get_status()
print(f"Sistema inicializado: {status['initialized']}")
print(f"Motor funcionando: {status['running']}")
print(f"Dirección actual: {status['direction']}")
print(f"Estado relays: {status['relay_states']}")

# Probar relays individualmente
await driver._set_relay_direction("forward")   # Solo relay 1
await asyncio.sleep(1)
await driver._set_relay_direction("backward")  # Solo relay 2  
await asyncio.sleep(1)
await driver._set_relay_direction("stop")      # Ninguno
```

### Logs de Sistema

```bash
# Ver logs en tiempo real
tail -f logs/fruprint_ultra_*.log | grep -i relay

# Buscar errores específicos
grep "ERROR" logs/fruprint_ultra_*.log | grep -i relay
```

## API REST para Control Remoto

### Endpoints Disponibles

```bash
# Iniciar motor adelante
curl -X POST http://raspberrypi:8000/control/start

# Parar motor
curl -X POST http://raspberrypi:8000/control/stop

# Parada de emergencia
curl -X POST http://raspberrypi:8000/control/emergency_stop

# Obtener estado
curl http://raspberrypi:8000/status
```

### Respuesta de Estado

```json
{
  "status": {
    "state": "running",
    "is_running": true,
    "direction": "forward",
    "control_type": "relay_motor"
  },
  "relay_states": {
    "relay1": "ON",
    "relay2": "OFF"
  },
  "pins": {
    "relay1_forward": 18,
    "relay2_backward": 19,
    "enable": 26
  }
}
```

## Mantenimiento

### Verificaciones Periódicas

1. **Contactos de relays**: Inspeccionar cada 6 meses
2. **Conexiones**: Apretar terminales cada 3 meses  
3. **Temperatura**: Verificar calentamiento excesivo
4. **Logs**: Revisar errores semanalmente

### Reemplazo de Relays

```python
# Probar relay individual antes de reemplazar
# Relay 1
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.LOW)  # Debería activar relay
time.sleep(1)
GPIO.output(18, GPIO.HIGH) # Debería desactivar relay

# Relay 2  
GPIO.setup(19, GPIO.OUT)
GPIO.output(19, GPIO.LOW)  # Debería activar relay
time.sleep(1)
GPIO.output(19, GPIO.HIGH) # Debería desactivar relay
```

## Ventajas del Sistema de Relays

### ✅ Ventajas

- **Simplicidad**: Configuración y uso muy sencillo
- **Robustez**: Resistente a ruido eléctrico
- **Aislamiento**: Protección galvánica del RPi
- **Alta corriente**: Maneja motores de hasta 5-7A
- **Bajo costo**: Componentes económicos
- **Mantenimiento**: Fácil diagnóstico y reparación

### ⚠️ Limitaciones

- **Sin control de velocidad**: Solo ON/OFF
- **Tiempo de conmutación**: ~10ms delay
- **Desgaste mecánico**: Contactos se desgastan
- **Ruido audible**: Click al conmutar

## Comparación con Otras Opciones

| Característica | Relays 12V | L298N | PWM Direct |
|----------------|------------|-------|------------|
| **Costo** | $ | $$ | $ |
| **Simplicidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Control velocidad** | ❌ | ✅ | ✅ |
| **Alta corriente** | ✅ (10A) | ⚠️ (2A) | ❌ |
| **Aislamiento** | ✅ | ❌ | ❌ |
| **Ruido** | ⚠️ Click | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Durabilidad** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Conclusión

El sistema de control con relays de 12V es **ideal para aplicaciones industriales** donde se requiere:

- ✅ Control bidireccional simple
- ✅ Alta robustez y aislamiento  
- ✅ Manejo de alta corriente
- ✅ Bajo costo y mantenimiento simple

Es la **opción recomendada** para sistemas de banda transportadora que no requieren control variable de velocidad pero necesitan máxima confiabilidad.
