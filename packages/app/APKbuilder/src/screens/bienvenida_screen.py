from kivy.utils import platform
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
import os

Builder.load_file("screens/bienvenida_screen.kv")

if platform == 'android':
    from androidstorage4kivy import SharedStorage

class BienvenidaScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    rom_path = StringProperty("")

    def abrir_explorador(self):
        if platform == 'android':
            ss = SharedStorage()
            ss.choose_file(mime_type="application/octet-stream", callback=self.procesar_archivo)
        else:
            self.ids.label_rom.text = "Selector solo disponible en Android."

    def procesar_archivo(self, uri):
        if not uri:
            self.ids.label_rom.text = "No se seleccionó ningún archivo."
            return

        if platform == 'android':
            ss = SharedStorage()
            path = ss.get_path_from_uri(uri)
        else:
            path = uri  # En otros sistemas, podrías implementar filechooser

        if path and path.lower().endswith(".gbc"):
            self.rom_path = path
            self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(path)}"
            self.rom_cargado = True
        else:
            self.ids.label_rom.text = "Archivo no válido. Debe ser .gbc"

    def elegir_servidor(self):
        self.servidor_elegido = True
        self.ids.label_servidor.text = "Servidor elegido correctamente."

    def iniciar_juego(self):
        if self.rom_cargado and self.servidor_elegido:
            self.ids.label_estado.text = f"Iniciando juego con {os.path.basename(self.rom_path)}"
            self.manager.get_screen('emulador').rom_path = self.rom_path
            self.manager.current = 'emulador'
        else:
            self.ids.label_estado.text = "Falta seleccionar ROM o servidor."
