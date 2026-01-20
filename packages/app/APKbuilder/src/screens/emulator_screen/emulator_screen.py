from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.lang import Builder

from screens.emulator_screen.components.controlpad import ControlPad
from screens.emulator_screen.components.menu_dropdown import MenuDropdown
from screens.emulator_screen.components.video_display import VideoDisplay
from screens.emulator_screen.components.chat_interface import ChatInterface
from services.emulator.emulator_core_interface import EmulatorCoreInterface

Builder.load_file("screens/emulator_screen/emulator_screen.kv")
Builder.load_file("screens/emulator_screen/components/controlpad.kv")
Builder.load_file("screens/emulator_screen/components/video_display.kv")


class EmulatorScreen(Screen):

    def on_enter(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.video_display = self.ids.video_display
        self.controlpad = self.ids.control_pad
        self.emulator = EmulatorCoreInterface(
            on_frame=self.video_display.update_frame,
            on_text_output=self.video_display.display_message
        )

        self.controlpad.on_button_press = self.emulator.send_input_press
        self.controlpad.on_button_release = self.emulator.send_input_release

        self.emulator.start()

    def onChatPressed(self):
        if not hasattr(self, "chat_interface"):
            self.chat_interface = ChatInterface(father_screen=self)
        self.chat_interface.mostrar_chat()
    
    def onMenuPressed(self, caller):
        if not hasattr(self, "dropdown"):
            self.dropdown = MenuDropdown()
            self.dropdown.father_screen = self
        self.dropdown.open(caller)
    
