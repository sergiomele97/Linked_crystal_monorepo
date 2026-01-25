from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock

from screens.menu_screen.menu_screen import MenuScreen
from screens.emulator_screen.emulator_screen import EmulatorScreen
from global_components.connection_status import ConnectionStatus

class GlobalLayout(FloatLayout):
    """Contenedor principal de la app, con componentes globales"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScreenManager con todas las pantallas
        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(name='bienvenida'))
        self.sm.add_widget(EmulatorScreen(name='emulator'))
        self.add_widget(self.sm)

        # Indicador de conexión global
        self.connection_status = ConnectionStatus()
        self.add_widget(self.connection_status)

