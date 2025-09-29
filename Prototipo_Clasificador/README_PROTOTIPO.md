# 🧠 VisiFruit - Sistema Inteligente de Clasificación con IA (Prototipo)

Sistema completo de clasificación automática de frutas que integra **Inteligencia Artificial**, **etiquetadora DRV8825** y **servomotores MG995** para clasificación por categorías.

---

## 🎯 Características Principales

### Hardware Utilizado
- **🤖 IA de Detección**: RT-DETR / YOLO para reconocimiento de frutas
- **🏷️ Etiquetadora**: Motor stepper con driver DRV8825
- **🔄 Clasificación**: 3 servomotores MG995 (uno por categoría)
- **🎚️ Banda Transportadora**: Control con relays
- **📷 Cámara**: Visión por computadora para detección

### Categorías Soportadas
- 🍎 **Manzanas** (Apple) → Servo 1 → Pin BCM 17
- 🍐 **Peras** (Pear) → Servo 2 → Pin BCM 27
- 🍋 **Limones** (Lemon) → Servo 3 → Pin BCM 22

---

## 🚀 Flujo de Operación

```
1. Fruta en banda → 2. Cámara captura → 3. IA detecta clase
        ↓
4. DRV8825 etiqueta → 5. Tiempo de viaje → 6. MG995 clasifica
        ↓
7. Fruta cae en caja correspondiente
```

### Temporización Automática
El sistema calcula automáticamente los delays basándose en:
- Velocidad de la banda (m/s)
- Distancia cámara-etiquetadora
- Distancia etiquetadora-clasificador
- Tiempo de respuesta del servo

**Ejemplo con banda a 0.2 m/s:**
- Distancia cámara → clasificador: 0.5m
- Delay automático: 2.5 segundos

---

## 📦 Instalación

### Requisitos de Hardware
```
Raspberry Pi 4/5 con:
- GPIO disponibles
- Cámara USB o Pi Camera
- Alimentación 5V 3A+ para servos
- Driver DRV8825 con disipador
```

### Instalación de Software

#### 1. Dependencias del Sistema
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias de Python
sudo apt install python3-pip python3-opencv python3-numpy -y

# pigpio para control PWM preciso
sudo apt install pigpio python3-pigpio -y
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

#### 2. Dependencias de Python
```bash
cd Prototipo_Clasificador

# Instalar requirements
pip3 install -r requirements.txt

# O manualmente:
pip3 install numpy opencv-python torch ultralytics
pip3 install pigpio RPi.GPIO asyncio
pip3 install psutil logging
```

#### 3. Permisos GPIO
```bash
sudo usermod -a -G gpio $USER
sudo chmod 666 /dev/gpiomem
```

---

## ⚙️ Configuración

### Archivo de Configuración: `Config_Prototipo.json`

#### Configurar Pines de Servos
```json
"servo_settings": {
  "apple": {
    "pin_bcm": 17,
    "activation_angle": 90,
    "activation_duration_s": 1.0
  },
  "pear": {
    "pin_bcm": 27,
    "activation_angle": 90
  },
  "lemon": {
    "pin_bcm": 22,
    "activation_angle": 90
  }
}
```

#### Configurar DRV8825
```json
"labeler_settings": {
  "step_pin_bcm": 19,
  "dir_pin_bcm": 26,
  "enable_pin_bcm": 21,
  "base_speed_sps": 1500,
  "activation_duration_seconds": 0.6
}
```

#### Ajustar Temporización
```json
"timing": {
  "belt_speed_mps": 0.2,
  "camera_to_classifier_distance_m": 0.5,
  "min_detection_interval_s": 0.5
}
```

---

## 🎮 Uso

### Inicio Rápido
```bash
# Desde la carpeta principal del proyecto
python3 Prototipo_Clasificador/smart_classifier_system.py
```

### Prueba de Componentes Individuales

#### Probar Servomotores
```bash
python3 Prototipo_Clasificador/mg995_servo_controller.py
```

#### Verificar Configuración
```bash
python3 -c "import json; print(json.load(open('Prototipo_Clasificador/Config_Prototipo.json')))"
```

---

## 🔧 Calibración

### 1. Calibración de Servos

Ajustar ángulos para cada servo según la mecánica:

```python
# En Config_Prototipo.json
"servo_settings": {
  "apple": {
    "default_angle": 0,      # Posición cerrada
    "activation_angle": 90,  # Posición abierta
    "invert": false          # true si servo está invertido
  }
}
```

### 2. Calibración de Temporización

**Medir distancias reales:**
```bash
# Medir con cinta métrica:
# - Cámara → Etiquetadora
# - Etiquetadora → Clasificador (servos)

# Actualizar en Config_Prototipo.json
"timing": {
  "camera_to_classifier_distance_m": 0.5  # TU MEDIDA AQUÍ
}
```

**Probar velocidad de banda:**
```bash
# Marcar fruta, medir tiempo que tarda en recorrer 1 metro
# Velocidad = distancia / tiempo
# Ejemplo: 1m en 5s = 0.2 m/s

"belt_speed_mps": 0.2  # TU VELOCIDAD AQUÍ
```

### 3. Calibración de IA

