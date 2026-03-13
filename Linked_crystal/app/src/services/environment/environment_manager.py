import os
from kivy.utils import platform


if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass

    def solicitar_permisos():
        VERSION = autoclass('android.os.Build$VERSION')
        SDK_INT = VERSION.SDK_INT
        
        # In Android 13+ (API 33+), READ_EXTERNAL_STORAGE is deprecated for non-media files.
        if SDK_INT >= 33:
            return

        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])
else:
    def solicitar_permisos():
        pass

def inicializar_entorno():
    import logging
    logging.getLogger("websockets").setLevel(logging.CRITICAL)
    logging.getLogger("websockets.protocol").setLevel(logging.CRITICAL)
    logging.getLogger("websockets.client").setLevel(logging.CRITICAL)
    logging.getLogger("websockets.server").setLevel(logging.CRITICAL)

    import os
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()

    if platform != 'android':
        from kivy.config import Config
        Config.set('graphics', 'width', '360')
        Config.set('graphics', 'height', '640')
        Config.set('graphics', 'resizable', False)
