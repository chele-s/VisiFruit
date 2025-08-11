import React, { useEffect, useRef } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  useTheme,
} from '@mui/material'
import {
  TrendingUp,
  Speed,
  CheckCircle,
  Warning,
  Refresh,
  Fullscreen,
} from '@mui/icons-material'
import { animate, stagger } from 'animejs'
import { useAppSelector } from '../../types/redux'
import MetricsChart from '../charts/MetricsChart'
import ProductionStatus from '../production/ProductionStatus'
import AlertsList from '../alerts/AlertsList'

const DashboardView: React.FC = () => {
  const theme = useTheme()
  const dashboardRef = useRef<HTMLDivElement>(null)
  
  const { status } = useAppSelector(state => state.production)

  useEffect(() => {
    // Animación de entrada del dashboard
    if (dashboardRef.current) {
      const cards = dashboardRef.current.querySelectorAll('.dashboard-card')
      
      animate(cards, {
        translateY: [50, 0],
        opacity: [0, 1],
        duration: 800,
        delay: stagger(200, { start: 300 }),
        ease: 'outCubic',
      })
    }
  }, [])

  const statsCards = [
    {
      title: 'Eficiencia Actual',
      value: `${status.efficiency.toFixed(1)}%`,
      icon: <Speed />,
      color: status.efficiency > 80 ? 'success' : status.efficiency > 60 ? 'warning' : 'error',
      progress: status.efficiency,
      subtitle: `Objetivo: ${status.targetRate}/min`,
    },
    {
      title: 'Producción Hoy',
      value: status.itemsProcessedToday.toLocaleString(),
      icon: <TrendingUp />,
      color: 'primary',
      progress: (status.itemsProcessedToday / 5000) * 100,
      subtitle: 'Frutas etiquetadas',
    },
    {
      title: 'Calidad',
      value: `${status.qualityScore.toFixed(1)}%`,
      icon: <CheckCircle />,
      color: status.qualityScore > 90 ? 'success' : 'warning',
      progress: status.qualityScore,
      subtitle: 'Control de calidad',
    },
    {
      title: 'Tiempo Activo',
      value: status.uptimeToday,
      icon: <Warning />,
      color: 'info',
      progress: parseFloat(status.uptimeToday.replace('%', '')),
      subtitle: 'Disponibilidad del sistema',
    },
  ]

  return (
    <Box ref={dashboardRef} sx={{ width: '100%', height: '100%' }}>
      {/* Header del Dashboard */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 4,
        }}
      >
        <Box>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: theme.gradients.primary,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              mb: 1,
            }}
          >
            Dashboard de Control
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitoreo en tiempo real del sistema VisiFruit
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            sx={{
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
              '&:hover': {
                transform: 'scale(1.05) rotate(180deg)',
                boxShadow: theme.shadows[6],
              },
              transition: 'all 0.3s ease',
            }}
          >
            <Refresh />
          </IconButton>
          <IconButton
            sx={{
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
              '&:hover': {
                transform: 'scale(1.05)',
                boxShadow: theme.shadows[6],
              },
              transition: 'all 0.3s ease',
            }}
          >
            <Fullscreen />
          </IconButton>
        </Box>
      </Box>

      {/* Tarjetas de estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statsCards.map((card) => (
          <Grid key={card.title} size={{ xs: 12, sm: 6, lg: 3 }}>
            <Card
              className="dashboard-card neon-glow"
              sx={{
                height: '100%',
                background: theme.gradients.glass,
                backdropFilter: 'blur(20px)',
                border: `1px solid rgba(255, 255, 255, 0.1)`,
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 4,
                  background: theme.gradients[card.color === 'primary' ? 'primary' : 'secondary'],
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      background: `rgba(${card.color === 'success' ? '76, 175, 80' : card.color === 'warning' ? '255, 193, 7' : card.color === 'error' ? '244, 67, 54' : '0, 229, 160'}, 0.1)`,
                      color:
                        card.color === 'primary'
                          ? theme.palette.primary.main
                          : card.color === 'success'
                          ? theme.palette.success.main
                          : card.color === 'warning'
                          ? theme.palette.warning.main
                          : card.color === 'error'
                          ? theme.palette.error.main
                          : card.color === 'info'
                          ? theme.palette.info.main
                          : theme.palette.primary.main,
                      mr: 2,
                    }}
                  >
                    {card.icon}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      {card.title}
                    </Typography>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      {card.value}
                    </Typography>
                  </Box>
                </Box>
                
                <LinearProgress
                  variant="determinate"
                  value={Math.min(card.progress, 100)}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    mb: 1,
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: theme.gradients[card.color === 'primary' ? 'primary' : 'secondary'],
                      borderRadius: 3,
                    },
                  }}
                />
                
                <Typography variant="caption" color="text.secondary">
                  {card.subtitle}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Contenido principal del dashboard */}
      <Grid container spacing={3}>
        {/* Estado de producción */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card
            className="dashboard-card neon-glow"
            sx={{
              height: 400,
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Estado de Producción
                </Typography>
                <Chip
                  label={status.status === 'running' ? 'Activo' : 'Detenido'}
                  color={status.status === 'running' ? 'success' : 'default'}
                  sx={{
                    fontWeight: 600,
                    ...(status.status === 'running' && {
                      animation: 'pulse 2s infinite',
                    }),
                  }}
                />
              </Box>
              <ProductionStatus />
            </CardContent>
          </Card>
        </Grid>

        {/* Lista de alertas */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card
            className="dashboard-card neon-glow"
            sx={{
              height: 400,
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Alertas Recientes
              </Typography>
              <AlertsList />
            </CardContent>
          </Card>
        </Grid>

        {/* Gráfico de métricas */}
        <Grid size={{ xs: 12 }}>
          <Card
            className="dashboard-card neon-glow"
            sx={{
              height: 350,
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Métricas de Rendimiento
              </Typography>
              <MetricsChart />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default DashboardView