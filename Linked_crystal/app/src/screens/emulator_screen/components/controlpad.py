from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior

class ImageButton(ButtonBehavior, Image):
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if not self.collide_point(*touch.pos):
                self.dispatch('on_release')
        return super().on_touch_up(touch)

class ControlPad(FloatLayout):
    on_button_press = ObjectProperty(None)
    on_button_release = ObjectProperty(None)

    _pressed_buttons = set()

    def press(self, button_name):
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
