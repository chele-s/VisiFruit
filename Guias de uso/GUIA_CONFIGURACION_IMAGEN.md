# 📷 Guía de Configuración de Imagen - VisiFruit Prototipo

## 🔄 Rotación de Cámara

Si tu cámara está físicamente rotada, ajusta el parámetro `rotation_degrees` en `Config_Prototipo.json`:

```json
"camera_settings": {
  "rotation_degrees": -90,  // Valores: -180, -90, 0, 90, 180, 270
  "flip_horizontal": false, // Voltear horizontalmente
  "flip_vertical": false    // Voltear verticalmente
}
```

### Valores de Rotación:
- **-90°** o **270°**: Rotar 90° antihorario (←)
- **90°**: Rotar 90° horario (→)
- **180°** o **-180°**: Rotar 180° (↓)
- **0°**: Sin rotación (↑)

---

## ✨ Mejoras de Imagen para Poca Luz

Si el sistema **no detecta bien con poca luz**, activa las mejoras de imagen:

```json
"image_enhancement": {
  "enabled": true,              // Activar/desactivar todas las mejoras
  
  // CLAHE - Mejora el contraste localmente (RECOMENDADO)
  "clahe_enabled": true,        // Muy efectivo para poca luz
  "clahe_clip_limit": 2.0,      // Rango: 1.0-4.0 (mayor = más contraste)
  "clahe_tile_size": 8,         // Tamaño de región: 8 o 16
  
  // Corrección Gamma - Aclara u oscurece la imagen
  "gamma_correction": 1.2,      // < 1.0 = más oscuro, > 1.0 = más claro
                                // Rango recomendado: 0.8 - 1.5
  
  // Auto ajustes
  "auto_brightness": true,      // Ajuste automático de brillo
  "auto_contrast": true,        // Ajuste automático de contraste
  "equalize_histogram": true,   // Ecualización de histograma
  
  // Reducción de ruido (puede ralentizar)
  "denoise": false              // Solo si hay mucho ruido
}
```

---

## 🎯 Configuraciones Recomendadas por Escenario

### 📍 Escenario 1: Luz Baja / Interior Oscuro
```json
"image_enhancement": {
  "enabled": true,
  "clahe_enabled": true,
  "clahe_clip_limit": 3.0,      // Más agresivo
  "clahe_tile_size": 8,
  "gamma_correction": 1.3,       // Aclarar imagen
  "auto_contrast": true,
  "denoise": false
}
```

### 📍 Escenario 2: Luz Variable (Día/Noche)
```json
"image_enhancement": {
  "enabled": true,
  "clahe_enabled": true,
  "clahe_clip_limit": 2.5,
  "clahe_tile_size": 8,
  "gamma_correction": 1.2,
  "auto_brightness": true,
  "auto_contrast": true,
  "denoise": false
}
```

### 📍 Escenario 3: Buena Iluminación
```json
"image_enhancement": {
  "enabled": true,              // Aún ayuda
  "clahe_enabled": true,
  "clahe_clip_limit": 1.5,      // Menos agresivo
  "clahe_tile_size": 16,
  "gamma_correction": 1.0,      // Sin cambios
  "auto_contrast": false,
  "denoise": false
}
```

### 📍 Escenario 4: Mucho Ruido / Imagen Granulada
```json
"image_enhancement": {
  "enabled": true,
  "clahe_enabled": true,
  "clahe_clip_limit": 2.0,
  "clahe_tile_size": 8,
  "gamma_correction": 1.1,
  "denoise": true               // ⚠️ Puede ralentizar
}
```

---

## 🔧 Ajustes Paso a Paso

### 1️⃣ Corregir Rotación (Si está necesario)
```bash
# Editar Config_Prototipo.json
"rotation_degrees": -90,  # Ajustar según orientación física
```

### 2️⃣ Activar Mejoras Básicas
```bash
# Activar CLAHE (lo más efectivo)
"clahe_enabled": true,
"clahe_clip_limit": 2.0,
```

### 3️⃣ Ajustar Brillo si es Necesario
```bash
# Si la imagen se ve oscura
"gamma_correction": 1.3,  # Aumentar para aclarar

# Si la imagen se ve muy clara/quemada
"gamma_correction": 0.9,  # Reducir para oscurecer
```

