import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  AlertTitle,
  Divider,
  Chip,
  Stack
} from '@mui/material'
import { Refresh, Home, Settings } from '@mui/icons-material'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  retryCount: number
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
      retryCount: 0
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary capturó un error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo,
      retryCount: this.state.retryCount + 1
    })

    // Log del error para debugging
    if (import.meta.env.DEV) {
      console.group('🔍 ErrorBoundary - Detalles del Error')
      console.error('Error:', error)
      console.error('Error Info:', errorInfo)
      console.error('Component Stack:', errorInfo.componentStack)
      console.groupEnd()
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  getErrorType = (error: Error): string => {
    if (error.message.includes('chartData.slice')) {
      return 'Error de Datos del Gráfico'
    }
    if (error.message.includes('fetch')) {
      return 'Error de Conexión'
    }
    if (error.message.includes('JSON')) {
      return 'Error de Formato de Datos'
    }
    return 'Error del Sistema'
  }

  getErrorSuggestions = (error: Error): string[] => {
    const suggestions: string[] = []
    
    if (error.message.includes('chartData.slice')) {
      suggestions.push('Verificar que el backend esté enviando arrays de datos')
      suggestions.push('Revisar la estructura de respuesta de la API')
      suggestions.push('Comprobar que los datos no sean null o undefined')
    }
    
    if (error.message.includes('fetch')) {
      suggestions.push('Verificar que el backend esté ejecutándose en el puerto 8001')
      suggestions.push('Comprobar la conexión a internet')
      suggestions.push('Revisar logs del backend para errores de conexión')
    }
    
    if (error.message.includes('JSON')) {
      suggestions.push('Verificar el formato de respuesta del backend')
      suggestions.push('Revisar que no haya caracteres especiales corruptos')
      suggestions.push('Comprobar la codificación de caracteres')
    }
    
    if (suggestions.length === 0) {
      suggestions.push('Revisar la consola del navegador para más detalles')
      suggestions.push('Verificar logs del backend')
      suggestions.push('Comprobar la configuración de la aplicación')
    }
    
    return suggestions
  }

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, retryCount } = this.state
      const errorType = error ? this.getErrorType(error) : 'Error Desconocido'
      const suggestions = error ? this.getErrorSuggestions(error) : []

      return (
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)'
          }}
        >
          <Paper
            elevation={24}
            sx={{
              maxWidth: 600,
              width: '100%',
              p: 4,
              borderRadius: 3,
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}
          >
            {/* Header del Error */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Typography variant="h4" component="h1" gutterBottom color="error.main">
                🚨 {errorType}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Ha ocurrido un error inesperado en esta sección del sistema
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Información del Error */}
            <Alert severity="error" sx={{ mb: 3 }}>
              <AlertTitle>Detalles Técnicos</AlertTitle>
              <Typography variant="body2" fontFamily="monospace" sx={{ wordBreak: 'break-word' }}>
                {error?.message || 'Error desconocido'}
              </Typography>
            </Alert>

            {/* Sugerencias de Solución */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom color="primary.main">
                💡 Posibles Soluciones:
              </Typography>
              <Stack spacing={1}>
                {suggestions.map((suggestion, index) => (
                  <Chip
                    key={index}
                    label={suggestion}
                    variant="outlined"
                    size="small"
                    color="primary"
                  />
                ))}
              </Stack>
            </Box>

            {/* Stack Trace (solo en desarrollo) */}
            {import.meta.env.DEV && errorInfo && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom color="warning.main">
                  🐛 Stack Trace (Desarrollo)
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    maxHeight: 200,
                    overflow: 'auto',
                    background: '#f5f5f5',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem'
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {errorInfo.componentStack}
                  </pre>
                </Paper>
              </Box>
            )}

            {/* Contador de Reintentos */}
            {retryCount > 1 && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  ⚠️ Este error ha ocurrido {retryCount} veces. 
                  Considera recargar la página o contactar soporte.
                </Typography>
              </Alert>
            )}

            {/* Botones de Acción */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={this.handleRetry}
                color="primary"
                size="large"
              >
                Reintentar
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Home />}
                onClick={this.handleGoHome}
                color="secondary"
                size="large"
              >
                Ir al Inicio
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Settings />}
                onClick={this.handleReload}
                color="warning"
                size="large"
              >
                Recargar Página
              </Button>
            </Box>

            {/* Información Adicional */}
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Si el problema persiste, verifica que el backend esté ejecutándose correctamente 
                en el puerto 8001 y que tengas conexión a internet.
              </Typography>
            </Box>
          </Paper>
        </Box>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
