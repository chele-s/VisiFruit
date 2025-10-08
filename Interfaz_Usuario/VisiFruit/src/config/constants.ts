// Configuración global de la aplicación VisiFruit

export const APP_CONFIG = {
  name: 'VisiFruit',
  version: '3.0.0-ULTRA-FRONTEND',
  description: 'Sistema Inteligente de Etiquetado',
  
  // URLs de la API
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8001',
    websocketUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws/realtime',
    
    // Sistema principal (main_etiquetadora.py o smart_classifier_system.py en modo prototipo)
    // Ambos usan el puerto 8000 para compatibilidad
    mainSystemUrl: import.meta.env.VITE_MAIN_API_URL || 'http://localhost:8000',
    
    // Demo system web server (demo_sistema_web_server.py)  
    demoSystemUrl: import.meta.env.VITE_DEMO_API_URL || 'http://localhost:8002',
    
    timeout: 10000, // 10 segundos
  },
  
  // Configuración de actualización de datos
  refresh: {
    production: 5000,     // 5 segundos
    metrics: 10000,       // 10 segundos
    alerts: 30000,        // 30 segundos
    system: 15000,        // 15 segundos
  },
  
  // Límites y umbrales
  limits: {
    maxHistoryPoints: 100,
    maxAlerts: 50,
    maxReconnectAttempts: 5,
    chartMaxPoints: 50,
  },
  
  // Configuración de tema
  theme: {
    primary: '#00E5A0',
    secondary: '#FF6B6B',
    tertiary: '#4ECDC4',
    dark: '#0A0F14',
    paper: '#1A1F24',
  },
  
  // Configuración de animaciones
  animations: {
    enabled: true,
    reducedMotion: false,
    duration: {
      fast: 300,
      normal: 600,
      slow: 1000,
    },
  },
  
  // Configuración de 3D
  three: {
    enableGPUAcceleration: true,
    maxFPS: 60,
    qualityLevel: 'high',
    antialias: true,
    shadows: true,
  },
  
  // Configuración de notificaciones
  notifications: {
    position: 'top-right',
    duration: 5000,
    maxVisible: 5,
    soundEnabled: true,
  },
  
  // Categorías de frutas soportadas
  fruitCategories: [
    { id: 'apple', name: 'Manzanas', emoji: '🍎', color: '#FF6B6B' },
    { id: 'orange', name: 'Naranjas', emoji: '🍊', color: '#FFA500' },
    { id: 'pear', name: 'Peras', emoji: '🍐', color: '#00E5A0' },
    { id: 'banana', name: 'Plátanos', emoji: '🍌', color: '#FFD700' },
    { id: 'grape', name: 'Uvas', emoji: '🍇', color: '#8A2BE2' },
  ],
  
  // Configuración de rendimiento
  performance: {
    enableLazyLoading: true,
    enableVirtualization: true,
    enableMemoryOptimization: true,
    maxCacheSize: 100, // MB
  },
  
  // Configuración de logging
  logging: {
    level: import.meta.env.DEV ? 'debug' : 'info',
    enableConsoleLogging: true,
    enableRemoteLogging: false,
  }
}

// Estados de producción
export const PRODUCTION_STATES = {
  IDLE: 'idle',
  RUNNING: 'running',
  PAUSED: 'paused',
  STOPPED: 'stopped',
  ERROR: 'error',
} as const

// Niveles de alerta
export const ALERT_LEVELS = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
} as const

// Categorías de alerta
export const ALERT_CATEGORIES = {
  SYSTEM: 'system',
  PRODUCTION: 'production',
  QUALITY: 'quality',
  MAINTENANCE: 'maintenance',
  SECURITY: 'security',
} as const

// Configuración de rutas
export const ROUTES = {
  DASHBOARD: '/dashboard',
  PRODUCTION: '/production',
  ANALYTICS: '/analytics',
  THREED: '/3d-view',
  SETTINGS: '/settings',
  ALERTS: '/alerts',
  REPORTS: '/reports',
} as const

// Configuración de localStorage keys
export const STORAGE_KEYS = {
  THEME: 'visifruit_theme',
  USER_PREFERENCES: 'visifruit_preferences',
  CACHE: 'visifruit_cache',
  SESSION: 'visifruit_session',
} as const

// Mensajes de la aplicación
export const MESSAGES = {
  LOADING: 'Cargando sistema VisiFruit...',
  CONNECTING: 'Conectando con el sistema...',
  CONNECTION_ERROR: 'Error de conexión. Reintentando...',
  OFFLINE: 'Sistema sin conexión',
  MAINTENANCE: 'Sistema en mantenimiento',
  SUCCESS: 'Operación completada exitosamente',
  ERROR: 'Ha ocurrido un error inesperado',
} as const

// Configuración de WebSocket
export const WEBSOCKET_CONFIG = {
  reconnectInterval: 1000,
  maxReconnectInterval: 30000,
  reconnectDecay: 1.5,
  timeoutInterval: 2000,
  maxReconnectAttempts: 5,
  binaryType: 'blob' as BinaryType,
} as const

// Configuración de métricas
export const METRICS_CONFIG = {
  updateInterval: 5000,
  retentionPeriod: 24 * 60 * 60 * 1000, // 24 horas
  batchSize: 10,
  compressionEnabled: true,
} as const

export default APP_CONFIG