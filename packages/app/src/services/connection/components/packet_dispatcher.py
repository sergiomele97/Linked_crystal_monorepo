from models.packet import Packet
from kivy.app import App
from services.logger import log

class PacketDispatcher:
    PACKET_SIZE = 24

    def __init__(self):
        self.my_id = None
        self.app = App.get_running_app()
        self.packet_store = self.app.appData.serverPackets
        self.chat_manager = None

    def set_chat_manager(self, chat_manager):
        self.chat_manager = chat_manager

    def handle_data(self, data):
        if not data:
            return

        # Initial Handshake (Raw ID)
        if len(data) == 4 and self.my_id is None:
            self.my_id = int.from_bytes(data, "little")
            self.app.appData.userID = self.my_id
            log(f"My ID: {self.my_id}")
            return

        # Multiplexed Data
        if len(data) < 1:
            return
            
        type_byte = data[0]
        payload = data[1:]

        if type_byte == 0x01: # Game Data
            self._handle_game_data(payload)
        elif type_byte == 0x02: # Chat Data
            self._handle_chat_data(payload)

    def _handle_game_data(self, payload):
        n = len(payload) // self.PACKET_SIZE
        self.packet_store.clear()
        
        for i in range(n):
            chunk = payload[i * self.PACKET_SIZE:(i + 1) * self.PACKET_SIZE]
            if len(chunk) != self.PACKET_SIZE:
                continue
            try:
                p = Packet.from_bytes(chunk)
                if self.my_id is not None and p.player_id == self.my_id:
                    continue
                self.packet_store.append(p)
            except Exception as e:
                log(f"Packet Decode Error: {e}")

    def _handle_chat_data(self, payload):
        if len(payload) < 4:
            return
            
        sender_id = int.from_bytes(payload[0:4], "little")
        try:
            msg = payload[4:].decode('utf-8')
            if self.chat_manager:
                self.chat_manager.receive_message(sender_id, msg)
        except Exception:
            pass
