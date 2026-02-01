from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from services.devTools.devTools import DevTools

from screens.emulator_screen.components.link_interface import LinkInterface
from screens.emulator_screen.components.debug_log_interface import DebugLogInterface
from env import ENV


class MenuDropdown(FloatLayout):
    father_screen = ObjectProperty(None)
    devTools = DevTools()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.3, 0.5)
        self.pos_hint = {"x": 0.65, "y": 0.05}
        self.build_content()
        self.teclado_visible = False

    def build_content(self):
        btn1 = Button(
            text="Save RAM",
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0.7},
            background_color=(0.25, 0.55, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        btn1.bind(on_release=self.opcion1)
        self.add_widget(btn1)

        btn2 = Button(
            text="Link",
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0.35},
            background_color=(0.25, 0.55, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        btn2.bind(on_release=self.opcion2)
        self.add_widget(btn2)

        if ENV in ["local", "desarrollo"]:
            btn3 = Button(
                text="Debug logs",
                size_hint=(1, 0.3),
                pos_hint={"x": 0, "y": 0},
                background_color=(0.25, 0.55, 0.8, 1),
                color=(1, 1, 1, 1)
            )
            btn3.bind(on_release=self.opcion3)
            self.add_widget(btn3)

    # ---------------- FUNCIONES ---------------- #

    def opcion1(self, *args):
        self.father_screen.emulator.save_RAM()
        self.close()

    def opcion2(self, *args):
        if self.teclado_visible:
            self.cerrar_teclado()
        self.close()
        # Abrir la interfaz Link
        self.link_interface = LinkInterface(father_screen=self.father_screen)
        self.link_interface.mostrar_teclado_link()
        self.teclado_visible = True

    def opcion3(self, *args):
        self.close()
        self.debug_log_interface = DebugLogInterface(father_screen=self.father_screen)
        self.debug_log_interface.mostrar_logs()

    def cerrar_teclado(self):
        if self.teclado_visible:
            self.teclado_visible = False
            if hasattr(self, 'link_interface'):
                self.link_interface.cerrar_teclado()

    # ---------------- DROPDOWN ---------------- #

    def open(self, caller=None):
        if not self.parent:
            self.father_screen.add_widget(self)
        self.father_screen.bind(on_touch_down=self._on_touch_down_outside)

    def close(self, *args):
        if self.parent:
            self.father_screen.remove_widget(self)
        if self.father_screen:
            self.father_screen.unbind(on_touch_down=self._on_touch_down_outside)

    def _on_touch_down_outside(self, instance, touch):
        if not self.collide_point(*touch.pos):
            self.close()
            return True
        return False
