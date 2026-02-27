from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.properties import ObjectProperty

from services.devTools.devTools import DevTools

class MenuDropdown(FloatLayout):
    father_screen = ObjectProperty(None)
    devTools = DevTools()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.3, 0.4)
        self.pos_hint = {"x": 0.65, "y": 0.5}
        self.build_content()

    def build_content(self):
        btn1 = Button(text="Opción 1", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.7})
        btn1.bind(on_release=self.opcion1)
        self.add_widget(btn1)

        btn2 = Button(text="Opción 2", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.4})
        btn2.bind(on_release=self.opcion2)
        self.add_widget(btn2)

        # Android-only: Exportar RAM (habilitado en desarrollo también para tests)
        if platform == 'android' or self.devTools:
            btn_export = Button(text="Exportar RAM", size_hint=(1, 0.3), pos_hint={"x": 0, "y": 0.1})
            btn_export.bind(on_release=self.export_ram)
            self.add_widget(btn_export)

    def opcion1(self, *args):
        self.devTools.listInternalStorageContent(self.father_screen)
        self.close()

    def opcion2(self, *args):
        print("Opción 2 seleccionada")
        self.close()

    def export_ram(self, *args):
        # Delegar al father_screen para mantener la lógica en MenuScreen
        try:
            if self.father_screen and hasattr(self.father_screen, 'export_ram'):
                self.father_screen.export_ram()
        except Exception:
            pass
        self.close()

    def open(self, caller=None):
        if not self.parent: 
            self.father_screen.add_widget(self)
        self.father_screen.bind(on_touch_down=self._on_touch_down_outside)

    def close(self, *args):
        if self.parent:  
            self.father_screen.remove_widget(self)
        if self.father_screen:
            self.father_screen.unbind(on_touch_down=self._on_touch_down_outside)

    def _on_touch_down_outside(self, instance, touch):
        if not self.collide_point(*touch.pos):
            self.close()
            return True 
        return False
