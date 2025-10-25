# Mejoras del Servidor de Inferencia - VisiFruit

## 🚀 Nuevas Funcionalidades

Se han agregado funcionalidades avanzadas para mejorar el monitoreo y visualización en tiempo real del servidor de inferencia.

---

## 1. 📊 Logging Frecuente con Estadísticas FPS

### Comportamiento Anterior
- Solo logueaba cuando **detectaba frutas**
- Difícil saber si el servidor estaba procesando correctamente

### Comportamiento Nuevo
✅ **Log cada 30 frames** (configurable) con estadísticas:
```
📊 FPS: 28.5 | Latencia: 21.3ms | Frames: 300 | Detecciones: 45
```

✅ **Log individual** cuando detecta frutas:
```
✅ 1 frutas en 22.1ms (inf:20.7ms) | FPS: 29.2
```

### Configuración
```bash
# En .env o variables de entorno
LOG_EVERY_N_FRAMES=30  # Mostrar estadísticas cada N frames
```

---

## 2. 🎥 Streaming MJPEG en Vivo con Bounding Boxes

### Nueva Funcionalidad
**Vista previa en tiempo real** de las detecciones con:
- ✅ Bounding boxes de colores por clase
  - **Verde**: Manzanas
  - **Azul**: Peras
  - **Amarillo**: Limones
- ✅ Confianza de cada detección
- ✅ FPS y contador de detecciones en pantalla

### Cómo Usar

#### Desde tu Navegador
Abre esta URL mientras el servidor está corriendo:
```
http://TU_IP_LAPTOP:9000/stream
```

Ejemplo:
```
http://192.168.137.1:9000/stream
```

#### Desde HTML
```html
<!DOCTYPE html>
<html>
<head>
    <title>VisiFruit - Vista en Vivo</title>
</head>
<body>
    <h1>Detección de Frutas en Vivo</h1>
    <img src="http://192.168.137.1:9000/stream" 
         style="width: 100%; max-width: 1280px;">
    
    <div id="stats">
        <h2>Estadísticas</h2>
        <p id="fps">FPS: --</p>
        <p id="detections">Detecciones: --</p>
    </div>
    
    <script>
        // Actualizar estadísticas cada segundo
        setInterval(async () => {
            const response = await fetch('http://192.168.137.1:9000/perf');
            const stats = await response.json();
            
            document.getElementById('fps').textContent = 
                `FPS: ${stats.fps}`;
            document.getElementById('detections').textContent = 
                `Detecciones: ${stats.total_detections}`;
        }, 1000);
    </script>
</body>
</html>
```

### Configuración
```bash
# Habilitar/deshabilitar streaming
ENABLE_MJPEG_STREAM=true  # Por defecto: true
```

---

## 3. 📈 Endpoint de Estadísticas de Rendimiento

### Nuevo Endpoint: `/perf`
**Sin autenticación** para facilitar monitoreo.

#### Ejemplo de Respuesta
```json
{
  "fps": 29.2,
  "avg_latency_ms": 21.3,
  "frames_processed": 874,
  "total_detections": 156,
  "uptime_seconds": 325.4,
  "requests_total": 874,
  "requests_success": 874,
  "timestamp": "2025-10-13T12:15:30.123456"
}
```

#### Uso desde Terminal
```bash
# Verificar FPS en tiempo real
curl http://192.168.137.1:9000/perf | jq '.fps'

# Monitoreo continuo (cada segundo)
watch -n 1 'curl -s http://192.168.137.1:9000/perf | jq "."'
```

#### Uso desde Python
```python
import requests

response = requests.get('http://192.168.137.1:9000/perf')
stats = response.json()

print(f"FPS: {stats['fps']}")
print(f"Latencia: {stats['avg_latency_ms']}ms")
print(f"Detecciones totales: {stats['total_detections']}")
```

---

## 4. 💾 Guardar Frames Anotados (Opcional)

### Funcionalidad
Guarda automáticamente **frames con detecciones** con:
- Bounding boxes dibujados
- Etiquetas de clase y confianza
- Timestamp en el nombre del archivo

### Configuración
```bash
# Habilitar guardado de frames
SAVE_ANNOTATED_FRAMES=true  # Por defecto: false

# Directorio de salida
ANNOTATED_FRAMES_DIR=logs/annotated_frames  # Por defecto
```

### Ejemplo de Archivo Guardado
```
logs/annotated_frames/detection_20251013_121530_456789_2fruits.jpg
                       ^^^^^^^^  ^^^^^^^^  ^^^^^^  ^^^^^^^
                       Fecha     Hora      µs      Cantidad
```

---

## 5. 🔧 Configuración Completa

### Variables de Entorno (.env)

```bash
# ==================== MODELO ====================
MODEL_PATH=weights/best.pt
MODEL_DEVICE=cuda  # cuda o cpu
MODEL_FP16=true    # Usar FP16 en GPU

# ==================== SERVIDOR ====================
SERVER_HOST=0.0.0.0
SERVER_PORT=9000
SERVER_WORKERS=1

# ==================== AUTENTICACIÓN ====================
AUTH_ENABLED=true
AUTH_TOKENS=visifruittoken2025,debugtoken

# ==================== RENDIMIENTO ====================
RATE_LIMIT=60/minute
MAX_IMAGE_SIZE=1920
JPEG_QUALITY=85
ENABLE_CACHE=true
CACHE_TTL=60

# ==================== VISUALIZACIÓN Y LOGGING ====================
LOG_EVERY_N_FRAMES=30              # Log estadísticas cada N frames
ENABLE_MJPEG_STREAM=true           # Habilitar streaming en vivo
SAVE_ANNOTATED_FRAMES=false        # Guardar frames con detecciones
ANNOTATED_FRAMES_DIR=logs/annotated_frames
```

---

## 6. 📍 Endpoints Disponibles

| Endpoint    | Método | Auth | Descripción                                    |
|-------------|--------|------|------------------------------------------------|
| `/`         | GET    | No   | Info del servidor                               |
| `/health`   | GET    | No   | Estado de salud (CPU, GPU, memoria)             |
| `/infer`    | POST   | Sí   | Inferencia de imagen                            |
| `/stats`    | GET    | Sí   | Estadísticas completas                          |
| `/perf`     | GET    | No   | Estadísticas de rendimiento en tiempo real      |
| `/stream`   | GET    | No   | Streaming MJPEG con bounding boxes              |

---

## 7. 🎯 Ejemplo de Uso Completo

### Paso 1: Iniciar el Servidor
```bash
cd VisiFruit
python ai_inference_server.py
```

### Paso 2: Ver el Log
Ahora verás logs cada 30 frames:
```
12:05:30 - INFO - ai_inference_server - 📊 FPS: 29.3 | Latencia: 21.1ms | Frames: 30 | Detecciones: 5
12:05:31 - INFO - ai_inference_server - ✅ 1 frutas en 22.1ms (inf:20.7ms) | FPS: 29.2
12:05:32 - INFO - ai_inference_server - 📊 FPS: 29.1 | Latencia: 21.3ms | Frames: 60 | Detecciones: 12
```

### Paso 3: Abrir el Stream en el Navegador
```
http://TU_IP:9000/stream
```

### Paso 4: Monitorear Estadísticas
En otra terminal:
```bash
curl http://TU_IP:9000/perf
```

---

## 8. 🔍 Resolución de Problemas

### No veo el streaming
1. Verifica que `ENABLE_MJPEG_STREAM=true`
2. Comprueba que el servidor está procesando frames
3. Abre la consola del navegador para ver errores

### El servidor procesa lento
1. Verifica que estás usando GPU (`MODEL_DEVICE=cuda`)
2. Reduce el tamaño de imagen (`MAX_IMAGE_SIZE=1280`)
3. Aumenta el umbral de confianza (`conf=0.5` en las peticiones)

### Muchos logs
```bash
# Reducir frecuencia de logs
LOG_EVERY_N_FRAMES=100  # Log cada 100 frames
```

