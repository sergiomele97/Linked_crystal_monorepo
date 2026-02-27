from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.lang import Builder
import os

from screens.menu_screen.components.rom_selector import select_rom
from screens.menu_screen.components.menu_dropdown import MenuDropdown
from kivy.utils import platform
import shutil
try:
    from plyer import filechooser
except Exception:
    filechooser = None

kv_path = os.path.join(os.path.dirname(__file__), "menu_screen.kv")
Builder.load_file(kv_path)

class MenuScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    loading = BooleanProperty(False)

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
                App.get_running_app().appData.romPath = destino_path
                self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(destino_path)}"
                self.rom_cargado = True
            else:
                self.ids.label_rom.text = "Archivo no válido."
        select_rom(self, cuando_selecciona_archivo)

    def elegir_servidor(self):
        self.connectionManager.getServerListAndSelect(self)

    def iniciar_juego(self):
        self.ids.output_label.text = f"¡Iniciando juego!"
        emulator_screen = self.manager.get_screen('emulator')
        self.manager.current = 'emulator'

    def export_ram(self):
        """Exporta el archivo .ram desde el sandbox de la app a la ubicación elegida por el usuario (Android-only).
        Implementación mínima: usa `plyer.filechooser.save_file` y copia el archivo.
        """
        if platform != 'android' or filechooser is None:
            # No disponible fuera de Android o si plyer no está
            try:
                self.ids.output_label.text = "Exportar RAM solo disponible en Android"
            except Exception:
                pass
            return

        # Ruta local esperada dentro del sandbox
        try:
            from android.storage import app_storage_path
            import os
            local_ram = os.path.join(app_storage_path(), 'rom_seleccionada.gbc.ram')
        except Exception:
            local_ram = None

        if not local_ram or not os.path.exists(local_ram):
            try:
                self.ids.output_label.text = "No se encontró archivo .ram en el sandbox"
            except Exception:
                pass
            return

        # Pedir al usuario dónde guardar
        try:
            result = filechooser.save_file(title="Guardar RAM", suggested_filename='rom_seleccionada.gbc.ram')
            if not result:
                return
            # plyer.filechooser.save_file puede devolver lista
            dest_path = result[0] if isinstance(result, (list, tuple)) else result
            # Copiar archivo
            shutil.copyfile(local_ram, dest_path)
            try:
                self.ids.output_label.text = f"RAM exportada a: {dest_path}"
            except Exception:
                pass
        except Exception as e:
            try:
                self.ids.output_label.text = f"Error exportando RAM: {e}"
            except Exception:
                pass
