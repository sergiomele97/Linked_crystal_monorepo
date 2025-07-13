from kivy.utils import platform


if platform == 'android':
    from android.permissions import request_permissions, Permission

    def solicitar_permisos():
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])

    # Otros imports o funciones específicas Android pueden ir aquí

else:
    from kivy.config import Config

    # Configuraciones para escritorio
    Config.set('graphics', 'width', '360')
    Config.set('graphics', 'height', '640')
    Config.set('graphics', 'resizable', False)

    def solicitar_permisos():
        # No se necesitan permisos en escritorio
        pass
