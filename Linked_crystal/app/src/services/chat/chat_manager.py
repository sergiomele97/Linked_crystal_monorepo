from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from kivy.app import App

class ChatManager(EventDispatcher):
    messages = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def receive_message(self, sender_id, text):
        """Called by ConnectionLoop when a message arrives."""
        sender_name = f"Jugador {sender_id}"
        self.add_message(text, sender=sender_name)

    def send_message(self, text):
        """Called by ChatInterface to send a message."""
        text = text.strip()
        if not text:
            return

        self.add_message(text, sender="Tú")

        app = App.get_running_app()
        if hasattr(app, "connection_manager"):
            app.connection_manager.connectionLoop.send_chat(text)

    def add_message(self, text, sender="Sistema"):
        """Internal method to append to the list."""
        self.messages.append({"sender": sender, "text": text})
