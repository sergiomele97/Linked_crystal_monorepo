from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.properties import ObjectProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle

from services.devTools.devTools import DevTools


class MenuDropdown(FloatLayout):
    father_screen = ObjectProperty(None)
    devTools = DevTools()

    your_id = StringProperty("----")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.3, 0.4)
        self.pos_hint = {"x": 0.65, "y": 0.05}
        self.build_content()
        self.teclado_visible = False

    def build_content(self):
        btn1 = Button(
            text="Save RAM",
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0.7}
        )
        btn1.bind(on_release=self.opcion1)
        self.add_widget(btn1)

        btn2 = Button(
            text="Link",
            size_hint=(1, 0.3),
            pos_hint={"x": 0, "y": 0.4}
        )
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
        self.mostrar_teclado_link()

    # ---------------- INTERFAZ LINK ---------------- #

    def mostrar_teclado_link(self):
        self.numero_actual = ""
        self.teclado_visible = True

        self.teclado = FloatLayout(
            size_hint=(1, 0.45),
            pos_hint={"x": 0, "y": 0}
        )

        with self.teclado.canvas.before:
            Color(0.12, 0.12, 0.18, 0.97)
            self.rect_fondo = RoundedRectangle(
                pos=self.teclado.pos,
                size=self.teclado.size,
                radius=[20]
            )
        self.teclado.bind(pos=self._update_rect, size=self._update_rect)

        # ---- YOUR ID ----
        lbl_your_id = Label(
            text=f"Your ID: {self.your_id}",
            size_hint=(1, 0.1),
            pos_hint={"x": 0.05, "y": 0.9},
            halign="left",
            valign="middle",
            font_size=16,
            color=(0.8, 0.9, 1, 1)
        )
        lbl_your_id.bind(size=lbl_your_id.setter("text_size"))
        self.teclado.add_widget(lbl_your_id)

        # ---- SPINNER (VISUAL, SEGURO) ----
        self.spinner = Image(
            source="resources/image/spinner.zip",
            size_hint=(0.12, 0.12),
            pos_hint={"right": 0.97, "top": 0.97},
            allow_stretch=True,
            keep_ratio=True,
            anim_delay=0.05,   # animación normal
            opacity=0          # oculto por defecto
        )
        self.teclado.add_widget(self.spinner)

        # ---- ENTER OTHER ID ----
        lbl_msg = Label(
            text="Enter the other player's ID:",
            size_hint=(1, 0.08),
            pos_hint={"x": 0.05, "y": 0.82},
            halign="left",
            valign="middle",
            font_size=15,
            color=(1, 1, 1, 1)
        )
        lbl_msg.bind(size=lbl_msg.setter("text_size"))
        self.teclado.add_widget(lbl_msg)

        # ---- DISPLAY ----
        self.display = Label(
            text="",
            size_hint=(1, 0.12),
            pos_hint={"x": 0.05, "y": 0.68},
            halign="left",
            valign="middle",
            font_size=28,
            color=(1, 1, 0.8, 1)
        )
        self.display.bind(size=self.display.setter("text_size"))
        self.teclado.add_widget(self.display)

        # ---- BOTONES ----
        btn_w = 0.28
        btn_h = 0.12

        posiciones = [
            ("1", 0.08, 0.50), ("2", 0.36, 0.50), ("3", 0.64, 0.50),
            ("4", 0.08, 0.36), ("5", 0.36, 0.36), ("6", 0.64, 0.36),
            ("7", 0.08, 0.22), ("8", 0.36, 0.22), ("9", 0.64, 0.22),
        ]

        for texto, x, y in posiciones:
            btn = Button(
                text=texto,
                size_hint=(btn_w, btn_h),
                pos_hint={"x": x, "y": y}
            )
            btn.bind(on_release=self.pulsar_numero)
            self.teclado.add_widget(btn)

        # ---- FILA INFERIOR ----
        btn_clear = Button(
            text="CLEAR",
            size_hint=(btn_w, btn_h),
            pos_hint={"x": 0.08, "y": 0.08}
        )
        btn_clear.bind(on_release=self.borrar_numero)
        self.teclado.add_widget(btn_clear)

        btn_zero = Button(
            text="0",
            size_hint=(btn_w, btn_h),
            pos_hint={"x": 0.36, "y": 0.08}
        )
        btn_zero.bind(on_release=self.pulsar_numero)
        self.teclado.add_widget(btn_zero)

        btn_connect = Button(
            text="CONNECT",
            size_hint=(btn_w, btn_h),
            pos_hint={"x": 0.64, "y": 0.08}
        )
        btn_connect.bind(on_release=self.confirmar_numero)
        self.teclado.add_widget(btn_connect)

        self.father_screen.bind(on_touch_down=self._cerrar_si_fuera)
        self.father_screen.add_widget(self.teclado)

    # ---------------- LOGICA ---------------- #

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
        print(f"Connect pressed. Other ID: {self.numero_actual}")
        # SOLO visual
        self.spinner.opacity = 1

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
