import React, { useEffect, useRef, useState } from 'react'
import {
  Box,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  Factory as ProductionIcon,
  ViewInAr as View3DIcon,
} from '@mui/icons-material'
import { animate } from 'animejs'
import { useAppSelector, useAppDispatch } from '../../types/redux'
import { toggleSidebar, setCurrentView } from '../../store/slices/uiSlice'
import Sidebar from './Sidebar'
import DashboardView from '../views/DashboardView'
import ProductionView from '../views/ProductionView'
import BeltControlView from '../views/BeltControlView'
import AnalyticsView from '../views/AnalyticsView'
import Dashboard3DView from '../views/Dashboard3DView'
import AlertsList from '../alerts/AlertsList'
import MetricsChart from '../charts/MetricsChart'

const MainLayout: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const dispatch = useAppDispatch()
  
  const { currentView, sidebarOpen } = useAppSelector(state => state.ui)
  const { unreadCount } = useAppSelector(state => state.alerts)
  
  const appBarRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [notificationsAnchor, setNotificationsAnchor] = useState<null | HTMLElement>(null)

  useEffect(() => {
    // Animación de entrada del AppBar
    if (appBarRef.current) {
      animate(appBarRef.current, {
        translateY: [-100, 0],
        opacity: [0, 1],
        duration: 1000,
        ease: 'outCubic',
        delay: 500,
      })
    }

    // Animación de entrada del contenido
    if (contentRef.current) {
      animate(contentRef.current, {
        opacity: [0, 1],
        duration: 800,
        ease: 'outCubic',
        delay: 800,
      })
    }
  }, [])

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationsClick = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationsAnchor(event.currentTarget)
  }

  const handleNotificationsClose = () => {
    setNotificationsAnchor(null)
  }

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar())
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <DashboardView />
      case 'production':
        return <ProductionView />
      case 'belt-control':
        return <BeltControlView />
      case 'analytics':
        return <AnalyticsView />
      case 'metrics':
        return (
          <Box sx={{ height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Métricas</Typography>
            <Box sx={{ height: 'calc(100% - 40px)' }}>
              <MetricsChart />
            </Box>
          </Box>
        )
      case 'alerts':
        return (
          <Box sx={{ height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Alertas</Typography>
            <Box sx={{ height: 'calc(100% - 40px)' }}>
              <AlertsList />
            </Box>
          </Box>
        )
      case 'reports':
        return <Typography>Reportes (en construcción)</Typography>
      case 'maintenance':
        return <Typography>Mantenimiento (en construcción)</Typography>
      case 'config':
        return <Typography>Configuración (en construcción)</Typography>
      case '3d-view':
        return <Dashboard3DView />
      default:
        return <DashboardView />
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', width: '100%', overflow: 'hidden', position: 'relative' }}>
      {/* AppBar */}
      <AppBar
        ref={appBarRef}
        position="fixed"
        elevation={0}
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          background: theme.gradients.glass,
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid rgba(255, 255, 255, 0.1)`,
          transition: theme.transitions.create(['margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(sidebarOpen && !isMobile && {
            marginLeft: 280,
            width: `calc(100% - 280px)`,
          }),
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={handleToggleSidebar}
            sx={{
              mr: 2,
              '&:hover': {
                transform: 'scale(1.1)',
                transition: 'transform 0.2s ease',
              },
            }}
          >
            <MenuIcon />
          </IconButton>

          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                background: theme.gradients.primary,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                mr: 2,
              }}
            >
              VisiFruit
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sistema Inteligente de Etiquetado
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Botones de vista rápida */}
            <IconButton
              color={currentView === 'dashboard' ? 'primary' : 'inherit'}
              onClick={() => dispatch(setCurrentView('dashboard'))}
              sx={{ 
                '&:hover': { 
                  transform: 'scale(1.1)',
                  boxShadow: theme.shadows[6],
                },
                transition: 'all 0.2s ease',
              }}
            >
              <DashboardIcon />
            </IconButton>
            
            <IconButton
              color={currentView === 'production' ? 'primary' : 'inherit'}
              onClick={() => dispatch(setCurrentView('production'))}
              sx={{ 
                '&:hover': { 
                  transform: 'scale(1.1)',
                  boxShadow: theme.shadows[6],
                },
                transition: 'all 0.2s ease',
              }}
            >
              <ProductionIcon />
            </IconButton>
            
            <IconButton
              color={currentView === '3d-view' ? 'primary' : 'inherit'}
              onClick={() => dispatch(setCurrentView('3d-view'))}
              sx={{ 
                '&:hover': { 
                  transform: 'scale(1.1)',
                  boxShadow: theme.shadows[6],
                },
                transition: 'all 0.2s ease',
              }}
            >
              <View3DIcon />
            </IconButton>

            {/* Notificaciones */}
            <IconButton
              color="inherit"
              onClick={handleNotificationsClick}
              sx={{ 
                '&:hover': { 
                  transform: 'scale(1.1)',
                  boxShadow: theme.shadows[6],
                },
                transition: 'all 0.2s ease',
              }}
            >
              <Badge 
                badgeContent={unreadCount} 
                color="error"
                sx={{
                  '& .MuiBadge-badge': {
                    fontSize: '0.75rem',
                    height: 18,
                    minWidth: 18,
                    animation: unreadCount > 0 ? 'pulse 2s infinite' : 'none',
                  },
                  '@keyframes pulse': {
                    '0%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(1.1)' },
                    '100%': { transform: 'scale(1)' },
                  },
                }}
              >
                <NotificationsIcon />
              </Badge>
            </IconButton>

            {/* Configuraciones */}
            <IconButton
              color="inherit"
              sx={{ 
                '&:hover': { 
                  transform: 'scale(1.1) rotate(90deg)',
                  boxShadow: theme.shadows[6],
                },
                transition: 'all 0.3s ease',
              }}
            >
              <SettingsIcon />
            </IconButton>

            {/* Avatar del usuario */}
            <IconButton
              onClick={handleMenuClick}
              sx={{ 
                '&:hover': { 
                  transform: 'scale(1.05)',
                  boxShadow: theme.shadows[6],
                },
                transition: 'all 0.2s ease',
              }}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  background: theme.gradients.primary,
                  color: '#000',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                }}
              >
                VF
              </Avatar>
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Sidebar />

      {/* Contenido principal */}
      <Box
        ref={contentRef}
        component="main"
        sx={{
          flexGrow: 1,
          height: '100vh',
          mt: 8,
          p: { xs: 2, md: 3 },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ...(sidebarOpen && !isMobile && {
            marginLeft: 280,
            width: `calc(100% - 280px)`,
          }),
          overflow: 'auto',
          overflowX: 'hidden',
          position: 'relative',
          boxSizing: 'border-box',
        }}
      >
        {renderCurrentView()}
      </Box>

      {/* Menú del usuario */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            background: theme.gradients.glass,
            backdropFilter: 'blur(20px)',
            border: `1px solid rgba(255, 255, 255, 0.1)`,
            borderRadius: 2,
            mt: 1,
          },
        }}
      >
        <MenuItem onClick={handleMenuClose}>Perfil</MenuItem>
        <MenuItem onClick={handleMenuClose}>Configuración</MenuItem>
        <MenuItem onClick={handleMenuClose}>Cerrar Sesión</MenuItem>
      </Menu>

      {/* Menú de notificaciones */}
      <Menu
        anchorEl={notificationsAnchor}
        open={Boolean(notificationsAnchor)}
        onClose={handleNotificationsClose}
        PaperProps={{
          sx: {
            background: theme.gradients.glass,
            backdropFilter: 'blur(20px)',
            border: `1px solid rgba(255, 255, 255, 0.1)`,
            borderRadius: 2,
            mt: 1,
            maxWidth: 350,
          },
        }}
      >
        <MenuItem onClick={handleNotificationsClose}>
          <Typography variant="body2">No hay notificaciones nuevas</Typography>
        </MenuItem>
      </Menu>
    </Box>
  )
}

export default MainLayout