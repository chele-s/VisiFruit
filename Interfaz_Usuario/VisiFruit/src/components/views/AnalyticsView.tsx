import React, { useEffect, useRef, useState } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  IconButton,
  useTheme,
} from '@mui/material'
import {
  Analytics,
  TrendingUp,
  Assessment,
  PieChart,
  BarChart,
  ShowChart,
  Download,
  Refresh,
} from '@mui/icons-material'
import { animate, stagger } from 'animejs'
import {
  AreaChart,
  Area,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'
 

type ChartType = 'line' | 'area' | 'bar' | 'pie' | 'radar'
type TimePeriod = '1h' | '6h' | '24h' | '7d' | '30d'

const AnalyticsView: React.FC = () => {
  const theme = useTheme()
  const analyticsRef = useRef<HTMLDivElement>(null)
  
  const [chartType, setChartType] = useState<ChartType>('area')
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('24h')
  
  // Datos simulados para diferentes tipos de análisis
  const [productionData] = useState(() => {
    const data = []
    const now = new Date()
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000)
      data.push({
        time: time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        throughput: 70 + Math.random() * 40,
        efficiency: 75 + Math.random() * 20,
        quality: 85 + Math.random() * 12,
        errors: Math.random() * 10,
        downtime: Math.random() * 5,
        temperature: 35 + Math.random() * 15,
        speed: 0.3 + Math.random() * 0.4,
      })
    }
    
    return data
  })

  const [fruitDistribution] = useState([
    { name: 'Manzanas', value: 45, color: '#FF6B6B', emoji: '🍎' },
    { name: 'Naranjas', value: 30, color: '#FFA500', emoji: '🍊' },
    { name: 'Peras', value: 15, color: '#00E5A0', emoji: '🍐' },
    { name: 'Plátanos', value: 10, color: '#FFD700', emoji: '🍌' },
  ])

  const [qualityMetrics] = useState([
    { metric: 'Precisión', value: 95, fullMark: 100 },
    { metric: 'Velocidad', value: 87, fullMark: 100 },
    { metric: 'Consistencia', value: 92, fullMark: 100 },
    { metric: 'Detección', value: 98, fullMark: 100 },
    { metric: 'Clasificación', value: 89, fullMark: 100 },
  ])

  const [performanceData] = useState(() => {
    const categories = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    return categories.map(day => ({
      day,
      processed: 3000 + Math.random() * 2000,
      defective: 50 + Math.random() * 100,
      efficiency: 80 + Math.random() * 15,
    }))
  })

  useEffect(() => {
    if (analyticsRef.current) {
      const cards = analyticsRef.current.querySelectorAll('.analytics-card')
      
      animate(cards, {
        translateY: [50, 0],
        opacity: [0, 1],
        duration: 800,
        delay: stagger(150, { start: 300 }),
        ease: 'outCubic',
      })
    }
  }, [])

  const handleChartTypeChange = (_event: React.MouseEvent<HTMLElement>, newType: ChartType | null) => {
    if (newType !== null) {
      setChartType(newType)
      
      // Animación de cambio
      const chartContainer = document.querySelector('.main-chart')
      if (chartContainer) {
        animate(chartContainer, {
          scale: [0.95, 1],
          opacity: [0.7, 1],
          duration: 400,
          ease: 'outCubic',
        })
      }
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            background: theme.gradients.glass,
            backdropFilter: 'blur(20px)',
            border: `1px solid rgba(255, 255, 255, 0.1)`,
            borderRadius: 2,
            p: 2,
            boxShadow: theme.shadows[8],
          }}
        >
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            {label}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: entry.color,
                }}
              />
              <Typography variant="body2" color="text.secondary">
                {entry.name}:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, color: entry.color }}>
                {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
                {entry.name.includes('eficiencia') || entry.name.includes('calidad') ? '%' : ''}
              </Typography>
            </Box>
          ))}
        </Box>
      )
    }
    return null
  }

  const renderMainChart = () => {
    const commonChartData = productionData
    const commonMargin = { top: 5, right: 30, left: 20, bottom: 5 }

    switch (chartType) {
      case 'area':
        return (
          <AreaChart data={commonChartData} margin={commonMargin}>
            <defs>
              <linearGradient id="throughputGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00E5A0" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#00E5A0" stopOpacity={0.1}/>
              </linearGradient>
              <linearGradient id="qualityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4ECDC4" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#4ECDC4" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="time" stroke={theme.palette.text.secondary} fontSize={12} />
            <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="throughput"
              name="Throughput"
              stroke="#00E5A0"
              fillOpacity={1}
              fill="url(#throughputGradient)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="quality"
              name="Calidad"
              stroke="#4ECDC4"
              fillOpacity={1}
              fill="url(#qualityGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        )

      case 'bar':
        return (
          <RechartsBarChart data={commonChartData} margin={commonMargin}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="time" stroke={theme.palette.text.secondary} fontSize={12} />
            <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="throughput" name="Throughput" fill="#00E5A0" />
            <Bar dataKey="efficiency" name="Eficiencia" fill="#4ECDC4" />
          </RechartsBarChart>
        )

      case 'pie':
        return (
          <RechartsPieChart width={400} height={300}>
            <Tooltip />
            <RechartsPieChart dataKey="value" data={fruitDistribution} cx="50%" cy="50%" outerRadius={100}>
              {fruitDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </RechartsPieChart>
            <Legend />
          </RechartsPieChart>
        )

      case 'radar':
        return (
          <RadarChart width={400} height={300} data={qualityMetrics}>
            <PolarGrid stroke="rgba(255, 255, 255, 0.2)" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: theme.palette.text.secondary }} />
            <PolarRadiusAxis tick={{ fontSize: 10, fill: theme.palette.text.secondary }} />
            <Radar
              name="Métricas"
              dataKey="value"
              stroke="#00E5A0"
              fill="#00E5A0"
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Tooltip />
          </RadarChart>
        )

      default:
        return (
          <LineChart data={commonChartData} margin={commonMargin}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
            <XAxis dataKey="time" stroke={theme.palette.text.secondary} fontSize={12} />
            <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
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
        )
    }
  }

  return (
    <Box ref={analyticsRef} sx={{ width: '100%', height: '100%' }}>
      {/* Header */}
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
            Análisis Avanzado
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Insights y métricas detalladas del sistema
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Período</InputLabel>
            <Select
              value={timePeriod}
              onChange={(e) => setTimePeriod(e.target.value as TimePeriod)}
            >
              <MenuItem value="1h">1 Hora</MenuItem>
              <MenuItem value="6h">6 Horas</MenuItem>
              <MenuItem value="24h">24 Horas</MenuItem>
              <MenuItem value="7d">7 Días</MenuItem>
              <MenuItem value="30d">30 Días</MenuItem>
            </Select>
          </FormControl>
          
          <IconButton
            sx={{
              background: theme.gradients.glass,
              '&:hover': { transform: 'rotate(180deg) scale(1.05)' },
              transition: 'all 0.3s ease',
            }}
          >
            <Refresh />
          </IconButton>
          
          <IconButton
            sx={{
              background: theme.gradients.glass,
              '&:hover': { transform: 'scale(1.05)' },
              transition: 'all 0.3s ease',
            }}
          >
            <Download />
          </IconButton>
        </Box>
      </Box>

      {/* Controles de gráfico */}
      <Card
        className="analytics-card"
        sx={{
          mb: 3,
          background: theme.gradients.glass,
          backdropFilter: 'blur(20px)',
          border: `1px solid rgba(255, 255, 255, 0.1)`,
        }}
      >
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Visualización de Datos
            </Typography>
            
            <ToggleButtonGroup
              value={chartType}
              exclusive
              onChange={handleChartTypeChange}
              size="small"
              sx={{
                '& .MuiToggleButton-root': {
                  color: 'text.secondary',
                  border: `1px solid rgba(255, 255, 255, 0.1)`,
                  '&.Mui-selected': {
                    color: theme.palette.primary.main,
                    backgroundColor: 'rgba(0, 229, 160, 0.1)',
                    border: `1px solid ${theme.palette.primary.main}`,
                  },
                },
              }}
            >
              <ToggleButton value="line">
                <ShowChart />
              </ToggleButton>
              <ToggleButton value="area">
                <Analytics />
              </ToggleButton>
              <ToggleButton value="bar">
                <BarChart />
              </ToggleButton>
              <ToggleButton value="pie">
                <PieChart />
              </ToggleButton>
              <ToggleButton value="radar">
                <Assessment />
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Gráfico principal */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card
            className="analytics-card main-chart"
            sx={{
              height: 400,
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Métricas de Rendimiento
                </Typography>
                <Chip
                  label={chartType.toUpperCase()}
                  color="primary"
                  size="small"
                  sx={{ fontWeight: 600 }}
                />
              </Box>
              
              <Box sx={{ height: 'calc(100% - 60px)' }}>
                <ResponsiveContainer width="100%" height="100%">
                  {renderMainChart()}
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* KPIs y estadísticas */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card
            className="analytics-card"
            sx={{
              height: 400,
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                KPIs Principales
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {[
                  { 
                    label: 'Throughput Promedio', 
                    value: '87.3/min', 
                    change: '+5.2%', 
                    color: 'success',
                    icon: <TrendingUp />
                  },
                  { 
                    label: 'Eficiencia Global', 
                    value: '92.1%', 
                    change: '+1.8%', 
                    color: 'primary',
                    icon: <Analytics />
                  },
                  { 
                    label: 'Calidad Promedio', 
                    value: '94.7%', 
                    change: '+0.5%', 
                    color: 'info',
                    icon: <Assessment />
                  },
                  { 
                    label: 'Tiempo de Inactividad', 
                    value: '2.3%', 
                    change: '-0.7%', 
                    color: 'error',
                    icon: <BarChart />
                  },
                ].map((kpi) => (
                  <Box
                    key={kpi.label}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      background: `rgba(${
                        kpi.color === 'primary' ? '0, 229, 160' :
                        kpi.color === 'success' ? '76, 175, 80' :
                        kpi.color === 'info' ? '33, 150, 243' :
                        '244, 67, 54'
                      }, 0.1)`,
                      border: `1px solid rgba(${
                        kpi.color === 'primary' ? '0, 229, 160' :
                        kpi.color === 'success' ? '76, 175, 80' :
                        kpi.color === 'info' ? '33, 150, 243' :
                        '244, 67, 54'
                      }, 0.3)`,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ mr: 1, color: (
                        kpi.color === 'primary' ? theme.palette.primary.main :
                        kpi.color === 'success' ? theme.palette.success.main :
                        kpi.color === 'info' ? theme.palette.info.main :
                        kpi.color === 'error' ? theme.palette.error.main :
                        theme.palette.primary.main
                      ) }}>
                        {kpi.icon}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {kpi.label}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {kpi.value}
                      </Typography>
                      <Chip
                        label={kpi.change}
                        size="small"
                        color={kpi.change.startsWith('+') ? 'success' : 'error'}
                        sx={{ fontSize: '0.7rem', fontWeight: 600 }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Gráfico de rendimiento semanal */}
        <Grid size={{ xs: 12 }}>
          <Card
            className="analytics-card"
            sx={{
              height: 300,
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Rendimiento Semanal
              </Typography>
              
              <ResponsiveContainer width="100%" height="90%">
                <RechartsBarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                  <XAxis dataKey="day" stroke={theme.palette.text.secondary} fontSize={12} />
                  <YAxis stroke={theme.palette.text.secondary} fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="processed" name="Procesadas" fill="#00E5A0" />
                  <Bar dataKey="defective" name="Defectuosas" fill="#FF6B6B" />
                </RechartsBarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default AnalyticsView