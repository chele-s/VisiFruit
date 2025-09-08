# 🚀 Demos VisiFruit v3.0 RT-DETR

Colección de demos para probar los componentes del sistema VisiFruit de forma individual y completa.

## 📋 Demos Disponibles

### 🎮 Demo Sistema Completo
**Archivo:** `demo_sistema_completo.py`

Demo interactiva completa que integra todos los componentes:
- ✅ Motor DC banda transportadora (L298N/Relays)
- ✅ Driver DRV8825 stepper (real o simulado)
- ✅ Sensor láser YK0008
- ✅ Control completo por consola
- ✅ Estadísticas en tiempo real
- ✅ Modo simulación automático

```bash
python Control_Etiquetado/demo_sistema_completo.py
```

**Características:**
- Control interactivo por comandos
- Simulación automática si hardware no disponible
- Monitoreo láser con activación automática del stepper
- Demo automática con secuencia predefinida
- Estadísticas y métricas en tiempo real

### ⚡ Demo Prueba Rápida
**Archivo:** `demo_quick_test.py`

Pruebas rápidas de componentes individuales:

```bash
# Probar solo motor DC
python Control_Etiquetado/demo_quick_test.py motor

# Probar solo stepper DRV8825
python Control_Etiquetado/demo_quick_test.py stepper

# Probar solo sensor láser
python Control_Etiquetado/demo_quick_test.py laser

# Probar todos los componentes
python Control_Etiquetado/demo_quick_test.py all
```

### 🎢 Demo Relay Motor (Original)
**Archivo:** `demo_relay_motor.py`

Demo completa del motor DC con relays:
- Control manual interactivo
- Demo automática con secuencias
- Pruebas de seguridad
- Compatibilidad Pi5 y legacy

```bash
python Control_Etiquetado/demo_relay_motor.py
```

### 🔧 Demo Relay Simple
**Archivo:** `demo_relay_forward_simple.py`

Demo básica: solo motor adelante por 5 segundos.

```bash
python Control_Etiquetado/demo_relay_forward_simple.py
```

### 📡 Demo Láser + Stepper
**Archivo:** `demo_laser_stepper.py`

Demo específica de integración láser-stepper:
- Monitoreo continuo del sensor láser
- Activación automática del stepper al detectar trigger
- Configuración desde `Config_Etiquetadora.json`

```bash
python Control_Etiquetado/demo_laser_stepper.py
```

## 🎛️ Comandos Demo Sistema Completo

### 🎢 Control Banda Transportadora
- `B1` - Iniciar banda ADELANTE
- `B2` - Iniciar banda ATRÁS  
- `B0` - PARAR banda

### 🔧 Control Stepper DRV8825
- `S1` - Activar stepper manualmente
- `S0` - Toggle habilitación láser→stepper
- `SS` - Configurar parámetros stepper

### 📡 Control Sensor MH Flying Fish
- `L1` - Iniciar monitoreo sensor
- `L0` - Parar monitoreo sensor  
- `LT` - Simular trigger sensor
- `LD` - Diagnóstico sensor (lecturas en tiempo real)

### 🔧 Sistema
- `I` - Mostrar información detallada
- `D` - Demo automática completa
- `R` - Resetear estadísticas
- `Q` - Salir

## ⚙️ Configuración

Las demos utilizan `Config_Etiquetadora.json` para la configuración de pines y parámetros:

```json
{
  "sensor_settings": {
    "trigger_sensor": {
      "type": "laser_yk0008",
      "pin_bcm": 17,
      "trigger_level": "falling",
      "debounce_time_ms": 30,
      "pull_up_down": "PUD_UP"
    }
  },
  "laser_stepper_settings": {
    "enabled": true,
    "step_pin_bcm": 19,
    "dir_pin_bcm": 26,
    "enable_pin_bcm": 21,
    "base_speed_sps": 1500,
    "activation_on_laser": {
      "enabled": true,
      "activation_duration_seconds": 0.6,
      "intensity_percent": 80.0,
      "min_interval_seconds": 0.15
    }
  },
  "conveyor_belt_settings": {
    "relay1_pin": 18,
    "relay2_pin": 19,
    "enable_pin": 26
  }
}
```

## 🔌 Conexiones Hardware

### Motor DC (L298N/Relays)
- **Relay 1 (Adelante):** GPIO 18
- **Relay 2 (Atrás):** GPIO 19  
- **Enable:** GPIO 26

### DRV8825 Stepper
- **STEP:** GPIO 19
- **DIR:** GPIO 26
- **EN:** GPIO 21 (activo bajo)
- **Alimentación:** 12V para VMOT, 3.3V para lógica

### Sensor MH Flying Fish
- **Señal:** GPIO 4 (cambiado desde GPIO 17 para mejor detección)
- **VCC:** 3.3V (recomendado)
- **Funcionamiento:** HIGH sin detección (~2.7V), LOW con detección (~0.1V)
- **GND:** GND
- **Pull-up:** Interno (PUD_UP)

## 🎭 Modo Simulación

Todas las demos incluyen modo simulación automático:
- ✅ Se activa si hardware no disponible
- ✅ Simula todas las funciones
- ✅ Ideal para desarrollo en Windows
- ✅ Permite probar lógica sin hardware

## 🔍 Troubleshooting

### Error "Módulos no disponibles"
```bash
# Instalar dependencias
pip install -r requirements.txt

# Para Raspberry Pi específicamente
pip install RPi.GPIO lgpio
```

### Error GPIO "Permission denied"
```bash
# Ejecutar con sudo en Raspberry Pi
sudo python Control_Etiquetado/demo_sistema_completo.py
```

### Hardware no responde
1. Verificar conexiones GPIO
2. Verificar alimentación (12V para motores)
3. Comprobar pines en configuración
4. Usar modo simulación para probar lógica

## 📊 Estadísticas Demo

La demo del sistema completo proporciona:
- 🔴 **Triggers láser:** Contador de detecciones
- 🔧 **Activaciones stepper:** Contador de activaciones exitosas  
- 🎢 **Inicios banda:** Contador de arranques del motor
- ⏱️ **Tiempo activo:** Uptime del sistema
- 📊 **Tasa triggers:** Triggers por minuto

## 🚀 Uso Recomendado

1. **Desarrollo inicial:** `demo_quick_test.py` para probar componentes
2. **Pruebas hardware:** `demo_relay_forward_simple.py` para motor básico
3. **Integración:** `demo_laser_stepper.py` para láser + stepper
4. **Sistema completo:** `demo_sistema_completo.py` para operación total
5. **Producción:** `main_etiquetadora.py` para sistema completo RT-DETR

## 📝 Notas

- Las demos son compatibles con Raspberry Pi 5 (lgpio) y versiones anteriores (RPi.GPIO)
- El modo simulación permite desarrollo en Windows/Linux sin hardware
- Todas las configuraciones son modificables en `Config_Etiquetadora.json`
- Los pines GPIO son configurables y siguen numeración BCM

---

**VisiFruit v3.0 RT-DETR** - Sistema inteligente de etiquetado con IA Transformer 🍎🤖
