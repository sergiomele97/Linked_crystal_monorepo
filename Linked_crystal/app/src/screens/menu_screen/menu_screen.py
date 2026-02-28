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
        """Exporta el archivo .ram desde el sandbox de la app usando el Share Intent de Android.
        Esto permite al usuario guardar el archivo en cualquier ubicación o enviarlo por otras apps.
        """
        if platform != 'android':
            try:
                self.ids.output_label.text = "Exportar RAM solo disponible en Android"
            except Exception:
                pass
            return

        from android.storage import app_storage_path
        local_ram = os.path.join(app_storage_path(), 'rom_seleccionada.gbc.ram')

        if not os.path.exists(local_ram):
            try:
                self.ids.output_label.text = "No se encontró archivo .ram en el sandbox"
            except Exception:
                pass
            return

        # Intent nativo de Android para compartir (Exportar)
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            File = autoclass('java.io.File')
            FileProvider = autoclass('androidx.core.content.FileProvider')
            
            context = PythonActivity.mActivity
            file_obj = File(local_ram)
            
            # Buildozer configura el FileProvider con el nombre del paquete + .fileprovider
            authority = context.getPackageName() + ".fileprovider"
            uri = FileProvider.getUriForFile(context, authority, file_obj)

            shareIntent = Intent(Intent.ACTION_SEND)
            shareIntent.setType("application/octet-stream")
            shareIntent.putExtra(Intent.EXTRA_STREAM, uri)
            shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            
            # Crear el selector de aplicaciones (Chooser)
            title = cast('java.lang.CharSequence', autoclass('java.lang.String')("Exportar RAM"))
            chooserIntent = Intent.createChooser(shareIntent, title)
            
            context.startActivity(chooserIntent)
            
            try:
                self.ids.output_label.text = "Selector de exportación abierto"
            except Exception:
                pass
                
        except Exception as e:
            try:
                self.ids.output_label.text = f"Error al exportar: {e}"
            except Exception:
                pass
