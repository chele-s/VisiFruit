import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface ProductionStatus {
  status: 'idle' | 'running' | 'paused' | 'stopped' | 'error'
  currentRate: number
  targetRate: number
  efficiency: number
  itemsProcessedToday: number
  activeLabelers: number
  activeGroup: {
    id: number
    category: string
    emoji: string
  }
  beltSpeed: number
  qualityScore: number
  uptimeToday: string
  lastSwitch: string
}

interface ProductionState {
  status: ProductionStatus
  isLoading: boolean
  error: string | null
  history: ProductionStatus[]
  currentSession: {
    sessionId: string
    startedAt: string
    targetRate: number
    durationMinutes?: number
    qualityThreshold: number
    autoStop: boolean
  } | null
}

const initialState: ProductionState = {
  status: {
    status: 'idle',
    currentRate: 0,
    targetRate: 100,
    efficiency: 0,
    itemsProcessedToday: 0,
    activeLabelers: 0,
    activeGroup: {
      id: 0,
      category: 'apple',
      emoji: '🍎'
    },
    beltSpeed: 0,
    qualityScore: 0,
    uptimeToday: '0%',
    lastSwitch: new Date().toISOString()
  },
  isLoading: false,
  error: null,
  history: [],
  currentSession: null
}

const productionSlice = createSlice({
  name: 'production',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    updateProductionStatus: (state, action: PayloadAction<ProductionStatus>) => {
      // Agregar al historial antes de actualizar
      if (state.status) {
        state.history.push(state.status)
        // Mantener solo los últimos 100 registros
        if (state.history.length > 100) {
          state.history.shift()
        }
      }
      state.status = action.payload
    },
    setCurrentSession: (state, action: PayloadAction<ProductionState['currentSession']>) => {
      state.currentSession = action.payload
    },
    clearHistory: (state) => {
      state.history = []
    }
  }
})

export const {
  setLoading,
  setError,
  updateProductionStatus,
  setCurrentSession,
  clearHistory
} = productionSlice.actions

export default productionSlice.reducer