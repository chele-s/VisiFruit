# 🍎 VisiFruit Launcher - Interfaz Gráfica Moderna

## Descripción

El **VisiFruit Launcher** es una aplicación con interfaz gráfica moderna que permite iniciar, monitorear y controlar todo el sistema VisiFruit de manera visual y fácil.

## ✨ Características

### 🎨 Interfaz Moderna
- **Tema oscuro/claro**: Interfaz elegante usando CustomTkinter
- **Botones grandes y coloridos**: Fácil identificación de funciones
- **Indicadores de estado en tiempo real**: Visualización del estado de cada servicio
- **Logs con colores**: Mensajes formateados con emojis y códigos de color

### 🚀 Funcionalidades
- **Inicio completo del sistema**: Un solo clic para iniciar todo
- **Control individual**: Iniciar/detener backend, frontend o sistema principal por separado
- **Monitoreo en tiempo real**: Verificación automática del estado de los servicios
- **Apertura automática del navegador**: Se abre automáticamente el frontend cuando está listo
- **Enlaces rápidos**: Acceso directo a todas las URLs importantes
- **Gestión de procesos**: Control inteligente de todos los servicios

### 🔧 Control del Sistema
- **Backend API** (Puerto 8001): API REST y WebSockets
- **Frontend React** (Puerto 3000): Interfaz de usuario web
- **Sistema Principal** (Puerto 8000): Sistema de etiquetado industrial

## 🛠️ Instalación y Uso

### Opción 1: Ejecutable (.exe) - Recomendado

1. **Compilar el ejecutable**:
   ```bash
   # Método fácil
   build_launcher.bat
   
   # O manualmente
   pip install -r launcher_requirements.txt
   python build_launcher.py --onefile --windowed
   ```

2. **Ejecutar**:
   - Ve a la carpeta `dist/`
   - Ejecuta `VisiFruit_Launcher.exe`
   - ¡Listo!

### Opción 2: Python directo

1. **Instalar dependencias**:
   ```bash
   pip install -r launcher_requirements.txt
   ```

2. **Ejecutar**:
   ```bash
   python visifruit_launcher.py
   ```

## 📋 Dependencias

### Obligatorias
- **Python 3.8+**
- **tkinter** (incluido con Python)
- **requests** (para verificar estado de servicios)

### Opcionales (para mejor apariencia)
- **customtkinter** (interfaz moderna)
- **pillow** (para iconos)
- **colorlog** (logs con colores)

### Para compilar .exe
- **pyinstaller** (compilación a ejecutable)

## 🎮 Uso del Launcher

### Panel de Control
- **🚀 Iniciar Sistema Completo**: Inicia backend + frontend automáticamente
- **⏹️ Detener Todo**: Cierra todos los servicios de una vez
- **🔧 Backend**: Control individual del backend
- **💻 Frontend**: Control individual del frontend  
- **🏭 Sistema Principal**: Control del sistema de etiquetado

### Indicadores de Estado
- **● Verde**: Servicio funcionando correctamente
- **● Rojo**: Servicio detenido o con problemas

### Registro de Actividad
- **ℹ️ Info**: Información general
- **✅ Éxito**: Operaciones completadas
- **⚠️ Advertencia**: Situaciones que requieren atención
- **❌ Error**: Problemas que necesitan solución

### Enlaces Rápidos
- **🌐 Frontend**: Abre la interfaz web principal
- **🔧 Backend API**: Documentación de la API
- **🏭 Sistema Principal**: Dashboard del sistema industrial
- **📊 WebSocket Test**: Herramienta para probar WebSockets

## 🔧 Configuración

### Variables de Entorno
El launcher configura automáticamente:
```bash
PYTHONIOENCODING=utf-8
PYTHONLEGACYWINDOWSSTDIO=utf-8
PYTHONPATH=<ruta_del_proyecto>
FRUPRINT_ENV=development
```

### Puertos por Defecto
- **8001**: Backend API y WebSockets
- **3000**: Frontend React (desarrollo)
- **8000**: Sistema principal de etiquetado

## 🛡️ Resolución de Problemas

### Error: "No se encuentra main_etiquetadora.py"
- **Solución**: Ejecuta el launcher desde la raíz del proyecto VisiFruit

### Error: "Entorno virtual no encontrado"
- **Solución**: Crea el entorno virtual:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```

### Error: "Node.js no está instalado"
- **Solución**: Instala Node.js desde https://nodejs.org/

### Error: "Puerto ocupado"
- **Solución**: Cierra otros procesos que usen los puertos 8000, 8001, 3000
- **O usa**: Botón "⏹️ Detener Todo" en el launcher

### Servicios no se inician
1. Verifica que estés en la carpeta correcta del proyecto
2. Revisa los logs en el panel de actividad
3. Asegúrate de que las dependencias estén instaladas
4. Verifica que los puertos estén libres

## 🎨 Personalización

### Cambiar Tema
```python
# En visifruit_launcher.py
ctk.set_appearance_mode("light")  # o "dark"
ctk.set_default_color_theme("green")  # o "blue", "dark-blue"
```

### Modificar Puertos
Edita las URLs en el código:
```python
# En create_links_panel()
links = [
    ("🌐 Frontend", "http://localhost:3000"),
    ("🔧 Backend API", "http://localhost:8001/api/docs"),
    # ...
]
```

## 🔄 Actualizaciones

Para actualizar el launcher:

1. **Actualizar código**:
   ```bash
   git pull origin main  # Si usas git
   ```

2. **Recompilar ejecutable**:
   ```bash
   build_launcher.bat
   ```

3. **Reemplazar ejecutable** en la carpeta de distribución

## 📞 Soporte

### Logs
Los logs se guardan en:
- **launcher.log**: Actividad del launcher
- **logs/**: Logs del sistema principal

### Reportar Problemas
Incluye siempre:
1. **Versión de Python**: `python --version`
2. **Sistema operativo**: Windows 10/11
3. **Contenido de logs**: Últimas líneas relevantes
4. **Pasos para reproducir**: Qué hiciste antes del error

## 🚀 Próximas Características

- [ ] **Dashboard integrado**: Ver métricas sin abrir navegador
- [ ] **Notificaciones del sistema**: Alertas en tiempo real
- [ ] **Actualizaciones automáticas**: Auto-update del launcher
- [ ] **Configuración visual**: Panel de configuración en GUI
- [ ] **Temas personalizados**: Más opciones de apariencia
- [ ] **Backup automático**: Copia de seguridad de configuraciones

---

## 📄 Licencia

Este launcher es parte del proyecto VisiFruit y sigue la misma licencia del proyecto principal.

---

**¡Disfruta de tu nuevo launcher visual! 🎉**
