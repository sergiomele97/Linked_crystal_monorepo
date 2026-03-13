from services.environment.environment_manager import inicializar_entorno
inicializar_entorno()

from kivy.app import App
from kivy.core.window import Window
from models.appData import appData
from global_components.global_layout import GlobalLayout
from services.connection.main_conn.connection_manager import ConnectionManager

class LinkedCrystalApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon = 'resources/image/LinkedCrystalIcon.png'
        self.appData = appData()
        self.connection_manager = ConnectionManager()
        Window.softinput_mode = "below_target"

    def build(self):
        return GlobalLayout()

    def on_pause(self):
        """Disparado en Android cuando la app va a segundo plano"""
        self._save_on_lifecycle()
        return True

    def on_resume(self):
        """Disparado en Android cuando la app vuelve al primer plano"""
        pass

    def on_stop(self):
        """Disparado cuando la app se cierra definitivamente"""
        self._save_on_lifecycle()

    def _save_on_lifecycle(self):
        """Busca el emulador y fuerza un guardado de seguridad"""
        try:
            # self.root es el GlobalLayout
            if hasattr(self.root, 'sm'):
                sm = self.root.sm
                if sm.current == 'emulator':
                    emulator_screen = sm.get_screen('emulator')
                    if hasattr(emulator_screen, 'emulator'):
                        emulator_screen.emulator.save_RAM()
        except Exception as e:
            # En el ciclo de vida, mejor no crashear
            print(f"Error en guardado de ciclo de vida: {e}")

if __name__ == '__main__':
    LinkedCrystalApp().run()
