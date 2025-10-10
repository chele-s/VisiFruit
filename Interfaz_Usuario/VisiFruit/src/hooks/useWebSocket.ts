import { useEffect, useRef, useState } from 'react'
import { useAppDispatch } from '../types/redux'
import { updateProductionStatus, setActiveGroup, setLastDetected } from '../store/slices/productionSlice'
import { addAlert } from '../store/slices/alertsSlice'
import { updateRealTimeMetrics } from '../store/slices/metricsSlice'

interface WebSocketMessage {
  type: 'production_update' | 'alert' | 'metrics_update' | 'system_status' | 'data'
  data: any
  timestamp: string
}

export const useWebSocket = (url?: string) => {
  // Usar configuración dinámica por defecto
  const defaultUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws/realtime'
  const wsUrl = url || defaultUrl
  // WS del sistema principal (ultra_dashboard)
  const deriveUltraWs = () => {
    const explicit = import.meta.env.VITE_MAIN_WS_URL as string | undefined
    if (explicit) return explicit
    const httpBase = (import.meta.env.VITE_MAIN_API_URL as string) || 'http://localhost:8000'
    try {
      const u = new URL(httpBase)
      u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
      u.pathname = '/ws/ultra_dashboard'
      return u.toString()
    } catch {
      return 'ws://localhost:8000/ws/ultra_dashboard'
    }
  }
  const ultraWsUrl = deriveUltraWs()
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const websocket = useRef<WebSocket | null>(null)
  const ultraWebsocket = useRef<WebSocket | null>(null)
  const dispatch = useAppDispatch()
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const maxReconnectAttempts = 5
  const reconnectAttempts = useRef(0)

  const connect = () => {
    try {
      websocket.current = new WebSocket(wsUrl)

      websocket.current.onopen = () => {
        console.log('✅ WebSocket conectado')
        setIsConnected(true)
        setConnectionError(null)
        reconnectAttempts.current = 0
      }

      websocket.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('Error procesando mensaje WebSocket:', error)
        }
      }

      websocket.current.onclose = (event) => {
        console.log('❌ WebSocket desconectado:', event.code, event.reason)
        setIsConnected(false)
        
        // Intentar reconectar si no fue un cierre intencional
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttempts.current) * 1000 // Backoff exponencial
          console.log(`🔄 Intentando reconectar en ${delay}ms (intento ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`)
          
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setConnectionError('Máximo número de intentos de reconexión alcanzado')
        }
      }

      websocket.current.onerror = (error) => {
        console.error('❌ Error WebSocket:', error)
        setConnectionError('Error de conexión WebSocket')
      }

      // Conectar al WS del sistema principal (ultra_dashboard)
      try {
        ultraWebsocket.current = new WebSocket(ultraWsUrl)
        ultraWebsocket.current.onopen = () => {
          console.log('✅ Ultra WebSocket conectado')
        }
        ultraWebsocket.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            handleUltraMessage(data)
          } catch (e) {
            console.error('Error procesando mensaje Ultra WS:', e)
          }
        }
        ultraWebsocket.current.onerror = (e) => {
          console.warn('⚠️ Error Ultra WebSocket:', e)
        }
        ultraWebsocket.current.onclose = () => {
          console.log('🔌 Ultra WebSocket desconectado')
        }
      } catch (e) {
        console.warn('No se pudo conectar al Ultra WebSocket:', e)
      }

    } catch (error) {
      console.error('Error creando WebSocket:', error)
      setConnectionError('Error al crear la conexión WebSocket')
    }
  }

  const handleMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'production_update':
        dispatch(updateProductionStatus(message.data))
        break
        
      case 'alert':
        dispatch(addAlert({
          ...message.data,
          timestamp: message.timestamp
        }))
        break
        
      case 'metrics_update':
        dispatch(updateRealTimeMetrics(message.data))
        break
        
      case 'system_status':
        // Manejar actualizaciones de estado del sistema
        console.log('Estado del sistema actualizado:', message.data)
        break

      case 'data': {
        // Mensajes enrutados desde el backend dashboard (8001)
        const payload = message.data
        // Si es simulación, tomar la última detección como "categoría activa"
        if (payload && payload.type === 'simulation' && Array.isArray(payload.detections) && payload.detections.length > 0) {
          const last = payload.detections[payload.detections.length - 1]
          const cat = String(last.category || '').toLowerCase()
          const emojiMap: Record<string, string> = { apple: '🍎', pear: '🍐', lemon: '🍋', orange: '🍊', banana: '🍌', grape: '🍇' }
          const idMap: Record<string, number> = { apple: 0, pear: 1, lemon: 2, orange: 3, banana: 4, grape: 5 }
          if (cat) {
            dispatch(setActiveGroup({ id: idMap[cat] ?? 0, category: cat, emoji: emojiMap[cat] ?? '🍏' }))
            // Actualizar última detección
            dispatch(setLastDetected({
              category: cat,
              emoji: emojiMap[cat] ?? '🍏',
              confidence: last.confidence ?? 0,
              timestamp: last.timestamp || new Date().toISOString()
            }))
          }
        }
        break
      }
      
      default:
        console.warn('Tipo de mensaje WebSocket desconocido:', message.type)
    }
  }

  const handleUltraMessage = (data: any) => {
    // Mensajes directos del sistema principal (8000)
    // Estructura esperada: { timestamp, system_state, metrics, active_labeler, ... }
    if (data && typeof data === 'object') {
      if (typeof data.active_labeler === 'number') {
        const id = data.active_labeler
        const idToCat: Record<number, { category: string; emoji: string }> = {
          0: { category: 'apple', emoji: '🍎' },
          1: { category: 'pear', emoji: '🍐' },
          2: { category: 'lemon', emoji: '🍋' },
          3: { category: 'orange', emoji: '🍊' }
        }
        const mapped = idToCat[id] || { category: 'apple', emoji: '🍎' }
        dispatch(setActiveGroup({ id, category: mapped.category, emoji: mapped.emoji }))
      }
    }
  }

  const sendMessage = (message: any) => {
    if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
      websocket.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket no está conectado')
    }
  }

  const disconnect = () => {
    if (reconnectTimeout.current !== null) {
      clearTimeout(reconnectTimeout.current)
    }
    
    if (websocket.current) {
      websocket.current.close(1000, 'Desconexión intencional')
    }
    if (ultraWebsocket.current) {
      try {
        ultraWebsocket.current.close(1000, 'Desconexión intencional')
      } catch {}
    }
  }

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [wsUrl, ultraWsUrl])

  return {
    isConnected,
    connectionError,
    sendMessage,
    disconnect,
    reconnect: connect
  }
}