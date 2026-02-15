from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock

from screens.emulator_screen.components.chat.message_list import MessageList

class DebugLogView(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.85, 0.5)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.background_color = (0, 0, 0, 0)
        self.auto_dismiss = True

        self._setup_ui()
        self.log_manager = None
        self.bind(on_open=self._on_open)
        self.bind(on_dismiss=self._on_dismiss)

    def _setup_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        with layout.canvas.before:
            Color(0.05, 0.05, 0.05, 0.95)
            self.rect = RoundedRectangle(radius=[15])
        
        layout.bind(pos=self._update_rect, size=self._update_rect)

        self.msg_list = MessageList()
        self.msg_list.scroll_to_bottom = True

        layout.add_widget(self.msg_list)
        self.add_widget(layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def set_log_manager(self, manager):
        self.log_manager = manager

    def _on_open(self, *args):
        if self.log_manager:
            self.msg_list.clear()
            for log_entry in self.log_manager.logs:
                self.msg_list.add_message(log_entry['text'], log_entry['sender'])
            
            self.log_manager.bind(logs=self._on_logs_update)

    def _on_dismiss(self, *args):
        if self.log_manager:
            self.log_manager.unbind(logs=self._on_logs_update)

    def _on_logs_update(self, instance, value):
        if value:
            last = value[-1]
            Clock.schedule_once(
                lambda dt: self.msg_list.add_message(last['text'], last['sender']), 
                0
            )
