from kivy.uix.floatlayout import FloatLayout
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from io import BytesIO

class VideoDisplay(FloatLayout):

    def on_kv_post(self, base_widget):
        self.image_widget = self.ids.emu_image
        self.label = self.ids.label

    def display_message(self, message):
        self.label.text = message

    def update_frame(self, image):
        with BytesIO() as byte_io:
            image.save(byte_io, format='PNG')
            byte_io.seek(0)
            kivy_image = CoreImage(byte_io, ext="png")
        Clock.schedule_once(lambda dt: setattr(self.image_widget, 'texture', kivy_image.texture), 0)
