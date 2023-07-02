import unittest
from unittest.mock import *
from PY.python.basics.buffs import *
from PY.python.basics.KEYWORDS import *
from PY.python.basics.gameplay import *
from PY.python.basics.character import *

class Sword(OneHandWeapon):
    def __init__(self):
        super().__init__(10, (1, 2))

    def action(self) -> tuple[Action, ...]:
        return Bash(), Slash()

class TestDodge(unittest.TestCase):
    def test_may_affect(self):
        dodge = Dodge()
        self.assertTrue(dodge.may_affect(Timing.Defend, {}))
        self.assertFalse(dodge.may_affect(Timing.Attack, {}))
    
    def test_affect(self):
        dodge = Dodge()
        attack = Attack(amount=(10, 20), acc=1.0)
        baton = {ATTACK: attack}
        dodge.affect(Timing.Defend, baton)
        self.assertEqual(attack.acc, 0.5)

        #baton = {IGNORE_EVADE,False}
        #dodge.affect(Timing.Defend, baton)
        #方法未实现，/
    
    def test_name(self):
        dodge = Dodge()
        self.assertEqual(dodge.name, "Dodge")
    
    def test_repr(self):
        dodge = Dodge()
        self.assertEqual(repr(dodge), "D")

class TestStrength(unittest.TestCase):
    def test_may_affect(self):
        strength = Strength()
        self.assertTrue(strength.may_affect(Timing.Attack, {}))
        self.assertFalse(strength.may_affect(Timing.Defend, {}))
    
    def test_affect(self):
        strength = Strength()
        attack = Attack(amount=(10, 20), mag=1.0)
        baton = {ATTACK: attack}
        strength.affect(Timing.Attack, baton)
        self.assertEqual(attack.mag, 1.5)
    
    def test_name(self):
        strength = Strength()
        self.assertEqual(strength.name, "Strength")
    
    def test_repr(self):
        strength = Strength()
        self.assertEqual(repr(strength), "S")

class TestProtected(unittest.TestCase):
    pass
#特殊方法测试在test_buffs_ues.py

class test_combo(unittest.TestCase):



    def test_may_affect(self):
        combo = Combo()
        baton = {COMBO: True}
        assert combo.may_affect(Timing.Defend, baton) == True


    def test_affect(self):
        combo = Combo()
        baton = {COMBO: True}
        combo.affect(Timing.Defend, baton)
        assert baton[COMBO] == True

    def test_repr(self):
        combo = Combo()
        assert repr(combo) == "C"