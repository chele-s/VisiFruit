import React, { useRef, useEffect, useState, Suspense } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Slider,
  Switch,
  FormControlLabel,
  IconButton,
  Chip,
  useTheme,
} from '@mui/material'
import {
  Fullscreen,
  Settings,
  CameraAlt,
  ViewInAr,
} from '@mui/icons-material'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, Text, Box as ThreeBox, Sphere, Cylinder } from '@react-three/drei'
import * as THREE from 'three'
import { animate } from 'animejs'
import { useAppSelector } from '../../types/redux'

// Componente 3D para representar la cinta transportadora
const ConveyorBelt: React.FC<{ speed: number; isRunning: boolean }> = ({ speed, isRunning }) => {
  const beltRef = useRef<THREE.Group>(null)
  const [hovered, setHovered] = useState(false)

  useFrame((state) => {
    if (beltRef.current && isRunning) {
      const delta = state.clock.getDelta()
      beltRef.current.position.x += speed * delta * 2
      if (beltRef.current.position.x > 10) {
        beltRef.current.position.x = -10
      }
    }
  })

  return (
    <group>
      {/* Base de la cinta */}
      <ThreeBox
        args={[20, 0.2, 2]}
        position={[0, -1, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={hovered ? "#00E5A0" : "#2A2F34"}
          metalness={0.3}
          roughness={0.7}
        />
      </ThreeBox>
      
      {/* Secciones móviles de la cinta */}
      <group ref={beltRef}>
        {Array.from({ length: 10 }, (_, i) => (
          <ThreeBox
            key={i}
            args={[1.8, 0.1, 1.8]}
            position={[-10 + i * 2.2, -0.9, 0]}
          >
            <meshStandardMaterial
              color="#1A1F24"
              metalness={0.1}
              roughness={0.9}
            />
          </ThreeBox>
        ))}
      </group>
    </group>
  )
}

// Componente 3D para frutas
const Fruit: React.FC<{
  position: [number, number, number]
  type: string
  emoji: string
  labeled: boolean
}> = ({ position, type, emoji, labeled }) => {
  const fruitRef = useRef<THREE.Group>(null)
  const [hovered, setHovered] = useState(false)

  useFrame((state) => {
    if (fruitRef.current) {
      fruitRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 2) * 0.1
      fruitRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 3) * 0.05
    }
  })

  return (
    <group
      ref={fruitRef}
      position={position}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <Sphere args={[0.3]} scale={hovered ? 1.2 : 1}>
        <meshStandardMaterial
          color={type === 'apple' ? '#FF6B6B' : type === 'orange' ? '#FFA500' : '#4ECDC4'}
          metalness={0.1}
          roughness={0.3}
          emissive={hovered ? '#003300' : '#000000'}
        />
      </Sphere>
      
      {labeled && (
        <Text
          position={[0, 0.6, 0]}
          fontSize={0.2}
          color="#00E5A0"
          anchorX="center"
          anchorY="middle"
        >
          {emoji} ✓
        </Text>
      )}
      
      {/* Efecto de partículas cuando está etiquetada */}
      {labeled && (
        <group>
          {Array.from({ length: 6 }, (_, i) => (
            <Sphere
              key={i}
              args={[0.02]}
              position={[
                Math.cos(i * Math.PI / 3) * 0.5,
                0.4 + Math.sin(i * Math.PI / 3) * 0.2,
                Math.sin(i * Math.PI / 3) * 0.5,
              ]}
            >
              <meshBasicMaterial color="#00E5A0" />
            </Sphere>
          ))}
        </group>
      )}
    </group>
  )
}

// Estación de etiquetado
const LabelingStation: React.FC<{
  position: [number, number, number]
  active: boolean
  stationId: number
}> = ({ position, active, stationId }) => {
  const stationRef = useRef<THREE.Group>(null)

  useFrame((state) => {
    if (stationRef.current && active) {
      stationRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 4) * 0.1
    }
  })

  return (
    <group ref={stationRef} position={position}>
      {/* Base de la estación */}
      <Cylinder args={[0.3, 0.4, 1.5]} position={[0, 0.75, 0]}>
        <meshStandardMaterial
          color={active ? "#00E5A0" : "#666666"}
          metalness={0.5}
          roughness={0.2}
          emissive={active ? "#004400" : "#000000"}
        />
      </Cylinder>
      
      {/* Brazo del etiquetador */}
      <ThreeBox args={[0.1, 0.8, 0.1]} position={[0, 1.5, 0]}>
        <meshStandardMaterial
          color={active ? "#4ECDC4" : "#444444"}
          metalness={0.7}
          roughness={0.1}
        />
      </ThreeBox>
      
      {/* Indicador de estado */}
      <Sphere args={[0.1]} position={[0, 2, 0]}>
        <meshBasicMaterial
          color={active ? "#00FF00" : "#FF0000"}
        />
      </Sphere>
      
      <Text
        position={[0, -0.3, 0]}
        fontSize={0.15}
        color="#FFFFFF"
        anchorX="center"
        anchorY="middle"
      >
        Station {stationId}
      </Text>
    </group>
  )
}

