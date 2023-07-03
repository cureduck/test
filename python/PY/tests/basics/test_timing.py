import unittest
from PY.python.basics.timing import Timing

class TestTiming(unittest.TestCase):

    def test_timing(self):
        self.assertEqual(Timing.Healing, 1)
        self.assertEqual(Timing.Attack, 2)
        self.assertEqual(Timing.Mislead, 512)
        self.assertEqual(Timing.Defend, 4)
        self.assertEqual(Timing.Move, 8)
        self.assertEqual(Timing.Buffed, 16)
        self.assertEqual(Timing.GetSpeed, 32)
        self.assertEqual(Timing.Equip, 64)
        self.assertEqual(Timing.Unequip, 128)
        self.assertEqual(Timing.GetMaxHp, 256)
        self.assertEqual(Timing.Death, 1024)