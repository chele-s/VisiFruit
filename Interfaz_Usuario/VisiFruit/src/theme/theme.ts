import { createTheme } from '@mui/material/styles'
import type { ThemeOptions } from '@mui/material/styles'

// Paleta de colores personalizada para VisiFruit
const palette = {
  primary: {
    main: '#00E5A0',      // Verde vibrante (VisiFruit)
    light: '#4DFFBA',
    dark: '#00B087',
    contrastText: '#000000',
  },
  secondary: {
    main: '#FF6B6B',      // Coral vibrante
    light: '#FF9F9F',
    dark: '#CC5555',
    contrastText: '#FFFFFF',
  },
  tertiary: {
    main: '#4ECDC4',      // Turquesa
    light: '#7DFFED',
    dark: '#3EA39A',
    contrastText: '#000000',
  },
  error: {
    main: '#FF5252',
    light: '#FF8A80',
    dark: '#D32F2F',
  },
  warning: {
    main: '#FFC107',
    light: '#FFECB3',
    dark: '#FF8F00',
  },
  info: {
    main: '#2196F3',
    light: '#64B5F6',
    dark: '#1976D2',
  },
  success: {
    main: '#4CAF50',
    light: '#81C784',
    dark: '#388E3C',
  },
  background: {
    default: '#0A0F14',    // Azul muy oscuro
    paper: '#1A1F24',      // Gris azulado oscuro
    glass: 'rgba(26, 31, 36, 0.8)', // Efecto glassmorphism
  },
  surface: {
    main: '#2A2F34',      // Superficie elevada
    light: '#3A3F44',     // Superficie más elevada
    dark: '#1A1F24',      // Superficie baja
  },
  text: {
    primary: '#FFFFFF',
    secondary: 'rgba(255, 255, 255, 0.7)',
    disabled: 'rgba(255, 255, 255, 0.38)',
  },
  divider: 'rgba(255, 255, 255, 0.12)',
}

// Gradientes personalizados
const gradients = {
  primary: 'linear-gradient(135deg, #00E5A0 0%, #4ECDC4 100%)',
  secondary: 'linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%)',
  tertiary: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)',
  dark: 'linear-gradient(135deg, #0A0F14 0%, #1A1F24 100%)',
  glass: 'linear-gradient(135deg, rgba(26, 31, 36, 0.8) 0%, rgba(42, 47, 52, 0.6) 100%)',
  neon: 'linear-gradient(135deg, #00E5A0 0%, #4ECDC4 50%, #FF6B6B 100%)',
  rainbow: 'linear-gradient(90deg, #00E5A0 0%, #4ECDC4 25%, #2196F3 50%, #FF6B6B 75%, #FFC107 100%)',
}

// Sombras con efecto neón
const shadows = [
  'none',
  '0px 2px 4px rgba(0, 229, 160, 0.1)',
  '0px 4px 8px rgba(0, 229, 160, 0.15)',
  '0px 8px 16px rgba(0, 229, 160, 0.2)',
  '0px 12px 24px rgba(0, 229, 160, 0.25)',
  '0px 16px 32px rgba(0, 229, 160, 0.3)',
  // Sombras neón para elementos especiales
  '0px 0px 20px rgba(0, 229, 160, 0.4)',
  '0px 0px 30px rgba(0, 229, 160, 0.5)',
  '0px 0px 40px rgba(0, 229, 160, 0.6)',
  // Continuar con sombras normales
  '0px 20px 40px rgba(0, 0, 0, 0.3)',
  '0px 24px 48px rgba(0, 0, 0, 0.35)',
  '0px 28px 56px rgba(0, 0, 0, 0.4)',
  '0px 32px 64px rgba(0, 0, 0, 0.45)',
  '0px 36px 72px rgba(0, 0, 0, 0.5)',
  '0px 40px 80px rgba(0, 0, 0, 0.55)',
  '0px 44px 88px rgba(0, 0, 0, 0.6)',
  '0px 48px 96px rgba(0, 0, 0, 0.65)',
  '0px 52px 104px rgba(0, 0, 0, 0.7)',
  '0px 56px 112px rgba(0, 0, 0, 0.75)',
  '0px 60px 120px rgba(0, 0, 0, 0.8)',
  '0px 64px 128px rgba(0, 0, 0, 0.85)',
  '0px 68px 136px rgba(0, 0, 0, 0.9)',
  '0px 72px 144px rgba(0, 0, 0, 0.95)',
  '0px 76px 152px rgba(0, 0, 0, 1)',
  '0px 80px 160px rgba(0, 0, 0, 1)',
]

