# ✅ Guía de Verificación - WebSocket y Datos en Tiempo Real

Esta guía te ayudará a verificar que el frontend esté correctamente conectado y recibiendo datos en tiempo real de los backends.

## 📋 Requisitos Previos

### 1. Variables de Entorno Configuradas

Verifica que tu archivo `.env` en `Interfaz_Usuario/VisiFruit/.env` contenga:

```bash
# Backend del Dashboard (puerto 8001)
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws/realtime

# Sistema Principal (puerto 8000)
VITE_MAIN_API_URL=http://localhost:8000
VITE_MAIN_WS_URL=ws://localhost:8000/ws/ultra_dashboard
```

**Para red local (Raspberry Pi):**
```bash
VITE_API_URL=http://192.168.1.150:8001
VITE_WS_URL=ws://192.168.1.150:8001/ws/realtime
VITE_MAIN_API_URL=http://192.168.1.150:8000
VITE_MAIN_WS_URL=ws://192.168.1.150:8000/ws/ultra_dashboard
```

> 💡 **Nota**: Si no tienes el archivo `.env`, copia `.env.example` a `.env`

### 2. Backend en Puerto 8001

El backend del dashboard debe configurarse para correr en puerto **8001**. 

**Opción A:** Modificar el archivo `.env` principal:
```bash
# En: VisiFruit/.env
SERVER_PORT=8001
```

**Opción B:** Ejecutar con variable de entorno:
```bash
cd Interfaz_Usuario/Backend
set SERVER_PORT=8001 && python main.py
```

### 3. Sistema Principal en Puerto 8000

El sistema principal (`ultra_api.py`) debe correr en puerto **8000** (es el default).

---

## 🚀 Pasos de Verificación

### Paso 1: Iniciar Backends

#### Terminal 1 - Backend Dashboard (puerto 8001)
```bash
cd Interfaz_Usuario/Backend
set SERVER_PORT=8001
python main.py
```

**Esperado:**
```
[OK] Backend Ultra-Avanzado inicializado exitosamente
[START] Iniciando servidor API en 0.0.0.0:8001
```

#### Terminal 2 - Sistema Principal (puerto 8000) - OPCIONAL
```bash
python main_etiquetadora_v4.py
```

**Esperado:**
```
✅ Servidor API escuchando en http://0.0.0.0:8000
```

### Paso 2: Verificar Endpoints de Salud

```bash
# Backend Dashboard (8001)
curl http://localhost:8001/health

# Sistema Principal (8000) - si está corriendo
curl http://localhost:8000/health
```

**Respuesta esperada (8001):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T15:30:00",
  "uptime_seconds": 123.45
}
```

### Paso 3: Iniciar Frontend

```bash
cd Interfaz_Usuario/VisiFruit
npm run dev
```

**Esperado:**
```
VITE v5.x.x ready in XXX ms
➜ Local:   http://localhost:5173/
```

### Paso 4: Verificar Conexiones WebSocket

Abre el navegador en `http://localhost:5173` y abre la consola del navegador (F12).

**Deberías ver:**
```
✅ WebSocket conectado
✅ Ultra WebSocket conectado
```

**Si ves errores:**
- `WebSocket connection failed` → Verifica que el backend (8001) esté corriendo
- `Ultra WebSocket connection failed` → Normal si el sistema principal (8000) no está corriendo

### Paso 5: Probar Simulación de Detecciones

#### Opción A: Script de Python (Recomendado)

```bash
cd Interfaz_Usuario/VisiFruit
python test_simulate.py --count 10 --interval 2
```

**Deberías ver:**
```
🧪 TEST DE SIMULACIÓN DE DETECCIONES - VISIFRUIT
✅ Backend conectado correctamente
🚀 Iniciando simulaciones...
[15:30:00] Simulación 1/10... ✅ OK
   └─ Detectadas: 5 frutas
      🍎 apple: 2
      🍐 pear: 2
      🍋 lemon: 1
```

#### Opción B: cURL Manual

```bash
curl -X POST http://localhost:8001/api/system/simulate
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "detections": [
    {
      "id": "abc123",
      "category": "apple",
      "confidence": 0.95,
      "timestamp": "2025-10-10T15:30:00"
    }
  ]
}
```

