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

        # Demo automática (opcional)
        Clock.schedule_once(lambda dt: self.run_demo(), 1)

    def run_demo(self):
        """Demostración de iconos de conexión"""
        self.connection_status.show_ok(duration=5)
        Clock.schedule_once(lambda dt: self.connection_status.show_nok(duration=5), 6)

    # Métodos para controlar el indicador desde cualquier parte
    def show_connection_ok(self, duration=5):
        self.connection_status.show_ok(duration)

    def show_connection_nok(self, duration=5):
        self.connection_status.show_nok(duration)
