from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.lang import Builder
import os

from screens.menu_screen.components.rom_selector import select_rom
from screens.menu_screen.components.menu_dropdown import MenuDropdown

Builder.load_file("screens/menu_screen/menu_screen.kv")

class MenuScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    loading = BooleanProperty(False)  # controla visibilidad del spinner.zip
    listaServidores = ListProperty([])
    current_path = StringProperty("/")

    def on_pre_enter(self):
        self.connectionManager = App.get_running_app().connection_manager

    def open_menu(self, caller):
        if not hasattr(self, "dropdown"):
            self.dropdown = MenuDropdown()
            self.dropdown.father_screen = self
        self.dropdown.open(caller)

    def abrir_explorador(self):
        def cuando_selecciona_archivo(destino_path):
            if destino_path:
                App.get_running_app().rom_path = destino_path
                self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(destino_path)}"
                self.rom_cargado = True
            else:
                self.ids.label_rom.text = "Archivo no válido."

        select_rom(self, cuando_selecciona_archivo)

    def elegir_servidor(self):
        self.loading = True
        self.ids.label_servidor.text = "Cargando servidores..."
        self.ids.loading_spinner.anim_delay = 0.05  # activa animación

        def success(result):
            self.listaServidores = result
            self.servidor_elegido = True
            self.loading = False
            self.ids.label_servidor.text = "Servidor elegido correctamente."
            self.ids.loading_spinner.anim_delay = -1  # pausa animación

        def error(err):
            self.loading = False
            self.ids.label_servidor.text = f"Error al cargar: {err}"
            self.ids.loading_spinner.anim_delay = -1  # pausa animación

        self.connectionManager.getServerList(on_success=success, on_error=error)

    def iniciar_juego(self):
        self.ids.output_label.text = f"¡Iniciando juego con {os.path.basename(App.get_running_app().rom_path)}!"
        emulator_screen = self.manager.get_screen('emulator')
        self.manager.current = 'emulator'
