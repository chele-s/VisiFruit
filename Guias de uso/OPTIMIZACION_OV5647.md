# 📷 Optimización OV5647 + YOLOv8 - VisiFruit

Sistema optimizado para detección de frutas con cámara OV5647 y YOLOv8 en Raspberry Pi 5.

## 🎯 Características de la Optimización

### 1. **Driver Picamera2 Mejorado**
- ✅ Detección automática del modelo de cámara (OV5647)
- ✅ Resolución nativa óptima: **1296x972** @ 30 FPS
- ✅ Formato RGB888 para mejor calidad de color
- ✅ Auto-exposición optimizada para objetos en movimiento
- ✅ Balance de blancos automático
- ✅ Reducción de ruido de alta calidad
- ✅ Warmup automático para estabilización AE/AWB

### 2. **Pre-procesamiento Inteligente**
- 🎨 Corrección automática de brillo y contraste
- 🔍 Mejora adaptativa de nitidez
- 🌈 Corrección de balance de color
- 🧹 Reducción de ruido preservando bordes
- ⚡ Procesamiento optimizado para baja latencia

### 3. **Integración YOLOv8 Optimizada**
- 🤖 Inferencia CPU ultra-optimizada para Raspberry Pi 5
- 🚀 Dual-worker para máximo throughput
- 📊 Input size balanceado: 640x640
- 🎯 Confidence threshold ajustado: 0.35
- 💾 Caché inteligente de frames

## 📐 Configuración Aplicada

### Cámara OV5647
```json
{
  "type": "csi_camera",
  "name": "OV5647 Camera Module v1",
  "frame_width": 1296,
  "frame_height": 972,
  "fps": 30,
  "auto_exposure": true,
  "auto_white_balance": true,
  "brightness": 0.0,
  "contrast": 1.1,
  "saturation": 1.05,
  "sharpness": 1.2
}
```

### YOLOv8
```json
{
  "model_type": "yolov8",
  "confidence_threshold": 0.35,
  "input_size": 640,
  "device": "cpu",
  "num_threads": 4,
  "num_workers": 2
}
```

## 🚀 Cómo Usar

### 1. Test Rápido (Verificación)
```bash
cd ~/VisiFruit
source venv/bin/activate

# Test rápido de 10 frames
python test_camera_ai_optimized.py --quick
```

### 2. Test Completo (Benchmark)
```bash
# Test completo con 100 frames
python test_camera_ai_optimized.py --full

# Solo benchmark de IA
python test_camera_ai_optimized.py --benchmark
```

### 3. Ejecutar el Sistema Completo
```bash
# Modo PROTOTIPO con optimizaciones
python main_etiquetadora_v4.py
# Selecciona opción [2] MODO PROTOTIPO
```

## 📊 Rendimiento Esperado

Con las optimizaciones aplicadas:

| Métrica | Valor Esperado | Notas |
|---------|---------------|-------|
| **FPS Cámara** | ~30 FPS | Captura nativa |
| **Inferencia IA** | 150-250ms | ~4-6 FPS por worker |
| **Throughput Total** | 8-12 FPS | Pipeline completo |
| **Latencia** | <200ms | Detección + clasificación |

### Breakdown de Tiempos
```
Pipeline Completo:
├─ Captura cámara:     ~33ms  (30 FPS)
├─ Pre-procesamiento:  ~15ms  (mejoras de imagen)
├─ Inferencia YOLOv8:  ~180ms (detección CPU)
└─ Post-procesamiento: ~10ms  (clasificación)
──────────────────────────────
   TOTAL:              ~238ms (~4.2 FPS end-to-end)
```

## 🔧 Ajustes Finos

### Si necesitas MÁS VELOCIDAD:
```json
// Config_Prototipo.json
{
  "camera_settings": {
    "frame_width": 960,      // ← Reducir a 960x720
    "frame_height": 720
  },
  "ai_model_settings": {
    "input_size": 480,       // ← Reducir a 480
    "confidence_threshold": 0.40  // ← Aumentar umbral
  }
}
```
**Resultado esperado:** ~6-8 FPS total, pero menor precisión.

