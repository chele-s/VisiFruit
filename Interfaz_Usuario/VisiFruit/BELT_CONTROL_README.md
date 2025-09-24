# 🎛️ Control Avanzado de Banda Transportadora - VisiFruit

## 📋 Descripción

Página especializada para el control avanzado de la banda transportadora del sistema VisiFruit, con soporte dual para conexión tanto con `main_etiquetadora.py` como con `demo_sistema_completo.py`.

## ✨ Características Principales

### 🚀 Control Inteligente
- **Start/Stop avanzado**: Controles de dirección con animaciones fluidas
- **Control de velocidad**: Slider inteligente con configuración persistente
- **Parada de emergencia**: Botón de emergencia con confirmación visual
- **Auto-habilitación**: Sistema de habilitación/deshabilitación automático

### ⚙️ Configuración Persistente
- **Velocidad por defecto**: Se guarda en localStorage y persiste entre sesiones
- **Velocidad de sensor**: Configuración específica para activación automática
- **Configuración de seguridad**: Umbrales de temperatura y límites operativos
- **Modo mantenimiento**: Configuración especializada para tareas de mantenimiento

### 🌐 Conexión Dual
- **Sistema Principal**: Conecta con `main_etiquetadora.py` en puerto 8000
- **Sistema Demo**: Conecta con `demo_sistema_completo.py` 
- **Modo Combinado**: Puede ejecutar acciones en ambos sistemas simultáneamente
- **Auto-reconexión**: Detección automática de estado de conexión

### 📊 Monitoreo en Tiempo Real
- **Métricas live**: Temperatura, consumo, vibración, tiempo activo
- **Estado visual**: Chips de estado con animaciones y colores dinámicos
- **Historial**: Registro de últimas acciones y timestamps
- **Diagnósticos**: Información de firmware y sistema

## 🏗️ Estructura de Archivos

```
src/
├── components/
│   ├── production/
│   │   └── BeltAdvancedControls.tsx     # Componente principal de control
│   └── views/
│       └── BeltControlView.tsx          # Vista completa con conexiones
├── services/
│   └── api.ts                           # Endpoints API actualizados
└── store/slices/
    └── uiSlice.ts                       # Tipos de vista actualizados
```

## 🔧 APIs Soportadas

### Main System (main_etiquetadora.py)
```typescript
// Control básico
POST /belt/start_forward
POST /belt/start_backward
POST /belt/stop
POST /belt/emergency_stop

// Configuración
POST /belt/set_speed
POST /belt/toggle_enable
GET  /belt/status

// Stepper láser
POST /laser_stepper/toggle
POST /laser_stepper/test

// Motor DC
POST /motor/activate_group
GET  /motor/status

// Desviadores
GET  /diverters/status
POST /diverters/classify
POST /diverters/calibrate
POST /diverters/emergency_stop
```

### Demo System (demo_sistema_completo.py)
- Simulación de endpoints equivalentes
- Misma interfaz, comportamiento adaptado para demo
- Respuestas mockeadas para desarrollo sin hardware

## 📱 Interfaz de Usuario

### Panel Principal
- **Estado en tiempo real**: Métricas visuales con código de colores
- **Controles grandes**: Botones grandes con animaciones táctiles
- **Slider de velocidad**: Control preciso de 0.1 a 2.5 m/s
- **Información del sistema**: Estado, conexiones, versión de firmware

### Dialog de Configuración
- **Pestañas organizadas**: General, Sensores, Seguridad
- **Configuración persistente**: Guardado automático en localStorage
- **Validación en tiempo real**: Verificación de valores válidos
- **Presets inteligentes**: Configuraciones predefinidas por tipo de operación

### Sistema de Conexiones
- **Indicadores visuales**: Estado de conexión con colores y iconos
- **Configuración flexible**: URLs configurables por sistema
- **Auto-reconexión**: Testeo automático cada 10 segundos
- **Modo offline**: Funcionalidad limitada sin conexión

## 🎨 Estilo y Animaciones

### Importación Correcta de Anime.js
```typescript
import { animate, stagger } from 'animejs';
```

