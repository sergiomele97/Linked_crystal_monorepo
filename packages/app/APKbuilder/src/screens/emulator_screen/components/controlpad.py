from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior

class ImageButton(ButtonBehavior, Image):
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            # Si el touch estaba "agarrado" por este botón (porque pulsamos dentro),
            # nos aseguramos de que al soltar el dedo SIEMPRE se libere el botón,
            # incluso si arrastramos el dedo fuera del área del botón.
            if not self.collide_point(*touch.pos):
                self.dispatch('on_release')
        return super().on_touch_up(touch)

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
