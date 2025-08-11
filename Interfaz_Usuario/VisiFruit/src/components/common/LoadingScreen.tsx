import React, { useEffect, useRef } from 'react'
import { Box, Typography, LinearProgress } from '@mui/material'
import { animate, createTimeline } from 'animejs';

const LoadingScreen: React.FC = () => {
  const logoRef = useRef<HTMLDivElement>(null)
  const textRef = useRef<HTMLDivElement>(null)
  const progressRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (logoRef.current && textRef.current && progressRef.current) {
      const timeline = createTimeline({
        loop: false,
        autoplay: true,
      })

      // Animación del logo
      timeline.add(logoRef.current, {
        scale: [0, 1.2, 1],
        opacity: [0, 1],
        rotate: [0, 360],
        duration: 1500,
        easing: 'easeOutElastic(1, .8)',
      })

      // Animación del texto
      timeline.add(textRef.current, {
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 800,
        easing: 'easeOutCubic',
      }, '-=800')

      // Animación de la barra de progreso
      timeline.add(progressRef.current, {
        opacity: [0, 1],
        scaleX: [0, 1],
        duration: 600,
        easing: 'easeOutCubic',
      }, '-=400')

      // Efecto de brillo pulsante en el logo
      animate(logoRef.current, {
        boxShadow: [
          '0 0 20px rgba(0, 229, 160, 0.3)',
          '0 0 40px rgba(0, 229, 160, 0.6)',
          '0 0 20px rgba(0, 229, 160, 0.3)'
        ],
        duration: 2000,
        loop: true,
        easing: 'easeInOutSine',
        delay: 1500,
      })
    }
  }, [])

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: theme => theme.gradients.dark,
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(ellipse at center, rgba(0, 229, 160, 0.1) 0%, transparent 70%)',
          animation: 'pulse 3s ease-in-out infinite',
        },
        '@keyframes pulse': {
          '0%, 100%': {
            opacity: 0.3,
          },
          '50%': {
            opacity: 0.8,
          },
        },
      }}
    >
      {/* Logo animado */}
      <Box
        ref={logoRef}
        sx={{
          width: 120,
          height: 120,
          borderRadius: '50%',
          background: theme => theme.gradients.primary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 4,
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: -4,
            left: -4,
            right: -4,
            bottom: -4,
            borderRadius: '50%',
            background: theme => theme.gradients.neon,
            opacity: 0.6,
            filter: 'blur(8px)',
            zIndex: -1,
          }
        }}
      >
        <Typography
          variant="h2"
          sx={{
            fontSize: '3rem',
            fontWeight: 800,
            background: 'linear-gradient(45deg, #000 0%, #333 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          🍎
        </Typography>
      </Box>

      {/* Texto del loading */}
      <Box ref={textRef} sx={{ textAlign: 'center', mb: 4 }}>
        <Typography
          variant="h3"
          sx={{
            background: theme => theme.gradients.primary,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            mb: 1,
            fontWeight: 700,
          }}
        >
          VisiFruit
        </Typography>
        <Typography
          variant="body1"
          sx={{
            color: 'text.secondary',
            fontSize: '1.1rem',
          }}
        >
          Sistema Inteligente de Etiquetado
        </Typography>
      </Box>

      {/* Barra de progreso */}
      <Box
        ref={progressRef}
        sx={{
          width: 300,
          maxWidth: '80%',
        }}
      >
        <LinearProgress
          sx={{
            height: 6,
            borderRadius: 3,
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            '& .MuiLinearProgress-bar': {
              background: theme => theme.gradients.primary,
              borderRadius: 3,
            },
          }}
        />
      </Box>

      {/* Partículas flotantes */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: '20%',
            left: '10%',
            width: 4,
            height: 4,
            borderRadius: '50%',
            background: theme => theme.palette.primary.main,
            animation: 'float1 6s ease-in-out infinite',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            top: '60%',
            right: '20%',
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: theme => theme.palette.secondary.main,
            animation: 'float2 8s ease-in-out infinite',
          },
          '@keyframes float1': {
            '0%, 100%': {
              transform: 'translateY(0px) translateX(0px)',
            },
            '25%': {
              transform: 'translateY(-20px) translateX(10px)',
            },
            '50%': {
              transform: 'translateY(-40px) translateX(-5px)',
            },
            '75%': {
              transform: 'translateY(-20px) translateX(-10px)',
            },
          },
          '@keyframes float2': {
            '0%, 100%': {
              transform: 'translateY(0px) translateX(0px)',
            },
            '33%': {
              transform: 'translateY(-30px) translateX(-15px)',
            },
            '66%': {
              transform: 'translateY(-15px) translateX(20px)',
            },
          },
        }}
      />
    </Box>
  )
}

export default LoadingScreen