from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.utils import platform
import os

Builder.load_file("screens/bienvenida_screen.kv")

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

else:
    rootpath = ""
    def solicitar_permisos():
        pass

    def abrir_selector_nativo(callback):
        # Para escritorio: usa una ruta fija de prueba
        callback("/ruta/de/rom_de_prueba.gbc")


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
            popup = self._crear_popup_explorador()
            popup.open()

    def _crear_popup_explorador(self):
        contenido = BoxLayout(orientation='vertical')
        archivos_box = BoxLayout(orientation='vertical', size_hint_y=0.9)
        nav_box = BoxLayout(size_hint_y=None, height="40dp")

        btn_up = Button(text="Subir carpeta", size_hint_x=0.3)
        btn_ruta = Button(text=self.current_path, size_hint_x=0.7, disabled=True)

        popup = Popup(title="Selecciona un ROM .gbc",
                      content=contenido,
                      size_hint=(0.9, 0.9))

        def actualizar_lista():
            archivos_box.clear_widgets()
            btn_ruta.text = self.current_path
            try:
                elementos = os.listdir(self.current_path)
            except Exception:
                elementos = []
            elementos.sort()
            carpetas = [e for e in elementos if os.path.isdir(os.path.join(self.current_path, e))]
            archivos = [e for e in elementos if os.path.isfile(os.path.join(self.current_path, e))]

            for carpeta in carpetas:
                btn = Button(text=f"[CARPETA] {carpeta}", halign="left", markup=True, size_hint_y=None, height="40dp")
                def ir_carpeta(inst, carpeta=carpeta):
                    self.current_path = os.path.join(self.current_path, carpeta)
                    actualizar_lista()
                btn.bind(on_release=ir_carpeta)
                archivos_box.add_widget(btn)

            for archivo in archivos:
                btn = Button(text=archivo, halign="left", size_hint_y=None, height="40dp")
                def seleccionar(inst, archivo=archivo):
                    path_archivo = os.path.join(self.current_path, archivo)
                    if archivo.lower().endswith(".gbc"):
                        self.rom_path = path_archivo
                        if self.ids.get("label_rom"):
                            self.ids.label_rom.text = f"ROM seleccionada:\n{archivo}"
                        self.rom_cargado = True
                        popup.dismiss()
                    else:
                        if self.ids.get("label_rom"):
                            self.ids.label_rom.text = "Archivo no válido."
                btn.bind(on_release=seleccionar)
                archivos_box.add_widget(btn)

            btn_up.disabled = (self.current_path == rootpath or self.current_path == "")

        def subir_carpeta(instance):
            if self.current_path and self.current_path != rootpath:
                self.current_path = os.path.dirname(self.current_path)
                actualizar_lista()

        btn_up.bind(on_release=subir_carpeta)

        nav_box.add_widget(btn_up)
        nav_box.add_widget(btn_ruta)

        contenido.add_widget(nav_box)
        contenido.add_widget(archivos_box)

        actualizar_lista()

        return popup

    def elegir_servidor(self):
        self.servidor_elegido = True
        if self.ids.get("label_servidor"):
            self.ids.label_servidor.text = "Servidor elegido correctamente."

    def iniciar_juego(self):
        if self.ids.get("label_estado"):
            self.ids.label_estado.text = f"¡Iniciando juego con {os.path.basename(self.rom_path)} y servidor elegido!"
        self.manager.current = 'emulador'
