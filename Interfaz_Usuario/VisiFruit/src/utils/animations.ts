import { animate, createTimeline, stagger, engine } from 'animejs'

type AnimationTargets = Parameters<typeof animate>[0]
type AnimationParams = Parameters<typeof animate>[1]
type AnimationInstance = ReturnType<typeof animate>

// Configuraciones de animaciones predefinidas
export const animationConfig = {
  // Duraciones estándar
  duration: {
    fast: 300,
    normal: 600,
    slow: 1000,
    verySlow: 1500,
  },
  
  // Easings personalizados (nombres v4)
  easing: {
    smooth: 'outCubic',
    bounce: 'outElastic(1, .8)',
    quick: 'outQuart',
    gentle: 'inOutSine',
  },
  
  // Delays estándar
  delay: {
    none: 0,
    short: 100,
    medium: 200,
    long: 400,
  }
}

// Animaciones reutilizables
export const animations = {
  // Animación de entrada fade + slide
  fadeInUp: (targets: AnimationTargets, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      translateY: [50, 0],
      opacity: [0, 1],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.smooth,
      ...(options as any),
    })
  },

  // Animación de entrada con escalado
  scaleIn: (targets: AnimationTargets, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      scale: [0, 1],
      opacity: [0, 1],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.bounce,
      ...(options as any),
    })
  },

  // Animación de stagger para listas
  staggerFadeIn: (targets: AnimationTargets, staggerDelay: number = 100, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      translateY: [30, 0],
      opacity: [0, 1],
      duration: animationConfig.duration.normal,
      delay: stagger(staggerDelay),
      ease: animationConfig.easing.smooth,
      ...(options as any),
    })
  },

  // Animación de hover para botones
  buttonHover: (target: AnimationTargets) => {
    return animate(target, {
      scale: [1, 1.05],
      duration: animationConfig.duration.fast,
      ease: animationConfig.easing.quick,
    })
  },

  // Animación de hover reset
  buttonHoverReset: (target: AnimationTargets) => {
    return animate(target, {
      scale: [1.05, 1],
      duration: animationConfig.duration.fast,
      ease: animationConfig.easing.quick,
    })
  },

  // Animación de pulso para elementos activos
  pulse: (targets: AnimationTargets, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      scale: [1, 1.1, 1],
      duration: animationConfig.duration.slow,
      loop: true,
      ease: animationConfig.easing.gentle,
      ...(options as any),
    })
  },

  // Animación de rotación para elementos de carga
  rotate: (targets: AnimationTargets, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      rotate: '1turn',
      duration: animationConfig.duration.slow,
      loop: true,
      ease: 'linear',
      ...(options as any),
    })
  },

  // Animación de shake para errores
  shake: (targets: AnimationTargets) => {
    return animate(targets, {
      translateX: [0, -10, 10, -10, 10, 0],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.quick,
    })
  },

  // Animación de bounce para elementos exitosos
  bounce: (targets: AnimationTargets) => {
    return animate(targets, {
      translateY: [0, -20, 0],
      scale: [1, 1.1, 1],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.bounce,
    })
  },

  // Animación de flash para notificaciones
  flash: (targets: AnimationTargets, color: string = '#00E5A0') => {
    return animate(targets, {
      backgroundColor: [color, 'transparent'],
      duration: animationConfig.duration.fast,
      alternate: true,
      loop: 3,
      ease: animationConfig.easing.gentle,
    })
  },

  // Animación de slide para paneles
  slideInRight: (targets: AnimationTargets, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      translateX: [100, 0],
      opacity: [0, 1],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.smooth,
      ...(options as any),
    })
  },

  slideInLeft: (targets: AnimationTargets, options: Partial<AnimationParams> = {}) => {
    return animate(targets, {
      translateX: [-100, 0],
      opacity: [0, 1],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.smooth,
      ...(options as any),
    })
  },

  // Animación de morphing para iconos
  morphIcon: (targets: AnimationTargets, fromPath: string, toPath: string) => {
    return animate(targets, {
      d: [fromPath, toPath],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.smooth,
    })
  },

  // Animación de contador numérico
  countUp: (
    target: HTMLElement,
    from: number,
    to: number,
    options: Partial<AnimationParams> = {}
  ) => {
    const obj = { value: from }
    
    return animate(obj, {
      value: to,
      duration: animationConfig.duration.slow,
      ease: animationConfig.easing.smooth,
      onUpdate: () => {
        target.textContent = Math.round((obj as any).value).toString()
      },
      ...(options as any),
    })
  },

  // Timeline complejo para loading screens
  loadingSequence: (logoTarget: AnimationTargets, textTarget: AnimationTargets, progressTarget: AnimationTargets) => {
    const tl = createTimeline({
      loop: false,
      autoplay: true,
    })

    tl.add(logoTarget as any, {
      scale: [0, 1.2, 1],
      opacity: [0, 1],
      rotate: [0, '1turn'],
      duration: animationConfig.duration.verySlow,
      ease: animationConfig.easing.bounce,
    })
    .add(textTarget as any, {
      opacity: [0, 1],
      translateY: [30, 0],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.smooth,
    }, '-=800')
    .add(progressTarget as any, {
      opacity: [0, 1],
      scaleX: [0, 1],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.smooth,
    }, '-=400')

    return tl
  }
}

