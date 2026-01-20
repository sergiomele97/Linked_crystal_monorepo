from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock

class ChatInterface:
    def __init__(self, father_screen):
        self.father_screen = father_screen
        self.chat_visible = False
        self.messages = []

    def mostrar_chat(self):
        if self.chat_visible:
            return
        
        self.chat_visible = True
        
        # Main container with some transparency
        self.layout = FloatLayout(
            size_hint=(0.8, 0.5),
            pos_hint={"center_x": 0.5, "center_y": 0.6}
        )

        # Background
        with self.layout.canvas.before:
            Color(0.1, 0.1, 0.1, 0.9)
            self.rect_fondo = RoundedRectangle(
                pos=self.layout.pos,
                size=self.layout.size,
                radius=[15]
            )
        self.layout.bind(pos=self._update_rect, size=self._update_rect)

        # Container for scroll and input
        container = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # ScrollView for messages
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.messages_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.messages_layout.bind(minimum_height=self.messages_layout.setter('height'))
        
        self.scroll.add_widget(self.messages_layout)
        container.add_widget(self.scroll)

        # Input area
        input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=5)
        
        self.text_input = TextInput(
            multiline=False,
            hint_text="Escribe un mensaje...",
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            padding=(10, 10)
        )
        self.text_input.bind(on_text_validate=self.enviar_mensaje)
        
        btn_enviar = Button(
            text="Send",
            size_hint=(0.2, 1),
            background_color=(0.2, 0.6, 1, 1)
        )
        btn_enviar.bind(on_release=self.enviar_mensaje)
        
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(btn_enviar)
        
        container.add_widget(input_layout)
        
        self.layout.add_widget(container)
        
        # Add to screen
        self.father_screen.add_widget(self.layout)
        self.father_screen.bind(on_touch_down=self._cerrar_si_fuera)
        
        # Focus on text input with a small delay for PC
        Clock.schedule_once(lambda dt: self._set_focus(), 0.1)

    def _set_focus(self):
        if self.chat_visible:
            self.text_input.focus = True

    def _update_rect(self, *args):
        self.rect_fondo.pos = self.layout.pos
        self.rect_fondo.size = self.layout.size

    def enviar_mensaje(self, *args):
        msg = self.text_input.text.strip()
        if msg:
            self.agregar_mensaje(f"Tú: {msg}")
            self.text_input.text = ""
            # Here we would send it to the server in the future
            print(f"Chat: {msg}")

    def agregar_mensaje(self, text):
        lbl = Label(
            text=text,
            size_hint_y=None,
            height=30,
            halign="left",
            valign="middle",
            color=(1, 1, 1, 1)
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.messages_layout.add_widget(lbl)
        
        # Scroll to bottom
        self.scroll.scroll_y = 0

    def cerrar_chat(self):
        if self.chat_visible:
            self.father_screen.remove_widget(self.layout)
            self.chat_visible = False
            self.father_screen.unbind(on_touch_down=self._cerrar_si_fuera)

    def _cerrar_si_fuera(self, instance, touch):
        if self.chat_visible and not self.layout.collide_point(*touch.pos):
            self.cerrar_chat()
            return True
        return False
