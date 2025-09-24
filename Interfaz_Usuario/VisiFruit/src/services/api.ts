import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// URL base del backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

// Tipos de datos de la API
export interface ProductionStatusResponse {
  status: string
  current_rate: number
  target_rate: number
  efficiency: number
  items_processed_today: number
  active_labelers: number
  active_group: {
    id: number
    category: string
    emoji: string
  }
  belt_speed: number
  quality_score: number
  uptime_today: string
  last_switch: string
}

export interface ProductionStartRequest {
  target_rate?: number
  duration_minutes?: number
  quality_threshold?: number
  auto_stop?: boolean
}

export interface SystemMetricsResponse {
  cpu_usage: number
  memory_usage: number
  disk_space: number
  temperature: number
  network_traffic: number
  timestamp: string
}

export interface AlertResponse {
  id: string
  title: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  category: string
  timestamp: string
  acknowledged: boolean
  resolved: boolean
}

export interface SystemStatusResponse {
  system_info: {
    name: string
    version: string
    uptime: string
    installation_id: string
  }
  components: any
  resources: any
}

export interface MetricsSummaryResponse {
  period: string
  generated_at: string
  production: {
    total_items: number
    items_per_hour: number
    efficiency: number
    quality_score: number
    downtime_minutes: number
  }
  system: {
    uptime_percentage: number
    cpu_avg: number
    memory_avg: number
    errors_count: number
    alerts_count: number
  }
  components: any
}

// Cliente API personalizado
class VisiFruitAPI {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 segundos timeout

