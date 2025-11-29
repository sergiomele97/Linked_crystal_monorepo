from models.connectionData import ConnectionData
from models.ramData import RamData

class appData:
    def __init__(self):
        self.romPath = ''
        self.ramData = RamData()
        self.connectionData = ConnectionData()
        