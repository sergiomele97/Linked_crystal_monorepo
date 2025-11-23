from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.lang import Builder
import os

Builder.load_file(os.path.join(os.path.dirname(__file__), "connection_indicator.kv"))

class ConnectionIndicator(FloatLayout):
    mostrarConexionOK = BooleanProperty(False)
    mostrarConexionNOK = BooleanProperty(False)

    def show_ok(self, duration=5):
        self.mostrarConexionNOK = False
        self.mostrarConexionOK = True
        Clock.schedule_once(lambda dt: self.hide_icons(), duration)

    def show_nok(self, duration=5):
        self.mostrarConexionOK = False
        self.mostrarConexionNOK = True
        Clock.schedule_once(lambda dt: self.hide_icons(), duration)

    def hide_icons(self):
        self.mostrarConexionOK = False
        self.mostrarConexionNOK = False
