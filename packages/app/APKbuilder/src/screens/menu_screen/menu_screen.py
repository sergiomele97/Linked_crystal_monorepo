from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.utils import platform
from kivy.clock import Clock
from kivy.resources import resource_find
import os

Builder.load_file("screens/menu_screen/menu_screen.kv")

# ANDROID ENVIRONMENT VARIABLES ------------------------------------------------------------------
if platform == 'android':
    rootpath = "/storage/emulated/0/"
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast
    from android import activity
    from android.storage import app_storage_path

    def solicitar_permisos(callback=None):
        def permisos_callback(permissions, grants):
            if all(grants):
                if callback:
                    callback()
            else:
                print("[ERROR] Permisos no concedidos")
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE], permisos_callback)

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')

    def abrir_selector_nativo(callback):
        def on_activity_result(requestCode, resultCode, intent_data):
            if requestCode == 1:
                activity.unbind(on_activity_result=on_activity_result)  # Desvincular
                if resultCode == -1 and intent_data is not None:
                    uri = intent_data.getData()
                    if uri:
                        callback(uri)  # PASAMOS el URI directamente
                    else:
                        print("No se pudo obtener el URI del archivo.")
                else:
                    print("Selección cancelada o sin datos.")

        activity.bind(on_activity_result=on_activity_result)

        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("*/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.startActivityForResult(intent, 1)

    def copiar_desde_uri(uri, destino_path):
        currentActivity = PythonActivity.mActivity
        ContentResolver = currentActivity.getContentResolver()
        input_stream = ContentResolver.openInputStream(uri)
        try:
            with open(destino_path, "wb") as out_file:
                buf = bytearray(1024)
                while True:
                    read = input_stream.read(buf)
                    if read == -1:
                        break
                    out_file.write(buf[:read])
        finally:
            input_stream.close()

else:
    rootpath = "/"
    def solicitar_permisos(callback=None):
        if callback:
            callback()

    def abrir_selector_nativo(callback):
        callback("/ruta/de/rom_de_prueba.gbc")

    def abrir_explorador_desktop(screen_instance):
        from kivy.uix.filechooser import FileChooserListView
        contenido = BoxLayout(orientation='vertical')
        selector = FileChooserListView(filters=["*.GBC"], path=".")  # Ajusta path si quieres
        btn_select = Button(text="Seleccionar ROM", size_hint_y=None, height="40dp")

        def seleccionar_archivo(instance):
            selected = selector.selection
            if selected and selected[0].endswith(".GBC"):
                screen_instance.rom_path = selected[0]
                screen_instance.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(screen_instance.rom_path)}"
                screen_instance.rom_cargado = True
                popup.dismiss()
            else:
                screen_instance.ids.label_rom.text = "Archivo no válido."

        btn_select.bind(on_release=seleccionar_archivo)
        contenido.add_widget(selector)
        contenido.add_widget(btn_select)

        popup = Popup(title="Selecciona un ROM .gbc",
                      content=contenido,
                      size_hint=(0.9, 0.9))
        popup.open()

class MenuScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    rom_path = StringProperty("")
    current_path = StringProperty(rootpath)

    def copiar_rom_a_storage_interno(self, uri):
        if platform == 'android':
            destino_dir = app_storage_path()
            if not os.path.exists(destino_dir):
                os.makedirs(destino_dir)
            nombre_archivo = "rom_seleccionada.gbc"
            destino_path = os.path.join(destino_dir, nombre_archivo)
            try:
                copiar_desde_uri(uri, destino_path)
                print(f"[INFO] Copiado ROM a storage interno: {destino_path}")
                return destino_path
            except Exception as e:
                print(f"[ERROR] No se pudo copiar ROM: {e}")
                return None
        else:
            return uri

    def abrir_explorador(self):
        def abrir_selector():
            if platform == 'android':
                def cuando_selecciona_archivo(uri):
                    if uri:
                        destino_path = self.copiar_rom_a_storage_interno(uri)
                        if destino_path:
                            self.rom_path = destino_path
                            if self.ids.get("label_rom"):
                                self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(destino_path)}"
                            self.rom_cargado = True
                        else:
                            if self.ids.get("label_rom"):
                                self.ids.label_rom.text = "Error copiando ROM a almacenamiento interno."
                    else:
                        if self.ids.get("label_rom"):
                            self.ids.label_rom.text = "Archivo no válido."
                abrir_selector_nativo(cuando_selecciona_archivo)
            else:
                abrir_explorador_desktop(self)

        solicitar_permisos(callback=abrir_selector)

    def elegir_servidor(self):
        self.servidor_elegido = True
        if self.ids.get("label_servidor"):
            self.ids.label_servidor.text = "Servidor elegido correctamente."

    def iniciar_juego(self):
        if self.ids.get("label_estado"):
            self.ids.label_estado.text = f"¡Iniciando juego con {os.path.basename(self.rom_path)} y servidor elegido!"

        emulator_screen = self.manager.get_screen('emulator')
        emulator_screen.rom_path = self.rom_path

        self.manager.current = 'emulator'
