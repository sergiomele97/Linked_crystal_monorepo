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
        """Exporta el archivo .ram usando el Storage Access Framework (SAF) de Android.
        Esto abre el selector nativo para que el usuario elija dónde guardar el archivo.
        """
        if platform != 'android':
            try:
                self.ids.output_label.text = "Exportar RAM solo disponible en Android"
            except Exception:
                pass
            return

        from android.storage import app_storage_path
        local_ram = os.path.join(app_storage_path(), 'gamerom.gbc.ram')

        if not os.path.exists(local_ram):
            try:
                self.ids.output_label.text = "No se encontró archivo .ram"
            except Exception:
                pass
            return

        # Intent nativo SAF (Storage Access Framework)
        try:
            from android import activity
            from jnius import autoclass, cast
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            
            def on_activity_result(requestCode, resultCode, intent_data):
                if requestCode == 2:
                    activity.unbind(on_activity_result=on_activity_result)
                    if resultCode == -1 and intent_data is not None:
                        # Usuario eligió destino correctamente
                        uri = intent_data.getData()
                        try:
                            # Leer RAM local
                            with open(local_ram, 'rb') as f_in:
                                data = f_in.read()
                            
                            # Escribir a la URI seleccionada
                            context = PythonActivity.mActivity
                            resolver = context.getContentResolver()
                            output_stream = resolver.openOutputStream(uri)
                            output_stream.write(data)
                            output_stream.close()
                            
                            self.ids.output_label.text = "¡RAM exportada correctamente!"
                        except Exception as e:
                            self.ids.output_label.text = f"Error al escribir: {e}"
                    else:
                        self.ids.output_label.text = "Exportación cancelada."

            # Registrar el callback para el resultado del Intent
            activity.bind(on_activity_result=on_activity_result)
            
            # Crear Intent para crear un documento
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("application/octet-stream")
            intent.putExtra(Intent.EXTRA_TITLE, "gamerom.gbc.ram")
            
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivityForResult(intent, 2)
            
            try:
                self.ids.output_label.text = "Selecciona destino para la RAM..."
            except Exception:
                pass
                
        except Exception as e:
            try:
                self.ids.output_label.text = f"Error SAF: {e}"
            except Exception:
                pass

    def import_ram(self):
        """Importa un archivo .ram desde el almacenamiento del teléfono al sandbox de la app.
        Usa ACTION_OPEN_DOCUMENT para permitir al usuario seleccionar el archivo.
        """
        if platform != 'android':
            try:
                self.ids.output_label.text = "Importar RAM solo disponible en Android"
            except Exception:
                pass
            return

        from android.storage import app_storage_path
        destino_ram = os.path.join(app_storage_path(), 'gamerom.gbc.ram')

        try:
            from android import activity
            from jnius import autoclass, cast
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            
            def on_activity_result(requestCode, resultCode, intent_data):
                if requestCode == 3:
                    activity.unbind(on_activity_result=on_activity_result)
                    if resultCode == -1 and intent_data is not None:
                        # Usuario seleccionó el archivo
                        uri = intent_data.getData()
                        try:
                            # Leer desde la URI seleccionada usando ContentResolver
                            context = PythonActivity.mActivity
                            resolver = context.getContentResolver()
                            input_stream = resolver.openInputStream(uri)
                            
                            # Escribir en el sandbox
                            with open(destino_ram, 'wb') as f_out:
                                buf = bytearray(1024)
                                while True:
                                    read = input_stream.read(buf)
                                    if read == -1:
                                        break
                                    f_out.write(buf[:read])
                            input_stream.close()
                            
                            self.ids.output_label.text = "¡RAM importada con éxito!"
                        except Exception as e:
                            self.ids.output_label.text = f"Error al importar: {e}"
                    else:
                        self.ids.output_label.text = "Importación cancelada."

            # Registrar el callback
            activity.bind(on_activity_result=on_activity_result)
            
            # Intent para abrir documento
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")  # O "application/octet-stream"
            
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivityForResult(intent, 3)
            
            try:
                self.ids.output_label.text = "Selecciona el archivo .ram a importar..."
            except Exception:
                pass
                
        except Exception as e:
            try:
                self.ids.output_label.text = f"Error SAF Import: {e}"
            except Exception:
                pass
