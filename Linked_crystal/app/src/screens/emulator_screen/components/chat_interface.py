from screens.emulator_screen.components.chat.chat_view import ChatView

class ChatInterface:
    def __init__(self, father_screen):
        self.father_screen = father_screen
        self.view = None
        
    def mostrar_chat(self):
        if not self.view:
            self.view = ChatView()
            if hasattr(self.father_screen, "chat_manager"):
                self.view.set_chat_manager(self.father_screen.chat_manager)
        self.view.open()
