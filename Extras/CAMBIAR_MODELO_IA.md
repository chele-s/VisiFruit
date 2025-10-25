# 🔄 Cómo Cambiar entre YOLOv8 y RT-DETR

## ⚡ Cambio Rápido (Recomendado)

### Para usar **YOLOv8** (por defecto - RECOMENDADO)
```bash
# Windows PowerShell
$env:MODEL_TYPE="yolov8"
python ai_inference_server.py
```

### Para usar **RT-DETR**
```bash
# Windows PowerShell
$env:MODEL_TYPE="rtdetr"
$env:MODEL_PATH="weights/rtdetr_best.pt"
python ai_inference_server.py
```

---

## 📋 Método con Archivo .env (Más Limpio)

### Paso 1: Crear archivo `.env`
Copia `.env.example` a `.env`:
```bash
copy .env.example .env
```

### Paso 2: Editar `.env`
Abre `.env` y cambia la línea:

**Para YOLOv8:**
```env
MODEL_TYPE=yolov8
MODEL_PATH=weights/best.pt
```

**Para RT-DETR:**
```env
MODEL_TYPE=rtdetr
MODEL_PATH=weights/rtdetr_best.pt
```

### Paso 3: Ejecutar servidor
```bash
python ai_inference_server.py
```

El servidor leerá automáticamente el `.env`

---

## ✅ Verificar Modelo Activo

Al iniciar el servidor, verás en los logs:

```
============================================================
🎯 CONFIGURACIÓN DEL SERVIDOR
   Arquitectura: YOLOv8          <-- Modelo activo
   Modelo: weights/best.pt
   Device: cuda
   FP16: True
============================================================
🔄 Cargando modelo YOLOv8 desde weights/best.pt
🎮 GPU detectada: NVIDIA GeForce RTX 3050 Ti Laptop GPU
✅ Modelo YOLOv8 cargado y listo
```

---

## 🎯 Recomendación para VisiFruit

**Usa YOLOv8** porque:
- ✅ 35-45 FPS (2-3x más rápido que RT-DETR)
- ✅ Latencia ~25ms (ideal para banda transportadora)
- ✅ Menor consumo de GPU
- ✅ Ya tienes modelo entrenado

**RT-DETR solo si**:
- Necesitas >95% precisión absoluta
- No te importa velocidad (12-18 FPS)
- Tienes GPU más potente

---

## 📚 Más Información

Lee la guía completa: `Guias de uso/Guias importantes/MODELO_YOLOV8_VS_RTDETR.md`

---

**Nota**: Si no tienes un modelo RT-DETR entrenado, necesitas entrenarlo primero con tus datos de frutas antes de usarlo.
