import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // Configuración del servidor de desarrollo
  server: {
    port: 3001,
    host: true,
    strictPort: false,  // Cambiado a false para buscar puerto disponible automáticamente
    cors: true,
    // Proxy para el backend (opcional - las URLs absolutas también funcionan)
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
        changeOrigin: true,
      },
    },
  },

  // Configuración de build para producción
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Optimizar para chunks más pequeños
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material', '@mui/icons-material'],
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          charts: ['recharts'],
        },
      },
    },
  },

  // Variables de entorno
  define: {
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
    __VERSION__: JSON.stringify(process.env.npm_package_version || '3.0.0'),
  },

  // Optimización de dependencias
  optimizeDeps: {
    include: ['react', 'react-dom', '@mui/material', '@react-three/fiber', 'three'],
  },
})