// Utilidades para animaciones
export const animationUtils = {
  // Pausar todas las animaciones
  pauseAll: () => {
    engine.pause()
  },

  // Reanudar todas las animaciones
  playAll: () => {
    engine.resume()
  },

  // Obtener duración aleatoria dentro de un rango
  randomDuration: (min: number, max: number) => {
    return Math.random() * (max - min) + min
  },

  // Crear stagger con variación aleatoria
  randomStagger: (base: number, variation: number = 0.2) => {
    return (_el: Element, i: number) => {
      const randomFactor = (Math.random() - 0.5) * variation
      return (base + base * randomFactor) * i
    }
  },

  // Crear animación que se ejecuta solo una vez por elemento
  once: (targets: AnimationTargets, animationFn: () => AnimationInstance) => {
    const elements: Element[] = (() => {
      if (typeof targets === 'string') return Array.from(document.querySelectorAll(targets))
      if (targets instanceof Element) return [targets]
      if (Array.isArray(targets)) return targets as Element[]
      try { return Array.from(targets as any) } catch { return [] }
    })()

    elements.forEach((el: Element) => {
      if (!el.hasAttribute('data-animated')) {
        el.setAttribute('data-animated', 'true')
        animationFn()
      }
    })
  }
}

// Preset de animaciones para diferentes tipos de componentes
export const componentAnimations = {
  card: {
    enter: (target: AnimationTargets) => animations.fadeInUp(target),
    hover: (target: AnimationTargets) => animations.buttonHover(target),
    hoverReset: (target: AnimationTargets) => animations.buttonHoverReset(target),
  },
  
  modal: {
    enter: (target: AnimationTargets) => animations.scaleIn(target),
    exit: (target: AnimationTargets) => animate(target, {
      scale: [1, 0],
      opacity: [1, 0],
      duration: animationConfig.duration.fast,
      ease: animationConfig.easing.quick,
    }),
  },
  
  notification: {
    enter: (target: AnimationTargets) => animations.slideInRight(target),
    flash: (target: AnimationTargets, color?: string) => animations.flash(target, color),
    exit: (target: AnimationTargets) => animate(target, {
      translateX: [0, 100],
      opacity: [1, 0],
      duration: animationConfig.duration.fast,
      ease: animationConfig.easing.quick,
    }),
  },
  
  list: {
    enter: (targets: AnimationTargets) => animations.staggerFadeIn(targets),
    remove: (target: AnimationTargets) => animate(target, {
      translateX: [0, -100],
      opacity: [1, 0],
      height: [null as any, 0],
      duration: animationConfig.duration.normal,
      ease: animationConfig.easing.quick,
    }),
  }
}

export default animations