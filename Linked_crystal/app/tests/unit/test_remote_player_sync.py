import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.drawing.entities.remote_player_entity import RemotePlayerEntity
from models.packet import Packet

class TestRemotePlayerSync(unittest.TestCase):
    def setUp(self):
        # Initialize at (10, 10)
        self.player = RemotePlayerEntity(player_id=1, initial_x=10, initial_y=10)

    def test_initial_state(self):
        self.assertEqual(self.player.target_x, 10)
        self.assertEqual(self.player.target_y, 10)
        self.assertFalse(self.player.is_moving)

    def test_single_move(self):
        # Packet for (10, 11)
        packet = Packet(player_id=1, x=10, y=11, speed=1)
        self.player.update_from_network(packet)
        
        self.assertTrue(self.player.is_moving)
        self.assertEqual(self.player.target_x, 10)
        self.assertEqual(self.player.target_y, 11)
        self.assertEqual(self.player.direction, "down")
        self.assertIsNone(self.player.pending_target)

    def test_buffered_move(self):
        # Start move to (10, 11)
        packet1 = Packet(player_id=1, x=10, y=11, speed=1)
        self.player.update_from_network(packet1)
        
        # While moving, receive packet for (10, 12)
        packet2 = Packet(player_id=1, x=10, y=12, speed=1)
        self.player.update_from_network(packet2)
        
        # Should be buffered
        self.assertEqual(self.player.target_x, 10)
        self.assertEqual(self.player.target_y, 11)
        self.assertEqual(self.player.pending_target, (10, 12))
        
        # Advance till end of move 1
        for _ in range(16):
            self.player.updateFineCoords(local_speed=1)
            
        # Move 1 should be finished and Move 2 should be started immediately
        self.assertTrue(self.player.is_moving)
        self.assertEqual(self.player.target_x, 10)
        self.assertEqual(self.player.target_y, 12)
        self.assertIsNone(self.player.pending_target)
        self.assertEqual(self.player.move_tick, 0.0)

    def test_speed_propagation(self):
        # Remote at x2
        packet = Packet(player_id=1, x=10, y=11, speed=2)
        self.player.update_from_network(packet)
        self.assertEqual(self.player.remote_speed, 2)
        
        # At local x1, it should finish in 8 ticks
        for _ in range(8):
            self.player.updateFineCoords(local_speed=1)
        
        self.assertFalse(self.player.is_moving)
        self.assertEqual(self.player.x_fine_coord, 10 * 16)
        self.assertEqual(self.player.y_fine_coord, 11 * 16)

    def test_direction_on_chained_move(self):
        # Move Down: (10, 10) -> (10, 11)
        self.player.update_from_network(Packet(player_id=1, x=10, y=11))
        
        # Queue Move Right: (10, 11) -> (11, 11)
        self.player.update_from_network(Packet(player_id=1, x=11, y=11))
        
        # Finish first move
        for _ in range(16):
            self.player.updateFineCoords()
            
        # Second move starts
        self.assertTrue(self.player.is_moving)
        self.assertEqual(self.player.direction, "right")

if __name__ == '__main__':
    unittest.main()
