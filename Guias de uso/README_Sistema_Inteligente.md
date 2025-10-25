# Sistema de Detección Posicional Inteligente - VisiFruit 🍎🤖

## Descripción General

El Sistema de Detección Posicional Inteligente resuelve el problema fundamental de **cómo saber exactamente cuándo y por cuánto tiempo activar los etiquetadores** basándose en la distribución espacial real de las frutas detectadas.

### 🧠 **¿Cómo Funciona la Inteligencia?**

En lugar de usar tiempos fijos, el sistema:

1. **📸 Detecta** frutas individuales con YOLO
2. **🔍 Analiza** su distribución espacial (filas y columnas)
3. **📊 Agrupa** frutas cercanas en clústeres inteligentes
4. **⏱️ Calcula** tiempos de activación específicos para cada grupo
5. **🎯 Activa** etiquetadores con precisión adaptativa

## ✨ **Ventajas del Sistema Inteligente**

### Antes (Sistema Clásico):
- ❌ Tiempo fijo para todas las situaciones
- ❌ No considera distribución de frutas
- ❌ Desperdicia tiempo y etiquetas
- ❌ Difícil calibración manual

### Ahora (Sistema Inteligente):
- ✅ **Tiempo adaptativo** basado en distribución real
- ✅ **Detecta agrupaciones** (3 en línea, 2 en ancho, etc.)
- ✅ **Optimiza recursos** (tiempo exacto necesario)
- ✅ **Calibración visual** fácil e intuitiva

## 🚀 **Casos de Uso Prácticos**

### Escenario 1: 3 Manzanas en Línea
```
Detección: 3 frutas en columna (dirección de movimiento)
Cálculo: Tiempo base + 2×tiempo_adicional + margen
Resultado: Activación de 500ms (en lugar de 200ms fijo)
```

### Escenario 2: 2 Naranjas en Ancho + 1 Uva
```
Detección: 2 clústeres separados
Clúster 1: 2 frutas lado a lado → 350ms
Clúster 2: 1 fruta solitaria → 200ms
Resultado: 2 activaciones independientes con delays precisos
```

### Escenario 3: Grupo Mixto 2×3
```
Detección: 6 frutas en formación 2 filas × 3 columnas
Cálculo: Factor espacial 1.5× por distribución compleja
Resultado: Activación extendida de 800ms con movimiento lateral
```

## 📁 **Estructura del Sistema**

```
IA_Etiquetado/
├── smart_position_detector.py     # 🧠 Motor inteligente principal
├── visual_calibrator.py           # 🎛️ Interfaz de calibración visual
├── integration_example.py         # 🔗 Sistema integrado completo
├── Train_Yolo.py                  # 🏋️ Entrenamiento de modelos
└── README_Sistema_Inteligente.md  # 📖 Esta documentación
```

## 🎛️ **Calibración Visual**

### Características del Calibrador:
- **🖱️ Interfaz gráfica** con sliders en tiempo real
- **📐 ROI visual** configurable arrastrando
- **📏 Conversión automática** píxeles ↔ metros
- **🎯 Vista previa** de posiciones cámara/etiquetador
- **💾 Presets** para configuraciones comunes
- **📊 Calculadora** de tiempos en tiempo real

### Parámetros Configurables:
1. **Dimensiones Físicas**
   - Ancho/largo de banda
   - Velocidad de movimiento
   - Posiciones de componentes

2. **Agrupación de Frutas**
   - Distancia máxima para agrupar
   - Número mínimo por grupo

3. **Tiempos de Activación**
   - Tiempo base por fruta
   - Tiempo adicional por fruta extra
   - Margen de seguridad

## 🔧 **Instalación y Uso**

### 1. Dependencias
```bash
pip install ultralytics torch torchvision pillow opencv-python
pip install scikit-learn matplotlib tkinter numpy
```

### 2. Ejecutar Sistema Completo
```bash
python IA_Etiquetado/integration_example.py
```

### 3. Ejecutar Solo Calibrador Visual
```bash
python IA_Etiquetado/visual_calibrator.py
```

### 4. Probar Detección Inteligente
```bash
python IA_Etiquetado/smart_position_detector.py
```

## 📊 **Menú Principal del Sistema**

```
SISTEMA INTEGRADO VISIFRUIT - DETECCIÓN INTELIGENTE
==================================================
1. Demo completo (YOLO + Detección Inteligente + Banda)
2. Solo sincronización posicional (clásica)
3. Prueba detección inteligente
4. Calibrador visual
5. Entrenar modelo YOLO
6. Mostrar información de timing
0. Salir
```

## 🧮 **Fórmulas Matemáticas**

