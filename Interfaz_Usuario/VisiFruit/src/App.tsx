import { useEffect, useRef } from 'react';
import { Box } from '@mui/material';
import { animate } from 'animejs';
import { useAppSelector } from './types/redux';
import MainLayout from './components/layout/MainLayout';
import LoadingScreen from './components/common/LoadingScreen';
import './App.css';

function App() {
  const appRef = useRef<HTMLDivElement>(null);
  const { isLoading } = useAppSelector(state => state.ui);

  useEffect(() => {
    if (appRef.current) {
      animate(appRef.current, {
        opacity: [0, 1],
        scale: [0.9, 1],
        duration: 1200,
        easing: 'easeOutCubic',
        delay: 300,
      });
    }
  }, []);

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Box
      ref={appRef}
      sx={{
        height: '100vh',
        width: '100%',
        maxWidth: '100vw',
        overflow: 'hidden',
        background: theme => theme.gradients.dark,
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            'radial-gradient(ellipse at center, rgba(0, 229, 160, 0.05) 0%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        },
      }}
    >
      <MainLayout />
    </Box>
  );
}

export default App;