const themeOptions: ThemeOptions = {
  palette,
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '3.5rem',
      fontWeight: 800,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      background: gradients.primary,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
    },
    h2: {
      fontSize: '2.75rem',
      fontWeight: 700,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontSize: '2.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.875rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.5rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.6,
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 600,
      textTransform: 'none',
      letterSpacing: '0.02em',
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: shadows as any,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: `${palette.primary.main} ${palette.background.paper}`,
          '&::-webkit-scrollbar': {
            width: 8,
            height: 8,
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: palette.background.paper,
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: palette.primary.main,
            borderRadius: 4,
            '&:hover': {
              backgroundColor: palette.primary.light,
            },
          },
        },
        '*': {
          margin: 0,
          padding: 0,
          boxSizing: 'border-box',
        },
        html: {
          height: '100%',
        },
        '#root': {
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: gradients.glass,
          backdropFilter: 'blur(20px)',
          border: `1px solid rgba(255, 255, 255, 0.1)`,
          borderRadius: 16,
          overflow: 'hidden',
          '&.neon-glow': {
            boxShadow: shadows[6],
            '&:hover': {
              boxShadow: shadows[7],
              transform: 'translateY(-2px)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            },
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 600,
          padding: '12px 24px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: shadows[2],
            transform: 'translateY(-1px)',
          },
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          background: gradients.primary,
          color: '#000000',
          '&:hover': {
            background: gradients.primary,
            boxShadow: shadows[4],
          },
          '&.neon': {
            boxShadow: shadows[6],
            '&:hover': {
              boxShadow: shadows[8],
            },
          },
        },
        outlined: {
          borderColor: palette.primary.main,
          color: palette.primary.main,
          '&:hover': {
            backgroundColor: 'rgba(0, 229, 160, 0.08)',
            borderColor: palette.primary.light,
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: gradients.glass,
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid rgba(255, 255, 255, 0.1)`,
          boxShadow: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: gradients.dark,
          borderRight: `1px solid rgba(255, 255, 255, 0.1)`,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
        filled: {
          '&.success': {
            backgroundColor: palette.success.main,
            color: '#000000',
          },
          '&.warning': {
            backgroundColor: palette.warning.main,
            color: '#000000',
          },
          '&.error': {
            backgroundColor: palette.error.main,
            color: '#FFFFFF',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          height: 8,
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
        },
        bar: {
          borderRadius: 4,
          background: gradients.primary,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            borderRadius: 12,
            '& fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.2)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.3)',
            },
            '&.Mui-focused fieldset': {
              borderColor: palette.primary.main,
              boxShadow: `0 0 0 2px rgba(0, 229, 160, 0.2)`,
            },
          },
        },
      },
    },
  },
}

// Extender el tipo Theme para incluir propiedades personalizadas
declare module '@mui/material/styles' {
  interface Palette {
    tertiary: Palette['primary']
    surface: Palette['primary']
  }

  interface PaletteOptions {
    tertiary?: PaletteOptions['primary']
    surface?: PaletteOptions['primary']
  }

  interface Theme {
    gradients: typeof gradients
  }

  interface ThemeOptions {
    gradients?: typeof gradients
  }
}

export const theme = createTheme({
  ...themeOptions,
  gradients,
})

// Hook personalizado para usar el tema
export const useTheme = () => theme