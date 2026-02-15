from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from services.logger import log


class VideoDisplay(FloatLayout):
    def on_kv_post(self, base_widget):
        self.image_widget = self.ids.emu_image
        self._texture = None  

    def display_message(self, message):
        log(message)

    def update_frame(self, arr):
        """Recibe un numpy.ndarray (h, w, 4) con RGBA"""
        h, w, _ = arr.shape

        if self._texture is None:
            self._texture = Texture.create(size=(w, h), colorfmt="rgba")
            self._texture.flip_vertical()
            self.image_widget.texture = self._texture  

        self._texture.blit_buffer(arr.tobytes(), colorfmt="rgba", bufferfmt="ubyte")

        Clock.schedule_once(lambda dt: self.image_widget.canvas.ask_update(), 0)
