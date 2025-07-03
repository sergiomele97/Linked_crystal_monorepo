from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.properties import StringProperty
from kivy.utils import platform

from pyboy import PyBoy
import threading
import time
import os
from io import BytesIO


# ANDROID ENVIRONMENT VARIABLES ------------------------------------------------------------------
if platform == 'android':
    from android.permissions import request_permissions, Permission

    def solicitar_permisos():
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])

# DESKTOP ENVIRONMENT VARIABLES ------------------------------------------------------------------
else:
    def solicitar_permisos():
        pass


class EmuladorScreen(Screen):

    rom_path = StringProperty("")

    def on_enter(self):
        # Para evitar añadir widgets múltiples veces
        if hasattr(self, 'layout'):
            return

        self.layout = BoxLayout(orientation='vertical')

        # Imagen ocupa la mitad superior
        self.image_widget = Image(size_hint=(1, 0.5), allow_stretch=True, keep_ratio=True)

        # Label ocupa parte inferior (puedes ajustar el size_hint como gustes)
        self.label = Label(text='Iniciando PyBoy…', size_hint=(1, 0.5))

        self.layout.add_widget(self.image_widget)
        self.layout.add_widget(self.label)

        self.add_widget(self.layout)

        threading.Thread(target=self.run_pyboy, daemon=True).start()

    def update_label(self, ticks):
        self.label.text = f'PyBoy\nTicks ejecutados: {ticks}'

    def capture_image(self, pyboy):
        image = pyboy.screen.image
        with BytesIO() as byte_io:
            image.save(byte_io, format='PNG')
            byte_io.seek(0)
            kivy_image = CoreImage(byte_io, ext="png")
        self.image_widget.texture = kivy_image.texture

    def run_pyboy(self):
        solicitar_permisos()
        rom_path = self.rom_path

        if not os.path.exists(rom_path):
            print(f"[ERROR] ROM no encontrada o acceso denegado: {rom_path}")
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', "No se puede acceder al archivo ROM."), 0)
            return

        try:
            pyboy = PyBoy(rom_path, window="null", sound_emulated=True, sound=True)
            pyboy.set_emulation_speed(1)
        except Exception as e:
            print(f"[ERROR] PyBoy no pudo cargar el ROM: {e}")
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', "Error al cargar el ROM."), 0)
            return

        print(f"[INFO] ROM cargada desde: {rom_path}")

        ticks = 0
        last_time = time.time()

        def emular(dt):
            nonlocal ticks, last_time
            if pyboy.tick():
                ticks += 1
                # Capturar la imagen actual cada tick
                Clock.schedule_once(lambda dt: self.capture_image(pyboy), 0)

                current_time = time.time()
                if current_time - last_time >= 1:
                    Clock.schedule_once(lambda dt, t=ticks: self.update_label(t), 0)
                    last_time = current_time
            else:
                pyboy.stop(save=False)
                print("[PyBoy] Emulación finalizada")
                Clock.schedule_once(lambda dt: setattr(self.label, 'text', "Emulación finalizada"), 0)


        Clock.schedule_interval(emular, 1 / 60)
        Clock.schedule_once(lambda dt: self.capture_image(pyboy), 5)
