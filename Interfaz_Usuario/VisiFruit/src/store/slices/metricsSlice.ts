import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface MetricPoint {
  timestamp: string
  value: number
  label?: string
}

export interface SystemMetrics {
  cpuUsage: MetricPoint[]
  memoryUsage: MetricPoint[]
  diskSpace: MetricPoint[]
  temperature: MetricPoint[]
  networkTraffic: MetricPoint[]
}

export interface ProductionMetrics {
  throughput: MetricPoint[]
  quality: MetricPoint[]
  efficiency: MetricPoint[]
  defectRate: MetricPoint[]
  downtime: MetricPoint[]
}

export interface PerformanceMetrics {
  averageProcessingTime: number
  peakThroughput: number
  totalItemsProcessed: number
  accuracyRate: number
  systemHealth: number
}

interface MetricsState {
  systemMetrics: SystemMetrics
  productionMetrics: ProductionMetrics
  performanceMetrics: PerformanceMetrics
  realTimeMetrics: {
    fps: number
    latency: number
    memoryUsage: number
    cpuLoad: number
    temperature: number
  }
  isLoading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: MetricsState = {
  systemMetrics: {
    cpuUsage: [],
    memoryUsage: [],
    diskSpace: [],
    temperature: [],
    networkTraffic: []
  },
  productionMetrics: {
    throughput: [],
    quality: [],
    efficiency: [],
    defectRate: [],
    downtime: []
  },
  performanceMetrics: {
    averageProcessingTime: 0,
    peakThroughput: 0,
    totalItemsProcessed: 0,
    accuracyRate: 0,
    systemHealth: 0
  },
  realTimeMetrics: {
    fps: 30,
    latency: 50,
    memoryUsage: 45,
    cpuLoad: 30,
    temperature: 42
  },
  isLoading: false,
  error: null,
  lastUpdated: null
}

const metricsSlice = createSlice({
  name: 'metrics',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    updateSystemMetrics: (state, action: PayloadAction<Partial<SystemMetrics>>) => {
      state.systemMetrics = { ...state.systemMetrics, ...action.payload }
      state.lastUpdated = new Date().toISOString()
    },
    updateProductionMetrics: (state, action: PayloadAction<Partial<ProductionMetrics>>) => {
      state.productionMetrics = { ...state.productionMetrics, ...action.payload }
      state.lastUpdated = new Date().toISOString()
    },
    updatePerformanceMetrics: (state, action: PayloadAction<Partial<PerformanceMetrics>>) => {
      state.performanceMetrics = { ...state.performanceMetrics, ...action.payload }
      state.lastUpdated = new Date().toISOString()
    },
    updateRealTimeMetrics: (state, action: PayloadAction<Partial<MetricsState['realTimeMetrics']>>) => {
      state.realTimeMetrics = { ...state.realTimeMetrics, ...action.payload }
    },
    addMetricPoint: (state, action: PayloadAction<{
      category: keyof SystemMetrics | keyof ProductionMetrics
      point: MetricPoint
    }>) => {
      const { category, point } = action.payload
      
      // Verificar si es una métrica del sistema
      if (category in state.systemMetrics) {
        const metrics = state.systemMetrics[category as keyof SystemMetrics]
        metrics.push(point)
        // Mantener solo los últimos 100 puntos
        if (metrics.length > 100) {
          metrics.shift()
        }
      }
      
      // Verificar si es una métrica de producción
      if (category in state.productionMetrics) {
        const metrics = state.productionMetrics[category as keyof ProductionMetrics]
        metrics.push(point)
        // Mantener solo los últimos 100 puntos
        if (metrics.length > 100) {
          metrics.shift()
        }
      }
      
      state.lastUpdated = new Date().toISOString()
    },
    clearMetrics: (state) => {
      state.systemMetrics = {
        cpuUsage: [],
        memoryUsage: [],
        diskSpace: [],
        temperature: [],
        networkTraffic: []
      }
      state.productionMetrics = {
        throughput: [],
        quality: [],
        efficiency: [],
        defectRate: [],
        downtime: []
      }
    }
  }
})

export const {
  setLoading,
  setError,
  updateSystemMetrics,
  updateProductionMetrics,
  updatePerformanceMetrics,
  updateRealTimeMetrics,
  addMetricPoint,
  clearMetrics
} = metricsSlice.actions

export default metricsSlice.reducer