from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle

from kivy.app import App
from kivy.metrics import sp


class LinkInterface:
    def __init__(self, father_screen):
        self.father_screen = father_screen
        self.teclado_visible = False
        self.numero_actual = ""

    def mostrar_teclado_link(self):
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

        self.lbl_your_id = Label(
            text=f"Your ID: {App.get_running_app().appData.userID}",
            size_hint=(1, 0.1),
            pos_hint={"x": 0.05, "y": 0.9},
            halign="left",
            valign="middle",
            font_size=sp(15),
            color=(0.8, 0.9, 1, 1)
        )
        self.lbl_your_id.bind(size=self.lbl_your_id.setter("text_size"))
        self.teclado.add_widget(self.lbl_your_id)

        self.spinner = Image(
            source="resources/image/spinner.zip",
            size_hint=(0.12, 0.12),
            pos_hint={"right": 0.97, "top": 0.97},
            allow_stretch=True,
            keep_ratio=True,
            anim_delay=0.05,
            opacity=0
        )
        self.teclado.add_widget(self.spinner)

        self.lbl_msg = Label(
            text="Enter the other player's ID:",
            size_hint=(1, 0.08),
            pos_hint={"x": 0.05, "y": 0.82},
            halign="left",
            valign="middle",
            font_size=sp(15),
            color=(1, 1, 1, 1)
        )
        self.lbl_msg.bind(size=self.lbl_msg.setter("text_size"))
        self.teclado.add_widget(self.lbl_msg)

        self.display = Label(
            text="",
            size_hint=(1, 0.12),
            pos_hint={"x": 0.05, "y": 0.68},
            halign="left",
            valign="middle",
            font_size=sp(15),
            color=(1, 1, 0.8, 1)
        )
        self.display.bind(size=self.display.setter("text_size"))
        self.teclado.add_widget(self.display)

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
                pos_hint={"x": x, "y": y},
                background_color=(0.25, 0.55, 0.8, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=self.pulsar_numero)
            self.teclado.add_widget(btn)

        btn_clear = Button(
            text="CLEAR",
            size_hint=(btn_w, btn_h),
            pos_hint={"x": 0.08, "y": 0.08},
            background_color=(0.75, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        btn_clear.bind(on_release=self.borrar_numero)
        self.teclado.add_widget(btn_clear)

        btn_zero = Button(
            text="0",
            size_hint=(btn_w, btn_h),
            pos_hint={"x": 0.36, "y": 0.08},
            background_color=(0.25, 0.55, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        btn_zero.bind(on_release=self.pulsar_numero)
        self.teclado.add_widget(btn_zero)

        btn_connect = Button(
            text="CONNECT",
            size_hint=(btn_w, btn_h),
            pos_hint={"x": 0.64, "y": 0.08},
            background_color=(0.3, 0.8, 0.4, 1),
            color=(1, 1, 1, 1)
        )
        btn_connect.bind(on_release=self.confirmar_numero)
        self.teclado.add_widget(btn_connect)

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
        if not self.numero_actual:
            return

        print(f"Connect pressed. Other ID: {self.numero_actual}")
        self.spinner.opacity = 1
        
        app = App.get_running_app()
        my_id = app.appData.userID
        target_id = int(self.numero_actual)

        try:
            manager = app.connection_manager 
            full_url = manager.connectionLoop.get_url_callback() 
            
            if not full_url:
                print("Error: No hay un servidor seleccionado")
                return

            clean_address = full_url.replace("ws://", "").replace("wss://", "").split("/")[0]
            
            if ":" in clean_address:
                host, port = clean_address.split(":")
                port = int(port)
            else:
                host = clean_address
                port = 8080 

            self.father_screen.emulator.connect_link(
                my_id=my_id,
                target_id=target_id,
                host=host,
                port=port
            )
            
        except AttributeError as e:
            print(f"Error de referencia: Asegúrate de que app.connection_manager existe. {e}")
        except Exception as e:
            print(f"Error al conectar Link: {e}")
        
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
