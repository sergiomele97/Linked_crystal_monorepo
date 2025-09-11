from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty

class MenuDropdown(FloatLayout):
    menu_screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.3, 0.4)
        self.pos_hint = {"x": 0.65, "y": 0.5}
        self.build_content()

    def build_content(self):
        btn1 = Button(text="Opción 1", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.7})
        btn1.bind(on_release=self.opcion1)
        self.add_widget(btn1)

        btn2 = Button(text="Opción 2", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.4})
        btn2.bind(on_release=self.opcion2)
        self.add_widget(btn2)

        btn3 = Button(text="Cerrar", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.1})
        btn3.bind(on_release=self.close)
        self.add_widget(btn3)

    def open(self, caller=None):
        if not self.parent: 
            self.menu_screen.add_widget(self)
        self.menu_screen.bind(on_touch_down=self._on_touch_down_outside)

    def close(self, *args):
        if self.parent:  
            self.menu_screen.remove_widget(self)
        if self.menu_screen:
            self.menu_screen.unbind(on_touch_down=self._on_touch_down_outside)

    def opcion1(self, *args):
        print("Opción 1 seleccionada")
        self.close()

    def opcion2(self, *args):
        print("Opción 2 seleccionada")
        self.close()

    def _on_touch_down_outside(self, instance, touch):
        if not self.collide_point(*touch.pos):
            self.close()
            return True 
        return False
