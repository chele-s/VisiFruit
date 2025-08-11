import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// URL base del backend
const API_BASE_URL = 'http://localhost:8000'

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
      const response = await fetch(url, {
        ...options,
        headers: defaultHeaders,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
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
    return this.request<SystemMetricsResponse>('/api/system/metrics')
  }

  async getProductionHistory(period: string = '24h'): Promise<any[]> {
    return this.request<any[]>(`/api/metrics/production/history?period=${period}`)
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

  // Endpoints de Configuración
  async updateConfig(key: string, value: any): Promise<any> {
    return this.request('/api/config/update', {
      method: 'POST',
      body: JSON.stringify({ key, value }),
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