// Control de cámara personalizado
const CameraController: React.FC = () => {
  const { camera } = useThree()
  
  useEffect(() => {
    // Posición inicial de la cámara
    camera.position.set(0, 8, 12)
    camera.lookAt(0, 0, 0)
  }, [camera])

  return null
}

// Componente principal de la vista 3D
const Dashboard3DView: React.FC = () => {
  const theme = useTheme()
  const containerRef = useRef<HTMLDivElement>(null)
  
  const { status } = useAppSelector(state => state.production)
  
  const [cameraDistance, setCameraDistance] = useState(12)
  const [showGrid, setShowGrid] = useState(true)
  const [autoRotate, setAutoRotate] = useState(false)
  // Nota: calidad de render no utilizada por ahora

  // Estado de las frutas en la cinta
  const [fruits] = useState([
    { id: 1, position: [-4, 0, 0] as [number, number, number], type: 'apple', emoji: '🍎', labeled: true },
    { id: 2, position: [-1, 0, 0] as [number, number, number], type: 'orange', emoji: '🍊', labeled: false },
    { id: 3, position: [2, 0, 0] as [number, number, number], type: 'apple', emoji: '🍎', labeled: true },
    { id: 4, position: [5, 0, 0] as [number, number, number], type: 'pear', emoji: '🍐', labeled: false },
  ])

  useEffect(() => {
    if (containerRef.current) {
      animate(containerRef.current, {
        opacity: [0, 1],
        translateY: [50, 0],
        duration: 1000,
        ease: 'outCubic',
        delay: 300,
      })
    }
  }, [])

  const handleFullscreen = () => {
    if (containerRef.current) {
      containerRef.current.requestFullscreen?.()
    }
  }

  const handleScreenshot = () => {
    // Implementar captura de pantalla del canvas 3D
    console.log('Screenshot captured')
  }

  return (
    <Box ref={containerRef} sx={{ width: '100%', height: '100%' }}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Box>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              background: theme.gradients.primary,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              mb: 1,
            }}
          >
            Dashboard 3D Interactivo
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Visualización en tiempo real del sistema de etiquetado
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            icon={<ViewInAr />}
            label={`${status.activeLabelers}/4 Activas`}
            color="primary"
            sx={{ fontWeight: 600 }}
          />
          <IconButton
            onClick={handleScreenshot}
            sx={{
              background: theme.gradients.glass,
              '&:hover': { transform: 'scale(1.05)' },
            }}
          >
            <CameraAlt />
          </IconButton>
          <IconButton
            onClick={handleFullscreen}
            sx={{
              background: theme.gradients.glass,
              '&:hover': { transform: 'scale(1.05)' },
            }}
          >
            <Fullscreen />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ height: 'calc(100% - 100px)' }}>
        {/* Escena 3D principal */}
        <Grid size={{ xs: 12, lg: 9 }}>
          <Card
            sx={{
              height: '100%',
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
              overflow: 'hidden',
            }}
          >
            <CardContent sx={{ p: 0, height: '100%' }}>
              <Canvas
                shadows
                camera={{ position: [0, 8, cameraDistance], fov: 60 }}
                style={{ background: 'radial-gradient(ellipse at center, #1A1F24 0%, #0A0F14 100%)' }}
              >
                <Suspense fallback={null}>
                  <CameraController />
                  
                  {/* Iluminación */}
                  <ambientLight intensity={0.3} />
                  <directionalLight
                    position={[10, 10, 5]}
                    intensity={1}
                    castShadow
                    shadow-mapSize-width={2048}
                    shadow-mapSize-height={2048}
                  />
                  <pointLight position={[-10, 10, -10]} intensity={0.5} color="#00E5A0" />
                  <pointLight position={[10, 10, 10]} intensity={0.5} color="#4ECDC4" />
                  
                  {/* Entorno */}
                  <Environment preset="warehouse" />
                  
                  {/* Grilla opcional */}
                  {showGrid && (
                    <gridHelper args={[20, 20, "#333333", "#222222"]} position={[0, -1.1, 0]} />
                  )}
                  
                  {/* Cinta transportadora */}
                  <ConveyorBelt speed={status.beltSpeed} isRunning={status.status === 'running'} />
                  
                  {/* Estaciones de etiquetado */}
                  <LabelingStation position={[-3, 0, 2]} active={status.activeLabelers >= 1} stationId={1} />
                  <LabelingStation position={[0, 0, 2]} active={status.activeLabelers >= 2} stationId={2} />
                  <LabelingStation position={[3, 0, 2]} active={status.activeLabelers >= 3} stationId={3} />
                  <LabelingStation position={[6, 0, 2]} active={status.activeLabelers >= 4} stationId={4} />
                  
                  {/* Frutas en la cinta */}
                  {fruits.map((fruit) => (
                    <Fruit
                      key={fruit.id}
                      position={fruit.position}
                      type={fruit.type}
                      emoji={fruit.emoji}
                      labeled={fruit.labeled}
                    />
                  ))}
                  
                  {/* Texto informativo 3D */}
                  <Text
                    position={[0, 4, -8]}
                    fontSize={0.8}
                    color="#FFFFFF"
                    anchorX="center"
                    anchorY="middle"
                  >
                    VisiFruit - Sistema de Etiquetado Inteligente
                  </Text>
                  
                  {/* Controles de órbita */}
                  <OrbitControls
                    enablePan={true}
                    enableZoom={true}
                    enableRotate={true}
                    autoRotate={autoRotate}
                    autoRotateSpeed={0.5}
                    minDistance={5}
                    maxDistance={25}
                    minPolarAngle={Math.PI / 6}
                    maxPolarAngle={Math.PI / 2}
                  />
                </Suspense>
              </Canvas>
            </CardContent>
          </Card>
        </Grid>

        {/* Panel de controles */}
        <Grid size={{ xs: 12, lg: 3 }}>
          <Card
            sx={{
              height: '100%',
              background: theme.gradients.glass,
              backdropFilter: 'blur(20px)',
              border: `1px solid rgba(255, 255, 255, 0.1)`,
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Settings /> Controles 3D
              </Typography>

              {/* Distancia de cámara */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Distancia de Cámara
                </Typography>
                <Slider
                  value={cameraDistance}
                  onChange={(_, value) => setCameraDistance(value as number)}
                  min={5}
                  max={25}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                  sx={{
                    '& .MuiSlider-thumb': {
                      background: theme.gradients.primary,
                    },
                    '& .MuiSlider-track': {
                      background: theme.gradients.primary,
                    },
                  }}
                />
              </Box>

              {/* Switches de control */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showGrid}
                      onChange={(e) => setShowGrid(e.target.checked)}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': {
                          color: theme.palette.primary.main,
                        },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                          backgroundColor: theme.palette.primary.main,
                        },
                      }}
                    />
                  }
                  label="Mostrar Grilla"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={autoRotate}
                      onChange={(e) => setAutoRotate(e.target.checked)}
                    />
                  }
                  label="Rotación Automática"
                />
              </Box>

              {/* Estadísticas en tiempo real */}
              <Box
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'rgba(0, 229, 160, 0.05)',
                  border: `1px solid rgba(0, 229, 160, 0.2)`,
                  mb: 3,
                }}
              >
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                  Estado del Sistema
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Velocidad:
                    </Typography>
                    <Typography variant="body2">
                      {status.beltSpeed} m/s
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Eficiencia:
                    </Typography>
                    <Typography variant="body2" color="primary.main">
                      {status.efficiency.toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Calidad:
                    </Typography>
                    <Typography variant="body2" color="success.main">
                      {status.qualityScore.toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      Procesadas:
                    </Typography>
                    <Typography variant="body2">
                      {status.itemsProcessedToday.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </Box>

              {/* Leyenda */}
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
                  Leyenda
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        background: '#00E5A0',
                      }}
                    />
                    <Typography variant="caption">Estación Activa</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        background: '#666666',
                      }}
                    />
                    <Typography variant="caption">Estación Inactiva</Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography sx={{ fontSize: '12px' }}>✓</Typography>
                    <Typography variant="caption">Fruta Etiquetada</Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard3DView