**Ajustar umbral de confianza:**
```json
"ai_settings": {
  "confidence_threshold": 0.6  // Bajar si muchas detecciones se pierden
                                // Subir si hay muchos falsos positivos
}
```

---

## 📊 Monitoreo y Estadísticas

El sistema muestra estadísticas cada 10 segundos:

```
📊 Detectadas: 150 | Etiquetadas: 148 | Clasificadas: 145
   🍎 Manzanas: 50 | 🍐 Peras: 60 | 🍋 Limones: 40
```

### Logs Detallados
```bash
# Ver logs en tiempo real
tail -f logs/prototipo_clasificador.log

# Ver últimos errores
grep ERROR logs/prototipo_clasificador.log | tail -20
```

---

## 🛠️ Solución de Problemas

### Servos no responden
```bash
# 1. Verificar pigpiod
sudo systemctl status pigpiod

# 2. Verificar alimentación
# Los MG995 necesitan 4.8-7.2V y hasta 2A por servo

# 3. Test manual
python3 -c "import pigpio; pi = pigpio.pi(); pi.set_servo_pulsewidth(17, 1500); print('OK')"
```

### DRV8825 no funciona
```bash
# 1. Verificar conexiones
# 2. Verificar voltaje VMOT (8-35V)
# 3. Ajustar potenciómetro de corriente
# 4. Verificar enable_active_low en config
```

### IA no detecta correctamente
```bash
# 1. Verificar modelo existe
ls -lh IA_Etiquetado/Dataset_Frutas/best.pt

# 2. Probar con umbral más bajo
# Editar Config_Prototipo.json: "confidence_threshold": 0.4

# 3. Verificar iluminación de la cámara
# 4. Re-entrenar modelo si es necesario
```

### Sincronización incorrecta
```bash
# 1. Medir distancias reales con cinta métrica
# 2. Cronometrar velocidad real de la banda
# 3. Ajustar valores en "timing" de la config
# 4. Hacer pruebas con frutas marcadas
```

---

## 🔐 Seguridad

### Parada de Emergencia
- **Ctrl+C**: Detención ordenada del sistema
- **Parada de emergencia**: Desactiva inmediatamente todos los actuadores

### Límites de Seguridad
```json
"safety": {
  "max_continuous_activations": 10,  // Previene sobrecalentamiento
  "overheat_protection": true,
  "watchdog_timeout_s": 30
}
```

---

## 📈 Optimización

### Para Mayor Velocidad
```json
"timing": {
  "belt_speed_mps": 0.3,  // Aumentar gradualmente
  "min_detection_interval_s": 0.3  // Reducir intervalo
}
```

### Para Mayor Precisión
```json
"ai_settings": {
  "confidence_threshold": 0.7,  // Más estricto
  "enable_tracking": true  // Seguimiento de objetos
}
```

---

## 🎓 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────┐
│       SmartFruitClassifier (Cerebro)           │
├─────────────────────────────────────────────────┤
│                                                 │
│  📷 CameraController ─→ 🤖 EnterpriseFruitDetector
│                              ↓
│                       [Detección: manzana]
│                              ↓
│  🏷️ LabelerActuator (DRV8825) ← [Etiquetar]
│                              ↓
│                      [Delay calculado]
│                              ↓
│  🔄 MG995ServoController ← [Clasificar]
│         ├─→ Servo Manzanas (BCM 17)
│         ├─→ Servo Peras (BCM 27)
│         └─→ Servo Limones (BCM 22)
│                              ↓
│                  [Fruta cae en caja]
└─────────────────────────────────────────────────┘
```

---

## 🆚 Diferencias con Versión Profesional

| Característica | Prototipo | Profesional |
|----------------|-----------|-------------|
| Etiquetadoras | 1 (DRV8825) | 6 (2 por categoría) |
| Clasificación | Servos MG995 | Desviadores neumáticos |
| Motor posicionamiento | No | Motor DC lineal |
| Costo | $ | $$$ |
| Complejidad | Baja | Alta |
| Producción | ~20-30 frutas/min | ~100+ frutas/min |
| Ideal para | Pruebas, educación | Producción industrial |

---

## 📚 Referencias

- **RT-DETR**: https://github.com/lyuwenyu/RT-DETR
- **MG995 Datasheet**: https://datasheetspdf.com/pdf/791970/TowerPro/MG995/1
- **DRV8825**: https://www.ti.com/product/DRV8825
- **pigpio**: http://abyz.me.uk/rpi/pigpio/

---

## 🤝 Contribuciones

Desarrollado por: Gabriel Calderón, Elias Bautista, Cristian Hernandez

---

## 📝 Notas de Versión

### v1.0.0 (Septiembre 2025)
- ✅ Sistema inicial con IA + DRV8825 + MG995
- ✅ Clasificación automática en 3 categorías
- ✅ Sincronización temporal automática
- ✅ Modo simulación para desarrollo
- ✅ Estadísticas en tiempo real

---

## 🔮 Próximas Mejoras

- [ ] Interfaz web para monitoreo remoto
- [ ] Sistema de aprendizaje continuo
- [ ] Soporte para más categorías
- [ ] Detección de calidad de frutas
- [ ] Base de datos de trazabilidad
- [ ] API REST para integración

---

**¡Sistema listo para clasificar frutas inteligentemente! 🍎🍐🍋**
