from kivy.app import App
from global_components.global_layout import GlobalLayout
from services.connection.connection_manager import ConnectionManager

class LinkedCrystalApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rom_path = ""
        self.connection = ""
        self.connection_manager = ConnectionManager()

    def build(self):
        return GlobalLayout()

if __name__ == '__main__':
    LinkedCrystalApp().run()
