# 🌐 Conexión Frontend-Backend - Sistema VisiFruit

## 🎯 **Configuración Completa**

El sistema ahora está completamente configurado para que el frontend React se conecte al backend en el puerto 8001.

---

## ⚙️ **Configuraciones Realizadas**

### 🔧 **Frontend React (Puerto 3000)**

#### **Archivos Modificados:**
- ✅ `src/config/constants.ts` - URL actualizada a puerto 8001
- ✅ `src/services/api.ts` - API base URL actualizada
- ✅ `vite.config.ts` - Proxy y configuración mejorada
- ✅ `.env.example` - Variables de entorno configuradas

#### **URLs Configuradas:**
```typescript
// constants.ts
baseUrl: 'http://localhost:8001'
websocketUrl: 'ws://localhost:8001/ws'

// api.ts  
API_BASE_URL = 'http://localhost:8001'
```

### ⚡ **Proxy de Vite (Desarrollo)**
```typescript
// vite.config.ts
proxy: {
  '/api': 'http://localhost:8001',
  '/ws': 'ws://localhost:8001'
}
```

### 🔗 **Backend (Puerto 8001)**
- ✅ CORS configurado para frontend
- ✅ WebSockets habilitados
- ✅ API endpoints listos
- ✅ Documentación en `/api/docs`

---

## 🚀 **Cómo Ejecutar Todo**

### **Opción 1: Script Automático (Recomendado)**
```bash
# Windows Batch
start_sistema_completo.bat

# PowerShell  
powershell -ExecutionPolicy Bypass -File start_sistema_completo.ps1

# Esto iniciará:
# ✅ Backend en puerto 8001 (ventana 1)
# ✅ Frontend en puerto 3000 (ventana 2)
```

### **Opción 2: Manual**

**Terminal 1 - Backend:**
```bash
venv\Scripts\activate
cd Interfaz_Usuario\Backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd Interfaz_Usuario\VisiFruit
npm install  # Solo la primera vez
npm run dev
```

### **Opción 3: Solo Frontend**
```bash
# Si el backend ya está ejecutándose
start_frontend.bat
```

---

## 🔍 **Verificación de Conexión**

### **Script de Verificación Automático:**
```bash
# Verificar que todo esté conectado
python verificar_conexion.py --detallado

# Verificación rápida
python verificar_conexion.py
```

### **Verificación Manual:**
1. **Backend Health**: http://localhost:8001/health
2. **API Docs**: http://localhost:8001/api/docs  
3. **Frontend**: http://localhost:3000
4. **WebSocket Test**: ws://localhost:8001/ws/realtime

---

## 📊 **Arquitectura de Conexión**

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA VISIFRUIT v3.0                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend React (Puerto 3000)                              │
│  ├─ Vite Dev Server                                         │
│  ├─ Proxy /api → localhost:8001                             │
│  ├─ WebSocket → ws://localhost:8001/ws                      │
│  └─ HTTP Requests → http://localhost:8001                   │
│                         ⬇️                                   │
│  Backend Ultra (Puerto 8001)                               │
│  ├─ FastAPI Server                                          │
│  ├─ API Endpoints (/api/*)                                  │
│  ├─ WebSocket Endpoints (/ws/*)                             │
│  ├─ Metrics & Analytics                                     │
│  └─ Dashboard API Docs                                      │
│                         ⬇️                                   │
│  Sistema Principal (Puerto 8000) - Futuro                  │
│  ├─ Control de Etiquetadoras                               │
│  ├─ IA de Categorización                                    │
│  ├─ Motor DC Controller                                     │
│  └─ Sensores y Hardware                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 **Funcionalidades Conectadas**

### **📡 APIs Disponibles:**
- ✅ **Producción**: `/api/production/status`, `/api/production/start`
- ✅ **Métricas**: `/api/system/performance`, `/api/metrics/*`
- ✅ **Alertas**: `/api/alerts`, `/api/alerts/{id}/acknowledge`
- ✅ **Configuración**: `/api/config/update`
- ✅ **Reportes**: `/api/reports/generate`

### **🔌 WebSockets en Tiempo Real:**
- ✅ **Dashboard**: `/ws/dashboard` - Datos 3D en tiempo real
- ✅ **Métricas**: `/ws/realtime` - Métricas del sistema
- ✅ **Alertas**: `/ws/alerts` - Notificaciones instantáneas
- ✅ **Producción**: `/ws/production` - Estado de etiquetado

### **📊 Features del Frontend:**
- ✅ **Dashboard 3D** con Three.js
- ✅ **Métricas en Tiempo Real** con Recharts
- ✅ **Sistema de Alertas** Material-UI
- ✅ **Control de Producción** interactivo
- ✅ **Gestión de Estado** con Redux Toolkit
- ✅ **Cache Inteligente** con React Query

---

## 🛠️ **Variables de Entorno**

### **Frontend (.env):**
```bash
# URLs del Backend
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws

# Configuración de desarrollo  
VITE_DEV_PORT=3000
VITE_ENVIRONMENT=development

# Features habilitadas
VITE_ENABLE_3D=true
VITE_ENABLE_ANIMATIONS=true
VITE_ENABLE_WEBSOCKETS=true
```

### **Backend (automático):**
- Puerto configurado en `backend_modules/config_manager.py`
- CORS habilitado para frontend
- WebSockets configurados automáticamente

---

## 🚨 **Resolución de Problemas**

### **Error: Cannot connect to backend**
```bash
# 1. Verificar que el backend esté ejecutándose
curl http://localhost:8001/health

# 2. Verificar puertos
python check_ports.py

# 3. Ver logs del backend
# (Revisar la ventana del backend para errores)
```

### **Error: WebSocket connection failed**
```bash
# 1. Verificar configuración de WebSocket
python verificar_conexion.py --detallado

# 2. Verificar que no haya firewall bloqueando
# Windows: Revisar Windows Defender Firewall
```

### **Error: CORS issues**
```bash
# El backend ya tiene CORS configurado para localhost:3000
# Si usas otro puerto, actualiza la configuración en:
# Backend/main.py - CORSMiddleware allow_origins
```

### **Frontend no se conecta tras cambios**
```bash
# 1. Limpiar cache del navegador
# Ctrl+Shift+R o F12 > Network > Disable cache

# 2. Reiniciar servidor de desarrollo
# Ctrl+C en frontend y ejecutar npm run dev de nuevo

# 3. Verificar archivo .env
# Debe tener VITE_API_URL=http://localhost:8001
```

---

## 📈 **Monitoring y Logs**

### **Logs del Backend:**
- `Interfaz_Usuario/Backend/logs/backend_ultra.log`
- Console output en la ventana del backend

### **Network Inspector:**
- F12 en navegador → Network tab
- Verificar peticiones a `localhost:8001`
- Verificar WebSocket connections

### **React DevTools:**
- Extensión React DevTools para Chrome/Firefox
- Verificar estado de Redux
- Monitorear queries de React Query

---

## 🎉 **Estado Actual**

✅ **Frontend configurado** para puerto 8001  
✅ **Backend funcionando** en puerto 8001  
✅ **APIs conectadas** y funcionando  
✅ **WebSockets operativos** para tiempo real  
✅ **Scripts automatizados** para fácil uso  
✅ **Verificación automática** de conexión  
✅ **Documentación completa** generada  

**¡El sistema está listo para usar!** 🚀

---

*Configuración completada el 12 de Agosto de 2025*  
*Estado: ✅ COMPLETAMENTE FUNCIONAL*
