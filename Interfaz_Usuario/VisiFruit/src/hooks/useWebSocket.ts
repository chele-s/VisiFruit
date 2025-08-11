import { useEffect, useRef, useState } from 'react'
import { useAppDispatch } from '../types/redux'
import { updateProductionStatus } from '../store/slices/productionSlice'
import { addAlert } from '../store/slices/alertsSlice'
import { updateRealTimeMetrics } from '../store/slices/metricsSlice'

interface WebSocketMessage {
  type: 'production_update' | 'alert' | 'metrics_update' | 'system_status'
  data: any
  timestamp: string
}

export const useWebSocket = (url: string = 'ws://localhost:8000/ws') => {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const websocket = useRef<WebSocket | null>(null)
  const dispatch = useAppDispatch()
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const maxReconnectAttempts = 5
  const reconnectAttempts = useRef(0)

  const connect = () => {
    try {
      websocket.current = new WebSocket(url)

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
        
      default:
        console.warn('Tipo de mensaje WebSocket desconocido:', message.type)
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
  }

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [url])

  return {
    isConnected,
    connectionError,
    sendMessage,
    disconnect,
    reconnect: connect
  }
}