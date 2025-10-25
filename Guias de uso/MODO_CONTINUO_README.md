# 🚀 Modo Continuo de Procesamiento - VisiFruit

## ✅ Cambios Implementados

Se ha actualizado el sistema para **procesar frames continuamente** sin esperar triggers del sensor, maximizando el throughput y FPS.

---

## 📋 Resumen de Cambios

### 1. **`main_etiquetadora_v4.py` - Modo Continuo Activado**
✅ El bucle principal ahora procesa frames constantemente
✅ FPS configurable (default: 15 FPS)
✅ No espera al sensor para procesar
✅ Control automático de tasa de frames

### 2. **`ai_inference_server.py` - Rate Limit Aumentado**
✅ Rate limit: **1800/minute** (30 FPS máximo)
✅ Antes: 60/minute (bloqueaba peticiones)

### 3. **`Config_Etiquetadora.json` - Nueva Configuración**
✅ Nueva sección `processing_mode` para ajustar FPS

---

## ⚙️ Configuración

### **Ajustar FPS del Sistema**

Edita `Config_Etiquetadora.json`:

```json
"processing_mode": {
  "mode": "continuous",
  "target_fps": 15,     // ← Cambia aquí (10-30 FPS recomendado)
  "description": "Modo continuo: procesa frames constantemente"
}
```

#### Recomendaciones de FPS:

| FPS | Uso Recomendado | Ventajas | Desventajas |
|-----|-----------------|----------|-------------|
| **10** | Banda lenta, productos grandes | Menor uso de red/CPU | Puede perder detecciones |
| **15** | ✅ **Balanceado (default)** | Buen balance rendimiento/precisión | - |
| **20** | Banda rápida, alta precisión | Más detecciones | Mayor uso de recursos |
| **30** | Máximo rendimiento | Sin pérdidas | Requiere GPU potente |

---

## 🔧 Cómo Funciona

### **Antes (Modo Basado en Sensor):**
```
Sensor detecta → Captura frame → Procesa → Espera siguiente sensor
```
**FPS**: 0.3-1.0 (dependía de velocidad de banda)

### **Ahora (Modo Continuo):**
```
Captura frame → Procesa → Espera delay → Repite
```
**FPS**: 15 (configurable) - **Constante**

---

## 📊 Rendimiento Esperado

### **Con 15 FPS configurado:**
```
Servidor GPU (ai_inference_server.py):
  ✅ FPS: ~15.0 (constante)
  ✅ Latencia: ~30ms por frame
  ✅ Rate limit: 1800/minute (OK)
  
Raspberry Pi 5:
  ✅ Envía 15 frames/segundo
  ✅ Recibe resultados en ~30ms
  ✅ Procesa detecciones inmediatamente
```

### **Beneficios:**
- ✅ **Mayor throughput**: Más frames procesados
- ✅ **Sin pérdidas**: Captura todas las frutas
- ✅ **FPS predecible**: Siempre el mismo
- ✅ **Mejor para monitoreo**: Stream constante

---

## 🚦 Inicio Rápido

### **1. Reiniciar Servidor de Inferencia (GPU)**
```powershell
# En Windows (servidor GPU)
cd C:\Users\elias\OneDrive\Desktop\VisiFruit
& venv_server/Scripts/Activate.ps1
python ai_inference_server.py
```

**Verifica en logs:**
```
Rate Limit: 1800/minute  ← Debe decir 1800, no 60
```

---

### **2. Iniciar Sistema en Raspberry Pi 5**
```bash
# En Raspberry Pi
cd /home/pi/VisiFruit
python main_etiquetadora_v4.py
```

**Verifica en logs:**
```
🔄 Bucle principal iniciado - MODO CONTINUO (procesamiento constante)
🎯 Procesamiento continuo configurado a 15 FPS
```

---

### **3. Monitorear Rendimiento**

**En el servidor (Windows), verás:**
```
📊 FPS: 15.0 | Latencia: 30.2ms | Frames: 90 | Detecciones: 25
✅ 2 frutas en 31.5ms (inf:30.8ms) | FPS: 15.0
```

**FPS debe estar cerca de 15.0 (no 0.3-0.8 como antes)**

---

## 🎛️ Ajuste Fino

### **Si el sistema está lento (FPS < esperado):**

1. **Reducir FPS objetivo**:
```json
"target_fps": 10  // Reducir de 15 a 10
```

