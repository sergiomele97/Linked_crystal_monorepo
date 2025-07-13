from kivy.utils import platform
import os


# Android ----------------------------------------------------------------------------------------
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android import activity
    from jnius import autoclass, cast
    from android.storage import app_storage_path

    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')

    def solicitar_permisos(callback=None):
        def permisos_callback(permissions, grants):
            if all(grants) and callback:
                callback()
            else:
                print("[ERROR] Permisos no concedidos")
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE], permisos_callback)

    def abrir_selector_nativo(callback):
        def on_activity_result(requestCode, resultCode, intent_data):
            if requestCode == 1:
                activity.unbind(on_activity_result=on_activity_result)
                if resultCode == -1 and intent_data is not None:
                    callback(intent_data.getData())
                else:
                    callback(None)
        activity.bind(on_activity_result=on_activity_result)
        intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.setType("*/*")
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        currentActivity.startActivityForResult(intent, 1)

    def copiar_desde_uri(uri, destino_path):
        ContentResolver = PythonActivity.mActivity.getContentResolver()
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

    def copiar_rom_a_storage_interno(uri):
        destino_dir = app_storage_path()
        os.makedirs(destino_dir, exist_ok=True)
        destino_path = os.path.join(destino_dir, "rom_seleccionada.gbc")
        try:
            copiar_desde_uri(uri, destino_path)
            print(f"[INFO] Copiado ROM a: {destino_path}")
            return destino_path
        except Exception as e:
            print(f"[ERROR] No se pudo copiar: {e}")
            return None

    def abrir_explorador_desktop(screen_instance):
        pass  # No usado en Android


# Desktop ----------------------------------------------------------------------------------------
else:
    def solicitar_permisos(callback=None):
        if callback:
            callback()

    def abrir_selector_nativo(callback):
        callback("/ruta/de/rom_de_prueba.gbc")

    def copiar_desde_uri(uri, destino_path):
        pass  # No necesario en desktop

    def copiar_rom_a_storage_interno(uri):
        return uri  # El path ya es usable directamente

    def abrir_explorador_desktop(screen_instance):
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button

        contenido = BoxLayout(orientation='vertical')
        selector = FileChooserListView(filters=["*.GBC", "*.gbc"], path=".")
        btn_select = Button(text="Seleccionar ROM", size_hint_y=None, height="40dp")

        def seleccionar_archivo(instance):
            selected = selector.selection
            if selected and selected[0].lower().endswith(".gbc"):
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


# Global export ----------------------------------------------------------------------------------------
def select_rom(screen_instance, callback):
    def handle_selection(uri):
        if uri:
            path = copiar_rom_a_storage_interno(uri)
            callback(path)
        else:
            callback(None)

    solicitar_permisos(lambda: abrir_selector_nativo(handle_selection)
                        if platform == 'android'
                        else abrir_explorador_desktop(screen_instance))
