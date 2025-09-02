from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.lang import Builder

from screens.emulator_screen.components.controlpad import ControlPad
from screens.emulator_screen.components.video_display import VideoDisplay
from screens.emulator_screen.components.audio_manager import AudioManagerKivy
from screens.emulator_screen.components.emulator_core_interface import EmulatorCoreInterface

Builder.load_file("screens/emulator_screen/emulator_screen.kv")
Builder.load_file("screens/emulator_screen/components/controlpad.kv")
Builder.load_file("screens/emulator_screen/components/video_display.kv")


class EmulatorScreen(Screen):
    rom_path = StringProperty("")

    def on_enter(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.video_display = self.ids.video_display
        self.controlpad = self.ids.control_pad
        self.audio_manager = AudioManagerKivy()
        self.emulator = EmulatorCoreInterface(
            rom_path=self.rom_path,
            on_frame=self.video_display.update_frame,
            on_text_output=self.video_display.display_message,
            on_audio=self.audio_manager.play_audio_buffer
        )

        self.controlpad.on_button_press = self.emulator.send_input_press
        self.controlpad.on_button_release = self.emulator.send_input_release

        self.emulator.start()

    def onChatPressed(self):
        print("Chat button pressed")
    
    def onMenuPressed(self):
        print("Menu button pressed")
    
    # def on_request_close(self, *args):
    #     self.emulator.save_RAM()
    #     return False
