from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty

class ControlPad(FloatLayout):
    on_button_press = ObjectProperty(None)
    on_button_release = ObjectProperty(None)

    def press(self, button_name):
        if self.on_button_press:
            self.on_button_press(button_name)

    def release(self, button_name):
        if self.on_button_release:
            self.on_button_release(button_name)
