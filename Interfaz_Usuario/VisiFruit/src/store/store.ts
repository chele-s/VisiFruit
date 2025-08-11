import { configureStore } from '@reduxjs/toolkit'
import productionSlice from './slices/productionSlice'
import metricsSlice from './slices/metricsSlice'
import uiSlice from './slices/uiSlice'
import alertsSlice from './slices/alertsSlice'

export const store = configureStore({
  reducer: {
    production: productionSlice,
    metrics: metricsSlice,
    ui: uiSlice,
    alerts: alertsSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch