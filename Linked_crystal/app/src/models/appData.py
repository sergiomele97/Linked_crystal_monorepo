from models.packet import Packet
from models.ramData import RamData

class appData:
    def __init__(self):
        self.romPath = ''
        self.romFolderUri = None  # URI de la carpeta en Android
        self.ramData = RamData()
        self.packet = Packet()
        self.serverPackets = []
        self.userID = None
        