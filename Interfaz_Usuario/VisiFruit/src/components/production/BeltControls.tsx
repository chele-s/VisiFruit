import React, { useState, useEffect } from 'react';
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
  useTheme,
  styled,
} from '@mui/material';
import {
  ArrowForward,
  ArrowBack,
  Stop,
  DirectionsRun,
  PowerSettingsNew,
  Speed,
  Emergency,
  SwapHoriz,
  Settings,
} from '@mui/icons-material';
import { animate } from 'animejs';

// Interfaces para tipos de datos
interface BeltStatus {
  isRunning: boolean;
  direction: 'forward' | 'backward' | 'stopped';
  speed: number;
  motorTemperature: number;
  enabled: boolean;
  lastAction: string;
  actionTime: Date;
}

interface BeltControlsProps {
  onBeltAction?: (action: string, params?: any) => void;
  isConnected?: boolean;
  disabled?: boolean;
}

// Componente de botón animado personalizado
const AnimatedIconButton = styled(IconButton)(({ theme }) => ({
  position: 'relative',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    transform: 'scale(1.08)',
    boxShadow: theme.shadows[8],
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
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
    opacity: 0,
    transition: 'opacity 0.3s ease',
  },
  '&:hover::before': {
    opacity: 1,
  },
}));

const BeltControls: React.FC<BeltControlsProps> = ({
  onBeltAction,
  isConnected = true,
  disabled = false,
}) => {
  const theme = useTheme();
  const [beltStatus, setBeltStatus] = useState<BeltStatus>({
    isRunning: false,
    direction: 'stopped',
    speed: 0.5,
    motorTemperature: 35,
    enabled: true,
    lastAction: 'Sistema iniciado',
    actionTime: new Date(),
  });

  const [alertOpen, setAlertOpen] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'warning' | 'error'>('success');

  // Simular actualizaciones de estado desde el backend
  useEffect(() => {
    const interval = setInterval(() => {
      // Simular variación de temperatura del motor
      setBeltStatus(prev => ({
        ...prev,
        motorTemperature: prev.isRunning 
          ? Math.min(65, prev.motorTemperature + Math.random() * 2 - 1)
          : Math.max(25, prev.motorTemperature - 0.5),
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Efectos de animación
  useEffect(() => {
    const cards = document.querySelectorAll('.belt-control-card');
    animate(cards, {
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 600,
      delay: (el, i) => i * 150,
      easing: 'easeOutCubic',
    });
  }, []);

  const showAlert = (message: string, severity: 'success' | 'warning' | 'error' = 'success') => {
    setAlertMessage(message);
    setAlertSeverity(severity);
    setAlertOpen(true);
  };

  const handleBeltAction = async (action: string, params?: any) => {
    if (disabled || !isConnected) {
      showAlert('Sistema desconectado o deshabilitado', 'error');
      return;
    }

    try {
      const newStatus = { ...beltStatus };
      let actionDescription = '';

      switch (action) {
        case 'start_forward':
          newStatus.isRunning = true;
          newStatus.direction = 'forward';
          actionDescription = 'Banda iniciada hacia adelante';
          break;
        case 'start_backward':
          newStatus.isRunning = true;
          newStatus.direction = 'backward';
          actionDescription = 'Banda iniciada hacia atrás';
          break;
        case 'stop':
          newStatus.isRunning = false;
          newStatus.direction = 'stopped';
          actionDescription = 'Banda detenida';
          break;
        case 'emergency_stop':
          newStatus.isRunning = false;
          newStatus.direction = 'stopped';
          newStatus.enabled = false;
          actionDescription = 'PARADA DE EMERGENCIA';
          showAlert(actionDescription, 'error');
          break;
        case 'toggle_enable':
          newStatus.enabled = !newStatus.enabled;
          if (!newStatus.enabled) {
            newStatus.isRunning = false;
            newStatus.direction = 'stopped';
          }
          actionDescription = newStatus.enabled ? 'Sistema habilitado' : 'Sistema deshabilitado';
          break;
        case 'set_speed':
          newStatus.speed = params?.speed || newStatus.speed;
          actionDescription = `Velocidad ajustada a ${newStatus.speed.toFixed(1)} m/s`;
          break;
      }

      newStatus.lastAction = actionDescription;
      newStatus.actionTime = new Date();
      setBeltStatus(newStatus);

      // Llamar callback si existe
      if (onBeltAction) {
        await onBeltAction(action, params);
      }

      if (action !== 'emergency_stop') {
        showAlert(actionDescription, 'success');
      }

    } catch (error) {
      console.error('Error en acción de banda:', error);
      showAlert('Error al ejecutar acción', 'error');
    }
  };

  const getDirectionIcon = () => {
    switch (beltStatus.direction) {
      case 'forward':
        return <ArrowForward sx={{ color: theme.palette.success.main }} />;
      case 'backward':
        return <ArrowBack sx={{ color: theme.palette.warning.main }} />;
      default:
        return <Stop sx={{ color: theme.palette.grey[500] }} />;
    }
  };

  const getStatusChip = () => {
    if (!beltStatus.enabled) {
      return <Chip label="DESHABILITADO" color="error" variant="outlined" />;
    }
    
    switch (beltStatus.direction) {
      case 'forward':
        return <Chip label="ADELANTE" color="success" />;
      case 'backward':
        return <Chip label="ATRÁS" color="warning" />;
      default:
        return <Chip label="DETENIDO" color="default" />;
    }
  };

  const getTemperatureColor = (temp: number) => {
    if (temp > 55) return theme.palette.error.main;
    if (temp > 45) return theme.palette.warning.main;
    return theme.palette.success.main;
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Estado Principal */}
      <Card className="belt-control-card" sx={{
        background: theme.gradients?.glass || 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        border: `1px solid rgba(255, 255, 255, 0.1)`,
      }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              <DirectionsRun sx={{ color: theme.palette.primary.main }} />
              Control de Banda Transportadora
            </Typography>
            {getStatusChip()}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Box sx={{ 
              p: 2, 
              borderRadius: 2, 
              background: 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}>
              {getDirectionIcon()}
              <Typography variant="body2">
                Dirección: {beltStatus.direction === 'forward' ? 'Adelante' : 
                          beltStatus.direction === 'backward' ? 'Atrás' : 'Detenido'}
              </Typography>
            </Box>
            
            <Box sx={{ 
              p: 2, 
              borderRadius: 2, 
              background: 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}>
              <Speed sx={{ color: theme.palette.info.main }} />
              <Typography variant="body2">
                Velocidad: {beltStatus.speed.toFixed(1)} m/s
              </Typography>
            </Box>

            <Box sx={{ 
              p: 2, 
              borderRadius: 2, 
              background: 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}>
              <Box sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: getTemperatureColor(beltStatus.motorTemperature),
                animation: 'pulse 2s infinite',
              }} />
              <Typography variant="body2">
                Temp: {beltStatus.motorTemperature.toFixed(1)}°C
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Controles Principales */}
      <Card className="belt-control-card" sx={{
        background: theme.gradients?.glass || 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        border: `1px solid rgba(255, 255, 255, 0.1)`,
      }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
            Controles de Dirección
          </Typography>

          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mb: 3 }}>
            <Tooltip title="Iniciar banda hacia adelante" placement="top">
              <span>
                <AnimatedIconButton
                  size="large"
                  onClick={() => handleBeltAction('start_forward')}
                  disabled={disabled || !beltStatus.enabled || beltStatus.direction === 'forward'}
                  sx={{
                    background: 'rgba(76, 175, 80, 0.2)',
                    color: theme.palette.success.main,
                    width: 80,
                    height: 80,
                    '&:hover': {
                      background: 'rgba(76, 175, 80, 0.3)',
                    },
                    '&:disabled': {
                      opacity: 0.5,
                    },
                  }}
                >
                  <ArrowForward sx={{ fontSize: 40 }} />
                </AnimatedIconButton>
              </span>
            </Tooltip>

            <Tooltip title="Detener banda" placement="top">
              <span>
                <AnimatedIconButton
                  size="large"
                  onClick={() => handleBeltAction('stop')}
                  disabled={disabled || !beltStatus.enabled || beltStatus.direction === 'stopped'}
                  sx={{
                    background: 'rgba(158, 158, 158, 0.2)',
                    color: theme.palette.grey[400],
                    width: 80,
                    height: 80,
                    '&:hover': {
                      background: 'rgba(158, 158, 158, 0.3)',
                    },
                    '&:disabled': {
                      opacity: 0.5,
                    },
                  }}
                >
                  <Stop sx={{ fontSize: 40 }} />
                </AnimatedIconButton>
              </span>
            </Tooltip>

            <Tooltip title="Iniciar banda hacia atrás" placement="top">
              <span>
                <AnimatedIconButton
                  size="large"
                  onClick={() => handleBeltAction('start_backward')}
                  disabled={disabled || !beltStatus.enabled || beltStatus.direction === 'backward'}
                  sx={{
                    background: 'rgba(255, 193, 7, 0.2)',
                    color: theme.palette.warning.main,
                    width: 80,
                    height: 80,
                    '&:hover': {
                      background: 'rgba(255, 193, 7, 0.3)',
                    },
                    '&:disabled': {
                      opacity: 0.5,
                    },
                  }}
                >
                  <ArrowBack sx={{ fontSize: 40 }} />
                </AnimatedIconButton>
              </span>
            </Tooltip>
          </Box>

          {/* Control de Velocidad */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
              Control de Velocidad
            </Typography>
            <Box sx={{ px: 2 }}>
              <Slider
                value={beltStatus.speed}
                onChange={(_, newValue) => {
                  setBeltStatus(prev => ({ ...prev, speed: newValue as number }));
                }}
                onChangeCommitted={(_, newValue) => {
                  handleBeltAction('set_speed', { speed: newValue });
                }}
                min={0.1}
                max={2.0}
                step={0.1}
                marks={[
                  { value: 0.5, label: '0.5 m/s' },
                  { value: 1.0, label: '1.0 m/s' },
                  { value: 1.5, label: '1.5 m/s' },
                ]}
                disabled={disabled || !beltStatus.enabled}
                sx={{
                  color: theme.palette.primary.main,
                  '& .MuiSlider-thumb': {
                    boxShadow: theme.shadows[4],
                  },
                  '& .MuiSlider-track': {
                    background: theme.gradients?.primary || theme.palette.primary.main,
                  },
                }}
              />
            </Box>
          </Box>

          {/* Controles de Sistema */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={beltStatus.enabled}
                  onChange={() => handleBeltAction('toggle_enable')}
                  disabled={disabled}
                  color="primary"
                />
              }
              label="Sistema Habilitado"
            />

            <Tooltip title="PARADA DE EMERGENCIA" placement="top">
              <span>
                <AnimatedIconButton
                  onClick={() => handleBeltAction('emergency_stop')}
                  disabled={disabled}
                  sx={{
                    background: 'rgba(244, 67, 54, 0.2)',
                    color: theme.palette.error.main,
                    '&:hover': {
                      background: 'rgba(244, 67, 54, 0.4)',
                      transform: 'scale(1.1)',
                    },
                  }}
                >
                  <Emergency />
                </AnimatedIconButton>
              </span>
            </Tooltip>
          </Box>
        </CardContent>
      </Card>

      {/* Información del Sistema */}
      <Card className="belt-control-card" sx={{
        background: theme.gradients?.glass || 'rgba(255, 255, 255, 0.05)',
        backdropFilter: 'blur(10px)',
        border: `1px solid rgba(255, 255, 255, 0.1)`,
      }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Estado del Sistema
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Última Acción:</Typography>
              <Typography variant="body2">{beltStatus.lastAction}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Hora:</Typography>
              <Typography variant="body2">
                {beltStatus.actionTime.toLocaleTimeString('es-ES')}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">Estado de Conexión:</Typography>
              <Chip 
                label={isConnected ? "Conectado" : "Desconectado"} 
                color={isConnected ? "success" : "error"} 
                size="small" 
                variant="outlined"
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Snackbar para alertas */}
      <Snackbar
        open={alertOpen}
        autoHideDuration={4000}
        onClose={() => setAlertOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setAlertOpen(false)} 
          severity={alertSeverity} 
          sx={{ width: '100%' }}
        >
          {alertMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default BeltControls;