### Poco almacenamiento
```bash
# Deshabilitar guardado de frames
SAVE_ANNOTATED_FRAMES=false
```

---

## 9. 📊 Comparación de Rendimiento

### Antes
```
INFO:     192.168.137.100:49450 - "POST /infer HTTP/1.1" 200 OK
INFO:     192.168.137.100:49450 - "POST /infer HTTP/1.1" 200 OK
INFO:     192.168.137.100:49450 - "POST /infer HTTP/1.1" 200 OK
...
11:55:55 - INFO - ✅ Inferencia: 1 frutas en 100.5ms
```
❌ Solo loguea cuando detecta  
❌ No muestra FPS  
❌ No hay visualización

### Ahora
```
12:05:30 - INFO - 📊 FPS: 29.3 | Latencia: 21.1ms | Frames: 30 | Detecciones: 5
12:05:30 - INFO - ✅ 1 frutas en 22.1ms (inf:20.7ms) | FPS: 29.2
12:05:31 - INFO - 📊 FPS: 29.1 | Latencia: 21.3ms | Frames: 60 | Detecciones: 12
```
✅ Log frecuente cada N frames  
✅ Muestra FPS en tiempo real  
✅ Streaming MJPEG disponible  
✅ Estadísticas detalladas en `/perf`

---

## 10. 🎥 Interfaz Web de Ejemplo

Guarda este código como `monitor.html`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisiFruit - Monitor en Vivo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #4CAF50;
        }
        .video-container {
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        img {
            width: 100%;
            display: block;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }
        .stat-label {
            color: #888;
            margin-top: 5px;
        }
        .status {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍎 VisiFruit - Monitor en Vivo <span class="status"></span></h1>
        
        <div class="video-container">
            <img src="http://192.168.137.1:9000/stream" alt="Stream en vivo">
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="fps">--</div>
                <div class="stat-label">FPS</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="latency">--</div>
                <div class="stat-label">Latencia (ms)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="frames">--</div>
                <div class="stat-label">Frames Procesados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="detections">--</div>
                <div class="stat-label">Detecciones</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="uptime">--</div>
                <div class="stat-label">Uptime (s)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="success_rate">--</div>
                <div class="stat-label">Tasa de Éxito</div>
            </div>
        </div>
    </div>
    
    <script>
        const SERVER_URL = 'http://192.168.137.1:9000';
        
        async function updateStats() {
            try {
                const response = await fetch(`${SERVER_URL}/perf`);
                const stats = await response.json();
                
                document.getElementById('fps').textContent = stats.fps.toFixed(1);
                document.getElementById('latency').textContent = stats.avg_latency_ms.toFixed(1);
                document.getElementById('frames').textContent = stats.frames_processed;
                document.getElementById('detections').textContent = stats.total_detections;
                document.getElementById('uptime').textContent = stats.uptime_seconds.toFixed(0);
                
                const successRate = (stats.requests_success / stats.requests_total * 100) || 0;
                document.getElementById('success_rate').textContent = successRate.toFixed(1) + '%';
            } catch (error) {
                console.error('Error obteniendo estadísticas:', error);
            }
        }
        
        // Actualizar cada segundo
        setInterval(updateStats, 1000);
        updateStats();
    </script>
</body>
</html>
```

Abre `monitor.html` en tu navegador para ver el dashboard completo.

---

## ✅ Resumen de Mejoras

| Característica | Antes | Ahora |
|----------------|-------|-------|
| **Logging** | Solo con detecciones | Cada 30 frames |
| **FPS Visible** | ❌ No | ✅ Sí |
| **Vista Previa** | ❌ No | ✅ Streaming MJPEG |
| **Estadísticas RT** | ❌ No | ✅ Endpoint `/perf` |
| **Guardar Frames** | ❌ No | ✅ Opcional |
| **Bounding Boxes** | ❌ No | ✅ Con colores por clase |

---

## 🚀 ¡Listo para Usar!

El servidor ahora muestra **toda la información en tiempo real** que necesitas para monitorear el rendimiento y ver las detecciones en vivo.
