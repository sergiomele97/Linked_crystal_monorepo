from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock

class ChatInterface:
    def __init__(self, father_screen):
        self.father_screen = father_screen
        self.view = None
        self.messages = []

    def mostrar_chat(self):
        if self.view:
            self.view.open()
            return
        
        # Using ModalView for better focus and touch management
        self.view = ModalView(
            size_hint=(0.85, 0.5),
            pos_hint={"center_x": 0.5, "center_y": 0.6},
            background_color=(0, 0, 0, 0), # Transparent background for the modal itself
            auto_dismiss=True
        )

        # Main container
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Background for the layout
        with layout.canvas.before:
            Color(0.1, 0.1, 0.1, 0.95)
            self.rect_fondo = RoundedRectangle(
                pos=layout.pos,
                size=layout.size,
                radius=[15]
            )
        layout.bind(pos=self._update_rect, size=self._update_rect)

        # ScrollView for messages
        self.scroll = ScrollView(size_hint=(1, 0.8), do_scroll_x=False)
        
        # AnchorLayout ensures messages are pinned at the bottom when there are few
        self.anchor = AnchorLayout(anchor_y='bottom', size_hint_y=None)
        
        self.messages_layout = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=8,
            padding=[5, 10]
        )
        self.messages_layout.bind(minimum_height=self.messages_layout.setter('height'))
        
        self.anchor.add_widget(self.messages_layout)
        self.scroll.add_widget(self.anchor)
        layout.add_widget(self.scroll)

        # Bind heights to update anchor height
        self.scroll.bind(height=self._update_anchor_height)
        self.messages_layout.bind(height=self._update_anchor_height)

        # Input area
        input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)
        
        self.text_input = TextInput(
            multiline=False,
            hint_text="Escribe un mensaje...",
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            padding=(10, 10),
            font_size=16
        )
        self.text_input.bind(on_text_validate=self.enviar_mensaje)
        
        btn_enviar = Button(
            text="Send",
            size_hint=(0.25, 1),
            background_color=(0.2, 0.6, 1, 1),
            bold=True
        )
        btn_enviar.bind(on_release=self.enviar_mensaje)
        
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(btn_enviar)
        
        layout.add_widget(input_layout)
        
        self.view.add_widget(layout)
        
        # Focus management
        self.view.bind(on_open=self._on_open)
        self.view.open()

    def _on_open(self, instance):
        # Focus on text input with a small delay for PC
        Clock.schedule_once(lambda dt: self._set_focus(), 0.1)

    def _set_focus(self):
        self.text_input.focus = True

    def _update_rect(self, instance, value):
        self.rect_fondo.pos = instance.pos
        self.rect_fondo.size = instance.size

    def _update_anchor_height(self, *args):
        self.anchor.height = max(self.scroll.height, self.messages_layout.height)

    def enviar_mensaje(self, *args):
        msg = self.text_input.text.strip()
        if msg:
            self.agregar_mensaje(msg, sender="Tú")
            self.text_input.text = ""
            # Here we would send it to the server in the future
            print(f"Chat: {msg}")
        
        # Regain focus after sending
        Clock.schedule_once(lambda dt: self._set_focus(), 0.05)

    def agregar_mensaje(self, text, sender="Sistema"):
        full_text = f"[b]{sender}:[/b] {text}"
        
        # Label with markup for bold sender and text wrapping
        lbl = Label(
            text=full_text,
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="top",
            color=(1, 1, 1, 1),
            padding=(10, 5)
        )
        
        # Important for wrapping: bind width and update height based on texture
        lbl.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        self.messages_layout.add_widget(lbl)
        
        # Scroll to bottom after layout update
        Clock.schedule_once(self._scroll_to_bottom, 0.1)

    def _scroll_to_bottom(self, dt=None):
        if self.scroll.height < self.messages_layout.height:
            self.scroll.scroll_y = 0

    def cerrar_chat(self):
        if self.view:
            self.view.dismiss()
