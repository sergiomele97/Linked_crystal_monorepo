from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior

class ImageButton(ButtonBehavior, Image):
    pass

class ControlPad(FloatLayout):
    on_button_press = ObjectProperty(None)
    on_button_release = ObjectProperty(None)

    # Mantener un estado interno para los botones presionados
    _pressed_buttons = set()

    def press(self, button_name):
        # Solo registrar si no está ya presionado
        if button_name not in self._pressed_buttons:
            self._pressed_buttons.add(button_name)
            if self.on_button_press:
                self.on_button_press(button_name)

    def release(self, button_name):
        if button_name in self._pressed_buttons:
            self._pressed_buttons.remove(button_name)
            if self.on_button_release:
                self.on_button_release(button_name)

    def release_all(self):
        """Liberar todos los botones que puedan haberse quedado pegados."""
        for btn in list(self._pressed_buttons):
            self.release(btn)
