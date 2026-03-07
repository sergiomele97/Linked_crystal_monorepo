import unittest
from unittest.mock import MagicMock
import sys
import os

# Set up paths to import from src
# The test is in app/tests/unit/test_distance_culling.py
# src is in app/src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock Kivy to avoid issues in non-GUI environment
sys.modules['kivy'] = MagicMock()
sys.modules['kivy.app'] = MagicMock()
sys.modules['kivy.uix.label'] = MagicMock()
sys.modules['kivy.graphics'] = MagicMock()

# Mock the RemotePlayerEntity before importing manager
import services.drawing.entities.remote_player_entity
services.drawing.entities.remote_player_entity.RemotePlayerEntity = MagicMock()

from services.drawing.entities.remote_player_manager import RemotePlayerManager
from models.packet import Packet
from models.ramData import RamData

class TestDistanceCulling(unittest.TestCase):
    def setUp(self):
        self.ram = RamData()
        self.ram.player_x_coord = 20
        self.ram.player_y_coord = 20
        self.ram.map_bank = 0
        self.ram.map_number = 1

        self.serverPackets = []
        self.onScreenPlayers = {}
        
        self.manager = RemotePlayerManager(self.ram, self.serverPackets, self.onScreenPlayers)

    def test_close_player_is_visible(self):
        # Player at (25, 25) is within (11, 10) range from (20, 20)
        # dx = 5, dy = 5
        packet = Packet(player_id=1, x=25, y=25, map_bank=0, map_number=1, IsOverworld=True)
        self.serverPackets.append(packet)
        
        self.manager.updateOnScreenPlayersFromNetwork()
        
        self.assertIn(1, self.onScreenPlayers)
        self.assertEqual(len(self.onScreenPlayers), 1)

    def test_far_player_is_culled(self):
        # Player at (40, 40) is NOT within (11, 10) range from (20, 20)
        # dx = 20, dy = 20
        packet = Packet(player_id=2, x=40, y=40, map_bank=0, map_number=1, IsOverworld=True)
        self.serverPackets.append(packet)
        
        self.manager.updateOnScreenPlayersFromNetwork()
        
        self.assertNotIn(2, self.onScreenPlayers)
        self.assertEqual(len(self.onScreenPlayers), 0)

    def test_player_moving_out_of_range_is_removed(self):
        # 1. Player is close
        packet = Packet(player_id=3, x=25, y=25, map_bank=0, map_number=1, IsOverworld=True)
        self.serverPackets.append(packet)
        self.manager.updateOnScreenPlayersFromNetwork()
        self.assertIn(3, self.onScreenPlayers)

        # 2. Player moves far
        self.serverPackets.clear()
        packet_far = Packet(player_id=3, x=50, y=50, map_bank=0, map_number=1, IsOverworld=True)
        self.serverPackets.append(packet_far)
        self.manager.updateOnScreenPlayersFromNetwork()
        
        self.assertNotIn(3, self.onScreenPlayers)

    def test_filtering_by_map_still_works(self):
        # Player is close but in different map
        packet = Packet(player_id=4, x=21, y=21, map_bank=0, map_number=2, IsOverworld=True)
        self.serverPackets.append(packet)
        
        self.manager.updateOnScreenPlayersFromNetwork()
        
        self.assertNotIn(4, self.onScreenPlayers)

if __name__ == '__main__':
    unittest.main()
