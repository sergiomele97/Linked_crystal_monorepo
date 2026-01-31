from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.lang import Builder

from screens.emulator_screen.components.controlpad import ControlPad
from screens.emulator_screen.components.menu_dropdown import MenuDropdown
from screens.emulator_screen.components.video_display import VideoDisplay
from screens.emulator_screen.components.chat_interface import ChatInterface
from services.emulator.emulator_core_interface import EmulatorCoreInterface
from services.chat.chat_manager import ChatManager
from kivy.app import App
from kivy.clock import Clock

Builder.load_file("screens/emulator_screen/emulator_screen.kv")
Builder.load_file("screens/emulator_screen/components/controlpad.kv")
Builder.load_file("screens/emulator_screen/components/video_display.kv")


class EmulatorScreen(Screen):

    def on_enter(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Initialize ChatManager locally (hierarchy change)
        self.chat_manager = ChatManager()
        
        # Start link stats loop
        self.link_stats_event = Clock.schedule_interval(self.update_link_stats, 0.5)
        
        # Inject ChatManager into global connection manager (dependency injection)
        app = App.get_running_app()
        if hasattr(app, "connection_manager"):
            app.connection_manager.set_chat_manager(self.chat_manager)

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
    
    
    def update_link_stats(self, dt):
        if not self.emulator:
            return

        status = self.emulator.get_link_status()
        panel = self.ids.link_stats_panel
        
        if status["connected"]:
            panel.opacity = 1
            panel.disabled = False
            self.ids.link_tx_label.text = f"Packets: {status['tx']}"
        else:
            panel.opacity = 0
            panel.disabled = True

    def disconnect_link_action(self):
        if self.emulator:
            self.emulator.disconnect_link()
            self.ids.link_stats_panel.opacity = 0
