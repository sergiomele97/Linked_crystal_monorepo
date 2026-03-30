import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.drawing.entities.remote_player_entity import RemotePlayerEntity
from models.packet import Packet

class TestRemotePlayerSync(unittest.TestCase):
    def setUp(self):
        # Initial position at (10, 10), which is (160, 160) in fine coords
        self.player = RemotePlayerEntity(player_id=1, initial_x=10, initial_y=10)

    def test_sync_r1_l1(self):
        # Remote Speed 1, Local Speed 1 -> advance = 1.0
        # Each tick moves according to PIXEL_MOVEMENT_CORRECTION
        # 16 ticks total to complete movement
        p = Packet(player_id=1, x=11, y=10, speed=1)
        self.player.update_from_network(p)
        
        self.assertEqual(self.player.remote_speed, 1)
        self.assertTrue(self.player.is_moving)
        
        # Call 16 times
        for i in range(16):
            self.player.updateFineCoords(local_speed=1)
            
        self.assertFalse(self.player.is_moving)
        self.assertEqual(self.player.x_fine_coord, 11 * 16) # 176

    def test_sync_r2_l1(self):
        # Remote Speed 2, Local Speed 1 -> advance = 2.0
        # Should complete in 8 local frames
        p = Packet(player_id=1, x=11, y=10, speed=2)
        self.player.update_from_network(p)
        
        for i in range(8):
            self.player.updateFineCoords(local_speed=1)
            
        self.assertFalse(self.player.is_moving)
        self.assertEqual(self.player.x_fine_coord, 11 * 16)

    def test_sync_r1_l2(self):
        # Remote Speed 1, Local Speed 2 -> advance = 0.5
        # Should complete in 32 local frames
        p = Packet(player_id=1, x=11, y=10, speed=1)
        self.player.update_from_network(p)
        
        for i in range(32):
            self.player.updateFineCoords(local_speed=2)
            
        self.assertFalse(self.player.is_moving)
        self.assertEqual(self.player.x_fine_coord, 11 * 16)

    def test_sync_r2_l2(self):
        # Remote Speed 2, Local Speed 2 -> advance = 1.0
        # Should complete in 16 local frames
        p = Packet(player_id=1, x=11, y=10, speed=2)
        self.player.update_from_network(p)
        
        for i in range(16):
            self.player.updateFineCoords(local_speed=2)
            
        self.assertFalse(self.player.is_moving)
        self.assertEqual(self.player.x_fine_coord, 11 * 16)

if __name__ == '__main__':
    unittest.main()
