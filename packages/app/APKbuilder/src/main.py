import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

from kivy.app import App
from models.appData import appData
from global_components.global_layout import GlobalLayout
from services.connection.connection_manager import ConnectionManager

class LinkedCrystalApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.appData = appData()
        self.connection_manager = ConnectionManager()

    def build(self):
        return GlobalLayout()

if __name__ == '__main__':
    LinkedCrystalApp().run()