### Tema Consistente
- **Glass morphism**: Efecto vidrio con blur y transparencias
- **Gradientes neon**: Colores vibrantes del tema VisiFruit
- **Sombras inteligentes**: Efectos de profundidad y hover
- **Animaciones fluidas**: Transiciones suaves en todas las interacciones

### Componentes Estilizados
```typescript
// Botones ultra-animados
const UltraAnimatedButton = styled(IconButton)(({ theme }) => ({
  // Animaciones complejas con efectos de hover
}));

// Cards con efecto vidrio
const GlassCard = styled(Card)(({ theme }) => ({
  // Glassmorphism con bordes neon
}));
```

## 🔒 Seguridad y Validación

### Controles de Seguridad
- **Parada de emergencia**: Deshabilitación inmediata del sistema
- **Límites de velocidad**: Validación de rangos seguros (0.1-2.5 m/s)
- **Monitoreo de temperatura**: Alertas automáticas por sobrecalentamiento
- **Timeouts de operación**: Evitar operaciones bloqueadas

### Manejo de Errores
- **Conexión perdida**: Notificación inmediata y reintentos automáticos
- **Respuestas de error**: Parsing y display de mensajes del servidor
- **Validación local**: Verificación de parámetros antes del envío
- **Rollback automático**: Reversión de estado en caso de falla

## 🚀 Uso

### Navegación
1. Abrir VisiFruit frontend (http://localhost:3000)
2. Clickear "Control de Banda" en el sidebar
3. Verificar conexiones en la parte superior
4. Configurar velocidades y parámetros si es necesario
5. Usar los controles principales

### Configuración Inicial
1. Hacer click en el botón "Configuración" 
2. Establecer velocidad por defecto (ej: 1.0 m/s)
3. Configurar velocidad de activación por sensor (ej: 1.2 m/s)
4. Habilitar/deshabilitar auto-inicio por sensor
5. Establecer límites de seguridad (temperatura máxima)
6. Guardar configuración

### Uso con Sensores
1. Habilitar "Auto-inicio al detectar sensor" en configuración
2. Establecer velocidad de activación por sensor
3. El sistema iniciará automáticamente cuando detecte actividad del sensor
4. Usar "Activar Sensor de Prueba" para probar la funcionalidad

## 🔧 Configuración de Desarrollo

### Variables de Entorno
```bash
# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/realtime
VITE_MAIN_API_URL=http://localhost:8000
```

### Dependencias
```json
{
  "animejs": "^4.1.2",
  "@mui/material": "^7.2.0",
  "@mui/icons-material": "^7.2.0",
  "@tanstack/react-query": "^5.83.1"
}
```

## 🐛 Troubleshooting

### Errores Comunes

**Error de conexión**
- Verificar que main_etiquetadora.py o demo esté ejecutándose
- Confirmar puerto correcto (8000 por defecto)
- Revisar CORS si hay problemas de dominio cruzado

**Configuración no se guarda**
- Verificar localStorage del navegador
- Limpiar caché si es necesario
- Revisar permisos de almacenamiento local

**Animaciones no funcionan**
- Verificar que animejs esté correctamente importado
- Confirmar que el tema tiene gradientes definidos
- Revisar configuración de reducedMotion

### Logs de Debug
```javascript
// Activar logs detallados en consola
localStorage.setItem('debug_belt_control', 'true');
```

## 🔮 Próximas Características

- [ ] Perfiles de configuración (Desarrollo, Producción, Mantenimiento)
- [ ] Gráficos de métricas históricas
- [ ] Notificaciones push para eventos críticos
- [ ] API WebSocket para updates en tiempo real
- [ ] Sistema de calibración automática
- [ ] Integración con sistema de alertas global

---

## 👨‍💻 Desarrolladores

- **Gabriel Calderón** - Sistema principal y arquitectura
- **Elias Bautista** - Integración de hardware  
- **Cristian Hernandez** - Interfaces y UX

---

**Versión**: 3.0.0-ULTRA  
**Fecha**: Enero 2025  
**Licencia**: MIT
