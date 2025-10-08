import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  Alert,
  Paper,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ToggleButton,
  ToggleButtonGroup,
  useTheme,
} from '@mui/material';
import {
  DirectionsRun,
  Settings,
  CloudSync,
  Cloud,
  SmartToy,
  Speed,
  Engineering,
  VerifiedUser,
} from '@mui/icons-material';
import { animate } from 'animejs';
import BeltAdvancedControls from '../production/BeltAdvancedControls';
import APP_CONFIG from '../../config/constants';
// Tipos locales para sincronizar estado externo del control avanzado
type Direction = 'forward' | 'backward' | 'stopped'
type ExternalStepperStatus = {
  isActive: boolean
  currentPower: number
  activationCount: number
  lastActivation: Date | null
  activationDuration: number
  totalActiveTime: number
  sensorTriggers: number
  manualActivations: number
  driverTemperature: number
  currentStepRate: number
}
type ExternalBeltStatus = {
  isRunning: boolean
  direction: Direction
  currentSpeed: number
  targetSpeed: number
  motorTemperature: number
  enabled: boolean
  lastAction: string
  actionTime: Date
  powerConsumption: number
  vibrationLevel: number
  totalRuntime: number
  isConnected: boolean
  firmwareVersion: string
  stepperStatus: ExternalStepperStatus
}

// Interfaces
interface ConnectionConfig {
  type: 'main' | 'demo' | 'both';
  mainUrl: string;
  demoUrl: string;
  autoConnect: boolean;
}

interface SystemStatus {
  mainSystem: {
    connected: boolean;
    url: string;
    status: string;
    lastResponse: Date | null;
  };
  demoSystem: {
    connected: boolean;
    url: string;
    status: string;
    lastResponse: Date | null;
  };
}

