# tests/test_state_machine.py
import pytest
from unittest.mock import AsyncMock, patch

# Mockear las librerías de hardware antes de que se importen
import sys
from unittest.mock import MagicMock

# Mock de GPIO
sys.modules['utils.gpio_wrapper'] = MagicMock()

from fruprint_system.core.controller import SystemController

@pytest.mark.asyncio
@patch('fruprint_system.core.controller.SystemController._initialize_components', new_callable=AsyncMock)
@patch('fruprint_system.core.controller.SystemController._initialize_services', new_callable=AsyncMock)
async def test_state_transitions(mock_init_services, mock_init_components):
    """
    Verifica las transiciones básicas de la máquina de estados.
    """
    # Mocks para evitar inicialización real de hardware
    mock_init_components.return_value = None
    mock_init_services.return_value = None

    controller = SystemController("tests/test_config.json")
    
    # 1. Estado inicial debe ser 'offline'
    assert controller.state_machine.current_state.name == 'offline'
    
    # 2. Transición a 'initializing' y luego a 'idle'
    await controller.initialize_system()
    
    # Verificar que los métodos de inicialización fueron llamados
    mock_init_components.assert_called_once()
    mock_init_services.assert_called_once()
    
    # El estado final después de una inicialización exitosa debe ser 'idle'
    assert controller.state_machine.current_state.name == 'idle'

    # 3. Transición de 'idle' a 'running'
    await controller.state_machine.trigger('start_production')
    assert controller.state_machine.current_state.name == 'running'

    # 4. Transición de 'running' a 'stopping' y luego a 'idle'
    await controller.state_machine.trigger('stop_production')
    assert controller.state_machine.current_state.name == 'stopping'

    # La máquina de estados debería pasar automáticamente a 'idle'
    await asyncio.sleep(0.01) # dar tiempo a que se ejecute el callback
    assert controller.state_machine.current_state.name == 'idle'

    # 5. Transición a 'emergency_stop' desde 'idle'
    await controller.state_machine.trigger('emergency_stop')
    assert controller.state_machine.current_state.name == 'emergency_stop'
