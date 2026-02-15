from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App
from kivy.clock import Clock

from screens.emulator_screen.components.chat.chat_input import ChatInput
from screens.emulator_screen.components.chat.message_list import MessageList

class ChatView(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.85, 0.5)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.7}
        self.background_color = (0, 0, 0, 0)
        self.auto_dismiss = True

        self._setup_ui()
        self.chat_manager = None
        self.bind(on_open=self._on_open)
        self.bind(on_dismiss=self._on_dismiss)

    def _setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        with layout.canvas.before:
            Color(0.1, 0.1, 0.1, 0.95)
            self.rect = RoundedRectangle(radius=[15])
        
        layout.bind(pos=self._update_rect, size=self._update_rect)

        self.msg_list = MessageList()
        self.chat_input = ChatInput(send_callback=self._send_message)

        layout.add_widget(self.msg_list)
        layout.add_widget(self.chat_input)
        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def set_chat_manager(self, manager):
        self.chat_manager = manager

    def _on_open(self, *args):
        if self.chat_manager:
            self.msg_list.clear() 
            for msg in self.chat_manager.messages:
                self.msg_list.add_message(msg['text'], msg['sender'])
            
            self.chat_manager.bind(messages=self._on_messages_update)

        Clock.schedule_once(lambda dt: self.chat_input.focus(), 0.1)

    def _on_dismiss(self, *args):
        if self.chat_manager:
            self.chat_manager.unbind(messages=self._on_messages_update)

    def _on_messages_update(self, instance, value):
        if value:
            last = value[-1]
            Clock.schedule_once(
                lambda dt: self.msg_list.add_message(last['text'], last['sender']), 
                0
            )

    def _send_message(self, text):
        if text.strip() and self.chat_manager:
            self.chat_manager.send_message(text)
            return True
        return False