      const response = await fetch(url, {
        ...options,
        headers: defaultHeaders,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error')
        console.warn(`API ${response.status} error for ${url}:`, errorText)
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.error(`API request timeout: ${url}`)
        throw new Error(`Request timeout for ${url}`)
      }
      console.error(`API request failed: ${url}`, error)
      throw error
    }
  }

  // Endpoints de Producción
  async getProductionStatus(): Promise<ProductionStatusResponse> {
    return this.request<ProductionStatusResponse>('/api/production/status')
  }

  async startProduction(data: ProductionStartRequest): Promise<any> {
    return this.request('/api/production/start', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async stopProduction(reason: string): Promise<any> {
    return this.request('/api/production/stop', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  }

  // Endpoints de Métricas
  async getSystemMetrics(): Promise<SystemMetricsResponse> {
    return this.request<SystemMetricsResponse>('/api/system/performance')
  }

  async getProductionHistory(period: string = '24h'): Promise<any[]> {
    return this.request<any[]>(`/api/metrics/history/production?period=${period}`)
  }

  // Endpoints de Alertas
  async getAlerts(): Promise<any[]> {
    return this.request<any[]>('/api/alerts')
  }

  async acknowledgeAlert(alertId: string, acknowledgedBy: string): Promise<any> {
    return this.request(`/api/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by: acknowledgedBy }),
    })
  }

  // Endpoints de Banda Transportadora
  async startBeltForward(): Promise<any> {
    return this.request('/belt/start_forward', {
      method: 'POST',
    })
  }

  async startBeltBackward(): Promise<any> {
    return this.request('/belt/start_backward', {
      method: 'POST',
    })
  }

  async stopBelt(): Promise<any> {
    return this.request('/belt/stop', {
      method: 'POST',
    })
  }

  async emergencyStopBelt(): Promise<any> {
    return this.request('/belt/emergency_stop', {
      method: 'POST',
    })
  }

  async setBeltSpeed(speed: number): Promise<any> {
    return this.request('/belt/set_speed', {
      method: 'POST',
      body: JSON.stringify({ speed }),
    })
  }

  async toggleBeltEnable(): Promise<any> {
    return this.request('/belt/toggle_enable', {
      method: 'POST',
    })
  }

  async getBeltStatus(): Promise<any> {
    return this.request('/belt/status', {
      method: 'GET',
    })
  }

  // Endpoints de Stepper Láser (DRV8825)
  async toggleLaserStepper(enabled: boolean): Promise<any> {
    return this.request('/laser_stepper/toggle', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    })
  }

  async testLaserStepper(duration: number = 0.5, intensity: number = 80): Promise<any> {
    return this.request('/laser_stepper/test', {
      method: 'POST',
      body: JSON.stringify({ duration, intensity }),
    })
  }

  // Endpoints de Control del Motor DC
  async activateLabelerGroup(category: string): Promise<any> {
    return this.request('/motor/activate_group', {
      method: 'POST',
      body: JSON.stringify({ category }),
    })
  }

  async getMotorStatus(): Promise<any> {
    return this.request('/motor/status', {
      method: 'GET',
    })
  }

  // Endpoints de Sistema de Desviadores
  async getDiverstersStatus(): Promise<any> {
    return this.request('/diverters/status', {
      method: 'GET',
    })
  }

  async classifyFruit(category: string, delay: number = 0): Promise<any> {
    return this.request('/diverters/classify', {
      method: 'POST',
      body: JSON.stringify({ category, delay }),
    })
  }

  async calibrateDiverters(): Promise<any> {
    return this.request('/diverters/calibrate', {
      method: 'POST',
    })
  }

  async emergencyStopDiverters(): Promise<any> {
    return this.request('/diverters/emergency_stop', {
      method: 'POST',
    })
  }

  // Endpoints de Configuración
  async updateConfig(key: string, value: any): Promise<any> {
    return this.request('/api/config/update', {
      method: 'POST',
      body: JSON.stringify({ key, value }),
    })
  }

  // Endpoints del Sistema
  async getSystemStatus(): Promise<SystemStatusResponse> {
    return this.request<SystemStatusResponse>('/api/system/status')
  }

  async getHealthCheck(): Promise<any> {
    return this.request<any>('/health')
  }

  async getPerformanceMetrics(): Promise<any> {
    return this.request<any>('/api/system/performance')
  }

  // Endpoints de Métricas Avanzadas
  async getMetricsSummary(period: string = '24h'): Promise<MetricsSummaryResponse> {
    return this.request<MetricsSummaryResponse>(`/api/metrics/summary?period=${period}`)
  }

  async getPerformanceData(): Promise<any> {
    return this.request<any>('/api/metrics/performance')
  }

  // Simulación de producción para demo
  async simulateProduction(): Promise<any> {
    return this.request('/api/system/simulate', {
      method: 'POST',
    })
  }
}

// Instancia global de la API
export const api = new VisiFruitAPI()

// Hooks personalizados para React Query
export const useProductionStatus = () => {
  return useQuery({
    queryKey: ['production', 'status'],
    queryFn: () => api.getProductionStatus(),
    refetchInterval: 5000, // Actualizar cada 5 segundos
    staleTime: 1000, // Considerar stale después de 1 segundo
  })
}

export const useSystemMetrics = () => {
  return useQuery({
    queryKey: ['system', 'metrics'],
    queryFn: () => api.getSystemMetrics(),
    refetchInterval: 10000, // Actualizar cada 10 segundos
  })
}

export const useProductionHistory = (period: string = '24h') => {
  return useQuery({
    queryKey: ['production', 'history', period],
    queryFn: () => api.getProductionHistory(period),
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: (failureCount, error) => {
      // Solo reintentar 2 veces para errores de red, no para errores 404
      if (error instanceof Error && error.message.includes('404')) {
        return false
      }
      return failureCount < 2
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

export const useAlerts = () => {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => api.getAlerts(),
    refetchInterval: 30000, // Actualizar cada 30 segundos
  })
}

// Mutations para acciones
export const useStartProduction = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ProductionStartRequest) => api.startProduction(data),
    onSuccess: () => {
      // Invalidar y refetch el estado de producción
      queryClient.invalidateQueries({ queryKey: ['production', 'status'] })
    },
  })
}

export const useStopProduction = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (reason: string) => api.stopProduction(reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['production', 'status'] })
    },
  })
}

export const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ alertId, acknowledgedBy }: { alertId: string; acknowledgedBy: string }) =>
      api.acknowledgeAlert(alertId, acknowledgedBy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export const useUpdateConfig = () => {
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: any }) =>
      api.updateConfig(key, value),
  })
}

// Nuevos hooks para endpoints adicionales
export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: () => api.getSystemStatus(),
    refetchInterval: 15000, // Actualizar cada 15 segundos
    retry: 2,
  })
}

export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealthCheck(),
    refetchInterval: 30000, // Actualizar cada 30 segundos
    retry: 1,
  })
}

export const useMetricsSummary = (period: string = '24h') => {
  return useQuery({
    queryKey: ['metrics', 'summary', period],
    queryFn: () => api.getMetricsSummary(period),
    refetchInterval: 10000, // Actualizar cada 10 segundos
    staleTime: 5000,
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

export const usePerformanceData = () => {
  return useQuery({
    queryKey: ['metrics', 'performance'],
    queryFn: () => api.getPerformanceData(),
    refetchInterval: 5000, // Actualizar cada 5 segundos
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

// Hook para simulación (útil para demo)
export const useSimulateProduction = () => {
  return useMutation({
    mutationFn: () => api.simulateProduction(),
  })
}

// Hooks para Banda Transportadora
export const useBeltStatus = () => {
  return useQuery({
    queryKey: ['belt', 'status'],
    queryFn: () => api.getBeltStatus(),
    refetchInterval: 2000, // Actualizar cada 2 segundos
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 5000),
  })
}

export const useStartBeltForward = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.startBeltForward(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['belt', 'status'] })
    },
  })
}

export const useStartBeltBackward = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.startBeltBackward(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['belt', 'status'] })
    },
  })
}

export const useStopBelt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.stopBelt(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['belt', 'status'] })
    },
  })
}

export const useEmergencyStopBelt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.emergencyStopBelt(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['belt', 'status'] })
    },
  })
}

export const useSetBeltSpeed = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (speed: number) => api.setBeltSpeed(speed),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['belt', 'status'] })
    },
  })
}

export const useToggleBeltEnable = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.toggleBeltEnable(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['belt', 'status'] })
    },
  })
}

// Hooks para Stepper Láser
export const useToggleLaserStepper = () => {
  return useMutation({
    mutationFn: (enabled: boolean) => api.toggleLaserStepper(enabled),
  })
}

export const useTestLaserStepper = () => {
  return useMutation({
    mutationFn: ({ duration, intensity }: { duration?: number; intensity?: number }) => 
      api.testLaserStepper(duration, intensity),
  })
}

// Hooks para Motor DC
export const useMotorStatus = () => {
  return useQuery({
    queryKey: ['motor', 'status'],
    queryFn: () => api.getMotorStatus(),
    refetchInterval: 5000, // Actualizar cada 5 segundos
    retry: 2,
  })
}

export const useActivateLabelerGroup = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (category: string) => api.activateLabelerGroup(category),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['motor', 'status'] })
    },
  })
}

// Hooks para Desviadores
export const useDiverstersStatus = () => {
  return useQuery({
    queryKey: ['diverters', 'status'],
    queryFn: () => api.getDiverstersStatus(),
    refetchInterval: 5000, // Actualizar cada 5 segundos
    retry: 2,
  })
}

export const useClassifyFruit = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ category, delay }: { category: string; delay?: number }) => 
      api.classifyFruit(category, delay),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diverters', 'status'] })
    },
  })
}

export const useCalibrateDeviverters = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => api.calibrateDiverters(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diverters', 'status'] })
    },
  })
}