import os
from services.environment.environment_manager import inicializar_entorno
inicializar_entorno()

import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

import logging
logging.getLogger("websockets").setLevel(logging.CRITICAL)
logging.getLogger("websockets.protocol").setLevel(logging.CRITICAL)
logging.getLogger("websockets.client").setLevel(logging.CRITICAL)
logging.getLogger("websockets.server").setLevel(logging.CRITICAL)

from kivy.app import App
from kivy.core.window import Window
from models.appData import appData
from global_components.global_layout import GlobalLayout
from services.connection.main_conn.connection_manager import ConnectionManager

class LinkedCrystalApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.appData = appData()
        self.connection_manager = ConnectionManager()
        Window.softinput_mode = "below_target"

    def build(self):
        return GlobalLayout()

if __name__ == '__main__':
    LinkedCrystalApp().run()
