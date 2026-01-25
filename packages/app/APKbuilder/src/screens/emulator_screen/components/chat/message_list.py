from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.clock import Clock

class MessageList(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 0.8)
        self.do_scroll_x = False

        self.anchor = AnchorLayout(anchor_y='bottom', size_hint_y=None)
        self.layout = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=8,
            padding=[5, 10]
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))
        
        self.anchor.add_widget(self.layout)
        self.add_widget(self.anchor)

        # Bind heights
        self.bind(height=self._update_anchor_height)
        self.layout.bind(height=self._update_anchor_height)

    def _update_anchor_height(self, *args):
        self.anchor.height = max(self.height, self.layout.height)

    def add_message(self, text, sender):
        full_text = f"[b]{sender}:[/b] {text}"
        lbl = Label(
            text=full_text,
            markup=True,
            size_hint_y=None,
            halign="left",
            valign="top",
            color=(1, 1, 1, 1),
            padding=(10, 5)
        )
        lbl.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        self.layout.add_widget(lbl)
        Clock.schedule_once(self._scroll_to_bottom, 0.1)

    def clear(self):
        self.layout.clear_widgets()

    def _scroll_to_bottom(self, dt=None):
        if self.height < self.layout.height:
            self.scroll_y = 0
