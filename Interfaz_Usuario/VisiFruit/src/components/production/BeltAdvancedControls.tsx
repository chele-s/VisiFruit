import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  Switch,
  FormControlLabel,
  Slider,
  Tooltip,
  Alert,
  Snackbar,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  LinearProgress,
  Divider,
  Paper,
  Tabs,
  Tab,
  useTheme,
  styled,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  ArrowForward,
  ArrowBack,
  Stop,
  DirectionsRun,
  PowerSettingsNew,
  Speed,
  Emergency,
  Settings,
  Save,
  PlayArrow,
  Pause,
  SkipNext,
  Timeline,
  Memory,
  ThermostatAuto,
  ElectricBolt,
  MoreVert,
  Sync,
  RestartAlt,
  Build,
  Schedule,
  SmartToy,
} from '@mui/icons-material';
import { animate, stagger } from 'animejs';

// Interfaces para tipos de datos
interface BeltConfiguration {
  defaultSpeed: number;
  sensorActivationSpeed: number;
  accelerationRate: number;
  decelerationRate: number;
  autoStartOnSensor: boolean;
  emergencyStopEnabled: boolean;
  maintenanceMode: boolean;
  maxTemperature: number;
  name: string;
  description: string;
}

interface BeltStatus {
  isRunning: boolean;
  direction: 'forward' | 'backward' | 'stopped';
  currentSpeed: number;
  targetSpeed: number;
  motorTemperature: number;
  enabled: boolean;
  lastAction: string;
  actionTime: Date;
  powerConsumption: number;
  vibrationLevel: number;
  totalRuntime: number;
  isConnected: boolean;
  firmwareVersion: string;
}

interface BeltAdvancedControlsProps {
  onBeltAction?: (action: string, params?: any) => Promise<any>;
  isConnected?: boolean;
  disabled?: boolean;
  connectionType?: 'main' | 'demo' | 'both';
  onConfigChange?: (config: BeltConfiguration) => void;
}

// Componente de botón animado ultra-personalizado
const UltraAnimatedButton = styled(IconButton)(({ theme }) => ({
  position: 'relative',
  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
  borderRadius: 16,
  overflow: 'hidden',
  '&:hover': {
    transform: 'scale(1.08) translateY(-2px)',
    boxShadow: theme.shadows[12],
  },
  '&:active': {
    transform: 'scale(0.95)',
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 'inherit',
    background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
    opacity: 0,
    transition: 'opacity 0.3s ease',
  },
  '&:hover::before': {
    opacity: 1,
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    inset: 0,
    padding: '2px',
    background: theme.gradients.primary,
    borderRadius: 'inherit',
    mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
    maskComposite: 'xor',
    opacity: 0,
    transition: 'opacity 0.3s ease',
  },
  '&:hover::after': {
    opacity: 0.6,
  },
}));

const GlassCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(135deg, 
    rgba(26, 31, 36, 0.9) 0%,
    rgba(42, 47, 52, 0.8) 50%,
    rgba(26, 31, 36, 0.9) 100%
  )`,
  backdropFilter: 'blur(20px)',
  border: `1px solid rgba(0, 229, 160, 0.2)`,
  borderRadius: 20,
  overflow: 'visible',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '1px',
    background: theme.gradients.primary,
    opacity: 0.5,
  },
  '&.neon-glow': {
    boxShadow: `
      0 0 30px rgba(0, 229, 160, 0.3),
      0 8px 32px rgba(0, 0, 0, 0.3)
    `,
    '&:hover': {
      boxShadow: `
        0 0 40px rgba(0, 229, 160, 0.4),
        0 12px 48px rgba(0, 0, 0, 0.4)
      `,
      transform: 'translateY(-4px)',
    },
  },
}));

const BeltAdvancedControls: React.FC<BeltAdvancedControlsProps> = ({
  onBeltAction,
  isConnected = true,
  disabled = false,
  connectionType = 'both',
  onConfigChange,
}) => {
  const theme = useTheme();
  const controlsRef = useRef<HTMLDivElement>(null);

  // Estados principales
  const [beltStatus, setBeltStatus] = useState<BeltStatus>({
    isRunning: false,
    direction: 'stopped',
    currentSpeed: 0,
    targetSpeed: 0.5,
    motorTemperature: 35,
    enabled: true,
    lastAction: 'Sistema inicializado',
    actionTime: new Date(),
    powerConsumption: 0,
    vibrationLevel: 0,
    totalRuntime: 0,
    isConnected: true,
    firmwareVersion: 'v2.1.4',
  });

  const [configuration, setConfiguration] = useState<BeltConfiguration>(() => {
    // Cargar configuración guardada del localStorage
    const savedConfig = localStorage.getItem('visifruit_belt_config');
    return savedConfig ? JSON.parse(savedConfig) : {
      defaultSpeed: 1.0,
      sensorActivationSpeed: 1.2,
      accelerationRate: 0.5,
      decelerationRate: 0.8,
      autoStartOnSensor: true,
      emergencyStopEnabled: true,
      maintenanceMode: false,
      maxTemperature: 65,
      name: 'Banda Principal',
      description: 'Banda transportadora sistema VisiFruit',
    };
  });

  const [alertOpen, setAlertOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'warning' | 'error'>('success');
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);

  // Efectos de inicialización y animaciones
  useEffect(() => {
    if (controlsRef.current) {
      const cards = controlsRef.current.querySelectorAll('.belt-advanced-card');
      animate(cards, {
        opacity: [0, 1],
        translateY: [40, 0],
        scale: [0.9, 1],
        duration: 800,
        delay: stagger(150, { start: 300 }),
        easing: 'easeOutCubic',
      });
    }
  }, []);

  // Simular actualizaciones de estado desde el backend
  useEffect(() => {
    const interval = setInterval(() => {
      setBeltStatus(prev => {
        const newTemp = prev.isRunning 
          ? Math.min(configuration.maxTemperature, prev.motorTemperature + Math.random() * 2 - 1)
          : Math.max(25, prev.motorTemperature - 0.5);
        
        const newPower = prev.isRunning ? 150 + Math.random() * 50 : 0;
        const newVibration = prev.isRunning ? Math.random() * 2 : 0;
        
        return {
          ...prev,
          motorTemperature: newTemp,
          powerConsumption: newPower,
          vibrationLevel: newVibration,
          totalRuntime: prev.isRunning ? prev.totalRuntime + 1 : prev.totalRuntime,
        };
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [configuration.maxTemperature]);

  // Guardar configuración en localStorage cuando cambie
  useEffect(() => {
    localStorage.setItem('visifruit_belt_config', JSON.stringify(configuration));
    if (onConfigChange) {
      onConfigChange(configuration);
    }
  }, [configuration, onConfigChange]);

  const showAlert = useCallback((message: string, severity: 'success' | 'warning' | 'error' = 'success') => {
    setAlertMessage(message);
    setAlertSeverity(severity);
    setAlertOpen(true);
  }, []);

  const handleBeltAction = async (action: string, params?: any) => {
    if (disabled || !isConnected) {
      showAlert('Sistema desconectado o deshabilitado', 'error');
      return;
    }

    try {
      // Animación del botón clickeado
      const actionButton = document.querySelector(`[data-action="${action}"]`);
      if (actionButton) {
        animate(actionButton, {
          scale: [1, 0.95, 1.1, 1],
          duration: 300,
          easing: 'easeOutElastic(1, 0.5)',
        });
      }

      const newStatus = { ...beltStatus };
      let actionDescription = '';

      switch (action) {
        case 'start_forward':
          newStatus.isRunning = true;
          newStatus.direction = 'forward';
          newStatus.targetSpeed = configuration.defaultSpeed;
          actionDescription = `Banda iniciada hacia adelante a ${configuration.defaultSpeed.toFixed(1)} m/s`;
          break;
        case 'start_backward':
          newStatus.isRunning = true;
          newStatus.direction = 'backward';
          newStatus.targetSpeed = configuration.defaultSpeed;
          actionDescription = `Banda iniciada hacia atrás a ${configuration.defaultSpeed.toFixed(1)} m/s`;
          break;
        case 'stop':
          newStatus.isRunning = false;
          newStatus.direction = 'stopped';
          newStatus.targetSpeed = 0;
          newStatus.currentSpeed = 0;
          actionDescription = 'Banda detenida';
          break;
        case 'emergency_stop':
          newStatus.isRunning = false;
          newStatus.direction = 'stopped';
          newStatus.enabled = false;
          newStatus.targetSpeed = 0;
          newStatus.currentSpeed = 0;
          actionDescription = 'PARADA DE EMERGENCIA EJECUTADA';
          showAlert(actionDescription, 'error');
          break;
        case 'toggle_enable':
          newStatus.enabled = !newStatus.enabled;
          if (!newStatus.enabled) {
            newStatus.isRunning = false;
            newStatus.direction = 'stopped';
            newStatus.targetSpeed = 0;
            newStatus.currentSpeed = 0;
          }
          actionDescription = newStatus.enabled ? 'Sistema habilitado' : 'Sistema deshabilitado';
          break;
        case 'set_speed':
          newStatus.targetSpeed = params?.speed || newStatus.targetSpeed;
          if (newStatus.isRunning) {
            newStatus.currentSpeed = newStatus.targetSpeed;
          }
          actionDescription = `Velocidad objetivo establecida a ${newStatus.targetSpeed.toFixed(1)} m/s`;
          break;
        case 'sensor_activation':
          if (configuration.autoStartOnSensor && !newStatus.isRunning) {
            newStatus.isRunning = true;
            newStatus.direction = 'forward';
            newStatus.targetSpeed = configuration.sensorActivationSpeed;
            newStatus.currentSpeed = configuration.sensorActivationSpeed;
            actionDescription = `Activación por sensor: ${configuration.sensorActivationSpeed.toFixed(1)} m/s`;
          } else {
            actionDescription = 'Sensor activado (auto-inicio deshabilitado)';
          }
          break;
      }

      newStatus.lastAction = actionDescription;
      newStatus.actionTime = new Date();
      setBeltStatus(newStatus);

      // Llamar callback con configuración específica por conexión
      if (onBeltAction) {
        const apiParams = {
          ...params,
          connectionType,
          speed: action.includes('speed') ? newStatus.targetSpeed : undefined,
        };
        await onBeltAction(action, apiParams);
      }

      if (action !== 'emergency_stop') {
        showAlert(actionDescription, 'success');
      }

    } catch (error) {
      console.error('Error en acción de banda:', error);
      showAlert('Error al ejecutar acción', 'error');
    }
  };

  const handleConfigSave = () => {
    setConfiguration({ ...configuration });
    setConfigDialogOpen(false);
    showAlert('Configuración guardada correctamente', 'success');
  };

  const getDirectionIcon = () => {
    const iconProps = { fontSize: 'large' as const };
    switch (beltStatus.direction) {
      case 'forward':
        return <ArrowForward {...iconProps} sx={{ color: theme.palette.success.main }} />;
      case 'backward':
        return <ArrowBack {...iconProps} sx={{ color: theme.palette.warning.main }} />;
      default:
        return <Stop {...iconProps} sx={{ color: theme.palette.grey[500] }} />;
    }
  };

  const getStatusChip = () => {
    if (!beltStatus.enabled) {
      return <Chip label="SISTEMA DESHABILITADO" color="error" variant="filled" size="small" 
        sx={{ fontWeight: 600, animation: 'pulse 2s infinite' }} />;
    }
    
    switch (beltStatus.direction) {
      case 'forward':
        return <Chip label="FUNCIONANDO ADELANTE" color="success" variant="filled" size="small"
          sx={{ fontWeight: 600, animation: 'pulse 2s infinite' }} />;
      case 'backward':
        return <Chip label="FUNCIONANDO ATRÁS" color="warning" variant="filled" size="small"
          sx={{ fontWeight: 600, animation: 'pulse 2s infinite' }} />;
      default:
        return <Chip label="DETENIDO" color="default" variant="outlined" size="small" />;
    }
  };

  const getTemperatureColor = (temp: number) => {
    if (temp > configuration.maxTemperature * 0.9) return theme.palette.error.main;
    if (temp > configuration.maxTemperature * 0.75) return theme.palette.warning.main;
    return theme.palette.success.main;
  };

  const formatRuntime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <Box ref={controlsRef} sx={{ display: 'flex', flexDirection: 'column', gap: 4, p: 2 }}>
      {/* Encabezado Principal */}
      <GlassCard className="belt-advanced-card neon-glow">
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: '16px',
                  background: theme.gradients.primary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: theme.shadows[6],
                }}
              >
                <DirectionsRun sx={{ fontSize: 32, color: '#000' }} />
              </Box>
              <Box>
                <Typography variant="h4" sx={{ 
                  fontWeight: 700,
                  background: theme.gradients.primary,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  mb: 0.5,
                }}>
                  Control Avanzado de Banda
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                  {configuration.name} • {configuration.description}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {getStatusChip()}
              <IconButton
                onClick={(e) => setMenuAnchorEl(e.currentTarget)}
                sx={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  '&:hover': { background: 'rgba(255, 255, 255, 0.2)' },
                }}
              >
                <MoreVert />
              </IconButton>
            </Box>
          </Box>

          {/* Métricas principales en tiempo real */}
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, background: 'rgba(0, 229, 160, 0.1)', borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Speed sx={{ color: theme.palette.primary.main }} />
                  <Typography variant="subtitle2" fontWeight={600}>Velocidad</Typography>
                </Box>
                <Typography variant="h5" fontWeight={700}>
                  {beltStatus.currentSpeed.toFixed(1)} m/s
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Objetivo: {beltStatus.targetSpeed.toFixed(1)} m/s
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, background: 'rgba(255, 107, 107, 0.1)', borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <ThermostatAuto sx={{ color: getTemperatureColor(beltStatus.motorTemperature) }} />
                  <Typography variant="subtitle2" fontWeight={600}>Temperatura</Typography>
                </Box>
                <Typography variant="h5" fontWeight={700}>
                  {beltStatus.motorTemperature.toFixed(1)}°C
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={(beltStatus.motorTemperature / configuration.maxTemperature) * 100}
                  sx={{
                    mt: 1,
                    height: 4,
                    borderRadius: 2,
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getTemperatureColor(beltStatus.motorTemperature),
                    },
                  }}
                />
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, background: 'rgba(78, 205, 196, 0.1)', borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <ElectricBolt sx={{ color: theme.palette.tertiary.main }} />
                  <Typography variant="subtitle2" fontWeight={600}>Consumo</Typography>
                </Box>
                <Typography variant="h5" fontWeight={700}>
                  {beltStatus.powerConsumption.toFixed(0)}W
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Eficiencia: 89%
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, background: 'rgba(33, 150, 243, 0.1)', borderRadius: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Schedule sx={{ color: theme.palette.info.main }} />
                  <Typography variant="subtitle2" fontWeight={600}>Tiempo Activo</Typography>
                </Box>
                <Typography variant="h6" fontWeight={700}>
                  {formatRuntime(beltStatus.totalRuntime)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Hoy: {formatRuntime(beltStatus.totalRuntime * 0.3)}
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </GlassCard>

      {/* Controles Principales */}
      <GlassCard className="belt-advanced-card neon-glow">
        <CardContent>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
            <PlayArrow sx={{ color: theme.palette.primary.main }} />
            Controles de Dirección
          </Typography>

          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 4, mb: 4 }}>
            <Tooltip title="Iniciar banda hacia adelante" placement="top">
              <span>
                <UltraAnimatedButton
                  data-action="start_forward"
                  size="large"
                  onClick={() => handleBeltAction('start_forward')}
                  disabled={disabled || !beltStatus.enabled || beltStatus.direction === 'forward'}
                  sx={{
                    width: 100,
                    height: 100,
                    background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(76, 175, 80, 0.1))',
                    color: theme.palette.success.main,
                    '&:hover': {
                      background: 'linear-gradient(135deg, rgba(76, 175, 80, 0.5), rgba(76, 175, 80, 0.2))',
                    },
                    '&:disabled': { opacity: 0.3 },
                  }}
                >
                  <ArrowForward sx={{ fontSize: 48 }} />
                </UltraAnimatedButton>
              </span>
            </Tooltip>

            <Tooltip title="Detener banda" placement="top">
              <span>
                <UltraAnimatedButton
                  data-action="stop"
                  size="large"
                  onClick={() => handleBeltAction('stop')}
                  disabled={disabled || !beltStatus.enabled || beltStatus.direction === 'stopped'}
                  sx={{
                    width: 100,
                    height: 100,
                    background: 'linear-gradient(135deg, rgba(158, 158, 158, 0.3), rgba(158, 158, 158, 0.1))',
                    color: theme.palette.grey[400],
                    '&:hover': {
                      background: 'linear-gradient(135deg, rgba(158, 158, 158, 0.5), rgba(158, 158, 158, 0.2))',
                    },
                    '&:disabled': { opacity: 0.3 },
                  }}
                >
                  <Stop sx={{ fontSize: 48 }} />
                </UltraAnimatedButton>
              </span>
            </Tooltip>

            <Tooltip title="Iniciar banda hacia atrás" placement="top">
              <span>
                <UltraAnimatedButton
                  data-action="start_backward"
                  size="large"
                  onClick={() => handleBeltAction('start_backward')}
                  disabled={disabled || !beltStatus.enabled || beltStatus.direction === 'backward'}
                  sx={{
                    width: 100,
                    height: 100,
                    background: 'linear-gradient(135deg, rgba(255, 193, 7, 0.3), rgba(255, 193, 7, 0.1))',
                    color: theme.palette.warning.main,
                    '&:hover': {
                      background: 'linear-gradient(135deg, rgba(255, 193, 7, 0.5), rgba(255, 193, 7, 0.2))',
                    },
                    '&:disabled': { opacity: 0.3 },
                  }}
                >
                  <ArrowBack sx={{ fontSize: 48 }} />
                </UltraAnimatedButton>
              </span>
            </Tooltip>
          </Box>

          <Divider sx={{ my: 3, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

          {/* Control de Velocidad Avanzado */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Speed sx={{ color: theme.palette.primary.main }} />
              Control de Velocidad Inteligente
            </Typography>
            <Box sx={{ px: 3 }}>
              <Slider
                value={beltStatus.targetSpeed}
                onChange={(_, newValue) => {
                  setBeltStatus(prev => ({ ...prev, targetSpeed: newValue as number }));
                }}
                onChangeCommitted={(_, newValue) => {
                  handleBeltAction('set_speed', { speed: newValue });
                }}
                min={0.1}
                max={2.5}
                step={0.1}
                marks={[
                  { value: 0.5, label: '0.5 m/s' },
                  { value: 1.0, label: '1.0 m/s' },
                  { value: 1.5, label: '1.5 m/s' },
                  { value: 2.0, label: '2.0 m/s' },
                  { value: 2.5, label: '2.5 m/s' },
                ]}
                disabled={disabled || !beltStatus.enabled}
                sx={{
                  color: theme.palette.primary.main,
                  height: 12,
                  '& .MuiSlider-thumb': {
                    width: 24,
                    height: 24,
                    boxShadow: theme.shadows[8],
                    background: theme.gradients.primary,
                    border: '3px solid rgba(255, 255, 255, 0.2)',
                    '&:hover': {
                      boxShadow: theme.shadows[12],
                    },
                  },
                  '& .MuiSlider-track': {
                    height: 8,
                    background: theme.gradients.primary,
                    borderRadius: 4,
                  },
                  '& .MuiSlider-rail': {
                    height: 8,
                    borderRadius: 4,
                    background: 'rgba(255, 255, 255, 0.1)',
                  },
                  '& .MuiSlider-mark': {
                    width: 4,
                    height: 4,
                    borderRadius: '50%',
                    backgroundColor: theme.palette.primary.main,
                  },
                  '& .MuiSlider-markLabel': {
                    fontSize: '0.8rem',
                    fontWeight: 500,
                  },
                }}
              />
            </Box>
          </Box>

          {/* Controles de Sistema */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={beltStatus.enabled}
                    onChange={() => handleBeltAction('toggle_enable')}
                    disabled={disabled}
                    color="primary"
                    size="medium"
                  />
                }
                label={
                  <Typography variant="body1" fontWeight={600}>
                    Sistema Habilitado
                  </Typography>
                }
              />
              
              <Button
                variant="outlined"
                startIcon={<Settings />}
                onClick={() => setConfigDialogOpen(true)}
                sx={{
                  borderColor: theme.palette.primary.main,
                  color: theme.palette.primary.main,
                  '&:hover': {
                    backgroundColor: 'rgba(0, 229, 160, 0.08)',
                    borderColor: theme.palette.primary.light,
                  },
                }}
              >
                Configuración
              </Button>
            </Box>

            <Tooltip title="PARADA DE EMERGENCIA" placement="top">
              <span>
                <UltraAnimatedButton
                  data-action="emergency_stop"
                  onClick={() => handleBeltAction('emergency_stop')}
                  disabled={disabled}
                  sx={{
                    background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.4), rgba(244, 67, 54, 0.2))',
                    color: theme.palette.error.main,
                    width: 60,
                    height: 60,
                    '&:hover': {
                      background: 'linear-gradient(135deg, rgba(244, 67, 54, 0.6), rgba(244, 67, 54, 0.3))',
                      transform: 'scale(1.15)',
                    },
                  }}
                >
                  <Emergency sx={{ fontSize: 32 }} />
                </UltraAnimatedButton>
              </span>
            </Tooltip>
          </Box>
        </CardContent>
      </GlassCard>

      {/* Sistema de Configuración Inteligente */}
      <GlassCard className="belt-advanced-card">
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
            <SmartToy sx={{ color: theme.palette.tertiary.main }} />
            Configuración Inteligente de Sensores
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.05)', borderRadius: 2 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                  Activación Automática
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={configuration.autoStartOnSensor}
                      onChange={(e) => 
                        setConfiguration(prev => ({ ...prev, autoStartOnSensor: e.target.checked }))
                      }
                      color="primary"
                    />
                  }
                  label="Auto-inicio al detectar sensor"
                  sx={{ mb: 2 }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Velocidad al detectar sensor:
                </Typography>
                <Slider
                  value={configuration.sensorActivationSpeed}
                  onChange={(_, value) => 
                    setConfiguration(prev => ({ ...prev, sensorActivationSpeed: value as number }))
                  }
                  min={0.1}
                  max={2.5}
                  step={0.1}
                  marks={[
                    { value: 0.5, label: '0.5' },
                    { value: 1.5, label: '1.5' },
                    { value: 2.5, label: '2.5' },
                  ]}
                  sx={{ color: theme.palette.tertiary.main }}
                />
                <Typography variant="caption" color="text.secondary">
                  Configurado: {configuration.sensorActivationSpeed.toFixed(1)} m/s
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, background: 'rgba(255, 255, 255, 0.05)', borderRadius: 2 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                  Prueba de Sensor
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Simular activación del sensor para probar la configuración
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<Timeline />}
                  onClick={() => handleBeltAction('sensor_activation')}
                  disabled={disabled || !beltStatus.enabled}
                  sx={{
                    background: theme.gradients.tertiary,
                    color: '#000',
                    fontWeight: 600,
                    '&:hover': {
                      background: theme.gradients.tertiary,
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  Activar Sensor de Prueba
                </Button>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </GlassCard>

      {/* Estado del Sistema e Información */}
      <GlassCard className="belt-advanced-card">
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Memory sx={{ color: theme.palette.info.main }} />
              Estado del Sistema
            </Typography>
            <Chip
              label={isConnected ? `Conectado (${connectionType})` : "Desconectado"}
              color={isConnected ? "success" : "error"}
              variant="outlined"
              icon={isConnected ? <Sync /> : <Emergency />}
            />
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">Última Acción:</Typography>
                <Typography variant="body2" fontWeight={500}>{beltStatus.lastAction}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">Hora:</Typography>
                <Typography variant="body2">
                  {beltStatus.actionTime.toLocaleTimeString('es-ES')}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">Firmware:</Typography>
                <Typography variant="body2">{beltStatus.firmwareVersion}</Typography>
              </Box>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">Vibración:</Typography>
                <Typography variant="body2">{beltStatus.vibrationLevel.toFixed(2)} mm/s</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">Tipo de Conexión:</Typography>
                <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{connectionType}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                <Typography variant="body2" color="text.secondary">Modo:</Typography>
                <Typography variant="body2">
                  {configuration.maintenanceMode ? 'Mantenimiento' : 'Producción'}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </GlassCard>

      {/* Dialog de Configuración */}
      <Dialog 
        open={configDialogOpen} 
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="md"
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
          Configuración Avanzada de Banda
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Tabs value={currentTab} onChange={(_, newTab) => setCurrentTab(newTab)}>
            <Tab label="General" />
            <Tab label="Sensores" />
            <Tab label="Seguridad" />
          </Tabs>

          {currentTab === 0 && (
            <Box sx={{ mt: 3 }}>
              <TextField
                fullWidth
                label="Nombre de la Banda"
                value={configuration.name}
                onChange={(e) => setConfiguration(prev => ({ ...prev, name: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Descripción"
                multiline
                rows={3}
                value={configuration.description}
                onChange={(e) => setConfiguration(prev => ({ ...prev, description: e.target.value }))}
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" sx={{ mb: 1 }}>
                Velocidad por defecto: {configuration.defaultSpeed.toFixed(1)} m/s
              </Typography>
              <Slider
                value={configuration.defaultSpeed}
                onChange={(_, value) => setConfiguration(prev => ({ ...prev, defaultSpeed: value as number }))}
                min={0.1}
                max={2.5}
                step={0.1}
                sx={{ mb: 2 }}
              />
            </Box>
          )}

          {currentTab === 1 && (
            <Box sx={{ mt: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={configuration.autoStartOnSensor}
                    onChange={(e) => setConfiguration(prev => ({ ...prev, autoStartOnSensor: e.target.checked }))}
                  />
                }
                label="Auto-inicio al detectar sensor"
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" sx={{ mb: 1 }}>
                Velocidad de activación por sensor: {configuration.sensorActivationSpeed.toFixed(1)} m/s
              </Typography>
              <Slider
                value={configuration.sensorActivationSpeed}
                onChange={(_, value) => setConfiguration(prev => ({ ...prev, sensorActivationSpeed: value as number }))}
                min={0.1}
                max={2.5}
                step={0.1}
                sx={{ mb: 2 }}
              />
            </Box>
          )}

          {currentTab === 2 && (
            <Box sx={{ mt: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={configuration.emergencyStopEnabled}
                    onChange={(e) => setConfiguration(prev => ({ ...prev, emergencyStopEnabled: e.target.checked }))}
                  />
                }
                label="Parada de emergencia habilitada"
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" sx={{ mb: 1 }}>
                Temperatura máxima: {configuration.maxTemperature}°C
              </Typography>
              <Slider
                value={configuration.maxTemperature}
                onChange={(_, value) => setConfiguration(prev => ({ ...prev, maxTemperature: value as number }))}
                min={40}
                max={80}
                step={5}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={configuration.maintenanceMode}
                    onChange={(e) => setConfiguration(prev => ({ ...prev, maintenanceMode: e.target.checked }))}
                  />
                }
                label="Modo mantenimiento"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleConfigSave}
            variant="contained"
            startIcon={<Save />}
            sx={{
              background: theme.gradients.primary,
              color: '#000',
              fontWeight: 600,
            }}
          >
            Guardar Configuración
          </Button>
        </DialogActions>
      </Dialog>

      {/* Menu contextual */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={() => setMenuAnchorEl(null)}
        PaperProps={{
          sx: {
            background: theme.gradients.glass,
            backdropFilter: 'blur(20px)',
            border: `1px solid rgba(255, 255, 255, 0.1)`,
          },
        }}
      >
        <MenuItem onClick={() => { handleBeltAction('toggle_enable'); setMenuAnchorEl(null); }}>
          <ListItemIcon>
            <PowerSettingsNew />
          </ListItemIcon>
          <ListItemText primary={beltStatus.enabled ? "Deshabilitar Sistema" : "Habilitar Sistema"} />
        </MenuItem>
        <MenuItem onClick={() => { setConfigDialogOpen(true); setMenuAnchorEl(null); }}>
          <ListItemIcon>
            <Settings />
          </ListItemIcon>
          <ListItemText primary="Configuración Avanzada" />
        </MenuItem>
        <MenuItem onClick={() => { window.location.reload(); setMenuAnchorEl(null); }}>
          <ListItemIcon>
            <RestartAlt />
          </ListItemIcon>
          <ListItemText primary="Reiniciar Sistema" />
        </MenuItem>
      </Menu>

      {/* Snackbar para alertas */}
      <Snackbar
        open={alertOpen}
        autoHideDuration={5000}
        onClose={() => setAlertOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setAlertOpen(false)} 
          severity={alertSeverity} 
          sx={{ 
            width: '100%',
            background: theme.gradients.glass,
            backdropFilter: 'blur(20px)',
            border: `1px solid rgba(255, 255, 255, 0.1)`,
          }}
        >
          {alertMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default BeltAdvancedControls;
