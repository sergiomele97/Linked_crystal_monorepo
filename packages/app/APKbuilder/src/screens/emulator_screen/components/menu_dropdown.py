from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.graphics import Color, RoundedRectangle

from services.devTools.devTools import DevTools

class MenuDropdown(FloatLayout):
    father_screen = ObjectProperty(None)
    devTools = DevTools()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.3, 0.4)
        self.pos_hint = {"x": 0.65, "y": 0.05}
        self.build_content()
        self.teclado_visible = False

    def build_content(self):
        btn1 = Button(text="Opción 1", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.7})
        btn1.bind(on_release=self.opcion1)
        self.add_widget(btn1)

        btn2 = Button(text="Opción 2", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.4})
        btn2.bind(on_release=self.opcion2)
        self.add_widget(btn2)

    # ---------------- FUNCIONES ---------------- #

    def opcion1(self, *args):
        self.father_screen.emulator.save_RAM()
        self.close()

    def opcion2(self, *args):
        if self.teclado_visible:
            self.cerrar_teclado()
        self.close()
        self.mostrar_teclado_numerico()

    # ---------------- TECLADO NUMÉRICO ---------------- #

    def mostrar_teclado_numerico(self):
        self.numero_actual = ""
        self.teclado_visible = True

        # Teclado más alto para que cubra todos los botones
        self.teclado = FloatLayout(
            size_hint=(0.5, 0.65),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        # Fondo
        with self.teclado.canvas.before:
            Color(0.15, 0.15, 0.2, 0.95)
            self.rect_fondo = RoundedRectangle(pos=self.teclado.pos, size=self.teclado.size, radius=[20])
        self.teclado.bind(pos=self._update_rect, size=self._update_rect)

        # Mensaje superior
        self.label_mensaje = Label(
            text="Enter the other player's ID",
            size_hint=(1, 0.1),
            pos_hint={"x": 0, "y": 0.87},
            font_size=16,
            color=(1, 1, 1, 1)
        )
        self.teclado.add_widget(self.label_mensaje)

        # Display del número
        self.display = Label(
            text="",
            size_hint=(1, 0.15),
            pos_hint={"x": 0, "y": 0.72},
            font_size=32,
            color=(1, 1, 0.8, 1)
        )
        self.teclado.add_widget(self.display)

        # Botones numéricos
        numeros = [
            ("1", 0, 0.48), ("2", 0.33, 0.48), ("3", 0.66, 0.48),
            ("4", 0, 0.32), ("5", 0.33, 0.32), ("6", 0.66, 0.32),
            ("7", 0, 0.16), ("8", 0.33, 0.16), ("9", 0.66, 0.16),
            ("0", 0.33, 0.0),
        ]
        for texto, x, y in numeros:
            btn = Button(
                text=texto,
                size_hint=(0.33, 0.16),
                pos_hint={"x": x, "y": y},
                background_color=(0.2, 0.6, 0.8, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=self.pulsar_numero)
            self.teclado.add_widget(btn)

        # Botón borrar
        btn_borrar = Button(
            text="BORRAR",
            size_hint=(0.33, 0.16),
            pos_hint={"x": 0, "y": 0.0},
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        btn_borrar.bind(on_release=self.borrar_numero)
        self.teclado.add_widget(btn_borrar)

        # Botón enter
        btn_enter = Button(
            text="ENTER",
            size_hint=(0.33, 0.16),
            pos_hint={"x": 0.66, "y": 0.0},
            background_color=(0.3, 0.8, 0.4, 1),
            color=(1, 1, 1, 1)
        )
        btn_enter.bind(on_release=self.confirmar_numero)
        self.teclado.add_widget(btn_enter)

        self.father_screen.bind(on_touch_down=self._cerrar_si_fuera)
        self.father_screen.add_widget(self.teclado)

    def _update_rect(self, *args):
        self.rect_fondo.pos = self.teclado.pos
        self.rect_fondo.size = self.teclado.size

    def pulsar_numero(self, instance):
        if len(self.numero_actual) < 4:
            self.numero_actual += instance.text
            self.display.text = self.numero_actual

    def borrar_numero(self, *args):
        self.numero_actual = self.numero_actual[:-1]
        self.display.text = self.numero_actual

    def confirmar_numero(self, *args):
        print(f"Número introducido: {self.numero_actual}")
        self.cerrar_teclado()

    def cerrar_teclado(self):
        if self.teclado_visible:
            self.father_screen.remove_widget(self.teclado)
            self.teclado_visible = False
            self.father_screen.unbind(on_touch_down=self._cerrar_si_fuera)

    def _cerrar_si_fuera(self, instance, touch):
        if self.teclado_visible and not self.teclado.collide_point(*touch.pos):
            self.cerrar_teclado()
            return True
        return False

    # ---------------- FUNCIONES BASE ---------------- #

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
