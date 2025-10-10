import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Slider,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  ButtonGroup,
  IconButton,
  Chip,
  Alert,
  Collapse,
  TextField,
  Tooltip,
  LinearProgress,
  Paper,
  Divider,
  useTheme,
  styled,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  RotateRight,
  PlayArrow,
  TuneRounded,
  Engineering,
  Memory,
  Warning,
  CheckCircle,
  ExpandMore,
  ExpandLess,
  RestartAlt,
} from '@mui/icons-material';

// Interfaces
interface ServoCalibration {
  minPulseMs: number;
  maxPulseMs: number;
  minAngle: number;
  maxAngle: number;
  centerPulseMs: number;
  centerAngle: number;
}

interface ServoConfig {
  id: string;
  name: string;
  pinBcm: number;
  calibration: ServoCalibration;
  defaultAngle: number;
  activationAngle: number;
  direction: 'forward' | 'reverse';
  movementSpeed: number;
  smoothMovement: boolean;
  smoothSteps: number;
  minSafeAngle: number;
  maxSafeAngle: number;
  holdTorque: boolean;
  profile: 'mg995_standard' | 'mg995_extended' | 'mg996r' | 'custom';
}

interface ServoStatus {
  id: string;
  name: string;
  pin: number;
  initialized: boolean;
  currentAngle: number;
  targetAngle: number;
  isMoving: boolean;
  direction: string;
  profile: string;
  hardwarePwm: boolean;
  activationCount: number;
  lastActivation: Date | null;
}

interface ServoControlPanelProps {
  servos?: ServoConfig[];
  onServoAction?: (servoId: string, action: string, params?: any) => Promise<any>;
  onConfigUpdate?: (servoId: string, config: Partial<ServoConfig>) => Promise<any>;
  isConnected?: boolean;
  disabled?: boolean;
}

// Styled Components
const GlassCard = styled(Card)(() => ({
  background: `linear-gradient(135deg, 
    rgba(26, 31, 36, 0.95) 0%,
    rgba(42, 47, 52, 0.85) 50%,
    rgba(26, 31, 36, 0.95) 100%
  )`,
  backdropFilter: 'blur(20px)',
  border: `1px solid rgba(0, 229, 160, 0.2)`,
  borderRadius: 16,
  overflow: 'visible',
  position: 'relative',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: `0 8px 32px rgba(0, 229, 160, 0.15)`,
  },
}));

const ControlButton = styled(Button)(({ theme }) => ({
  borderRadius: 12,
  textTransform: 'none',
  fontWeight: 600,
  padding: '10px 20px',
  transition: 'all 0.3s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[8],
  },
}));