### Paso 6: Verificar UI en Tiempo Real

En el frontend:

1. **Navega a la vista "Producción"** (icono de fábrica en el toolbar)

2. **Ejecuta las simulaciones** (desde el script de Python)

3. **Verifica que veas:**
   - ✅ **Categoría Activa**: El emoji y la categoría cambian según la última detección
   - ✅ **Emoji pulsando**: El emoji hace una animación de pulso cuando hay detecciones
   - ✅ **Card "Última Detección"**: Aparece mostrando:
     - Emoji de la fruta
     - Nombre de la categoría
     - Porcentaje de confianza
     - Hora de detección
   - ✅ **Transición suave**: Los cambios se animan con fade-in

---

## 🐛 Solución de Problemas

### Problema 1: WebSocket no conecta

**Síntomas:**
```
❌ WebSocket desconectado: 1006
🔄 Intentando reconectar...
```

**Soluciones:**
1. Verifica que el backend esté corriendo:
   ```bash
   curl http://localhost:8001/health
   ```

2. Verifica las variables de entorno:
   ```bash
   # En PowerShell
   $env:VITE_WS_URL
   
   # Debería mostrar: ws://localhost:8001/ws/realtime
   ```

3. Reinicia el frontend:
   ```bash
   # Ctrl+C para detener
   npm run dev
   ```

### Problema 2: No se ven actualizaciones en UI

**Verificaciones:**

1. **Abre DevTools → Network → WS**
   - Deberías ver conexión a `ws://localhost:8001/ws/realtime`
   - Click en la conexión → Messages
   - Deberías ver mensajes JSON llegando

2. **Abre DevTools → Console**
   - Busca mensajes con `type: 'simulation'`

3. **Verifica Redux State:**
   - Instala Redux DevTools en tu navegador
   - Abre Redux DevTools → State
   - Navega a `production.status.lastDetected`
   - Debería actualizarse cuando llegan detecciones

### Problema 3: Puerto 8001 ocupado

**Windows:**
```powershell
# Ver qué proceso usa el puerto 8001
netstat -ano | findstr :8001

# Matar el proceso (reemplaza PID)
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
# Ver qué proceso usa el puerto 8001
lsof -i :8001

# Matar el proceso
kill -9 <PID>
```

### Problema 4: Backend principal (8000) no disponible

**Esto es OPCIONAL** para testing. El frontend funcionará con solo el backend del dashboard (8001).

Si quieres conectar el sistema principal:
```bash
python main_etiquetadora_v4.py
```

---

## 📊 Checklist Final

- [ ] Archivo `.env` configurado con `VITE_WS_URL` y `VITE_MAIN_API_URL`
- [ ] Backend dashboard corriendo en puerto 8001
- [ ] Frontend iniciado con `npm run dev`
- [ ] Consola muestra "✅ WebSocket conectado"
- [ ] Script `test_simulate.py` ejecuta sin errores
- [ ] Vista de Producción muestra "Categoría Activa" actualizándose
- [ ] Card "Última Detección" aparece y se actualiza
- [ ] Emoji pulsa con animación cuando hay detecciones
- [ ] Confidence percentage se muestra correctamente
- [ ] Timestamp se muestra en formato local

---

## 🎯 Próximos Pasos

Una vez que todo funcione:

1. **Conectar al sistema principal (8000):**
   - Esto agregará datos del motor lineal
   - Mappeo de `active_labeler` a categorías

2. **Conectar hardware real:**
   - Cámara para detecciones reales
   - Motores y etiquetadoras

3. **Testing de producción:**
   - Dejar correr por períodos largos
   - Monitorear memoria y CPU
   - Verificar reconexión automática de WebSockets

---

## 📞 Soporte

Si algo no funciona:

1. Revisa los logs del backend:
   ```bash
   tail -f Interfaz_Usuario/Backend/logs/backend_ultra.log
   ```

2. Revisa la consola del navegador (F12)

3. Verifica que todos los puertos estén libres:
   ```bash
   netstat -ano | findstr :8000
   netstat -ano | findstr :8001
   netstat -ano | findstr :5173
   ```

---

**¡Éxito! 🎉** Si completaste todos los pasos, tu frontend está correctamente integrado con los backends y listo para mostrar datos en tiempo real.
