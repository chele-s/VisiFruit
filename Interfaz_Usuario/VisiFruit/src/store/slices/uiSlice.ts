import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export type ThemeMode = 'light' | 'dark' | 'auto'
export type ViewMode =
  | 'dashboard'
  | 'production'
  | 'belt-control'
  | 'analytics'
  | 'metrics'
  | 'alerts'
  | 'reports'
  | 'maintenance'
  | 'config'
  | '3d-view'

interface UIState {
  themeMode: ThemeMode
  currentView: ViewMode
  sidebarOpen: boolean
  sidebarPinned: boolean
  animationsEnabled: boolean
  reducedMotion: boolean
  notifications: {
    enabled: boolean
    sound: boolean
    position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  }
  dashboard: {
    layout: 'grid' | 'flex' | 'masonry'
    compactMode: boolean
    showMetrics: boolean
    show3D: boolean
    autoRefresh: boolean
    refreshInterval: number
  }
  production: {
    showAdvanced: boolean
    realTimeUpdates: boolean
    showHistory: boolean
    chartType: 'line' | 'area' | 'bar'
  }
  performance: {
    enableGPUAcceleration: boolean
    maxFPS: number
    qualityLevel: 'low' | 'medium' | 'high' | 'ultra'
  }
  accessibility: {
    highContrast: boolean
    largeText: boolean
    screenReader: boolean
    keyboardNavigation: boolean
  }
  isLoading: boolean
  error: string | null
}

const initialState: UIState = {
  themeMode: 'dark',
  currentView: 'dashboard',
  sidebarOpen: true,
  sidebarPinned: false,
  animationsEnabled: true,
  reducedMotion: false,
  notifications: {
    enabled: true,
    sound: true,
    position: 'top-right'
  },
  dashboard: {
    layout: 'grid',
    compactMode: false,
    showMetrics: true,
    show3D: true,
    autoRefresh: true,
    refreshInterval: 5000
  },
  production: {
    showAdvanced: false,
    realTimeUpdates: true,
    showHistory: true,
    chartType: 'line'
  },
  performance: {
    enableGPUAcceleration: true,
    maxFPS: 60,
    qualityLevel: 'high'
  },
  accessibility: {
    highContrast: false,
    largeText: false,
    screenReader: false,
    keyboardNavigation: true
  },
  isLoading: false,
  error: null
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setThemeMode: (state, action: PayloadAction<ThemeMode>) => {
      state.themeMode = action.payload
    },
    setCurrentView: (state, action: PayloadAction<ViewMode>) => {
      state.currentView = action.payload
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload
    },
    toggleSidebarPin: (state) => {
      state.sidebarPinned = !state.sidebarPinned
    },
    setAnimationsEnabled: (state, action: PayloadAction<boolean>) => {
      state.animationsEnabled = action.payload
    },
    setReducedMotion: (state, action: PayloadAction<boolean>) => {
      state.reducedMotion = action.payload
    },
    updateNotificationSettings: (state, action: PayloadAction<Partial<UIState['notifications']>>) => {
      state.notifications = { ...state.notifications, ...action.payload }
    },
    updateDashboardSettings: (state, action: PayloadAction<Partial<UIState['dashboard']>>) => {
      state.dashboard = { ...state.dashboard, ...action.payload }
    },
    updateProductionSettings: (state, action: PayloadAction<Partial<UIState['production']>>) => {
      state.production = { ...state.production, ...action.payload }
    },
    updatePerformanceSettings: (state, action: PayloadAction<Partial<UIState['performance']>>) => {
      state.performance = { ...state.performance, ...action.payload }
    },
    updateAccessibilitySettings: (state, action: PayloadAction<Partial<UIState['accessibility']>>) => {
      state.accessibility = { ...state.accessibility, ...action.payload }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    resetToDefaults: (state) => {
      return { ...initialState, themeMode: state.themeMode }
    }
  }
})

export const {
  setThemeMode,
  setCurrentView,
  toggleSidebar,
  setSidebarOpen,
  toggleSidebarPin,
  setAnimationsEnabled,
  setReducedMotion,
  updateNotificationSettings,
  updateDashboardSettings,
  updateProductionSettings,
  updatePerformanceSettings,
  updateAccessibilitySettings,
  setLoading,
  setError,
  resetToDefaults
} = uiSlice.actions

export default uiSlice.reducer