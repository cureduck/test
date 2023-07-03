from unittest import TestCase

from basics import *


class TestCharacter(TestCase):
    def setUp(self) -> None:
        self.character = Character("player", 100, 100, 10, None, Sword())

    def test_init(self):
        assert self.character.name == "player"
        self.assertEqual(self.character.cur_hp, 100)
        assert self.character.cur_hp == 100
        assert self.character.base_max_hp == 100
        assert self.character.base_speed == 10
        assert self.character.buffs == Buffs()

    def test_buff(self):
        self.character.buffs = Buffs()
        assert self.character.buffs == Buffs()
        strength = Strength(1)
        self.character.buffs = Buffs(strength)
        assert self.character.buffs[0].name == 'Strength'

        target = Character("target", 100, 100, 10, None, Sword())
        self.character.attack(target, (10, 10), dict())

        assert target.cur_hp == 85

        assert len(self.character.buffs) == 0