const ServoControlPanel: React.FC<ServoControlPanelProps> = ({
  servos = [],
  onServoAction,
  onConfigUpdate,
  isConnected = true,
  disabled = false,
}) => {
  const theme = useTheme();
  
  // Estados
  const [servoConfigs, setServoConfigs] = useState<ServoConfig[]>(() => {
    // Configuración por defecto para 2 servos MG995
    const defaultServos: ServoConfig[] = [
      {
        id: 'servo1',
        name: 'Servo Clasificador 1',
        pinBcm: 12, // Hardware PWM en Pi 5
        calibration: {
          minPulseMs: 1.0,
          maxPulseMs: 2.0,
          minAngle: 0,
          maxAngle: 180,
          centerPulseMs: 1.5,
          centerAngle: 90,
        },
        defaultAngle: 90,
        activationAngle: 0,
        direction: 'forward',
        movementSpeed: 0.8,
        smoothMovement: true,
        smoothSteps: 20,
        minSafeAngle: 0,
        maxSafeAngle: 180,
        holdTorque: true,
        profile: 'mg995_standard',
      },
      {
        id: 'servo2',
        name: 'Servo Clasificador 2',
        pinBcm: 13, // Hardware PWM en Pi 5
        calibration: {
          minPulseMs: 1.0,
          maxPulseMs: 2.0,
          minAngle: 0,
          maxAngle: 180,
          centerPulseMs: 1.5,
          centerAngle: 90,
        },
        defaultAngle: 90,
        activationAngle: 180,
        direction: 'forward',
        movementSpeed: 0.8,
        smoothMovement: true,
        smoothSteps: 20,
        minSafeAngle: 0,
        maxSafeAngle: 180,
        holdTorque: true,
        profile: 'mg995_standard',
      },
    ];
    
    return servos.length > 0 ? servos : defaultServos;
  });
  
  const [servoStatuses, setServoStatuses] = useState<Record<string, ServoStatus>>({});
  const [expandedServos, setExpandedServos] = useState<Record<string, boolean>>({});
  const [testDialogOpen, setTestDialogOpen] = useState<string | null>(null);
  const [calibrationDialogOpen, setCalibrationDialogOpen] = useState<string | null>(null);
  const [testAngle, setTestAngle] = useState<number>(90);
  const [alertMessage, setAlertMessage] = useState<{ message: string; severity: 'success' | 'error' | 'warning' } | null>(null);

  // Cargar configuración guardada
  useEffect(() => {
    const savedConfig = localStorage.getItem('visifruit_servo_config');
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig);
        setServoConfigs(parsed);
      } catch (e) {
        console.error('Error loading servo config:', e);
      }
    }
  }, []);

  // Guardar configuración cuando cambie
  useEffect(() => {
    localStorage.setItem('visifruit_servo_config', JSON.stringify(servoConfigs));
  }, [servoConfigs]);

  // Actualizar estado de servos (polling simulado)
  useEffect(() => {
    const interval = setInterval(() => {
      // Simular actualización de estado
      setServoStatuses(prev => {
        const newStatuses: Record<string, ServoStatus> = {};
        
        servoConfigs.forEach(config => {
          const existing = prev[config.id];
          newStatuses[config.id] = {
            id: config.id,
            name: config.name,
            pin: config.pinBcm,
            initialized: true,
            currentAngle: existing?.currentAngle ?? config.defaultAngle,
            targetAngle: existing?.targetAngle ?? config.defaultAngle,
            isMoving: false,
            direction: config.direction,
            profile: config.profile,
            hardwarePwm: config.pinBcm === 12 || config.pinBcm === 13,
            activationCount: existing?.activationCount ?? 0,
            lastActivation: existing?.lastActivation ?? null,
          };
        });
        
        return newStatuses;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [servoConfigs]);

  const handleServoAction = async (servoId: string, action: string, params?: any) => {
    if (!isConnected || disabled) {
      setAlertMessage({ message: 'Sistema desconectado', severity: 'error' });
      return;
    }

    try {
      if (onServoAction) {
        await onServoAction(servoId, action, params);
        
        // Actualizar estado local
        if (action === 'move') {
          setServoStatuses(prev => ({
            ...prev,
            [servoId]: {
              ...prev[servoId],
              targetAngle: params.angle,
              isMoving: true,
            },
          }));
          
          // Simular movimiento completado
          setTimeout(() => {
            setServoStatuses(prev => ({
              ...prev,
              [servoId]: {
                ...prev[servoId],
                currentAngle: params.angle,
                isMoving: false,
              },
            }));
          }, 1000);
        } else if (action === 'activate') {
          setServoStatuses(prev => ({
            ...prev,
            [servoId]: {
              ...prev[servoId],
              activationCount: prev[servoId].activationCount + 1,
              lastActivation: new Date(),
            },
          }));
        }
        
        setAlertMessage({ message: `Acción ${action} ejecutada`, severity: 'success' });
      }
    } catch (error) {
      console.error('Error executing servo action:', error);
      setAlertMessage({ message: `Error: ${error}`, severity: 'error' });
    }
  };

  const handleConfigUpdate = (servoId: string, updates: Partial<ServoConfig>) => {
    setServoConfigs(prev => 
      prev.map(config => 
        config.id === servoId 
          ? { ...config, ...updates }
          : config
      )
    );
    
    if (onConfigUpdate) {
      onConfigUpdate(servoId, updates);
    }
  };

  const toggleExpanded = (servoId: string) => {
    setExpandedServos(prev => ({
      ...prev,
      [servoId]: !prev[servoId],
    }));
  };

  const getAnglePresets = () => [
    { label: '0°', value: 0 },
    { label: '45°', value: 45 },
    { label: '90°', value: 90 },
    { label: '135°', value: 135 },
    { label: '180°', value: 180 },
  ];

  const renderServoCard = (config: ServoConfig) => {
    const status = servoStatuses[config.id];
    const isExpanded = expandedServos[config.id];
    
    return (
      <GlassCard key={config.id} sx={{ mb: 2 }}>
        <CardContent>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  background: status?.hardwarePwm 
                    ? theme.gradients.primary 
                    : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Engineering sx={{ color: '#fff' }} />
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {config.name}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                  <Chip 
                    label={`GPIO ${config.pinBcm}`} 
                    size="small" 
                    color={status?.hardwarePwm ? 'success' : 'default'}
                    icon={<Memory sx={{ fontSize: 16 }} />}
                  />
                  {status?.hardwarePwm && (
                    <Chip 
                      label="Hardware PWM" 
                      size="small" 
                      color="primary"
                      variant="outlined"
                    />
                  )}
                  <Chip 
                    label={config.profile.replace('_', ' ').toUpperCase()} 
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Probar servo">
                <IconButton
                  onClick={() => setTestDialogOpen(config.id)}
                  disabled={disabled || !isConnected}
                  sx={{ color: theme.palette.primary.main }}
                >
                  <PlayArrow />
                </IconButton>
              </Tooltip>
              <Tooltip title="Calibrar servo">
                <IconButton
                  onClick={() => setCalibrationDialogOpen(config.id)}
                  disabled={disabled || !isConnected}
                  sx={{ color: theme.palette.secondary.main }}
                >
                  <TuneRounded />
                </IconButton>
              </Tooltip>
              <IconButton onClick={() => toggleExpanded(config.id)}>
                {isExpanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>
          </Box>

          {/* Status Display */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Posición Actual
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {status?.currentAngle ?? config.defaultAngle}°
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={(status?.currentAngle ?? config.defaultAngle) / 180 * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  background: theme.gradients.primary,
                },
              }}
            />
            {status?.isMoving && (
              <Typography variant="caption" color="primary" sx={{ mt: 0.5 }}>
                Moviendo a {status.targetAngle}°...
              </Typography>
            )}
          </Box>

          {/* Quick Controls */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
              Control Rápido
            </Typography>
            <ButtonGroup fullWidth variant="outlined" size="small">
              {getAnglePresets().map(preset => (
                <Button
                  key={preset.value}
                  onClick={() => handleServoAction(config.id, 'move', { angle: preset.value })}
                  disabled={disabled || !isConnected}
                  sx={{
                    backgroundColor: status?.currentAngle === preset.value 
                      ? 'rgba(0, 229, 160, 0.1)' 
                      : 'transparent',
                  }}
                >
                  {preset.label}
                </Button>
              ))}
            </ButtonGroup>
          </Box>

          {/* Control Slider */}
          <Box sx={{ px: 2, mb: 2 }}>
            <Slider
              value={status?.currentAngle ?? config.defaultAngle}
              onChange={(_, value) => handleServoAction(config.id, 'move', { angle: value as number })}
              min={config.minSafeAngle}
              max={config.maxSafeAngle}
              marks={[
                { value: config.minSafeAngle, label: `${config.minSafeAngle}°` },
                { value: config.defaultAngle, label: 'Default' },
                { value: config.activationAngle, label: 'Activation' },
                { value: config.maxSafeAngle, label: `${config.maxSafeAngle}°` },
              ]}
              disabled={disabled || !isConnected}
              sx={{
                color: theme.palette.primary.main,
                '& .MuiSlider-mark': {
                  backgroundColor: 'rgba(255, 255, 255, 0.3)',
                },
                '& .MuiSlider-markLabel': {
                  fontSize: '0.7rem',
                },
              }}
            />
          </Box>

          {/* Expanded Configuration */}
          <Collapse in={isExpanded}>
            <Divider sx={{ my: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Movement Settings */}
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                  Configuración de Movimiento
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={6}>
                    <TextField
                      fullWidth
                      label="Ángulo Default"
                      type="number"
                      size="small"
                      value={config.defaultAngle}
                      onChange={(e) => handleConfigUpdate(config.id, { 
                        defaultAngle: Number(e.target.value) 
                      })}
                      inputProps={{ min: 0, max: 180, step: 1 }}
                    />
                  </Grid>
                  <Grid size={6}>
                    <TextField
                      fullWidth
                      label="Ángulo Activación"
                      type="number"
                      size="small"
                      value={config.activationAngle}
                      onChange={(e) => handleConfigUpdate(config.id, { 
                        activationAngle: Number(e.target.value) 
                      })}
                      inputProps={{ min: 0, max: 180, step: 1 }}
                    />
                  </Grid>
                  <Grid size={6}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Dirección</InputLabel>
                      <Select
                        value={config.direction}
                        label="Dirección"
                        onChange={(e) => handleConfigUpdate(config.id, { 
                          direction: e.target.value as 'forward' | 'reverse' 
                        })}
                      >
                        <MenuItem value="forward">Normal</MenuItem>
                        <MenuItem value="reverse">Invertido</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid size={6}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Perfil</InputLabel>
                      <Select
                        value={config.profile}
                        label="Perfil"
                        onChange={(e) => handleConfigUpdate(config.id, { 
                          profile: e.target.value as any
                        })}
                      >
                        <MenuItem value="mg995_standard">MG995 Standard</MenuItem>
                        <MenuItem value="mg995_extended">MG995 Extended</MenuItem>
                        <MenuItem value="mg996r">MG996R</MenuItem>
                        <MenuItem value="custom">Custom</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </Box>

              {/* Speed Settings */}
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                  Velocidad: {(config.movementSpeed * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={config.movementSpeed}
                  onChange={(_, value) => handleConfigUpdate(config.id, { 
                    movementSpeed: value as number 
                  })}
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  marks
                  sx={{ color: theme.palette.secondary.main }}
                />
              </Box>

              {/* Switches */}
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.smoothMovement}
                      onChange={(e) => handleConfigUpdate(config.id, { 
                        smoothMovement: e.target.checked 
                      })}
                    />
                  }
                  label="Movimiento Suave"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.holdTorque}
                      onChange={(e) => handleConfigUpdate(config.id, { 
                        holdTorque: e.target.checked 
                      })}
                    />
                  }
                  label="Mantener Torque"
                />
              </Box>

              {/* Statistics */}
              {status && (
                <Paper sx={{ p: 2, background: 'rgba(0, 0, 0, 0.3)' }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    Estadísticas
                  </Typography>
                  <Grid container spacing={1}>
                    <Grid size={6}>
                      <Typography variant="caption" color="text.secondary">
                        Activaciones
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {status.activationCount}
                      </Typography>
                    </Grid>
                    <Grid size={6}>
                      <Typography variant="caption" color="text.secondary">
                        Última Activación
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {status.lastActivation 
                          ? new Date(status.lastActivation).toLocaleTimeString()
                          : 'Nunca'}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              )}
            </Box>
          </Collapse>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <ControlButton
              fullWidth
              variant="contained"
              onClick={() => handleServoAction(config.id, 'activate')}
              disabled={disabled || !isConnected}
              startIcon={<RotateRight />}
              sx={{
                background: theme.gradients.primary,
                color: '#000',
              }}
            >
              Activar
            </ControlButton>
            <ControlButton
              fullWidth
              variant="outlined"
              onClick={() => handleServoAction(config.id, 'reset')}
              disabled={disabled || !isConnected}
              startIcon={<RestartAlt />}
            >
              Reset
            </ControlButton>
          </Box>
        </CardContent>
      </GlassCard>
    );
  };

  // Test Dialog
  const renderTestDialog = () => {
    const servoId = testDialogOpen;
    if (!servoId) return null;
    
    const config = servoConfigs.find(c => c.id === servoId);
    if (!config) return null;
    
    return (
      <Dialog 
        open={true} 
        onClose={() => setTestDialogOpen(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Probar Servo: {config.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Mueve el slider para probar diferentes ángulos:
            </Typography>
            <Box sx={{ px: 2 }}>
              <Slider
                value={testAngle}
                onChange={(_, value) => setTestAngle(value as number)}
                min={0}
                max={180}
                step={5}
                marks={[
                  { value: 0, label: '0°' },
                  { value: 90, label: '90°' },
                  { value: 180, label: '180°' },
                ]}
                valueLabelDisplay="on"
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 1, mt: 3 }}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  handleServoAction(servoId, 'move', { angle: testAngle });
                }}
              >
                Mover a {testAngle}°
              </Button>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  // Test sweep
                  const angles = [0, 45, 90, 135, 180, 90];
                  angles.forEach((angle, i) => {
                    setTimeout(() => {
                      handleServoAction(servoId, 'move', { angle });
                    }, i * 1000);
                  });
                }}
              >
                Barrido Completo
              </Button>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(null)}>
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Calibration Dialog
  const renderCalibrationDialog = () => {
    const servoId = calibrationDialogOpen;
    if (!servoId) return null;
    
    const config = servoConfigs.find(c => c.id === servoId);
    if (!config) return null;
    
    return (
      <Dialog 
        open={true} 
        onClose={() => setCalibrationDialogOpen(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Calibrar Servo: {config.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="body2">
              Ajusta los parámetros de calibración. Cambios se guardan automáticamente.
            </Typography>
            
            <TextField
              label="Min Pulse (ms)"
              type="number"
              size="small"
              value={config.calibration.minPulseMs}
              onChange={(e) =>
                handleConfigUpdate(config.id, {
                  calibration: {
                    ...config.calibration,
                    minPulseMs: Number(e.target.value),
                  },
                })
              }
              inputProps={{ step: 0.05, min: 0.5, max: 2.5 }}
            />
            <TextField
              label="Max Pulse (ms)"
              type="number"
              size="small"
              value={config.calibration.maxPulseMs}
              onChange={(e) =>
                handleConfigUpdate(config.id, {
                  calibration: {
                    ...config.calibration,
                    maxPulseMs: Number(e.target.value),
                  },
                })
              }
              inputProps={{ step: 0.05, min: 0.5, max: 2.5 }}
            />
            <TextField
              label="Center Pulse (ms)"
              type="number"
              size="small"
              value={config.calibration.centerPulseMs}
              onChange={(e) =>
                handleConfigUpdate(config.id, {
                  calibration: {
                    ...config.calibration,
                    centerPulseMs: Number(e.target.value),
                  },
                })
              }
              inputProps={{ step: 0.05, min: 0.5, max: 2.5 }}
            />
            <Divider sx={{ my: 1, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
            <TextField
              label="Ángulo mínimo seguro"
              type="number"
              size="small"
              value={config.minSafeAngle}
              onChange={(e) => handleConfigUpdate(config.id, { minSafeAngle: Number(e.target.value) })}
              inputProps={{ min: 0, max: 180, step: 1 }}
            />
            <TextField
              label="Ángulo máximo seguro"
              type="number"
              size="small"
              value={config.maxSafeAngle}
              onChange={(e) => handleConfigUpdate(config.id, { maxSafeAngle: Number(e.target.value) })}
              inputProps={{ min: 0, max: 180, step: 1 }}
            />
            <Divider sx={{ my: 1, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
            <TextField
              label="Ángulo mínimo (calibración)"
              type="number"
              size="small"
              value={config.calibration.minAngle}
              onChange={(e) =>
                handleConfigUpdate(config.id, {
                  calibration: {
                    ...config.calibration,
                    minAngle: Number(e.target.value),
                  },
                })
              }
              inputProps={{ min: 0, max: 180, step: 1 }}
            />
            <TextField
              label="Ángulo máximo (calibración)"
              type="number"
              size="small"
              value={config.calibration.maxAngle}
              onChange={(e) =>
                handleConfigUpdate(config.id, {
                  calibration: {
                    ...config.calibration,
                    maxAngle: Number(e.target.value),
                  },
                })
              }
              inputProps={{ min: 0, max: 180, step: 1 }}
            />
            <TextField
              label="Ángulo centro (calibración)"
              type="number"
              size="small"
              value={config.calibration.centerAngle}
              onChange={(e) =>
                handleConfigUpdate(config.id, {
                  calibration: {
                    ...config.calibration,
                    centerAngle: Number(e.target.value),
                  },
                })
              }
              inputProps={{ min: 0, max: 180, step: 1 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCalibrationDialogOpen(null)}>
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          Control de Servos MG995
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label={isConnected ? 'Conectado' : 'Desconectado'}
            color={isConnected ? 'success' : 'error'}
            size="small"
            icon={isConnected ? <CheckCircle /> : <Warning />}
          />
          {isConnected && servoConfigs.every(c => 
            (c.pinBcm === 12 || c.pinBcm === 13)
          ) && (
            <Chip
              label="Hardware PWM"
              color="primary"
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      </Box>

      {/* Alert Messages */}
      {alertMessage && (
        <Alert 
          severity={alertMessage.severity}
          onClose={() => setAlertMessage(null)}
          sx={{ mb: 2 }}
        >
          {alertMessage.message}
        </Alert>
      )}

      {/* Servo Cards */}
      {servoConfigs.map(renderServoCard)}

      {/* Dialogs */}
      {renderTestDialog()}
      {renderCalibrationDialog()}
    </Box>
  );
};

export default ServoControlPanel;
