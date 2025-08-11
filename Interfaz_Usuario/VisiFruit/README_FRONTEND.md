# VisiFruit Frontend Ultra-Moderno 🍎✨

Un frontend súper expresivo y moderno para el sistema VisiFruit, construido con las últimas tecnologías y aprovechando al máximo **AnimeJS 4.1.2** para animaciones espectaculares.

## 🚀 Tecnologías Principales

### ⚡ Core Stack
- **React 19.1.0** + **TypeScript** - Base sólida y tipada
- **Vite 7.0.4** + **SWC** - Build ultrarrápido
- **MUI Material 7.2.0** - Sistema de diseño moderno

### 🎨 Animaciones & UX
- **AnimeJS 4.1.2** - Animaciones fluidas y expresivas
- **Glassmorphism** - Efectos de blur y transparencia
- **Gradientes neón** - Colores vibrantes y modernos
- **Micro-interacciones** - Feedback visual inmediato

### 🏗️ Estado & Datos
- **Redux Toolkit 2.8.2** - Estado global eficiente
- **TanStack Query 5.83.1** - Gestión de datos del servidor
- **WebSockets** - Actualizaciones en tiempo real

### 📊 Visualización
- **Recharts 3.1.0** - Gráficos interactivos y animados
- **React Three Fiber 9.3.0** - Dashboard 3D inmersivo
- **Three.js 0.178.0** - Renderizado 3D avanzado

## 🎯 Características Destacadas

### 🌟 Dashboard 3D Interactivo
```tsx
// Visualización 3D completa del sistema
- Cinta transportadora animada
- Frutas con efectos de partículas
- Estaciones de etiquetado interactivas
- Controles de cámara fluidos
- Iluminación dinámica
```

### 🎭 Animaciones Espectaculares
```tsx
// Aprovecha AnimeJS al máximo
- Animaciones de entrada staggered
- Transiciones entre vistas fluidas
- Loading screen con efectos complejos
- Hover effects con física realista
- Pulsos y brillos en elementos activos
```

### 🎨 Diseño Visual Moderno
```tsx
// Glassmorphism + Gradientes neón
background: 'linear-gradient(135deg, #00E5A0 0%, #4ECDC4 100%)'
backdropFilter: 'blur(20px)'
boxShadow: '0px 0px 20px rgba(0, 229, 160, 0.4)'
```

## 📁 Estructura del Proyecto

```
src/
├── components/          # Componentes React
│   ├── common/         # Componentes compartidos
│   ├── layout/         # Layout y navegación
│   ├── views/          # Vistas principales
│   ├── charts/         # Gráficos y visualizaciones
│   ├── production/     # Componentes de producción
│   └── alerts/         # Sistema de alertas
├── store/              # Estado Redux
│   └── slices/         # Slices de Redux Toolkit
├── services/           # APIs y servicios
├── hooks/              # Hooks personalizados
├── utils/              # Utilidades
├── theme/              # Configuración de tema
├── types/              # Tipos TypeScript
└── config/             # Configuración
```

## 🎨 Sistema de Diseño

### Paleta de Colores
```scss
$primary: #00E5A0;      // Verde vibrante (VisiFruit)
$secondary: #FF6B6B;    // Coral vibrante
$tertiary: #4ECDC4;     // Turquesa
$dark: #0A0F14;         // Azul muy oscuro
$paper: #1A1F24;        // Gris azulado oscuro
```

### Gradientes Personalizados
```scss
$gradient-primary: linear-gradient(135deg, #00E5A0 0%, #4ECDC4 100%);
$gradient-neon: linear-gradient(135deg, #00E5A0 0%, #4ECDC4 50%, #FF6B6B 100%);
$gradient-glass: linear-gradient(135deg, rgba(26, 31, 36, 0.8) 0%, rgba(42, 47, 52, 0.6) 100%);
```

### Efectos Visuales
- **Glassmorphism**: `backdrop-filter: blur(20px)`
- **Sombras neón**: `box-shadow: 0px 0px 20px rgba(0, 229, 160, 0.4)`
- **Bordes suaves**: `border-radius: 12px`

## 🎭 Animaciones con AnimeJS

### Configuraciones Predefinidas
```tsx
export const animationConfig = {
  duration: {
    fast: 300,
    normal: 600,
    slow: 1000,
  },
  easing: {
    smooth: 'easeOutCubic',
    bounce: 'easeOutElastic(1, .8)',
    quick: 'easeOutQuart',
  }
}
```

