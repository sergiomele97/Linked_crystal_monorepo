from kivy.utils import platform


if platform == 'android':
    from android.permissions import request_permissions, Permission

    def solicitar_permisos():
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])
else:
    def solicitar_permisos():
        # No se necesitan permisos en escritorio
        pass

def inicializar_entorno():
    if platform != 'android':
        from kivy.config import Config
        Config.set('graphics', 'width', '360')
        Config.set('graphics', 'height', '640')
        Config.set('graphics', 'resizable', False)
