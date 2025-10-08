# VisiFruit Frontend - Guía de Conexión
======================================

Esta guía explica cómo configurar las conexiones del frontend con el sistema backend de VisiFruit, especialmente para acceso desde diferentes computadoras en la red local.

## 📡 Puertos del Sistema VisiFruit

El sistema VisiFruit utiliza los siguientes puertos:

- **Puerto 8000**: Sistema principal de etiquetado
  - `main_etiquetadora.py` (modo profesional)
  - `smart_classifier_system.py` (modo prototipo)
  - Controla banda, etiquetadoras, servos, clasificadores
  
- **Puerto 8001**: Backend de métricas y dashboard
  - `Interfaz_Usuario/Backend/main.py`
  - API de métricas, alertas, reportes
  - WebSockets en tiempo real
  
- **Puerto 8002**: Sistema demo (opcional)
  - `demo_sistema_web_server.py`
  - Para pruebas sin hardware real
  
- **Puerto 3000**: Frontend (este proyecto)
  - Interfaz de usuario web

## 🔧 Configuración para Localhost

Si ejecutas el frontend en la misma computadora donde corre el backend (típicamente para desarrollo), las URLs por defecto funcionarán:

- Backend: `http://localhost:8001`
- Sistema Principal: `http://localhost:8000`
- WebSocket: `ws://localhost:8001/ws/realtime`

**No necesitas hacer nada especial en este caso.**

## 🌐 Configuración para Acceso Remoto

Si quieres acceder al frontend desde una computadora diferente a donde corre el backend (por ejemplo, frontend en tu laptop y backend en una Raspberry Pi):

### Paso 1: Encontrar la IP de tu Raspberry Pi

En la Raspberry Pi, ejecuta:
```bash
hostname -I
```

Esto te dará algo como: `192.168.1.150`

### Paso 2: Crear archivo de configuración

Crea un archivo `.env.local` en la raíz del proyecto frontend (`Interfaz_Usuario/VisiFruit/.env.local`) con el siguiente contenido:

```bash
# Reemplaza 192.168.1.150 con la IP de tu Raspberry Pi
VITE_API_URL=http://192.168.1.150:8001
VITE_WS_URL=ws://192.168.1.150:8001/ws/realtime
VITE_MAIN_API_URL=http://192.168.1.150:8000
VITE_DEMO_API_URL=http://192.168.1.150:8002
```

### Paso 3: Reiniciar el servidor de desarrollo

```bash
npm run dev
```

Ahora podrás acceder al frontend desde tu laptop y se conectará al backend en la Raspberry Pi.

## 🚀 Iniciar el Sistema Completo

### En la Raspberry Pi (o servidor):

1. **Iniciar Backend (puerto 8001)**:
```bash
cd Interfaz_Usuario/Backend
python main.py
```

2. **Iniciar Sistema Principal** (puerto 8000):

**Modo Profesional**:
```bash
python main_etiquetadora_v4.py
# Selecciona opción [1] MODO PROFESIONAL
```

**Modo Prototipo**:
```bash
python main_etiquetadora_v4.py
# Selecciona opción [2] MODO PROTOTIPO
```

O directamente:
```bash
cd Prototipo_Clasificador
python smart_classifier_system.py
```

### En tu computadora (laptop/desktop):

3. **Iniciar Frontend (puerto 3000)**:
```bash
cd Interfaz_Usuario/VisiFruit
npm install  # Solo la primera vez
npm run dev
```

## 📊 Verificar Conexiones

Una vez todo esté corriendo, el frontend mostrará el estado de las conexiones:

- **Backend Conectado** ✅: Puerto 8001 accesible
- **Sistema Principal Conectado** ✅: Puerto 8000 accesible

Si ves "desconectado" ❌:
1. Verifica que los servicios estén corriendo
2. Verifica que la IP sea correcta
3. Verifica que no haya firewall bloqueando los puertos
4. Verifica que estés en la misma red

