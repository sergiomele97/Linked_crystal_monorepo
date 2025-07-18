from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from screens.menu_screen.menu_screen import MenuScreen
from screens.emulator_screen.emulator_screen import EmulatorScreen

class MyScreenManager(ScreenManager):
    pass

class MiApp(App):
    def build(self):
        sm = MyScreenManager()
        sm.add_widget(MenuScreen(name='bienvenida'))
        sm.add_widget(EmulatorScreen(name='emulator'))
        return sm

if __name__ == '__main__':
    MiApp().run()

