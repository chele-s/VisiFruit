import React, { useEffect, useRef } from 'react'
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Typography,
  Divider,
  useTheme,
} from '@mui/material'
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import { animate, stagger } from 'animejs'
import { useAppSelector, useAppDispatch } from '../../types/redux'
import { acknowledgeAlert, removeAlert } from '../../store/slices/alertsSlice'
import type { Alert, AlertSeverity } from '../../store/slices/alertsSlice'
import { useAlerts } from '../../services/api'

const AlertsList: React.FC = () => {
  const theme = useTheme()
  const alertsRef = useRef<HTMLDivElement>(null)
  const dispatch = useAppDispatch()
  
  const { alerts } = useAppSelector(state => state.alerts)
  
  // Intentar obtener alertas reales del backend
  const { data: backendAlerts, isError: alertsError, isLoading } = useAlerts()

  // Datos simulados para la demo
  const demoAlerts: Alert[] = [
    {
      id: '1',
      title: 'Alta Temperatura',
      message: 'La temperatura del sistema ha superado los 65°C',
      severity: 'warning',
      category: 'system',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // hace 5 min
      acknowledged: false,
      resolved: false,
    },
    {
      id: '2',
      title: 'Calidad Reducida',
      message: 'El porcentaje de calidad ha bajado al 87%',
      severity: 'warning',
      category: 'quality',
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // hace 15 min
      acknowledged: false,
      resolved: false,
    },
    {
      id: '3',
      title: 'Mantenimiento Programado',
      message: 'Mantenimiento preventivo en 2 horas',
      severity: 'info',
      category: 'maintenance',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // hace 30 min
      acknowledged: true,
      resolved: false,
    },
    {
      id: '4',
      title: 'Backup Completado',
      message: 'Copia de seguridad realizada exitosamente',
      severity: 'info',
      category: 'system',
      timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // hace 1 hora
      acknowledged: true,
      resolved: true,
    },
  ]

  // Lógica de prioridad: 
  // 1. Alertas del estado local (Redux) - si existen
  // 2. Alertas del backend - si están disponibles
  // 3. Alertas demo - como fallback
  const getDisplayAlerts = (): Alert[] => {
    if (alerts.length > 0) {
      return alerts // Datos del estado local (más prioritarios)
    }
    
    if (backendAlerts && backendAlerts.length > 0 && !alertsError) {
      // Convertir formato del backend al formato local
      return backendAlerts.map((alert: any) => ({
        id: alert.id,
        title: alert.title || alert.message,
        message: alert.message,
        severity: alert.severity as AlertSeverity,
        category: alert.category,
        timestamp: alert.timestamp,
        acknowledged: alert.acknowledged || false,
        resolved: alert.resolved || false,
      }))
    }
    
    // Fallback a datos demo cuando no hay conexión
    return demoAlerts
  }
  
  const displayAlerts = getDisplayAlerts()

  useEffect(() => {
    if (alertsRef.current) {
      const alertItems = alertsRef.current.querySelectorAll('.alert-item')
      
      animate(alertItems, {
        translateX: [50, 0],
        opacity: [0, 1],
        duration: 500,
        delay: stagger(100, { start: 200 }),
        ease: 'outCubic',
      })
    }
  }, [displayAlerts])

  const getSeverityIcon = (severity: AlertSeverity) => {
    switch (severity) {
      case 'error':
      case 'critical':
        return <ErrorIcon />
      case 'warning':
        return <WarningIcon />
      case 'info':
        return <InfoIcon />
      default:
        return <InfoIcon />
    }
  }

  // Nota: el icono por categoría no se usa actualmente

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical':
      case 'error':
        return theme.palette.error.main
      case 'warning':
        return theme.palette.warning.main
      case 'info':
        return theme.palette.info.main
      default:
        return theme.palette.text.secondary
    }
  }

  const handleAcknowledge = (alertId: string) => {
    dispatch(acknowledgeAlert({
      id: alertId,
      acknowledgedBy: 'Usuario',
      notes: 'Confirmado desde el dashboard'
    }))

    // Animación de confirmación
    const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`)
    if (alertElement) {
      animate(alertElement, {
        backgroundColor: ['rgba(76, 175, 80, 0.1)', 'transparent'],
        duration: 1000,
        ease: 'outCubic',
      })
    }
  }

  const handleRemove = (alertId: string) => {
    const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`)
    if (alertElement) {
      animate(alertElement, {
        translateX: [0, 100],
        opacity: [1, 0],
        duration: 400,
        ease: 'inCubic',
        onComplete: () => {
          dispatch(removeAlert(alertId))
        }
      })
    }
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) {
      return 'Ahora'
    } else if (diffInMinutes < 60) {
      return `Hace ${diffInMinutes} min`
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60)
      return `Hace ${hours}h`
    } else {
      return date.toLocaleDateString('es-ES')
    }
  }

  if (displayAlerts.length === 0) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: 'text.secondary',
        }}
      >
        <CheckIcon sx={{ fontSize: '3rem', mb: 2, opacity: 0.5 }} />
        <Typography variant="body2">
          No hay alertas pendientes
        </Typography>
      </Box>
    )
  }

  // Mostrar indicador de estado de conexión
  const connectionStatus = alertsError ? 'error' : (isLoading ? 'loading' : (backendAlerts ? 'connected' : 'demo'))
  
  return (
    <Box ref={alertsRef} sx={{ height: '100%', overflow: 'hidden' }}>
      {/* Indicador de estado de conexión */}
      <Box 
        sx={{ 
          p: 1, 
          mb: 1,
          borderRadius: 1,
          backgroundColor: 
            connectionStatus === 'connected' ? 'rgba(76, 175, 80, 0.1)' :
            connectionStatus === 'error' ? 'rgba(244, 67, 54, 0.1)' :
            connectionStatus === 'loading' ? 'rgba(255, 193, 7, 0.1)' :
            'rgba(156, 39, 176, 0.1)',
          border: `1px solid ${
            connectionStatus === 'connected' ? '#4CAF5080' :
            connectionStatus === 'error' ? '#F4433680' :
            connectionStatus === 'loading' ? '#FFC10780' :
            '#9C27B080'
          }`,
        }}
      >
        <Typography 
          variant="caption" 
          sx={{ 
            color: 
              connectionStatus === 'connected' ? '#4CAF50' :
              connectionStatus === 'error' ? '#F44336' :
              connectionStatus === 'loading' ? '#FFC107' :
              '#9C27B0',
            fontWeight: 500
          }}
        >
          {connectionStatus === 'connected' && '🟢 Conectado al backend'}
          {connectionStatus === 'error' && '🔴 Error de conexión - Mostrando datos demo'}
          {connectionStatus === 'loading' && '🟡 Conectando...'}
          {connectionStatus === 'demo' && '🟣 Modo demo - Sin conexión al backend'}
        </Typography>
      </Box>
      
      <List
        sx={{
          height: '100%',
          overflow: 'auto',
          p: 0,
          '&::-webkit-scrollbar': {
            width: 4,
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 2,
          },
        }}
      >
        {displayAlerts.slice(0, 10).map((alert, index) => (
          <React.Fragment key={alert.id}>
            <ListItem
              className="alert-item"
              data-alert-id={alert.id}
              sx={{
                p: 1.5,
                borderRadius: 2,
                mb: 1,
                background: alert.acknowledged 
                  ? 'rgba(255, 255, 255, 0.02)' 
                  : 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${getSeverityColor(alert.severity)}40`,
                opacity: alert.resolved ? 0.6 : 1,
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: 3,
                  backgroundColor: getSeverityColor(alert.severity),
                },
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  transform: 'translateX(2px)',
                  transition: 'all 0.2s ease',
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 36,
                  color: getSeverityColor(alert.severity),
                }}
              >
                {getSeverityIcon(alert.severity)}
              </ListItemIcon>
              
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: 600,
                        textDecoration: alert.resolved ? 'line-through' : 'none',
                      }}
                    >
                      {alert.title}
                    </Typography>
                    <Chip
                      label={alert.category}
                      size="small"
                      variant="outlined"
                      sx={{
                        fontSize: '0.7rem',
                        height: 18,
                        borderColor: getSeverityColor(alert.severity),
                        color: getSeverityColor(alert.severity),
                      }}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        fontSize: '0.8rem',
                        mb: 0.5,
                        opacity: alert.resolved ? 0.7 : 1,
                      }}
                    >
                      {alert.message}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatTime(alert.timestamp)}
                    </Typography>
                  </Box>
                }
              />
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, ml: 1 }}>
                {!alert.acknowledged && !alert.resolved && (
                  <IconButton
                    size="small"
                    onClick={() => handleAcknowledge(alert.id)}
                    sx={{
                      color: theme.palette.success.main,
                      '&:hover': {
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        transform: 'scale(1.1)',
                      },
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <CheckIcon fontSize="small" />
                  </IconButton>
                )}
                
                <IconButton
                  size="small"
                  onClick={() => handleRemove(alert.id)}
                  sx={{
                    color: 'text.secondary',
                    '&:hover': {
                      color: theme.palette.error.main,
                      backgroundColor: 'rgba(244, 67, 54, 0.1)',
                      transform: 'scale(1.1)',
                    },
                    transition: 'all 0.2s ease',
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Box>
            </ListItem>
            
            {index < displayAlerts.length - 1 && (
              <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.05)' }} />
            )}
          </React.Fragment>
        ))}
      </List>
    </Box>
  )
}

export default AlertsList