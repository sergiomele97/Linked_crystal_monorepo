import unittest
import struct
from models.packet import Packet

class TestPacket(unittest.TestCase):
    def test_serialization(self):
        # T-PRO-01: Packet Serialization
        p = Packet(
            player_id=1,
            x=100,
            y=200,
            map_number=3,
            map_bank=4,
            IsOverworld=1
        )
        
        # Test to_bytes
        data = p.to_bytes()
        self.assertEqual(len(data), 24)
        
        # Verify specific bytes using struct.unpack (Little-Endian)
        # Format: "<I2i2iI" -> Uint32, Int32, Int32, Int32, Int32, Uint32
        unpacked = struct.unpack("<I2i2iI", data)
        self.assertEqual(unpacked[0], 1)
        self.assertEqual(unpacked[1], 100)
        self.assertEqual(unpacked[2], 200)
        self.assertEqual(unpacked[3], 3)
        self.assertEqual(unpacked[4], 4)
        self.assertEqual(unpacked[5], 1)

    def test_deserialization(self):
        # T-PRO-01: Packet Deserialization
        raw_data = struct.pack("<I2i2iI", 5, 50, 60, 7, 8, 0)
        p = Packet.from_bytes(raw_data)
        
        self.assertEqual(p.player_id, 5)
        self.assertEqual(p.player_x_coord, 50)
        self.assertEqual(p.player_y_coord, 60)
        self.assertEqual(p.map_number, 7)
        self.assertEqual(p.map_bank, 8)
        self.assertEqual(p.IsOverworld, 0)

if __name__ == "__main__":
    unittest.main()
