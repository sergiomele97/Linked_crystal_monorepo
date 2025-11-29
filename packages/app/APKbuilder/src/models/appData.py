from models.packet import packet
from models.ramData import RamData

class appData:
    def __init__(self):
        self.romPath = ''
        self.ramData = RamData()
        self.packet = packet()
        self.serverPackets = []
        