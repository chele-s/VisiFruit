import React, { useEffect, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  useTheme,
} from '@mui/material';
import { animate, stagger } from 'animejs';
import ServoControlPanel from '../production/ServoControlPanel';

const ServoControlView: React.FC = () => {
  const theme = useTheme();
  const viewRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Animaciones de entrada
    if (viewRef.current) {
      const elements = viewRef.current.querySelectorAll('.animate-in');
      animate(elements, {
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 800,
        delay: stagger(100),
        easing: 'easeOutCubic',
      });
    }
  }, []);

  // Función para manejar acciones de servos
  const handleServoAction = async (servoId: string, action: string, params?: any) => {
    try {
      // Llamar al backend
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/servo/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          servo_id: servoId,
          action,
          params,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing servo action:', error);
      throw error;
    }
  };

  // Función para actualizar configuración
  const handleConfigUpdate = async (servoId: string, config: any) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/servo/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          servo_id: servoId,
          config,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating servo config:', error);
      throw error;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }} ref={viewRef}>
      <Box className="animate-in" sx={{ mb: 4 }}>
        <Typography
          variant="h3"
          sx={{
            fontWeight: 700,
            background: theme.gradients.primary,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            mb: 1,
          }}
        >
          Control de Servos
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Sistema de control de servos MG995 para clasificación de frutas
        </Typography>
      </Box>

      <Paper
        className="animate-in"
        sx={{
          p: 3,
          background: theme.gradients.glass,
          backdropFilter: 'blur(20px)',
          border: `1px solid rgba(255, 255, 255, 0.1)`,
          borderRadius: 3,
        }}
      >
        <ServoControlPanel
          onServoAction={handleServoAction}
          onConfigUpdate={handleConfigUpdate}
          isConnected={true}
          disabled={false}
        />
      </Paper>
    </Container>
  );
};

export default ServoControlView;
