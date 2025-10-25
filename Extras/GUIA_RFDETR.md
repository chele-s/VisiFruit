# 🚀 Guía Rápida: RF-DETR en VisiFruit

## ¿Qué es RF-DETR?

**RF-DETR** (Roboflow Detection Transformer) es un modelo de detección de objetos de última generación desarrollado por Roboflow:

- ✅ **SOTA Performance**: Primer modelo real-time en superar 60 AP en COCO
- ⚡ **Ultra-Rápido**: Más rápido que YOLOv8 y RT-DETR en la mayoría de escenarios
- 🎯 **Alta Precisión**: Mejor adaptabilidad a problemas del mundo real (RF100-VL benchmark)
- 📦 **Fácil de usar**: Instalación simple, API intuitiva
- 🆓 **Open Source**: Licencia Apache 2.0

## 📊 Comparación de Modelos

| Modelo | Velocidad | Precisión | Uso Recomendado |
|--------|-----------|-----------|-----------------|
| **YOLOv8** | ⚡⚡⚡ Muy Rápido | ⭐⭐⭐ Buena | Tiempo real, edge devices |
| **RT-DETR** | ⚡⚡ Rápido | ⭐⭐⭐⭐ Muy Buena | Balance precisión/velocidad |
| **RF-DETR** | ⚡⚡⚡ Muy Rápido | ⭐⭐⭐⭐⭐ Excelente | SOTA, máximo rendimiento |

## 🔧 Instalación

### 1. Instalar RF-DETR

Activa tu entorno virtual y ejecuta:

```bash
# Windows (PowerShell)
& venv_server\Scripts\Activate.ps1
pip install rfdetr

# Linux/Mac
source venv_server/bin/activate
pip install rfdetr
```

### 2. Configurar `.env`

Crea o edita tu archivo `.env` basándote en `.env.example`:

```bash
# Copiar plantilla
cp .env.example .env
```

Edita `.env` y configura:

```env
# Usar RF-DETR
MODEL_TYPE=rfdetr

# Variante del modelo (nano, small, medium, base)
RFDETR_VARIANT=base

# Opcional: ruta a pesos personalizados
# Si no existe, usa checkpoint pre-entrenado de Roboflow COCO
MODEL_PATH=weights/best.pt

# GPU recomendada para mejor rendimiento
MODEL_DEVICE=cuda
MODEL_FP16=true
```

## 📦 Variantes de RF-DETR

RF-DETR viene en 4 variantes con diferentes balances velocidad/precisión:

### **Nano** - Máxima Velocidad
```env
RFDETR_VARIANT=nano
```
- **Velocidad**: ~150 FPS (RTX 3090)
- **mAP**: ~50-52% (COCO)
- **Uso**: Edge devices, máximo FPS
- **Parámetros**: ~3M

### **Small** - Balanceado
```env
RFDETR_VARIANT=small
```
- **Velocidad**: ~100 FPS
- **mAP**: ~55-57% (COCO)
- **Uso**: Balance óptimo para la mayoría de casos
- **Parámetros**: ~9M

### **Medium** - Alta Precisión
```env
RFDETR_VARIANT=medium
```
- **Velocidad**: ~70 FPS
- **mAP**: ~58-60% (COCO)
- **Uso**: Cuando necesitas más precisión
- **Parámetros**: ~20M

### **Base** - SOTA (Recomendado)
```env
RFDETR_VARIANT=base
```
- **Velocidad**: ~40-50 FPS
- **mAP**: ~60-62% (COCO)
- **Uso**: Máxima precisión disponible
- **Parámetros**: ~40M

## 🎯 Uso Básico

### Opción 1: Usar Checkpoint Pre-entrenado (COCO)

Perfecto para probar el modelo o si no tienes pesos custom:

```env
MODEL_TYPE=rfdetr
RFDETR_VARIANT=base
# No necesitas MODEL_PATH - usa checkpoint de Roboflow
```

El modelo viene pre-entrenado en el dataset COCO (80 clases) de Roboflow.

### Opción 2: Usar Pesos Personalizados (Fine-tuned)

Si has entrenado tu propio modelo RF-DETR:

```env
MODEL_TYPE=rfdetr
RFDETR_VARIANT=base
MODEL_PATH=weights/rfdetr_frutas.pt  # tus pesos fine-tuned
```

## 🚀 Ejecutar el Servidor

```bash
# Windows
& venv_server\Scripts\Activate.ps1
python ai_inference_server.py

# Linux/Mac
source venv_server/bin/activate
python ai_inference_server.py
```