const BeltControlView: React.FC = () => {
  const theme = useTheme();
  const viewRef = useRef<HTMLDivElement>(null);

  // Estados
  const [connectionConfig, setConnectionConfig] = useState<ConnectionConfig>(() => {
    const saved = localStorage.getItem('visifruit_belt_connections');
    return saved ? JSON.parse(saved) : {
      type: 'both',
      mainUrl: 'http://localhost:8000',
      demoUrl: 'http://localhost:8000', // Demo usa el mismo puerto pero diferentes endpoints
      autoConnect: true,
    };
  });

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    mainSystem: {
      connected: false,
      url: connectionConfig.mainUrl,
      status: 'Desconectado',
      lastResponse: null,
    },
    demoSystem: {
      connected: false,
      url: connectionConfig.demoUrl,
      status: 'Desconectado',
      lastResponse: null,
    },
  });

  const [connectionDialogOpen, setConnectionDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [externalStatus, setExternalStatus] = useState<ExternalBeltStatus | null>(null)

  // Animaciones de entrada
  useEffect(() => {
    if (viewRef.current) {
      const elements = viewRef.current.querySelectorAll('.belt-view-item');
      animate(elements, {
        opacity: [0, 1],
        translateY: [50, 0],
        duration: 800,
        delay: (_el, i) => (i as number) * 200,
        easing: 'easeOutCubic',
      });
    }
    
    // Simular carga inicial
    setTimeout(() => setIsLoading(false), 1000);
  }, []);

  // Guardar configuración de conexión
  useEffect(() => {
    localStorage.setItem('visifruit_belt_connections', JSON.stringify(connectionConfig));
  }, [connectionConfig]);

  // Función para testear conexiones
  const testConnection = useCallback(async (url: string, type: 'main' | 'demo') => {
    try {
      const response = await fetch(`${url}/health`, { 
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(5000),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(prev => ({
          ...prev,
          [`${type}System`]: {
            ...prev[`${type}System`],
            connected: true,
            status: data.status || 'Conectado',
            lastResponse: new Date(),
          },
        }));
        return true;
      }
    } catch (error) {
      setSystemStatus(prev => ({
        ...prev,
        [`${type}System`]: {
          ...prev[`${type}System`],
          connected: false,
          status: 'Error de conexión',
          lastResponse: null,
        },
      }));
    }
    return false;
  }, []);

  // Probar conexiones automáticamente
  useEffect(() => {
    if (connectionConfig.autoConnect) {
      const interval = setInterval(() => {
        if (connectionConfig.type === 'main' || connectionConfig.type === 'both') {
          testConnection(connectionConfig.mainUrl, 'main');
        }
        if (connectionConfig.type === 'demo' || connectionConfig.type === 'both') {
          testConnection(connectionConfig.demoUrl, 'demo');
        }
      }, 10000); // Cada 10 segundos

      // Test inicial inmediato
      if (connectionConfig.type === 'main' || connectionConfig.type === 'both') {
        testConnection(connectionConfig.mainUrl, 'main');
      }
      if (connectionConfig.type === 'demo' || connectionConfig.type === 'both') {
        testConnection(connectionConfig.demoUrl, 'demo');
      }

      return () => clearInterval(interval);
    }
  }, [connectionConfig, testConnection]);

  // Polling de estado real desde el sistema principal (prototipo API)
  useEffect(() => {
    let cancelled = false
    const pollIntervalMs = 2000

    const parseDirection = (dir: any): Direction => {
      if (dir === 'forward' || dir === 'backward' || dir === 'stopped') return dir
      return 'stopped'
    }

    const fetchStatusOnce = async () => {
      try {
        // Solo consultar si el sistema principal está marcado como conectado
        const base = connectionConfig.mainUrl
        // 1) Estado de banda
        const beltResp = await fetch(`${base}/belt/status`, { headers: { 'Accept': 'application/json' }, signal: AbortSignal.timeout(4000) })
        const beltJson = beltResp.ok ? await beltResp.json() : null
        // 2) Estado del stepper (DRV8825)
        const stepperResp = await fetch(`${base}/laser_stepper/status`, { headers: { 'Accept': 'application/json' }, signal: AbortSignal.timeout(4000) }).catch(() => null as any)
        const stepperJson = stepperResp && stepperResp.ok ? await stepperResp.json() : null
        // 3) Estado general para runtime (opcional)
        const statusResp = await fetch(`${base}/status`, { headers: { 'Accept': 'application/json' }, signal: AbortSignal.timeout(4000) }).catch(() => null as any)
        const statusJson = statusResp && statusResp.ok ? await statusResp.json() : null

        if (!cancelled && beltJson) {
          const isRunning = Boolean(beltJson.running)
          const direction = parseDirection(beltJson.direction)
          const speedMs = typeof beltJson.speed === 'number' ? beltJson.speed : (typeof beltJson.speed_percent === 'number' ? (beltJson.speed_percent / 100) * 2.0 : 0)
          // Mapear estado del stepper si disponible
          const isActive = Boolean(
            (typeof stepperJson?.driver?.is_active === 'boolean' && stepperJson.driver.is_active) ||
            (typeof stepperJson?.recently_active === 'boolean' && stepperJson.recently_active)
          )
          const stepper: ExternalStepperStatus = {
            isActive,
            currentPower: stepperJson?.enabled ? 100 : (isActive ? 80 : 0),
            activationCount: externalStatus?.stepperStatus.activationCount || 0,
            lastActivation: externalStatus?.stepperStatus.lastActivation || null,
            activationDuration: externalStatus?.stepperStatus.activationDuration || 0,
            totalActiveTime: externalStatus?.stepperStatus.totalActiveTime || 0,
            sensorTriggers: externalStatus?.stepperStatus.sensorTriggers || 0,
            manualActivations: externalStatus?.stepperStatus.manualActivations || 0,
            driverTemperature: externalStatus?.stepperStatus.driverTemperature || 25,
            currentStepRate: stepperJson?.driver?.enabled ? (stepperJson?.config?.base_speed_sps || 1500) : (externalStatus?.stepperStatus.currentStepRate || 0),
          }

          const now = new Date()
          setExternalStatus({
            isRunning,
            direction,
            currentSpeed: speedMs || 0,
            targetSpeed: speedMs || 0,
            motorTemperature: typeof beltJson.motor_temperature === 'number' ? beltJson.motor_temperature : 35,
            enabled: beltJson.enabled !== false,
            lastAction: isRunning ? (direction === 'forward' ? 'Banda en avance' : direction === 'backward' ? 'Banda en reversa' : 'Banda detenida') : 'Banda detenida',
            actionTime: now,
            powerConsumption: externalStatus?.powerConsumption || 0,
            vibrationLevel: externalStatus?.vibrationLevel || 0,
            totalRuntime: typeof statusJson?.stats?.uptime_s === 'number' ? statusJson.stats.uptime_s : (externalStatus?.totalRuntime || 0),
            isConnected: true,
            firmwareVersion: externalStatus?.firmwareVersion || 'v2.1.4',
            stepperStatus: stepper,
          })
        }
      } catch (err) {
        if (!cancelled) {
          // Marcar como desconectado pero no romper la UI
          setExternalStatus(prev => prev ? { ...prev, isConnected: false } : prev)
        }
      }
    }

    const id = setInterval(fetchStatusOnce, pollIntervalMs)
    // Fetch inicial rápido
    fetchStatusOnce()

    return () => { cancelled = true; clearInterval(id) }
  }, [connectionConfig, systemStatus.mainSystem.connected])

  // Handler para acciones de banda
  const handleBeltAction = async (action: string, params?: any) => {
    const promises: Promise<any>[] = [];
    const { connectionType = connectionConfig.type } = params || {};

    try {
      // Determinar a qué sistemas enviar la acción
      const shouldCallMain = connectionType === 'main' || connectionType === 'both';
      const shouldCallDemo = connectionType === 'demo' || connectionType === 'both';

      // Crear las llamadas API apropiadas
      if (shouldCallMain && systemStatus.mainSystem.connected) {
        const apiCall = callMainSystemAPI(action, params);
        promises.push(apiCall);
      }

      if (shouldCallDemo && systemStatus.demoSystem.connected) {
        const apiCall = callDemoSystemAPI(action, params);
        promises.push(apiCall);
      }

      // Ejecutar todas las llamadas en paralelo
      if (promises.length > 0) {
        await Promise.allSettled(promises);
      } else {
        throw new Error('No hay sistemas conectados para ejecutar la acción');
      }

    } catch (error) {
      console.error('Error ejecutando acción de banda:', error);
      throw error;
    }
  };

  // API para sistema principal (main_etiquetadora.py)
  const callMainSystemAPI = async (action: string, params?: any) => {
    const { mainUrl } = connectionConfig;
    
    let endpoint = '';
    let method = 'POST';
    let body: any = undefined;

    switch (action) {
      case 'start_forward':
        endpoint = '/belt/start_forward';
        break;
      case 'start_backward':
        endpoint = '/belt/start_backward';
        break;
      case 'stop':
        endpoint = '/belt/stop';
        break;
      case 'emergency_stop':
        endpoint = '/belt/emergency_stop';
        break;
      case 'set_speed':
        endpoint = '/belt/set_speed';
        body = JSON.stringify({ speed: params?.speed });
        break;
      case 'toggle_enable':
        endpoint = '/belt/toggle_enable';
        break;
      case 'sensor_activation':
        // Usar endpoint específico del prototipo para simular el sensor
        endpoint = '/sensor/simulate';
        method = 'POST';
        body = undefined;
        break;
      case 'stepper_manual_activation':
        // Prueba manual del DRV8825 (etiquetadora)
        endpoint = '/laser_stepper/test';
        method = 'POST';
        body = JSON.stringify({ 
          duration: params?.duration || 0.6,
          intensity: params?.intensity || 80.0
        });
        break;
      case 'stepper_sensor_trigger':
        // Activación asociada a trigger (equivalente a test con marca)
        endpoint = '/laser_stepper/test';
        method = 'POST';
        body = JSON.stringify({ 
          duration: params?.duration || 0.6,
          intensity: params?.intensity || 80.0,
          triggered_by: 'sensor_simulation'
        });
        break;
      default:
        throw new Error(`Acción no soportada: ${action}`);
    }

    const response = await fetch(`${mainUrl}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body,
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      throw new Error(`Error API principal: ${response.status}`);
    }

    return response.json();
  };

// API para sistema demo (demo_sistema_web_server.py en puerto 8002)
const callDemoSystemAPI = async (action: string, params?: any) => {
  try {
    const demoBaseUrl = APP_CONFIG.api.demoSystemUrl;
    
    let endpoint = '';
    let method = 'GET';
    let body = null;
    
    // Mapear acciones a endpoints del demo web server
    switch (action) {
      case 'start_forward':
        endpoint = '/belt/start_forward';
        method = 'POST';
        break;
      case 'start_backward':
        endpoint = '/belt/start_backward';
        method = 'POST';
        break;
      case 'stop':
        endpoint = '/belt/stop';
        method = 'POST';
        break;
      case 'emergency_stop':
        endpoint = '/belt/emergency_stop';
        method = 'POST';
        break;
      case 'set_speed':
        endpoint = '/belt/set_speed';
        method = 'POST';
        body = JSON.stringify({ speed: params?.speed || 0.5 });
        break;
      case 'toggle_enable':
        endpoint = '/belt/toggle_enable';
        method = 'POST';
        break;
      case 'get_status':
        endpoint = '/belt/status';
        method = 'GET';
        break;
      case 'health':
        endpoint = '/health';
        method = 'GET';
        break;
      case 'stepper_toggle':
        endpoint = '/laser_stepper/toggle';
        method = 'POST';
        body = JSON.stringify({ enabled: params?.enabled || true });
        break;
      case 'stepper_test':
        endpoint = '/laser_stepper/test';
        method = 'POST';
        body = JSON.stringify({ 
          duration: params?.duration || 0.6,
          intensity: params?.intensity || 80.0
        });
        break;
      case 'stepper_manual_activation':
        endpoint = '/laser_stepper/test';
        method = 'POST';
        body = JSON.stringify({ 
          duration: params?.duration || 0.6,
          intensity: params?.intensity || 80.0
        });
        break;
      case 'stepper_sensor_trigger':
        endpoint = '/laser_stepper/test';
        method = 'POST';
        body = JSON.stringify({ 
          duration: params?.duration || 0.6,
          intensity: params?.intensity || 80.0,
          triggered_by: 'sensor_simulation'
        });
        break;
      default:
        console.warn(`Demo API action not mapped: ${action}`);
        return { success: false, error: 'Action not supported', demo: true };
    }
    
    const response = await fetch(`${demoBaseUrl}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return { ...data, demo: true };
    
  } catch (error) {
    console.error(`Demo API error for ${action}:`, error);
    
    // Fallback a simulación si el demo server no está disponible
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.log('Demo server no disponible, usando simulación');
      return new Promise(resolve => {
        setTimeout(() => resolve({ 
          success: true, 
          demo: true, 
          simulation: true,
          message: `${action} ejecutado (simulación - demo server offline)`,
          action 
        }), 300);
      });
    }
    
    throw error;
  }
};

  const getConnectionStatusColor = (connected: boolean) => {
    return connected ? theme.palette.success.main : theme.palette.error.main;
  };

  const getConnectionIcon = (connected: boolean) => {
    return connected ? <CloudSync /> : <Cloud />;
  };

  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '80vh',
        flexDirection: 'column',
        gap: 2,
      }}>
        <DirectionsRun sx={{ fontSize: 64, color: theme.palette.primary.main, animation: 'pulse 2s infinite' }} />
        <Typography variant="h5">Cargando Control de Banda...</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box ref={viewRef}>
        {/* Encabezado */}
        <Box className="belt-view-item" sx={{ mb: 4 }}>
          <Typography 
            variant="h3" 
            sx={{ 
              fontWeight: 700,
              mb: 1,
              background: theme.gradients.primary,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Control Avanzado de Banda Transportadora
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
            Sistema inteligente con soporte dual para main_etiquetadora.py y demo_sistema_completo.py
          </Typography>

          {/* Estado de Conexiones */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Paper sx={{ 
                p: 2, 
                background: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${getConnectionStatusColor(systemStatus.mainSystem.connected)}40`,
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  {getConnectionIcon(systemStatus.mainSystem.connected)}
                  <Typography variant="subtitle1" fontWeight={600}>
                    Sistema Principal
                  </Typography>
                  <Chip 
                    size="small"
                    label={systemStatus.mainSystem.connected ? 'Conectado' : 'Desconectado'}
                    color={systemStatus.mainSystem.connected ? 'success' : 'error'}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {systemStatus.mainSystem.url}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {systemStatus.mainSystem.lastResponse 
                    ? `Última respuesta: ${systemStatus.mainSystem.lastResponse.toLocaleTimeString()}`
                    : 'Sin respuesta'
                  }
                </Typography>
              </Paper>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 4 }}>
              <Paper sx={{ 
                p: 2, 
                background: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${getConnectionStatusColor(systemStatus.demoSystem.connected)}40`,
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <SmartToy />
                  <Typography variant="subtitle1" fontWeight={600}>
                    Sistema Demo
                  </Typography>
                  <Chip 
                    size="small"
                    label={systemStatus.demoSystem.connected ? 'Conectado' : 'Desconectado'}
                    color={systemStatus.demoSystem.connected ? 'success' : 'error'}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {systemStatus.demoSystem.url}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {systemStatus.demoSystem.lastResponse 
                    ? `Última respuesta: ${systemStatus.demoSystem.lastResponse.toLocaleTimeString()}`
                    : 'Sin respuesta'
                  }
                </Typography>
              </Paper>
            </Grid>

            <Grid size={{ xs: 12, sm: 12, md: 4 }}>
              <Paper sx={{ p: 2, background: 'rgba(255, 255, 255, 0.05)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Settings />
                  <Typography variant="subtitle1" fontWeight={600}>
                    Configuración
                  </Typography>
                </Box>
                <ToggleButtonGroup
                  value={connectionConfig.type}
                  exclusive
                  onChange={(_, newType) => {
                    if (newType) {
                      setConnectionConfig(prev => ({ ...prev, type: newType }));
                    }
                  }}
                  size="small"
                  sx={{ mb: 1 }}
                >
                  <ToggleButton value="main">Principal</ToggleButton>
                  <ToggleButton value="demo">Demo</ToggleButton>
                  <ToggleButton value="both">Ambos</ToggleButton>
                </ToggleButtonGroup>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Settings />}
                  onClick={() => setConnectionDialogOpen(true)}
                  sx={{ mt: 1 }}
                >
                  Configurar Conexiones
                </Button>
              </Paper>
            </Grid>
          </Grid>

          {/* Alertas de estado */}
          {!systemStatus.mainSystem.connected && !systemStatus.demoSystem.connected && (
            <Alert 
              severity="warning" 
              sx={{ mb: 2 }}
              className="belt-view-item"
            >
              No hay sistemas conectados. Verifique las URLs y que los servicios estén ejecutándose.
            </Alert>
          )}

          {connectionConfig.type === 'both' && systemStatus.mainSystem.connected && systemStatus.demoSystem.connected && (
            <Alert 
              severity="success" 
              sx={{ mb: 2 }}
              className="belt-view-item"
            >
              Ambos sistemas conectados. Las acciones se ejecutarán en paralelo.
            </Alert>
          )}
        </Box>

        {/* Control Principal */}
        <Box className="belt-view-item">
          <BeltAdvancedControls
            onBeltAction={(action, params) => handleBeltAction(action, params)}
            isConnected={systemStatus.mainSystem.connected || systemStatus.demoSystem.connected}
            disabled={false}
            connectionType={connectionConfig.type}
            {...({ externalStatus: externalStatus || undefined } as any)}
            onConfigChange={(config) => {
              console.log('Configuración de banda actualizada:', config);
              // Guardar configuración del stepper en localStorage también
              if (config.stepperConfig) {
                localStorage.setItem('visifruit_stepper_config', JSON.stringify(config.stepperConfig));
              }
            }}
          />
        </Box>

        {/* Información adicional */}
        <Grid container spacing={3} sx={{ mt: 4 }} className="belt-view-item">
          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(78, 205, 196, 0.3)`,
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Speed sx={{ color: theme.palette.tertiary.main }} />
                  <Typography variant="h6" fontWeight={600}>
                    Características Avanzadas
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  • Control de velocidad inteligente
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  • Configuración persistente
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  • Activación automática por sensores
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  • Monitoreo en tiempo real
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  • Conexión dual main/demo
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(33, 150, 243, 0.3)`,
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Engineering sx={{ color: theme.palette.info.main }} />
                  <Typography variant="h6" fontWeight={600}>
                    Compatibilidad
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  ✅ main_etiquetadora.py
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  ✅ demo_sistema_completo.py
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  ✅ Control por API REST
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  ✅ Configuración guardada
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ✅ Modo offline/simulación
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(76, 175, 80, 0.3)`,
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <VerifiedUser sx={{ color: theme.palette.success.main }} />
                  <Typography variant="h6" fontWeight={600}>
                    Seguridad
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  🛡️ Parada de emergencia
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  🌡️ Monitoreo de temperatura
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  📊 Detección de anomalías
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  ⚡ Control de potencia
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  🔧 Modo mantenimiento
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Dialog de configuración de conexiones */}
        <Dialog
          open={connectionDialogOpen}
          onClose={() => setConnectionDialogOpen(false)}
          maxWidth="sm"
          fullWidth
          PaperProps={{
            sx: {
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            },
          }}
        >
          <DialogTitle sx={{ 
            background: theme.gradients.primary,
            color: '#000',
            fontWeight: 700,
          }}>
            Configuración de Conexiones
          </DialogTitle>
          <DialogContent sx={{ mt: 2 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Configure las URLs de conexión para cada sistema:
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                Sistema Principal (main_etiquetadora.py)
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                URL actual: {connectionConfig.mainUrl}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Puerto por defecto: 8000
              </Typography>
            </Box>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                Sistema Demo (demo_sistema_completo.py)
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                URL actual: {connectionConfig.demoUrl}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Mismo puerto, diferentes endpoints
              </Typography>
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={connectionConfig.autoConnect}
                  onChange={(e) => 
                    setConnectionConfig(prev => ({ ...prev, autoConnect: e.target.checked }))
                  }
                />
              }
              label="Conexión automática"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setConnectionDialogOpen(false)}>
              Cerrar
            </Button>
            <Button 
              onClick={() => {
                // Probar conexiones inmediatamente
                testConnection(connectionConfig.mainUrl, 'main');
                testConnection(connectionConfig.demoUrl, 'demo');
                setConnectionDialogOpen(false);
              }}
              variant="contained"
              sx={{
                background: theme.gradients.primary,
                color: '#000',
                fontWeight: 600,
              }}
            >
              Probar Conexiones
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default BeltControlView;
