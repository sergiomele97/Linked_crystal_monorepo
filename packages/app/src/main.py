from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from screens.bienvenida_screen import BienvenidaScreen
from screens.emulador_screen import EmuladorScreen

class MyScreenManager(ScreenManager):
    pass

class MiApp(App):
    def build(self):
        sm = MyScreenManager()
        sm.add_widget(BienvenidaScreen(name='bienvenida'))
        sm.add_widget(EmuladorScreen(name='emulador'))
        return sm

if __name__ == '__main__':
    MiApp().run()