### Si necesitas MÁS PRECISIÓN:
```json
{
  "ai_model_settings": {
    "input_size": 800,       // ← Aumentar a 800
    "confidence_threshold": 0.30  // ← Reducir umbral
  }
}
```
**Resultado esperado:** ~2-3 FPS total, pero mayor precisión.

## 🎨 Pre-procesamiento Configurable

Edita `Config_Prototipo.json`:

```json
{
  "camera_settings": {
    "image_enhancement": {
      "enabled": true,           // ← Activar mejoras
      "auto_brightness": true,   // Corrección automática de brillo
      "auto_contrast": true,     // CLAHE adaptativo
      "clahe_enabled": true,
      "clahe_clip_limit": 2.0,
      "denoise": false          // Usar solo en condiciones de poca luz
    }
  }
}
```

## 📈 Monitoreo de Rendimiento

El script de test genera un reporte JSON completo:

```bash
cat logs/camera_ai_benchmark_report.json
```

Ejemplo de salida:
```json
{
  "camera": {
    "performance": {
      "avg_fps": 29.8,
      "quality": {
        "avg_brightness": 128.5,
        "avg_contrast": 52.3,
        "avg_sharpness": 485.2
      }
    }
  },
  "ai": {
    "performance": {
      "avg_inference_time_ms": 185.4,
      "max_fps": 5.4,
      "total_detections": 45
    }
  },
  "recommendations": [
    {
      "severity": "success",
      "message": "Excelente rendimiento de IA..."
    }
  ]
}
```

## 🐛 Troubleshooting

### ❌ Error: "Picamera2 no disponible"
```bash
# Instalar Picamera2 en el venv
sudo apt update
sudo apt install -y python3-libcamera python3-picamera2

# Copiar a venv
cp -r /usr/lib/python3/dist-packages/picamera2 ~/VisiFruit/venv/lib/python3.11/site-packages/
cp -r /usr/lib/python3/dist-packages/libcamera ~/VisiFruit/venv/lib/python3.11/site-packages/
```

### ⚠️ Advertencia: "FPS muy bajo"
1. Verifica iluminación (la cámara necesita buena luz)
2. Reduce resolución a 960x720
3. Reduce input_size de YOLOv8 a 480
4. Desactiva pre-procesamiento (image_enhancement.enabled = false)

### 🔴 Error: "No se pudo capturar frame"
```bash
# Verificar que la cámara está conectada
libcamera-hello --list-cameras

# Verificar permisos
sudo usermod -a -G video $USER
# Reiniciar sesión

# Test básico
rpicam-hello
```

### 🟡 Detecciones imprecisas
1. Ajusta iluminación (evita sombras fuertes)
2. Verifica que el modelo está entrenado para tus frutas
3. Reduce confidence_threshold a 0.25
4. Activa pre-procesamiento de imagen
5. Aumenta contrast a 1.2 en camera_settings

## 📚 Archivos Modificados

```
VisiFruit/
├── utils/
│   ├── camera_controller.py          # ✨ Driver Picamera2 optimizado
│   └── frame_preprocessor.py         # ✨ Nuevo: Pre-procesamiento
├── Prototipo_Clasificador/
│   └── Config_Prototipo.json         # ✨ Configuración optimizada
├── test_camera_ai_optimized.py       # ✨ Nuevo: Script de test
└── OPTIMIZACION_OV5647.md            # 📄 Esta guía
```

## 🎯 Próximos Pasos

1. **Ejecuta el test:**
   ```bash
   python test_camera_ai_optimized.py --full
   ```

2. **Revisa el reporte:**
   ```bash
   cat logs/camera_ai_benchmark_report.json
   ```

3. **Ajusta parámetros según recomendaciones**

4. **Ejecuta el sistema:**
   ```bash
   python main_etiquetadora_v4.py
   # Selecciona [2] MODO PROTOTIPO
   ```

## 📞 Soporte

Si encuentras problemas:
1. Ejecuta `test_camera_ai_optimized.py --full`
2. Revisa los logs en `logs/`
3. Comparte el reporte JSON generado

---

**Última actualización:** Octubre 2025  
**Autores:** Gabriel Calderón, Elias Bautista, Cristian Hernandez  
**Versión:** 1.0 - OV5647 Edition
