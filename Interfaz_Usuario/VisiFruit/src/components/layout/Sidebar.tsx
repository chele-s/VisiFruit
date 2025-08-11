import React, { useEffect, useRef } from 'react'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  useMediaQuery,
  useTheme,
  Chip,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Factory as ProductionIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  ViewInAr as View3DIcon,
  Speed as MetricsIcon,
  Warning as AlertsIcon,
  Assessment as ReportsIcon,
  Build as MaintenanceIcon,
} from '@mui/icons-material'
import { animate, stagger } from 'animejs'
import { useAppSelector, useAppDispatch } from '../../types/redux'
import { setCurrentView, setSidebarOpen } from '../../store/slices/uiSlice'
import type { ViewMode } from '../../store/slices/uiSlice'

interface NavigationItem {
  id: ViewMode | 'settings'
  label: string
  icon: React.ReactNode
  badge?: number
  color?: string
}

const navigationItems: NavigationItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { id: 'production', label: 'Producción', icon: <ProductionIcon /> },
  { id: '3d-view', label: 'Vista 3D', icon: <View3DIcon />, color: 'primary' },
  { id: 'analytics', label: 'Análisis', icon: <AnalyticsIcon /> },
]

const systemItems: NavigationItem[] = [
  { id: 'metrics', label: 'Métricas', icon: <MetricsIcon /> },
  { id: 'alerts', label: 'Alertas', icon: <AlertsIcon />, badge: 3 },
  { id: 'reports', label: 'Reportes', icon: <ReportsIcon /> },
  { id: 'maintenance', label: 'Mantenimiento', icon: <MaintenanceIcon /> },
  { id: 'config', label: 'Configuración', icon: <SettingsIcon /> },
]

