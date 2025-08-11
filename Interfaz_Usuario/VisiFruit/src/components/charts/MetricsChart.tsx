import React, { useEffect, useRef, useState } from 'react'
import {
  Box,
  ToggleButton,
  ToggleButtonGroup,
  useTheme,
} from '@mui/material'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { animate } from 'animejs'

type ChartType = 'line' | 'area'

const MetricsChart: React.FC = () => {
  const theme = useTheme()
  const chartRef = useRef<HTMLDivElement>(null)
  const [chartType, setChartType] = useState<ChartType>('area')
  
  

  // Generar datos simulados para la demo
  const generateData = () => {
    const now = new Date()
    const data = []
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000)
      data.push({
        time: time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        eficiencia: 75 + Math.random() * 20,
        throughput: 80 + Math.random() * 30,
        calidad: 90 + Math.random() * 8,
        temperatura: 35 + Math.random() * 15,
        cpu: 20 + Math.random() * 40,
        memoria: 45 + Math.random() * 30,
      })
    }
    
    return data
  }

  const [data] = useState(generateData())

  useEffect(() => {
    if (chartRef.current) {
      animate(chartRef.current, {
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
        ease: 'outCubic',
      })
    }
  }, [])

  const handleChartTypeChange = (
    _event: React.MouseEvent<HTMLElement>,
    newType: ChartType | null,
  ) => {
    if (newType !== null) {
      setChartType(newType)
      
      // Animación de cambio de tipo
      if (chartRef.current) {
        animate(chartRef.current.querySelector('.recharts-wrapper') as Element, {
          scale: [0.95, 1],
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
          <Box sx={{ mb: 1, fontWeight: 600, color: 'text.primary' }}>
            {label}
          </Box>
          {payload.map((entry: any, index: number) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                mb: 0.5,
                fontSize: '0.875rem',
              }}
            >
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: entry.color,
                }}
              />
              <span style={{ color: theme.palette.text.secondary }}>
                {entry.name}:
              </span>
              <span style={{ color: entry.color, fontWeight: 600 }}>
                {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
                {entry.name.includes('temperatura') ? '°C' : 
                 entry.name.includes('%') || entry.name === 'eficiencia' || entry.name === 'calidad' ? '%' : ''}
              </span>
            </Box>
          ))}
        </Box>
      )
    }
    return null
  }

  const renderChart = () => {
    const commonChartData = data
    const commonMargin = { top: 5, right: 30, left: 20, bottom: 5 }

    if (chartType === 'area') {
      return (
        <AreaChart data={commonChartData} margin={commonMargin}>
          <defs>
            <linearGradient id="colorEficiencia" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00E5A0" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#00E5A0" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4ECDC4" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#4ECDC4" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorCalidad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#FF6B6B" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#FF6B6B" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis 
            dataKey="time" 
            stroke={theme.palette.text.secondary}
            fontSize={12}
          />
          <YAxis 
            stroke={theme.palette.text.secondary}
            fontSize={12}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Area
            type="monotone"
            dataKey="eficiencia"
            name="Eficiencia"
            stroke="#00E5A0"
            fillOpacity={1}
            fill="url(#colorEficiencia)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="throughput"
            name="Throughput"
            stroke="#4ECDC4"
            fillOpacity={1}
            fill="url(#colorThroughput)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="calidad"
            name="Calidad"
            stroke="#FF6B6B"
            fillOpacity={1}
            fill="url(#colorCalidad)"
            strokeWidth={2}
          />
        </AreaChart>
      )
    }

    return (
      <LineChart data={commonChartData} margin={commonMargin}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
        <XAxis 
          dataKey="time" 
          stroke={theme.palette.text.secondary}
          fontSize={12}
        />
        <YAxis 
          stroke={theme.palette.text.secondary}
          fontSize={12}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="eficiencia"
          name="Eficiencia"
          stroke="#00E5A0"
          strokeWidth={3}
          dot={{ fill: '#00E5A0', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#00E5A0', strokeWidth: 2 }}
        />
        <Line
          type="monotone"
          dataKey="throughput"
          name="Throughput"
          stroke="#4ECDC4"
          strokeWidth={3}
          dot={{ fill: '#4ECDC4', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#4ECDC4', strokeWidth: 2 }}
        />
        <Line
          type="monotone"
          dataKey="calidad"
          name="Calidad"
          stroke="#FF6B6B"
          strokeWidth={3}
          dot={{ fill: '#FF6B6B', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#FF6B6B', strokeWidth: 2 }}
        />
        <Line
          type="monotone"
          dataKey="temperatura"
          name="Temperatura"
          stroke="#FFC107"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ fill: '#FFC107', strokeWidth: 2, r: 3 }}
        />
      </LineChart>
    )
  }

  return (
    <Box ref={chartRef} sx={{ height: '100%', position: 'relative' }}>
      {/* Controles del gráfico */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          zIndex: 10,
        }}
      >
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
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
              },
            },
          }}
        >
          <ToggleButton value="line">Líneas</ToggleButton>
          <ToggleButton value="area">Áreas</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Contenedor del gráfico */}
      <Box sx={{ height: 'calc(100% - 20px)', mt: 2.5 }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </Box>
    </Box>
  )
}

export default MetricsChart