## 🔍 Solución de Problemas

### "Backend está apagado" o "Sistema principal desconectado"

**Problema**: El frontend no puede conectarse al backend.

**Soluciones**:
1. Verifica que el backend esté corriendo en la Raspberry Pi
2. Verifica la IP con `hostname -I` en la Raspberry Pi
3. Prueba acceder manualmente desde tu navegador:
   - `http://192.168.1.150:8001/health` (Backend)
   - `http://192.168.1.150:8000/health` (Sistema Principal)
4. Asegúrate de que `.env.local` tiene la IP correcta
5. Reinicia el servidor de desarrollo del frontend

### "Connection refused" o "ERR_CONNECTION_REFUSED"

**Problema**: El firewall está bloqueando las conexiones.

**Solución en Raspberry Pi**:
```bash
# Permitir puertos 8000 y 8001
sudo ufw allow 8000
sudo ufw allow 8001
sudo ufw reload
```

### WebSocket no conecta

**Problema**: WebSocket muestra errores o no se conecta.

**Soluciones**:
1. Verifica que `VITE_WS_URL` use `ws://` (no `wss://` para desarrollo local)
2. Verifica que el backend esté corriendo
3. Algunos routers bloquean WebSockets - prueba en la misma red WiFi

## 🎯 Acceso desde el Navegador en la Raspberry Pi

Si quieres ver la interfaz directamente en la Raspberry Pi (con pantalla conectada):

1. Inicia todos los servicios (backend + sistema principal)
2. Inicia el frontend normalmente
3. En el navegador de la Raspberry Pi, ve a: `http://localhost:3000`

## 📱 Acceso desde Móvil/Tablet

Puedes acceder desde dispositivos móviles en la misma red WiFi:

1. Configura el `.env.local` con la IP de la Raspberry Pi
2. Inicia el frontend con:
```bash
npm run dev -- --host 0.0.0.0
```
3. Desde tu móvil, accede a: `http://IP_DE_TU_LAPTOP:3000`

## 🌍 Variables de Entorno Disponibles

| Variable | Descripción | Por Defecto |
|----------|-------------|-------------|
| `VITE_API_URL` | URL del backend de métricas | `http://localhost:8001` |
| `VITE_WS_URL` | URL de WebSocket | `ws://localhost:8001/ws/realtime` |
| `VITE_MAIN_API_URL` | URL del sistema principal | `http://localhost:8000` |
| `VITE_DEMO_API_URL` | URL del sistema demo | `http://localhost:8002` |

## 📚 Más Información

- Ver `BELT_CONTROL_README.md` para control de banda
- Ver `README_FRONTEND.md` para documentación completa
- Ver logs del backend en `Interfaz_Usuario/Backend/logs/`
- Ver logs del sistema principal en `logs/`

## ✅ Lista de Verificación Rápida

Antes de reportar problemas, verifica:

- [ ] Backend está corriendo (`python Interfaz_Usuario/Backend/main.py`)
- [ ] Sistema principal está corriendo (modo profesional o prototipo)
- [ ] IP de la Raspberry Pi es correcta (`hostname -I`)
- [ ] Archivo `.env.local` existe con las IPs correctas
- [ ] Firewall permite puertos 8000 y 8001
- [ ] Estás en la misma red que la Raspberry Pi
- [ ] Puedes acceder a `/health` desde el navegador
- [ ] Has reiniciado el servidor de desarrollo después de cambiar `.env.local`

## 🆘 ¿Sigue sin funcionar?

1. Revisa los logs del backend
2. Revisa la consola del navegador (F12)
3. Intenta acceder a las URLs directamente en el navegador
4. Verifica que no haya conflictos de puertos
5. Reinicia todos los servicios

---

**Última actualización**: Octubre 2025  
**Versión**: 3.0.0-ULTRA-FRONTEND