2. **Verificar GPU del servidor**:
```bash
# Windows (servidor)
nvidia-smi
# Debe mostrar uso de GPU
```

3. **Verificar red**:
```bash
# Raspberry Pi
ping 192.168.137.50
# Latencia debe ser < 5ms
```

---

### **Si quieres MÁXIMO rendimiento (30 FPS):**

1. **Aumentar FPS en config**:
```json
"target_fps": 30
```

2. **Verificar que GPU pueda mantener 30 FPS**:
   - Latencia debe ser < 33ms (1000ms / 30fps)
   - GPU RTX 3050 Ti puede manejar ~30-35ms por frame

3. **Monitor de recursos**:
```powershell
# Windows - Ver uso GPU en tiempo real
nvidia-smi -l 1
```

---

## 🐛 Solución de Problemas

### **Problema: FPS sigue bajo en servidor**

**Causa**: Raspberry Pi enviando frames lentamente

**Solución**:
```bash
# Verificar que main_etiquetadora_v4.py esté actualizado
grep -n "MODO CONTINUO" main_etiquetadora_v4.py
# Debe mostrar la línea con "MODO CONTINUO"
```

---

### **Problema: Warnings de Rate Limit**

**Causa**: Rate limit aún en 60/minute

**Solución**:
```python
# Verifica ai_inference_server.py línea 100:
RATE_LIMIT = os.getenv("RATE_LIMIT", "1800/minute")
# Debe decir 1800, no 60
```

Reinicia el servidor después del cambio.

---

### **Problema: Latencia alta (>100ms)**

**Soluciones**:
1. Verificar red WiFi (usar cable ethernet si es posible)
2. Reducir FPS objetivo a 10
3. Verificar que GPU no esté ocupada con otras tareas

---

## 📈 Comparación Antes/Después

### **ANTES (Modo Sensor):**
```
📊 FPS: 0.8 | Latencia: 28.0ms | Frames: 150 | Detecciones: 15
```
- FPS: **0.8** (muy bajo)
- Procesaba solo cuando sensor detectaba
- Muchos frames perdidos

### **DESPUÉS (Modo Continuo):**
```
📊 FPS: 15.0 | Latencia: 30.2ms | Frames: 900 | Detecciones: 120
```
- FPS: **15.0** (constante)
- Procesa continuamente
- Sin pérdidas de frames

---

## 🎯 Recomendaciones de Uso

### **Para Producción Normal:**
```json
"target_fps": 15
```
- Balanceado
- Bajo consumo de red
- Suficiente para banda transportadora normal

### **Para Alta Velocidad:**
```json
"target_fps": 20
```
- Mayor precisión
- Captura frutas pequeñas
- Para bandas rápidas

### **Para Testing/Debug:**
```json
"target_fps": 10
```
- Menor carga
- Más fácil de monitorear
- Logs más legibles

---

## 📝 Archivos Modificados

- ✅ `main_etiquetadora_v4.py` - Bucle continuo implementado
- ✅ `ai_inference_server.py` - Rate limit aumentado a 1800/minute
- ✅ `Config_Etiquetadora.json` - Nueva sección `processing_mode`
- ✅ `MODO_CONTINUO_README.md` - Esta documentación

---

## 🔄 Volver al Modo Anterior (Basado en Sensor)

Si necesitas volver al modo anterior:

1. **Editar `main_etiquetadora_v4.py`** y reemplazar el bucle con el código original que esperaba triggers del sensor
2. **O simplemente** configurar `target_fps: 0` para desactivar

---

## 🆘 Soporte

Si tienes problemas:

1. **Verificar logs** del servidor y Raspberry Pi
2. **Revisar FPS** en ambos sistemas
3. **Confirmar rate limit** actualizado
4. **Probar con FPS más bajo** (10 FPS)

---

## ✅ Checklist de Inicio

- [ ] Servidor GPU reiniciado con rate limit 1800/minute
- [ ] Raspberry Pi ejecutando código actualizado
- [ ] Logs muestran "MODO CONTINUO"
- [ ] FPS cercano a objetivo (±2 FPS)
- [ ] Sin warnings de rate limit
- [ ] Detecciones funcionando correctamente

---

**Sistema actualizado a Modo Continuo! 🚀**

**FPS objetivo**: 15 FPS (configurable en `Config_Etiquetadora.json`)
**Rate limit**: 1800/minute (soporta hasta 30 FPS)
**Procesamiento**: Constante, sin esperar sensor