### Cálculo de Delay Base:
```python
delay_base = distancia_camara_etiquetador / velocidad_banda
# Ejemplo: 0.6m / 0.15m/s = 4.0s
```

### Tiempo de Activación Inteligente:
```python
tiempo_activacion = (
    tiempo_base + 
    (num_frutas - 1) × tiempo_por_fruta_extra
) × factor_espacial + margen_seguridad

# Factores espaciales:
# - Múltiples filas: +30% por fila adicional
# - Múltiples columnas: +20% por columna adicional  
# - Alta densidad (>20 frutas/m²): +40%
```

### Conversión Píxeles ↔ Metros:
```python
pixeles_por_metro = ancho_roi_px / ancho_banda_m
# Ejemplo: 1520px / 0.25m = 6080 px/m

mundo_x_m = (pixel_x - roi_x) / pixeles_por_metro
mundo_y_m = (pixel_y - roi_y) / pixeles_por_metro
```

## 📈 **Estadísticas y Métricas**

El sistema proporciona métricas avanzadas:

- **🎬 Frames procesados**: Total de imágenes analizadas
- **🍎 Frutas detectadas**: Detecciones individuales
- **📦 Grupos detectados**: Clústeres inteligentes formados  
- **🔢 Tamaño promedio grupo**: Frutas por clúster
- **🧠 Activaciones inteligentes**: Comandos de activación generados
- **⏱️ Tiempo total activación**: Duración acumulada
- **⚡ Eficiencia detección**: % frutas etiquetadas correctamente
- **🎯 Eficiencia agrupación**: % grupos procesados exitosamente

## 🔗 **Integración con Hardware**

### L298N Motor Driver:
```python
# Ejemplo de activación inteligente para L298N
async def _activate_smart_labeler(duration_s, cluster_info):
    if cluster_info['rows'] > 1:
        # Activar servo para movimiento lateral
        await servo_controller.move_lateral()
    
    if cluster_info['cols'] > 1:
        # Activación extendida para múltiples columnas
        await l298n_driver.start_belt(speed=75)
        await asyncio.sleep(duration_s)
        await l298n_driver.stop_belt()
```

### Sistema de Etiquetado:
```python
# Integración con labeler_actuator.py
from Control_Etiquetado.labeler_actuator import LabelerActuator

labeler = LabelerActuator(config)
await labeler.activate_smart_labeling(
    duration_ms=int(duration_s * 1000),
    pattern=cluster_info['rows'],
    intensity=cluster_info['fruit_count']
)
```

## 🎯 **Configuración para tu Maqueta 1m x 0.25m**

### Configuración Recomendada:
```json
{
  "belt_width_m": 0.25,
  "belt_length_m": 1.0,
  "belt_speed_mps": 0.15,
  "camera_position_x_m": 0.125,
  "camera_position_y_m": 0.2,
  "etiquetador_position_y_m": 0.8,
  "cluster_eps_m": 0.08,
  "base_activation_time_ms": 200,
  "time_per_additional_fruit_ms": 150,
  "safety_margin_ms": 50
}
```

### Tiempos Calculados:
- **1 fruta**: 250ms activación (200+50)
- **3 frutas**: 550ms activación (200+300+50)
- **5 frutas**: 850ms activación (200+600+50)

## 🔍 **Troubleshooting**

### Problema: Grupos no se detectan correctamente
**Solución**: Ajustar `cluster_eps_m` en calibrador visual
- Frutas muy separadas: Aumentar a 0.10-0.12m
- Frutas muy juntas: Reducir a 0.05-0.06m

### Problema: Activaciones muy largas/cortas
**Solución**: Calibrar tiempos base en pestaña "Tiempos"
- Etiquetado rápido: Reducir `base_activation_time_ms`
- Etiquetado lento: Aumentar `time_per_additional_fruit_ms`

### Problema: ROI no cubre área correcta
**Solución**: Usar calibrador visual para ajustar ROI
- Arrastrar bordes del ROI verde en la imagen
- Usar presets predefinidos como punto de partida

## 🚀 **Próximas Mejoras**

1. **🎥 Tracking de frutas** entre frames para mayor precisión
2. **📱 App móvil** para calibración remota  
3. **☁️ Análisis en la nube** para optimización continua
4. **🤖 Machine Learning** para predicción de patrones
5. **📊 Dashboard web** con métricas en tiempo real

## 📞 **Soporte**

Para preguntas o problemas:
- 📧 Email: soporte@visifruit.com
- 📱 WhatsApp: +52 123 456 7890
- 🌐 Web: https://visifruit.com/soporte

---

**¡El futuro del etiquetado inteligente está aquí! 🚀🍎**