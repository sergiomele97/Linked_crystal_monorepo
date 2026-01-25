from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.app import App
from kivy.clock import Clock

class ChatInput(BoxLayout):
    def __init__(self, send_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, 0.2)
        self.spacing = 10
        self.send_callback = send_callback

        self.text_input = TextInput(
            multiline=False,
            hint_text="Escribe un mensaje...",
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            padding=(10, 10),
            font_size=16
        )
        self.text_input.bind(on_text_validate=self.on_send)
        
        self.btn_enviar = Button(
            text="Send",
            size_hint=(0.25, 1),
            background_color=(0.2, 0.6, 1, 1),
            bold=True
        )
        self.btn_enviar.bind(on_release=self.on_send)
        
        self.add_widget(self.text_input)
        self.add_widget(self.btn_enviar)

    def on_send(self, *args):
        text = self.text_input.text
        if self.send_callback(text):
            self.text_input.text = ""
        Clock.schedule_once(lambda dt: setattr(self.text_input, 'focus', True), 0.1)

    def focus(self):
        self.text_input.focus = True
