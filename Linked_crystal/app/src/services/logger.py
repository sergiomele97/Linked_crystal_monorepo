from env import ENV
from kivy.app import App

import threading
from kivy.clock import Clock

LOG_BUFFER = []
LOG_LOCK = threading.Lock()
UI_UPDATE_SCHEDULED = False

def log(message):
    """
    Logs a message to the console and the debug log manager if in local/development environment.
    """
    global LOG_BUFFER, UI_UPDATE_SCHEDULED
    if ENV in ["local", "desarrollo"]:
        print(message)
        
        with LOG_LOCK:
            LOG_BUFFER.append(message)
        
        # Try to find the debug_log_manager
        app = App.get_running_app()
        if not (app and hasattr(app, "root") and app.root):
            return

        manager = None
        if hasattr(app.root, "sm"):
            try:
                emu_screen = app.root.sm.get_screen('emulator')
                if emu_screen and hasattr(emu_screen, "debug_log_manager"):
                    manager = emu_screen.debug_log_manager
            except:
                pass
        
        if manager:
            with LOG_LOCK:
                # Si ya hay una actualización programada, no hacemos nada más.
                # El hilo de la UI vaciará el buffer acumulado cuando despierte.
                if UI_UPDATE_SCHEDULED:
                    return
                UI_UPDATE_SCHEDULED = True
            
            # Forzamos la ejecución en el hilo de la UI
            # Usamos un pequeño delay (0.1s) para agrupar ráfagas de logs (ej. RAM sav)
            def update_logs(dt):
                global UI_UPDATE_SCHEDULED
                with LOG_LOCK:
                    messages_to_log = list(LOG_BUFFER)
                    LOG_BUFFER.clear()
                    UI_UPDATE_SCHEDULED = False
                
                for msg in messages_to_log:
                    manager.add_log(msg)
            
            Clock.schedule_once(update_logs, 0.1)
