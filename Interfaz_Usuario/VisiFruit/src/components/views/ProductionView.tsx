import React, { useEffect, useRef, useState } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  useTheme,
} from '@mui/material'
import {
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Speed,
  Timeline,
  Assignment,
  TuneRounded,
  DirectionsRun,
} from '@mui/icons-material'
import { animate, stagger } from 'animejs'
import { useAppSelector } from '../../types/redux'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import BeltControls from '../production/BeltControls'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index} style={{ height: '100%' }}>
      {value === index && <Box sx={{ height: '100%' }}>{children}</Box>}
    </div>
  )
}

const ProductionView: React.FC = () => {
  const theme = useTheme()
  const productionRef = useRef<HTMLDivElement>(null)
  
  
  const { status, currentSession } = useAppSelector(state => state.production)
  
  const [tabValue, setTabValue] = useState(0)
  const [configOpen, setConfigOpen] = useState(false)
  const [targetRate, setTargetRate] = useState(status.targetRate)
  const [fruitCategory, setFruitCategory] = useState(status.activeGroup.category)

  // Datos históricos simulados
  const [historicalData] = useState(() => {
    const data = []
    const now = new Date()
    
    for (let i = 47; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 30 * 60 * 1000) // cada 30 min
      data.push({
        time: time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        throughput: 70 + Math.random() * 40,
        efficiency: 75 + Math.random() * 20,
        quality: 88 + Math.random() * 10,
        defects: Math.random() * 5,
        downtime: Math.random() * 2,
      })
    }
    
    return data
  })

  useEffect(() => {
    if (productionRef.current) {
      const cards = productionRef.current.querySelectorAll('.production-card')
      
      animate(cards, {
        translateY: [60, 0],
        opacity: [0, 1],
        duration: 800,
        delay: stagger(200, { start: 400 }),
        ease: 'outCubic',
      })
    }
  }, [])

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    
    // Animación de cambio de tab
    const tabPanel = document.querySelector(`[data-tab="${newValue}"]`)
    if (tabPanel) {
      animate(tabPanel, {
        opacity: [0, 1],
        translateX: [50, 0],
        duration: 600,
        ease: 'outCubic',
      })
    }
  }

  const handleStartProduction = () => {
    // Implementar lógica para iniciar producción
    console.log('Starting production with rate:', targetRate)
    setConfigOpen(false)
  }

  const handleStopProduction = () => {
    // Implementar lógica para detener producción
    console.log('Stopping production')
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return theme.palette.success.main
      case 'paused': return theme.palette.warning.main
      case 'error': return theme.palette.error.main
      default: return theme.palette.grey[500]
    }
  }

  return (
    <Box ref={productionRef} sx={{ width: '100%', height: '100%' }}>
      {/* Header con controles */}
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
            Control de Producción
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Gestión avanzada del sistema de etiquetado
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={status.status === 'running' ? 'Produciendo' : 'Detenido'}
            sx={{
              background: `linear-gradient(45deg, ${getStatusColor(status.status)}20, ${getStatusColor(status.status)}40)`,
              color: getStatusColor(status.status),
              fontWeight: 600,
              ...(status.status === 'running' && {
                animation: 'pulse 2s infinite',
              }),
            }}
          />
          
          <Button
            variant="contained"
            startIcon={status.status === 'running' ? <Pause /> : <PlayArrow />}
            onClick={() => setConfigOpen(true)}
            sx={{
              background: theme.gradients.primary,
              color: '#000',
              fontWeight: 600,
              '&:hover': {
                boxShadow: theme.shadows[8],
                transform: 'translateY(-2px)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {status.status === 'running' ? 'Pausar' : 'Iniciar'}
          </Button>
          
          <IconButton
            onClick={handleStopProduction}
            disabled={status.status === 'stopped'}
            sx={{
              background: 'rgba(244, 67, 54, 0.1)',
              color: theme.palette.error.main,
              '&:hover': {
                background: 'rgba(244, 67, 54, 0.2)',
                transform: 'scale(1.05)',
              },
              '&:disabled': {
                opacity: 0.5,
              },
            }}
          >
            <Stop />
          </IconButton>
        </Box>
      </Box>

      {/* Tabs de navegación */}
      <Card
        className="production-card"
        sx={{
          mb: 3,
          background: theme.gradients.glass,
          backdropFilter: 'blur(20px)',
          border: `1px solid rgba(255, 255, 255, 0.1)`,
        }}
      >
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          sx={{
            '& .MuiTab-root': {
              fontWeight: 600,
              '&.Mui-selected': {
                color: theme.palette.primary.main,
              },
            },
            '& .MuiTabs-indicator': {
              background: theme.gradients.primary,
              height: 3,
            },
          }}
        >
          <Tab label="Estado Actual" icon={<Speed />} />
          <Tab label="Historial" icon={<Timeline />} />
          <Tab label="Controles de Banda" icon={<DirectionsRun />} />
          <Tab label="Configuración" icon={<Settings />} />
          <Tab label="Reportes" icon={<Assignment />} />
        </Tabs>
      </Card>

      {/* Contenido de las tabs */}
      <Box sx={{ height: 'calc(100% - 200px)' }}>
        {/* Tab 1: Estado Actual */}
        <TabPanel value={tabValue} index={0}>
          <Box data-tab="0" sx={{ height: '100%' }}>
            <Grid container spacing={3} sx={{ height: '100%' }}>
              {/* Métricas principales */}
              <Grid size={{ xs: 12, lg: 8 }}>
                <Card
                  className="production-card"
                  sx={{
                    height: '100%',
                    background: theme.gradients.glass,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                  }}
                >
                  <CardContent sx={{ p: 3, height: '100%' }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                      Métricas en Tiempo Real
                    </Typography>
                    
                    <Grid container spacing={3} sx={{ mb: 3 }}>
                      {[
                        { label: 'Throughput Actual', value: `${status.currentRate.toFixed(1)}/min`, color: 'primary' },
                        { label: 'Eficiencia', value: `${status.efficiency.toFixed(1)}%`, color: 'success' },
                        { label: 'Calidad', value: `${status.qualityScore.toFixed(1)}%`, color: 'info' },
                        { label: 'Uptime', value: status.uptimeToday, color: 'warning' },
                      ].map((metric) => (
                        <Grid key={metric.label} size={{ xs: 6, md: 3 }}>
                          <Box
                            sx={{
                              p: 2,
                              borderRadius: 2,
                              background: `rgba(${
                                metric.color === 'primary' ? '0, 229, 160' :
                                metric.color === 'success' ? '76, 175, 80' :
                                metric.color === 'info' ? '33, 150, 243' :
                                '255, 193, 7'
                              }, 0.1)`,
                              border: `1px solid rgba(${
                                metric.color === 'primary' ? '0, 229, 160' :
                                metric.color === 'success' ? '76, 175, 80' :
                                metric.color === 'info' ? '33, 150, 243' :
                                '255, 193, 7'
                              }, 0.3)`,
                              textAlign: 'center',
                            }}
                          >
                            <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5 }}>
                              {metric.value}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {metric.label}
                            </Typography>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>

                    {/* Gráfico de throughput */}
                    <Box sx={{ height: 250 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={historicalData.slice(-12)}>
                          <defs>
                            <linearGradient id="throughputGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#00E5A0" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#00E5A0" stopOpacity={0.1}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                          <XAxis dataKey="time" stroke={theme.palette.text.secondary} fontSize={12} />
                          <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
                          <Tooltip
                            contentStyle={{
                              background: theme.gradients.glass,
                              border: `1px solid rgba(255, 255, 255, 0.1)`,
                              borderRadius: 8,
                              backdropFilter: 'blur(20px)',
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="throughput"
                            stroke="#00E5A0"
                            fillOpacity={1}
                            fill="url(#throughputGradient)"
                            strokeWidth={2}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Panel de control */}
              <Grid size={{ xs: 12, lg: 4 }}>
                <Card
                  className="production-card"
                  sx={{
                    height: '100%',
                    background: theme.gradients.glass,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                  }}
                >
                  <CardContent sx={{ p: 3, height: '100%' }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                      Estado del Sistema
                    </Typography>
                    
                    {/* Información de sesión */}
                    {currentSession && (
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          background: 'rgba(0, 229, 160, 0.05)',
                          border: `1px solid rgba(0, 229, 160, 0.2)`,
                          mb: 3,
                        }}
                      >
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                          Sesión Activa
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          ID: {currentSession.sessionId}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Iniciada: {new Date(currentSession.startedAt).toLocaleTimeString('es-ES')}
                        </Typography>
                      </Box>
                    )}

                    {/* Categoría activa */}
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        background: theme.gradients.glass,
                        border: `1px solid rgba(255, 255, 255, 0.1)`,
                        mb: 3,
                        textAlign: 'center',
                      }}
                    >
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        Categoría Activa
                      </Typography>
                      <Box sx={{ fontSize: '2rem', mb: 1 }}>
                        {status.activeGroup.emoji}
                      </Box>
                      <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                        {status.activeGroup.category}
                      </Typography>
                    </Box>

                    {/* Estadísticas rápidas */}
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                        Estadísticas
                      </Typography>
                      
                      {[
                        { label: 'Items Procesados Hoy', value: status.itemsProcessedToday.toLocaleString() },
                        { label: 'Etiquetadoras Activas', value: `${status.activeLabelers}/4` },
                        { label: 'Velocidad de Banda', value: `${status.beltSpeed} m/s` },
                        { label: 'Último Cambio', value: new Date(status.lastSwitch).toLocaleTimeString('es-ES') },
                       ].map((stat) => (
                        <Box key={stat.label} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                          <Typography variant="body2" color="text.secondary">
                            {stat.label}:
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {stat.value}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Tab 2: Historial */}
        <TabPanel value={tabValue} index={1}>
          <Box data-tab="1">
            <Card
              className="production-card"
              sx={{
                height: 500,
                background: theme.gradients.glass,
                backdropFilter: 'blur(20px)',
                border: `1px solid rgba(255, 255, 255, 0.1)`,
              }}
            >
              <CardContent sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                  Historial de Producción (48h)
                </Typography>
                
                <ResponsiveContainer width="100%" height="90%">
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                    <XAxis dataKey="time" stroke={theme.palette.text.secondary} fontSize={12} />
                    <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        background: theme.gradients.glass,
                        border: `1px solid rgba(255, 255, 255, 0.1)`,
                        borderRadius: 8,
                        backdropFilter: 'blur(20px)',
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="throughput"
                      name="Throughput"
                      stroke="#00E5A0"
                      strokeWidth={2}
                      dot={{ fill: '#00E5A0', strokeWidth: 2, r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="efficiency"
                      name="Eficiencia"
                      stroke="#4ECDC4"
                      strokeWidth={2}
                      dot={{ fill: '#4ECDC4', strokeWidth: 2, r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="quality"
                      name="Calidad"
                      stroke="#FF6B6B"
                      strokeWidth={2}
                      dot={{ fill: '#FF6B6B', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Box>
        </TabPanel>

        {/* Tab 3: Controles de Banda */}
        <TabPanel value={tabValue} index={2}>
          <Box data-tab="2" sx={{ height: '100%' }}>
            <BeltControls 
              onBeltAction={async (action, params) => {
                console.log('Acción de banda:', action, params);
                // Aquí se integrará con la API del backend
                try {
                  const response = await fetch(`http://localhost:8000/belt/${action}`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(params || {}),
                  });
                  
                  if (!response.ok) {
                    throw new Error(`Error en la respuesta: ${response.status}`);
                  }
                  
                  const result = await response.json();
                  console.log('Resultado de la acción:', result);
                  return result;
                } catch (error) {
                  console.error('Error ejecutando acción de banda:', error);
                  throw error;
                }
              }}
              isConnected={true}
              disabled={false}
            />
          </Box>
        </TabPanel>

        {/* Tab 4: Configuración */}
        <TabPanel value={tabValue} index={3}>
          <Box data-tab="3">
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card
                  className="production-card"
                  sx={{
                    background: theme.gradients.glass,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                      Configuración de Producción
                    </Typography>
                    
                    <TextField
                      fullWidth
                      label="Tasa Objetivo (items/min)"
                      type="number"
                      value={targetRate}
                      onChange={(e) => setTargetRate(Number(e.target.value))}
                      sx={{ mb: 3 }}
                    />
                    
                    <FormControl fullWidth sx={{ mb: 3 }}>
                      <InputLabel>Categoría de Fruta</InputLabel>
                      <Select
                        value={fruitCategory}
                        onChange={(e) => setFruitCategory(e.target.value)}
                      >
                        <MenuItem value="apple">🍎 Manzanas</MenuItem>
                        <MenuItem value="orange">🍊 Naranjas</MenuItem>
                        <MenuItem value="pear">🍐 Peras</MenuItem>
                        <MenuItem value="banana">🍌 Plátanos</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={<TuneRounded />}
                      sx={{
                        background: theme.gradients.primary,
                        color: '#000',
                        fontWeight: 600,
                      }}
                    >
                      Aplicar Configuración
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card
                  className="production-card"
                  sx={{
                    background: theme.gradients.glass,
                    backdropFilter: 'blur(20px)',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                      Configuración Avanzada
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary">
                      Próximamente: Configuraciones avanzadas del sistema, calibración de sensores, 
                      parámetros de calidad, y más opciones de personalización.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>

        {/* Tab 5: Reportes */}
        <TabPanel value={tabValue} index={4}>
          <Box data-tab="4">
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Generación de Reportes
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Funcionalidad de reportes en desarrollo...
            </Typography>
          </Box>
        </TabPanel>
      </Box>

      {/* Dialog de configuración */}
      <Dialog
        open={configOpen}
        onClose={() => setConfigOpen(false)}
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
        <DialogTitle>Configurar Producción</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Tasa Objetivo (items/min)"
            type="number"
            fullWidth
            variant="outlined"
            value={targetRate}
            onChange={(e) => setTargetRate(Number(e.target.value))}
            sx={{ mb: 2 }}
          />
          
          <FormControl fullWidth>
            <InputLabel>Categoría de Fruta</InputLabel>
            <Select
              value={fruitCategory}
              onChange={(e) => setFruitCategory(e.target.value)}
            >
              <MenuItem value="apple">🍎 Manzanas</MenuItem>
              <MenuItem value="orange">🍊 Naranjas</MenuItem>
              <MenuItem value="pear">🍐 Peras</MenuItem>
              <MenuItem value="banana">🍌 Plátanos</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigOpen(false)}>Cancelar</Button>
          <Button
            onClick={handleStartProduction}
            variant="contained"
            sx={{
              background: theme.gradients.primary,
              color: '#000',
              fontWeight: 600,
            }}
          >
            {status.status === 'running' ? 'Aplicar Cambios' : 'Iniciar Producción'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ProductionView