from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from io import BytesIO

class VideoDisplay(Image):
    def update_frame(self, pyboy):
        image = pyboy.screen.image
        with BytesIO() as byte_io:
            image.save(byte_io, format='PNG')
            byte_io.seek(0)
            kivy_image = CoreImage(byte_io, ext="png")
        Clock.schedule_once(lambda dt: setattr(self, 'texture', kivy_image.texture), 0)