const Sidebar: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const dispatch = useAppDispatch()
  
  const { sidebarOpen, currentView } = useAppSelector(state => state.ui)
  const { status } = useAppSelector(state => state.production)
  
  const sidebarRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    if (sidebarOpen && listRef.current) {
      // Animar elementos de la lista cuando se abre el sidebar
      const listItems = listRef.current.querySelectorAll('.sidebar-item')
      
      animate(listItems, {
        translateX: [-50, 0],
        opacity: [0, 1],
        duration: 600,
        delay: stagger(100, { start: 200 }),
        ease: 'outCubic',
      })
    }
  }, [sidebarOpen])

  const handleNavigation = (viewId: ViewMode | 'settings') => {
    if (viewId !== 'settings') {
      dispatch(setCurrentView(viewId as ViewMode))
      
      // Efecto de pulso en el elemento seleccionado
      const selectedElement = document.querySelector(`[data-nav-id="${viewId}"]`)
      if (selectedElement) {
        animate(selectedElement, {
          scale: [1, 1.05, 1],
          duration: 300,
          ease: 'outCubic',
        })
      }
    }
    
    if (isMobile) {
      dispatch(setSidebarOpen(false))
    }
  }

  const handleClose = () => {
    dispatch(setSidebarOpen(false))
  }

  const drawerContent = (
    <Box
      ref={sidebarRef}
      sx={{
        width: 280,
        height: '100%',
        background: theme.gradients.dark,
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(180deg, rgba(0, 229, 160, 0.05) 0%, transparent 50%)',
          pointerEvents: 'none',
        },
      }}
    >
      {/* Logo y título */}
      <Box
        sx={{
          p: 3,
          borderBottom: `1px solid rgba(255, 255, 255, 0.1)`,
          position: 'relative',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '12px',
              background: theme.gradients.primary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: 2,
              fontSize: '1.5rem',
              boxShadow: theme.shadows[6],
            }}
          >
            🍎
          </Box>
          <Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: theme.gradients.primary,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              VisiFruit
            </Typography>
            <Typography variant="caption" color="text.secondary">
              v3.0 Ultra
            </Typography>
          </Box>
        </Box>
        
        {/* Estado de producción */}
        <Chip
          label={status.status === 'running' ? 'En Producción' : 'Detenido'}
          color={status.status === 'running' ? 'success' : 'default'}
          size="small"
          sx={{
            fontSize: '0.75rem',
            fontWeight: 600,
            ...(status.status === 'running' && {
              animation: 'pulse 2s infinite',
            }),
            '@keyframes pulse': {
              '0%, 100%': { opacity: 1 },
              '50%': { opacity: 0.7 },
            },
          }}
        />
      </Box>

      {/* Navegación principal */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <List ref={listRef} sx={{ p: 2 }}>
          <Typography
            variant="overline"
            sx={{
              px: 2,
              py: 1,
              color: 'text.secondary',
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.1em',
            }}
          >
            Principal
          </Typography>
          
          {navigationItems.map((item) => (
            <ListItem key={item.id} disablePadding className="sidebar-item">
              <ListItemButton
                data-nav-id={item.id}
                selected={currentView === item.id}
                onClick={() => handleNavigation(item.id)}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  mx: 1,
                  '&.Mui-selected': {
                    background: theme.gradients.primary,
                    color: '#000',
                    boxShadow: theme.shadows[6],
                    '& .MuiListItemIcon-root': {
                      color: '#000',
                    },
                    '&:hover': {
                      background: theme.gradients.primary,
                    },
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    transform: 'translateX(4px)',
                  },
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <ListItemIcon
                  sx={{
                    color: item.color === 'primary' ? theme.palette.primary.main : 'inherit',
                    minWidth: 40,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                    fontWeight: 500,
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    color="error"
                    sx={{ fontSize: '0.7rem', height: 20, minWidth: 20 }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}

          <Divider sx={{ my: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />

          <Typography
            variant="overline"
            sx={{
              px: 2,
              py: 1,
              color: 'text.secondary',
              fontSize: '0.75rem',
              fontWeight: 600,
              letterSpacing: '0.1em',
            }}
          >
            Sistema
          </Typography>

          {systemItems.map((item, index) => (
            <ListItem key={`${item.id}-${index}`} disablePadding className="sidebar-item">
              <ListItemButton
                onClick={() => handleNavigation(item.id)}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  mx: 1,
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    transform: 'translateX(4px)',
                  },
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.9rem',
                    fontWeight: 500,
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    color="warning"
                    sx={{ 
                      fontSize: '0.7rem', 
                      height: 20, 
                      minWidth: 20,
                      animation: 'pulse 2s infinite',
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Footer del sidebar */}
      <Box
        sx={{
          p: 2,
          borderTop: `1px solid rgba(255, 255, 255, 0.1)`,
          background: 'rgba(0, 0, 0, 0.2)',
        }}
      >
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          Sistema de Etiquetado Inteligente
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label={status.status === 'running' ? 'Online' : 'Offline'}
            size="small"
            color={status.status === 'running' ? 'success' : 'default'}
            sx={{ fontSize: '0.7rem' }}
          />
          <Chip
            label={`${status.efficiency.toFixed(1)}%`}
            size="small"
            color="info"
            sx={{ fontSize: '0.7rem' }}
          />
        </Box>
      </Box>
    </Box>
  )

  return (
    <>
      {/* Sidebar para desktop */}
      {!isMobile && (
        <Drawer
          variant="persistent"
          anchor="left"
          open={sidebarOpen}
          PaperProps={{
            sx: {
              background: 'transparent',
              border: 'none',
              overflow: 'hidden',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      {/* Sidebar para mobile */}
      {isMobile && (
        <Drawer
          variant="temporary"
          anchor="left"
          open={sidebarOpen}
          onClose={handleClose}
          ModalProps={{
            keepMounted: true, // Mejor rendimiento en mobile
          }}
          PaperProps={{
            sx: {
              background: 'transparent',
              border: 'none',
              overflow: 'hidden',
              width: 280,
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}
    </>
  )
}

export default Sidebar