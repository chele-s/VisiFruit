# 🔌 Configuración de Puertos - Sistema VisiFruit

## 📋 Distribución de Puertos

### 🎯 **Puerto 8000 - Sistema Principal**
- **Servicio**: Sistema de Etiquetado Principal (`main_etiquetadora.py`)
- **Configuración**: `Config_Etiquetadora.json` → `api_settings.port`
- **URL**: http://localhost:8000
- **Funcionalidad**: 
  - Control completo del sistema de etiquetado
  - Motor DC, etiquetadoras, IA, sensores
  - API de producción principal
  - WebSockets para dashboard 3D

### 🖥️ **Puerto 8001 - Backend Adicional**
- **Servicio**: Backend Ultra-Avanzado (`Interfaz_Usuario/Backend/main.py`)
- **Configuración**: Hardcodeado en código + config_manager.py
- **URL**: http://localhost:8001  
- **Funcionalidad**:
  - Métricas avanzadas y analytics
  - Sistema de alertas
  - Reportes y estadísticas
  - WebSockets para monitoreo

### 🌐 **Puerto 3000/5173 - Frontend React**
- **Servicio**: Interfaz de Usuario (VisiFruit React App)
- **Configuración**: `package.json` de React
- **URL**: http://localhost:3000 o http://localhost:5173
- **Funcionalidad**:
  - Dashboard principal del usuario
  - Interface web interactiva

## ⚠️ **Evitar Conflictos de Puerto**

1. **NO cambiar** el puerto 8000 del sistema principal
2. **SI necesitas cambiar puertos**, hazlo en este orden:
   - Backend adicional (8001) → 8002, 8003, etc.
   - Frontend React → 3001, 5174, etc.
   - Sistema principal (8000) solo en casos extremos

## 🔧 **Comandos de Inicio**

```bash
# Sistema Principal (Puerto 8000)
python main_etiquetadora.py

# Backend Adicional (Puerto 8001)
cd Interfaz_Usuario/Backend
python main.py
# O usar: start_backend.bat

# Frontend React (Puerto 3000/5173)
cd Interfaz_Usuario/VisiFruit
npm run dev
```

## 🚨 **Resolución de Problemas**

### Error: "Address already in use"
- **Causa**: Otro proceso usa el mismo puerto
- **Solución**: 
  1. Verificar qué proceso usa el puerto: `netstat -ano | findstr :8000`
  2. Terminar proceso: `taskkill /PID <PID> /F`
  3. O cambiar puerto en la configuración correspondiente

### Sistema se queda "estancado"
- **Causa más común**: Conflicto de puertos entre servicios
- **Solución**: Verificar que cada servicio use un puerto único

---
*Actualizado: $(Get-Date -Format "yyyy-MM-dd HH:mm")*
