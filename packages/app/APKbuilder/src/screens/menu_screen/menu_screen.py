from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.lang import Builder
import os

from .environment_rom_selection import select_rom

Builder.load_file("screens/menu_screen/menu_screen.kv")

class MenuScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    rom_path = StringProperty("")
    current_path = StringProperty("/")

    def abrir_explorador(self):
        def cuando_selecciona_archivo(destino_path):
            if destino_path:
                self.rom_path = destino_path
                self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(destino_path)}"
                self.rom_cargado = True
            else:
                self.ids.label_rom.text = "Archivo no válido."

        select_rom(self, cuando_selecciona_archivo)

    def elegir_servidor(self):
        self.servidor_elegido = True
        self.ids.label_servidor.text = "Servidor elegido correctamente."

    def iniciar_juego(self):
        self.ids.label_estado.text = f"¡Iniciando juego con {os.path.basename(self.rom_path)}!"
        emulator_screen = self.manager.get_screen('emulator')
        emulator_screen.rom_path = self.rom_path
        self.manager.current = 'emulator'
