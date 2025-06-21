from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.resources import resource_find

from pyboy import PyBoy
import threading
import time
import os
from io import BytesIO

ROM_FILENAME = "PandorasBlocks.GBC"

class MiApp(App):
    def build(self):
        self.label = Label(text='Iniciando PyBoy…')
        self.image_widget = Image(size_hint=(None, None), size=(320, 288))  # Tamaño típico GBC
        self.layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.image_widget)
        threading.Thread(target=self.run_pyboy, daemon=True).start()
        return self.layout

    def update_label(self, ticks):
        self.label.text = f'PyBoy corriendo\nTicks ejecutados: {ticks}'

    def capture_image(self, pyboy):
        """Captura una imagen del emulador y la muestra en la interfaz de Kivy."""
        image = pyboy.screen.image
        with BytesIO() as byte_io:
            image.save(byte_io, format='PNG')
            byte_io.seek(0)
            kivy_image = CoreImage(byte_io, ext="png")
        self.image_widget.texture = kivy_image.texture

    def run_pyboy(self):
        rom_path = resource_find(ROM_FILENAME)

        if rom_path is None or not os.path.exists(rom_path):
            error_msg = f"[ERROR] ROM no encontrada: {ROM_FILENAME}"
            print(error_msg)
            Clock.schedule_once(lambda dt: self.label.setter('text')(self.label, error_msg), 0)
            return

        print(f"[INFO] ROM encontrada en: {rom_path}")

        pyboy = PyBoy(rom_path, window="null", sound_emulated=True, sound=True)  # Inicia PyBoy sin ventana
        ticks = 0
        last_time = time.time()

        def emular(dt):
            nonlocal ticks, last_time
            if pyboy.tick():
                ticks += 1
                current_time = time.time()
                if current_time - last_time >= 1:
                    Clock.schedule_once(lambda dt, t=ticks: self.update_label(t), 0)
                    last_time = current_time
            else:
                pyboy.stop(save=False)
                print("[PyBoy] Emulación finalizada")
                Clock.schedule_once(lambda dt: self.label.setter('text')(self.label, "Emulación finalizada"), 0)

        Clock.schedule_interval(emular, 1/60)
        Clock.schedule_once(lambda dt: self.capture_image(pyboy), 5)

if __name__ == '__main__':
    MiApp().run()
