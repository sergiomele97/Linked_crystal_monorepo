from kivy.event import EventDispatcher
from kivy.properties import ListProperty

class DebugLogManager(EventDispatcher):
    logs = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def add_log(self, text):
        """Adds a message to the debug log history."""
        # Using the same format as ChatManager for compatibility with MessageList if possible
        # or at least a similar structure.
        self.logs.append({"sender": "Debug", "text": text})