Deberías ver en los logs:

```
🔄 Cargando modelo RF-DETR-Base
📦 Usando checkpoint pre-entrenado de Roboflow COCO
⚡ Modelo optimizado para inferencia (hasta 2x más rápido)
✅ Modelo RF-DETR-Base cargado y listo
```

## 🎨 Características Especiales de RF-DETR

### 1. Optimización Automática

RF-DETR incluye `.optimize_for_inference()` que acelera hasta 2x:

```python
# El servidor lo hace automáticamente
model.optimize_for_inference()
```

### 2. Formato de Entrada Flexible

RF-DETR acepta múltiples formatos:
- PIL Images
- NumPy arrays (RGB)
- Torch tensors
- Rutas de archivos

El servidor maneja la conversión automáticamente.

### 3. Salida en Formato Supervision

RF-DETR usa `supervision.Detections` nativamente, lo que facilita el post-procesamiento y visualización.

## 📈 Rendimiento Esperado

Con una **RTX 3050 Ti Laptop**:

| Variante | FPS Esperado | Latencia |
|----------|--------------|----------|
| Nano | ~80-100 | ~10-12ms |
| Small | ~60-70 | ~14-16ms |
| Medium | ~40-50 | ~20-25ms |
| Base | ~25-35 | ~28-40ms |

*Con FP16 habilitado y `optimize_for_inference()`*

## 🔄 Entrenar Tu Propio Modelo RF-DETR

### Usando Roboflow Train (Recomendado)

1. Sube tu dataset a [Roboflow](https://roboflow.com)
2. Selecciona "Train" > "RF-DETR"
3. Descarga los pesos entrenados
4. Configura `MODEL_PATH` con tus pesos

### Usando `rfdetr` Python Package

```python
from rfdetr import RFDETRBase
from roboflow import Roboflow

# Cargar dataset
rf = Roboflow(api_key="TU_API_KEY")
project = rf.workspace().project("frutas")
dataset = project.version(1).download("yolov8")

# Entrenar
model = RFDETRBase()
model.train(
    data="frutas/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16
)

# Guardar pesos
model.save("weights/rfdetr_frutas.pt")
```

## 🐛 Solución de Problemas

### Error: "RF-DETR no está instalado"

```bash
pip install rfdetr
```

### Error: "No se pudieron cargar pesos custom"

Verifica que:
1. El archivo `MODEL_PATH` existe
2. Los pesos son compatibles con la variante seleccionada
3. Los pesos están en formato PyTorch (.pt)

El servidor automáticamente fallback a checkpoint pre-entrenado si hay error.

### Rendimiento bajo

1. Verifica que `MODEL_DEVICE=cuda` y GPU esté disponible
2. Habilita `MODEL_FP16=true`
3. Considera usar una variante más pequeña (small/nano)
4. Cierra otras aplicaciones que usen GPU

### Colores invertidos en stream

Ya está corregido en la última versión. El servidor convierte automáticamente BGR→RGB para el stream MJPEG.

## 📚 Referencias

- **GitHub**: https://github.com/roboflow/rf-detr
- **Blog Post**: https://blog.roboflow.com/rf-detr/
- **Documentación**: https://rfdetr.roboflow.com/
- **Paper**: Próximamente en arXiv

## 💡 Consejos

1. **Para desarrollo/testing**: Usa `RFDETR_VARIANT=small` - buen balance
2. **Para producción**: Usa `RFDETR_VARIANT=base` - máxima precisión
3. **Para edge devices**: Usa `RFDETR_VARIANT=nano` - máxima velocidad
4. **Con GPU potente**: Usa `base` con FP16 para mejor rendimiento
5. **Sin GPU**: Considera YOLOv8 que es más optimizado para CPU

## 🔄 Cambiar entre Modelos

Es fácil cambiar entre diferentes modelos editando `.env`:

```bash
# YOLOv8 (rápido, probado)
MODEL_TYPE=yolov8
MODEL_PATH=weights/best.pt

# RT-DETR (transformer, preciso)
MODEL_TYPE=rtdetr
MODEL_PATH=weights/rtdetr_best.pt

# RF-DETR (SOTA, lo mejor de ambos)
MODEL_TYPE=rfdetr
RFDETR_VARIANT=base
```

Reinicia el servidor para aplicar cambios:
```bash
# CTRL+C para detener
python ai_inference_server.py
```

---

**¡Listo!** Ahora tienes RF-DETR integrado en tu sistema VisiFruit 🎉

Para más información, consulta la [documentación oficial](https://rfdetr.roboflow.com/).
