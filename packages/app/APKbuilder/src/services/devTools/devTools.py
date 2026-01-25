from kivy.utils import platform
import os

if platform == 'android':
    from android.storage import app_storage_path


class DevTools:
    def listInternalStorageContent(self, father_screen):
        """Lista archivos en almacenamiento interno y los muestra en el label del padre."""
        if platform == 'android':
            destino_dir = app_storage_path()
        else:
            destino_dir = "."  

        try:
            archivos = os.listdir(destino_dir)
            print(f"[TEST] Contenido de {destino_dir}: {archivos}")

            father_screen.ids.output_label.text = (
                f"Archivos en storage interno:\n{archivos}"
            )
        except Exception as e:
            print(f"[ERROR] No se pudo listar: {e}")
            menu_screen.ids.output_label.text = f"Error al listar: {e}"
