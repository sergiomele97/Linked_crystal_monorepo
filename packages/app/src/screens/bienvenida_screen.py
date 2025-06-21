from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button
from kivy.properties import StringProperty, BooleanProperty
import os

Builder.load_file("screens/bienvenida_screen.kv")

class BienvenidaScreen(Screen):
    rom_cargado = BooleanProperty(False)
    servidor_elegido = BooleanProperty(False)
    rom_path = StringProperty("")

    def abrir_explorador(self):
        contenido = BoxLayout(orientation='vertical')
        selector = FileChooserListView(filters=["*.gbc", "*.GBC"], path="/")
        btn_select = Button(text="Seleccionar ROM", size_hint_y=None, height="40dp")

        def seleccionar_archivo(instance):
            selected = selector.selection
            if selected and selected[0].lower().endswith(".gbc"):
                self.rom_path = selected[0]
                self.ids.label_rom.text = f"ROM seleccionada:\n{os.path.basename(self.rom_path)}"
                self.rom_cargado = True
                popup.dismiss()
            else:
                self.ids.label_rom.text = "Archivo no válido."

        btn_select.bind(on_release=seleccionar_archivo)
        contenido.add_widget(selector)
        contenido.add_widget(btn_select)

        popup = Popup(title="Selecciona un ROM .gbc",
                      content=contenido,
                      size_hint=(0.9, 0.9))
        popup.open()

    def elegir_servidor(self):
        self.servidor_elegido = True
        self.ids.label_servidor.text = "Servidor elegido correctamente."

    def iniciar_juego(self):
        if self.rom_cargado and self.servidor_elegido:
            self.ids.label_estado.text = f"Iniciando juego con {os.path.basename(self.rom_path)}"
            # Cambiar de pantalla y pasar el path a la otra
            self.manager.get_screen('emulador').rom_path = self.rom_path
            self.manager.current = 'emulador'
        else:
            self.ids.label_estado.text = "Falta seleccionar ROM o servidor."
