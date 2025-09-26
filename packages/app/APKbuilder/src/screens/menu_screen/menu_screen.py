from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.utils import platform
import os

from screens.menu_screen.components.rom_selector import select_rom
from screens.menu_screen.components.menu_dropdown import MenuDropdown

Builder.load_file("screens/menu_screen/menu_screen.kv")

class MenuScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    rom_path = StringProperty("")
    current_path = StringProperty("/")

    def open_menu(self, caller):
        if not hasattr(self, "dropdown"):
            self.dropdown = MenuDropdown()
            self.dropdown.father_screen = self
        self.dropdown.open(caller)

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
        self.ids.output_label.text = f"¡Iniciando juego con {os.path.basename(self.rom_path)}!"
        emulator_screen = self.manager.get_screen('emulator')
        emulator_screen.rom_path = self.rom_path
        self.manager.current = 'emulator'