### 4️⃣ Probar y Ajustar
- Reinicia el sistema después de cada cambio
- Observa los logs: verás `✨ Mejoras de imagen activadas: ...`
- Ajusta `clahe_clip_limit` entre 1.5 y 3.0 según resultados

---

## 📊 Parámetros Explicados

### CLAHE (Contrast Limited Adaptive Histogram Equalization)
- **¿Qué hace?** Mejora el contraste localmente en la imagen
- **Ideal para:** Condiciones de poca luz, sombras, iluminación desigual
- **clip_limit:** Mayor valor = más contraste (puede causar ruido si es muy alto)
- **tile_size:** Tamaño de región (8 = más detallado, 16 = más suave)

### Gamma Correction
- **¿Qué hace?** Ajusta el brillo general de la imagen
- **< 1.0:** Oscurece (ej: 0.8 = 20% más oscuro)
- **= 1.0:** Sin cambios
- **> 1.0:** Aclara (ej: 1.3 = 30% más claro)

### Auto Contrast/Brightness
- **¿Qué hace?** Normaliza automáticamente el histograma
- **Ideal para:** Luz variable, cambios de iluminación

### Denoise
- **¿Qué hace?** Reduce ruido/grano en la imagen
- **⚠️ Advertencia:** Puede ralentizar el procesamiento
- **Solo usar si:** La imagen tiene mucho ruido visible

---

## 🚀 Ejemplos de Uso

### Problema: "La IA no detecta frutas con luz baja"
**Solución:**
```json
"gamma_correction": 1.3,
"clahe_enabled": true,
"clahe_clip_limit": 3.0
```

### Problema: "La imagen se ve muy contrastada/artificial"
**Solución:**
```json
"clahe_clip_limit": 1.5,  // Reducir agresividad
"gamma_correction": 1.0   // Sin gamma
```

### Problema: "La cámara está rotada -90 grados"
**Solución:**
```json
"rotation_degrees": -90
```

---

## 📈 Monitoreo

Cuando inicies el sistema, verás en los logs:

```
🔄 Rotación de cámara: -90°
✨ Mejoras de imagen activadas: CLAHE, Gamma=1.2, Auto-Contraste
```

Esto confirma que la configuración está activa.

---

## ⚙️ Vista Previa Web

Puedes ver la imagen procesada en tiempo real:

```
http://localhost:8081/mjpeg
```

Esto te ayudará a ajustar los parámetros visualmente.

---

## 🛠️ Troubleshooting

### La detección no mejora después de activar mejoras
1. Verifica que `"enabled": true` esté en `image_enhancement`
2. Aumenta `clahe_clip_limit` gradualmente (2.0 → 2.5 → 3.0)
3. Aumenta `gamma_correction` para aclarar (1.2 → 1.3 → 1.4)
4. Verifica la vista previa web para ver el efecto

### El sistema se vuelve lento
1. Desactiva `"denoise": false` si está en true
2. Reduce `clahe_tile_size` a 16 (es más rápido)
3. Desactiva `auto_contrast` y `auto_brightness` si no son necesarios

### La imagen se ve distorsionada
1. Verifica que `rotation_degrees` sea correcto (-90, 90, 180, etc.)
2. Reduce `clahe_clip_limit` a valores más bajos (1.5-2.0)
3. Ajusta `gamma_correction` más cerca de 1.0

---

## 📝 Notas Importantes

- **Reinicia el sistema** después de cambiar la configuración
- **CLAHE** es la mejora más efectiva para poca luz
- **Gamma** es útil para ajuste rápido de brillo
- **Denoise** solo si hay ruido visible (ralentiza)
- Los cambios son **en tiempo real** al reiniciar

---

## 🎯 Configuración Actual Recomendada

Para tu caso (cámara -90° y poca luz):

```json
"camera_settings": {
  "rotation_degrees": -90,
  "flip_horizontal": false,
  "flip_vertical": false,
  "image_enhancement": {
    "enabled": true,
    "clahe_enabled": true,
    "clahe_clip_limit": 2.5,
    "clahe_tile_size": 8,
    "gamma_correction": 1.2,
    "auto_contrast": true,
    "denoise": false
  }
}
```

**Ajusta según tus resultados!** 🚀