### Animaciones Destacadas
- **Loading Screen**: Secuencia compleja con timeline
- **Stagger Animations**: Entradas escalonadas de elementos
- **Hover Effects**: Escalado y brillos suaves
- **Pulse Effects**: Para elementos activos
- **3D Transitions**: Rotaciones y transformaciones

## 📊 Vistas Principales

### 🏠 Dashboard Principal
- **Métricas en tiempo real** con tarjetas animadas
- **Estado de producción** con progreso circular
- **Lista de alertas** interactiva
- **Gráficos de rendimiento** con Recharts

### 🏭 Control de Producción
- **Panel de control** con botones animados
- **Configuración avanzada** por tabs
- **Historial detallado** con múltiples visualizaciones
- **Métricas en vivo** con actualizaciones fluidas

### 📈 Análisis Avanzado
- **Múltiples tipos de gráficos**: Líneas, áreas, barras, pie, radar
- **KPIs principales** con chips de cambio
- **Filtros temporales** dinámicos
- **Exportación de datos**

### 🎮 Dashboard 3D
- **Escena 3D completa** con React Three Fiber
- **Cinta transportadora animada**
- **Frutas con física realista**
- **Estaciones interactivas**
- **Controles de cámara** OrbitControls
- **Panel de configuración** 3D

## 🔧 Configuración y Uso

### Requisitos
```bash
Node.js >= 18.0.0
npm >= 9.0.0
```

### Instalación
```bash
cd Interfaz_Usuario/VisiFruit
npm install
```

### Desarrollo
```bash
npm run dev
# Servidor en http://localhost:5173
```

### Build Producción
```bash
npm run build
npm run preview
```

## 🎯 Características Técnicas

### ⚡ Rendimiento
- **Lazy Loading** de componentes
- **Memoización** inteligente
- **Optimización de re-renders**
- **Virtualización** de listas largas

### 🔄 Estado Global
```tsx
// Store Redux con slices especializados
- productionSlice: Estado de producción
- metricsSlice: Métricas del sistema
- uiSlice: Configuración de UI
- alertsSlice: Gestión de alertas
```

### 🌐 Conectividad
- **WebSockets** para datos en tiempo real
- **TanStack Query** para cacheo inteligente
- **Reconexión automática** con backoff exponencial
- **Estados de carga** elegantes

### 📱 Responsive Design
- **Breakpoints MUI** estándar
- **Sidebar colapsible** en móviles
- **Grids adaptables**
- **Touch-friendly** en pantallas táctiles

## 🎨 Ejemplos de Uso

### Animación Personalizada
```tsx
import { animations } from '../utils/animations'

// Animación de entrada para tarjetas
useEffect(() => {
  animations.staggerFadeIn('.card-item', 100, {
    duration: 800,
    easing: 'easeOutCubic'
  })
}, [])
```

### Hook de WebSocket
```tsx
import { useWebSocket } from '../hooks/useWebSocket'

const MyComponent = () => {
  const { isConnected, sendMessage } = useWebSocket()
  
  return (
    <div>
      <Chip 
        label={isConnected ? 'Conectado' : 'Desconectado'} 
        color={isConnected ? 'success' : 'error'} 
      />
    </div>
  )
}
```

### API con TanStack Query
```tsx
import { useProductionStatus } from '../services/api'

const ProductionPanel = () => {
  const { data: status, isLoading } = useProductionStatus()
  
  if (isLoading) return <LoadingScreen />
  
  return <ProductionStatus data={status} />
}
```

## 🚀 Próximas Mejoras

- [ ] **PWA Support** - Funcionalidad offline
- [ ] **Notificaciones Push** - Alertas del sistema
- [ ] **Temas personalizables** - Dark/Light modes
- [ ] **Exportación avanzada** - PDF, Excel, CSV
- [ ] **Dashboard personalizable** - Drag & drop widgets
- [ ] **Modo VR** - Visualización inmersiva

## 🤝 Contribución

Este frontend ha sido diseñado para ser completamente modular y extensible. Cada componente utiliza las mejores prácticas de React y aprovecha al máximo las capacidades de AnimeJS para crear una experiencia única.

---

**Desarrollado con ❤️ para VisiFruit v3.0**  
*Sistema Inteligente de Etiquetado Ultra-Moderno*