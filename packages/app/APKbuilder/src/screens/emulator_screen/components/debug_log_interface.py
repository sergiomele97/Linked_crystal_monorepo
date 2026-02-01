from screens.emulator_screen.components.debug_log.debug_log_view import DebugLogView

class DebugLogInterface:
    def __init__(self, father_screen):
        self.father_screen = father_screen
        self.view = None
        
    def mostrar_logs(self):
        if not self.view:
            self.view = DebugLogView()
            if hasattr(self.father_screen, "debug_log_manager"):
                self.view.set_log_manager(self.father_screen.debug_log_manager)
        self.view.open()
