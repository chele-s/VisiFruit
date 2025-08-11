import { useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Typography,
  CircularProgress,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Speed,
  HighQuality,
  Timer,
} from '@mui/icons-material';
import { animate, stagger } from 'animejs';
import { useAppSelector } from '../../types/redux';

const ProductionStatus: React.FC = () => {
  const theme = useTheme();
  const statusRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  const { status } = useAppSelector(state => state.production);

  useEffect(() => {
    if (statusRef.current) {
      animate(statusRef.current.querySelectorAll('.status-item'), {
        translateX: [-30, 0],
        opacity: [0, 1],
        duration: 600,
        delay: stagger(150),
        easing: 'easeOutCubic',
      });
    }

    if (progressRef.current) {
      const circle = progressRef.current.querySelector(
        '.MuiCircularProgress-circle',
      );
      if (circle) {
        animate(circle, {
          strokeDasharray: '0 100',
          duration: 1500,
          easing: 'easeOutCubic',
          delay: 500,
        });
      }
    }
  }, []);

  const getStatusColor = (currentStatus: string) => {
    switch (currentStatus) {
      case 'running':
        return 'success';
      case 'paused':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (currentStatus: string) => {
    switch (currentStatus) {
      case 'running':
        return 'En Producción';
      case 'paused':
        return 'Pausado';
      case 'stopped':
        return 'Detenido';
      case 'error':
        return 'Error';
      default:
        return 'Desconocido';
    }
  };

  return (
    <Box ref={statusRef} sx={{ height: '100%' }}>
      <Grid container spacing={3} sx={{ height: '100%' }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Box
            sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}
          >
            <Box className="status-item" sx={{ mb: 3 }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  mb: 2,
                }}
              >
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Estado del Sistema
                </Typography>
                <Chip
                  label={getStatusText(status.status)}
                  color={getStatusColor(status.status)}
                  sx={{
                    fontWeight: 600,
                    fontSize: '0.875rem',
                    ...(status.status === 'running' && {
                      animation: 'pulse 2s infinite',
                    }),
                  }}
                />
              </Box>

              <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                <Tooltip title="Iniciar Producción">
                  <IconButton
                    color="success"
                    disabled={status.status === 'running'}
                    sx={{
                      background: 'rgba(76, 175, 80, 0.1)',
                      '&:hover': {
                        background: 'rgba(76, 175, 80, 0.2)',
                        transform: 'scale(1.05)',
                        boxShadow: theme.shadows[4],
                      },
                      transition: 'all 0.3s ease',
                      '&:disabled': {
                        opacity: 0.5,
                      },
                    }}
                  >
                    <PlayArrow />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Pausar Producción">
                  <IconButton
                    color="warning"
                    disabled={status.status !== 'running'}
                    sx={{
                      background: 'rgba(255, 193, 7, 0.1)',
                      '&:hover': {
                        background: 'rgba(255, 193, 7, 0.2)',
                        transform: 'scale(1.05)',
                        boxShadow: theme.shadows[4],
                      },
                      transition: 'all 0.3s ease',
                      '&:disabled': {
                        opacity: 0.5,
                      },
                    }}
                  >
                    <Pause />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Detener Producción">
                  <IconButton
                    color="error"
                    disabled={status.status === 'stopped'}
                    sx={{
                      background: 'rgba(244, 67, 54, 0.1)',
                      '&:hover': {
                        background: 'rgba(244, 67, 54, 0.2)',
                        transform: 'scale(1.05)',
                        boxShadow: theme.shadows[4],
                      },
                      transition: 'all 0.3s ease',
                      '&:disabled': {
                        opacity: 0.5,
                      },
                    }}
                  >
                    <Stop />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Configuración">
                  <IconButton
                    sx={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      '&:hover': {
                        background: 'rgba(255, 255, 255, 0.1)',
                        transform: 'scale(1.05) rotate(90deg)',
                        boxShadow: theme.shadows[4],
                      },
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <Settings />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            <Box className="status-item" sx={{ mb: 3 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Categoría Activa
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  p: 2,
                  borderRadius: 2,
                  background: theme.gradients.glass,
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                }}
              >
                <Box
                  sx={{
                    fontSize: '2rem',
                    mr: 2,
                    filter: 'drop-shadow(0 0 10px rgba(0, 229, 160, 0.3))',
                  }}
                >
                  {status.activeGroup.emoji}
                </Box>
                <Box>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 600, textTransform: 'capitalize' }}
                  >
                    {status.activeGroup.category}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Grupo ID: {status.activeGroup.id}
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Box className="status-item" sx={{ flex: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                Métricas en Vivo
              </Typography>
              <Grid container spacing={2}>
                <Grid size={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Speed
                      sx={{
                        fontSize: '2rem',
                        color: theme.palette.primary.main,
                        mb: 1,
                      }}
                    />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {status.currentRate.toFixed(1)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Items/min
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <HighQuality
                      sx={{
                        fontSize: '2rem',
                        color: theme.palette.success.main,
                        mb: 1,
                      }}
                    />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {status.qualityScore.toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Calidad
                    </Typography>
                  </Box>
                </Grid>
                <Grid size={4}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Timer
                      sx={{
                        fontSize: '2rem',
                        color: theme.palette.info.main,
                        mb: 1,
                      }}
                    />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {status.uptimeToday}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Uptime
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              alignItems: 'center',
            }}
          >
            <Box
              className="status-item"
              sx={{ mb: 3, position: 'relative' }}
              ref={progressRef}
            >
              <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                <CircularProgress
                  variant="determinate"
                  value={status.efficiency}
                  size={120}
                  thickness={6}
                  sx={{
                    color: theme.palette.primary.main,
                    '& .MuiCircularProgress-circle': {
                      strokeLinecap: 'round',
                      filter: `drop-shadow(0 0 8px ${theme.palette.primary.main}40)`,
                    },
                  }}
                />
                <Box
                  sx={{
                    top: 0,
                    left: 0,
                    bottom: 0,
                    right: 0,
                    position: 'absolute',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column',
                  }}
                >
                  <Typography
                    variant="h4"
                    component="div"
                    sx={{ fontWeight: 700 }}
                  >
                    {status.efficiency.toFixed(0)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Eficiencia
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Box className="status-item" sx={{ width: '100%', mb: 3 }}>
              <Box sx={{ mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    mb: 1,
                  }}
                >
                  <Typography variant="body2">Progreso Diario</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {status.itemsProcessedToday} / 5000
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(status.itemsProcessedToday / 5000) * 100}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: theme.gradients.primary,
                      borderRadius: 4,
                    },
                  }}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    mb: 1,
                  }}
                >
                  <Typography variant="body2">Velocidad de Banda</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {status.beltSpeed} m/s
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(status.beltSpeed / 2) * 100}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: theme.gradients.secondary,
                      borderRadius: 4,
                    },
                  }}
                />
              </Box>
            </Box>

            <Box className="status-item" sx={{ width: '100%' }}>
              <Typography
                variant="subtitle2"
                sx={{ fontWeight: 600, mb: 2 }}
              >
                Información del Sistema
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box
                  sx={{ display: 'flex', justifyContent: 'space-between' }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Etiquetadoras Activas:
                  </Typography>
                  <Typography variant="body2">
                    {status.activeLabelers}/4
                  </Typography>
                </Box>
                <Box
                  sx={{ display: 'flex', justifyContent: 'space-between' }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Último Cambio:
                  </Typography>
                  <Typography variant="body2">
                    {new Date(status.lastSwitch).toLocaleTimeString('es-ES')}
                  </Typography>
                </Box>
                <Box
                  sx={{ display: 'flex', justifyContent: 'space-between' }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Tasa Objetivo:
                  </Typography>
                  <Typography variant="body2">
                    {status.targetRate}/min
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProductionStatus;