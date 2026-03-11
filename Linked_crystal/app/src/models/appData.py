from models.packet import Packet
from models.ramData import RamData

class appData:
    def __init__(self):
        self.romPath = ''
        self.originalRomName = ''
        self.ramData = RamData()
        self.packet = Packet()
        self.serverPackets = []
        self.userID = None
        