from env import ENV
from kivy.app import App

LOG_BUFFER = []

def log(message):
    """
    Logs a message to the console and the debug log manager if in local/development environment.
    """
    global LOG_BUFFER
    if ENV in ["local", "desarrollo"]:
        print(message)
        
        # Buffer the message
        LOG_BUFFER.append(message)
        
        # Try to find the debug_log_manager and flush buffer
        app = App.get_running_app()
        if app and hasattr(app, "root") and app.root:
            manager = None
            # Check GlobalLayout structure (self.sm is the ScreenManager)
            if hasattr(app.root, "sm"):
                try:
                    emu_screen = app.root.sm.get_screen('emulator')
                    if emu_screen and hasattr(emu_screen, "debug_log_manager"):
                        manager = emu_screen.debug_log_manager
                except:
                    pass
            
            if manager:
                # Flush buffer to manager
                for msg in LOG_BUFFER:
                    manager.add_log(msg)
                LOG_BUFFER = []
