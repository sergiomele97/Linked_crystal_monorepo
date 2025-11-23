from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock

from screens.menu_screen.menu_screen import MenuScreen
from screens.emulator_screen.emulator_screen import EmulatorScreen
from services.connection.connection_manager import ConnectionManager
from global_components.connection_indicator import ConnectionIndicator

class MyScreenManager(ScreenManager):
    pass

class RootWidget(FloatLayout):
    """Contenedor principal para que el indicador sea global"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ScreenManager
        self.sm = MyScreenManager()
        self.sm.add_widget(MenuScreen(name='bienvenida'))
        self.sm.add_widget(EmulatorScreen(name='emulator'))
        self.add_widget(self.sm)

        # Indicador global
        self.connection_indicator = ConnectionIndicator()
        self.add_widget(self.connection_indicator)

        # Prueba automática
        Clock.schedule_once(lambda dt: self.run_demo(), 1)

    def run_demo(self):
        """Demostración automática de los iconos"""
        self.connection_indicator.show_ok(duration=5)
        # Después de 6 segundos (5 + 1 de buffer), mostrar NOK
        Clock.schedule_once(lambda dt: self.connection_indicator.show_nok(duration=5), 6)

class LinkedCrystalApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rom_path: str = ""
        self.connection: str = ""
        self.connection_manager = ConnectionManager()

    def build(self):
        return RootWidget()

if __name__ == '__main__':
    appInstance = LinkedCrystalApp()
    appInstance.run()
