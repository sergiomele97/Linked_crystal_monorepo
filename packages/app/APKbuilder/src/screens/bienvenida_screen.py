from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.utils import platform
import os

Builder.load_file("screens/bienvenida_screen.kv")

# ANDROID ENVIRONMENT VARIABLES ------------------------------------------------------------------
if platform == 'android':
    rootpath = "/storage/emulated/0/"
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast
    from android import activity

    def solicitar_permisos():
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    DocumentsContract = autoclass('android.provider.DocumentsContract')
    File = autoclass('java.io.File')

    def abrir_selector_nativo(callback):
        def on_activity_result(requestCode, resultCode, intent_data):
            if requestCode == 1:
                activity.unbind(on_activity_result=on_activity_result)  # Desvincular
                if resultCode == -1 and intent_data is not None:
                    uri = intent_data.getData()
                    path = obtener_ruta_real(uri)
                    if path:
                        callback(path)
                    else:
                        print("No se pudo obtener la ruta real del archivo.")
                else:
                    print("Selección cancelada o sin datos.")

        activity.bind(on_activity_result=on_activity_result)

        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("*/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.startActivityForResult(intent, 1)

    def obtener_ruta_real(uri):
        try:
            path = None
            # Intenta obtener path real desde content uri
            from android.storage import primary_external_storage_path
            DocumentFile = autoclass("androidx.documentfile.provider.DocumentFile")
            path = uri.getPath()
            if path.startswith("/document/primary:"):
                return os.path.join(primary_external_storage_path(), path.split(":")[1])
        except Exception as e:
            print("Error al obtener ruta:", e)
        return None

# DESKTOP ENVIRONMENT VARIABLES ------------------------------------------------------------------
else:
    rootpath = "/"
    def solicitar_permisos():
        pass

    def abrir_selector_nativo(callback):
        # Para escritorio: usa una ruta fija de prueba
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


# BienvenidaScreen CLASS ------------------------------------------------------------------
class BienvenidaScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    rom_path = StringProperty("")
    current_path = StringProperty(rootpath)

    def abrir_explorador(self):
        solicitar_permisos()

        if platform == 'android':
            def cuando_selecciona_archivo(path):
                if path and path.lower().endswith(".gbc"):
                    self.rom_path = path
                    if self.ids.get("label_rom"):
                        self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(path)}"
                    self.rom_cargado = True
                else:
                    if self.ids.get("label_rom"):
                        self.ids.label_rom.text = "Archivo no válido."
            abrir_selector_nativo(cuando_selecciona_archivo)
        else:
            abrir_explorador_desktop(self)

    def elegir_servidor(self):
        self.servidor_elegido = True
        if self.ids.get("label_servidor"):
            self.ids.label_servidor.text = "Servidor elegido correctamente."

    def iniciar_juego(self):
        if self.ids.get("label_estado"):
            self.ids.label_estado.text = f"¡Iniciando juego con {os.path.basename(self.rom_path)} y servidor elegido!"

        emulador_screen = self.manager.get_screen('emulador')
        emulador_screen.rom_path = self.rom_path  # <- Aquí se pasa el ROM

        self.manager.current = 'emulador'
