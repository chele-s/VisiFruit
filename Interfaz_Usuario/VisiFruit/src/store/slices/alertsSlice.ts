import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical'
export type AlertCategory = 'system' | 'production' | 'quality' | 'maintenance' | 'security'

export interface Alert {
  id: string
  title: string
  message: string
  severity: AlertSeverity
  category: AlertCategory
  timestamp: string
  acknowledged: boolean
  acknowledgedBy?: string
  acknowledgedAt?: string
  resolved: boolean
  resolvedAt?: string
  notes?: string
  actions?: {
    label: string
    action: string
  }[]
  metadata?: {
    source?: string
    component?: string
    errorCode?: string
    troubleshootingUrl?: string
  }
}

interface AlertsState {
  alerts: Alert[]
  unreadCount: number
  filters: {
    severity: AlertSeverity[]
    category: AlertCategory[]
    acknowledged: boolean | null
    resolved: boolean | null
    dateRange: {
      start: string | null
      end: string | null
    }
  }
  sortBy: 'timestamp' | 'severity' | 'category'
  sortOrder: 'asc' | 'desc'
  isLoading: boolean
  error: string | null
}

const initialState: AlertsState = {
  alerts: [],
  unreadCount: 0,
  filters: {
    severity: [],
    category: [],
    acknowledged: null,
    resolved: null,
    dateRange: {
      start: null,
      end: null
    }
  },
  sortBy: 'timestamp',
  sortOrder: 'desc',
  isLoading: false,
  error: null
}

const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    addAlert: (state, action: PayloadAction<Alert>) => {
      state.alerts.unshift(action.payload)
      if (!action.payload.acknowledged) {
        state.unreadCount += 1
      }
    },
    updateAlert: (state, action: PayloadAction<{ id: string; updates: Partial<Alert> }>) => {
      const { id, updates } = action.payload
      const alertIndex = state.alerts.findIndex(alert => alert.id === id)
      if (alertIndex !== -1) {
        const wasUnread = !state.alerts[alertIndex].acknowledged
        state.alerts[alertIndex] = { ...state.alerts[alertIndex], ...updates }
        
        // Actualizar contador de no leídas
        if (wasUnread && updates.acknowledged) {
          state.unreadCount = Math.max(0, state.unreadCount - 1)
        } else if (!wasUnread && updates.acknowledged === false) {
          state.unreadCount += 1
        }
      }
    },
    acknowledgeAlert: (state, action: PayloadAction<{
      id: string
      acknowledgedBy: string
      notes?: string
    }>) => {
      const { id, acknowledgedBy, notes } = action.payload
      const alertIndex = state.alerts.findIndex(alert => alert.id === id)
      if (alertIndex !== -1 && !state.alerts[alertIndex].acknowledged) {
        state.alerts[alertIndex].acknowledged = true
        state.alerts[alertIndex].acknowledgedBy = acknowledgedBy
        state.alerts[alertIndex].acknowledgedAt = new Date().toISOString()
        if (notes) {
          state.alerts[alertIndex].notes = notes
        }
        state.unreadCount = Math.max(0, state.unreadCount - 1)
      }
    },
    resolveAlert: (state, action: PayloadAction<string>) => {
      const alertIndex = state.alerts.findIndex(alert => alert.id === action.payload)
      if (alertIndex !== -1) {
        state.alerts[alertIndex].resolved = true
        state.alerts[alertIndex].resolvedAt = new Date().toISOString()
        if (!state.alerts[alertIndex].acknowledged) {
          state.unreadCount = Math.max(0, state.unreadCount - 1)
        }
      }
    },
    removeAlert: (state, action: PayloadAction<string>) => {
      const alertIndex = state.alerts.findIndex(alert => alert.id === action.payload)
      if (alertIndex !== -1) {
        if (!state.alerts[alertIndex].acknowledged) {
          state.unreadCount = Math.max(0, state.unreadCount - 1)
        }
        state.alerts.splice(alertIndex, 1)
      }
    },
    clearAllAlerts: (state) => {
      state.alerts = []
      state.unreadCount = 0
    },
    markAllAsRead: (state) => {
      state.alerts.forEach(alert => {
        if (!alert.acknowledged) {
          alert.acknowledged = true
          alert.acknowledgedAt = new Date().toISOString()
        }
      })
      state.unreadCount = 0
    },
    updateFilters: (state, action: PayloadAction<Partial<AlertsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setSorting: (state, action: PayloadAction<{
      sortBy: AlertsState['sortBy']
      sortOrder: AlertsState['sortOrder']
    }>) => {
      state.sortBy = action.payload.sortBy
      state.sortOrder = action.payload.sortOrder
    },
    setAlerts: (state, action: PayloadAction<Alert[]>) => {
      state.alerts = action.payload
      state.unreadCount = action.payload.filter(alert => !alert.acknowledged).length
    }
  }
})

export const {
  setLoading,
  setError,
  addAlert,
  updateAlert,
  acknowledgeAlert,
  resolveAlert,
  removeAlert,
  clearAllAlerts,
  markAllAsRead,
  updateFilters,
  setSorting,
  setAlerts
} = alertsSlice.actions

export default alertsSlice.reducer