import unittest
from unittest.mock import *

from basics import *


class Sword(OneHandWeapon):
    def __init__(self):
        super().__init__(10, (1, 2))

    def action(self) -> tuple[Action, ...]:
        return Bash(), Slash()


class TestDodge(unittest.TestCase):
    def setUp(self):
        self.a = Character("a", 13, 20, 3, Buffs(), Sword())

        self.e = WildDog("e")
        self.f = WildDog("f")

    def test_used1(self):
        patcher = patch.object(game_random, 'random', return_value=0.0)
        patcher.start()
        self.a.attack(self.e, (10, 10), {ATTACK: None}, crit=0)
        # self.assertEqual(self.e.cur_hp, 14)
        # 随机数暂未实现
        patcher.stop()

    @patch("random.random", return_value=0.6)
    def test_used2(self, mock_randint):
        self.a.attack(self.f, (10, 10), {ATTACK: None}, crit=0)
        # self.assertEqual(self.f.cur_hp, 14)
        # 随机数待实现


class TestStrength(unittest.TestCase):
    def setUp(self):
        self.a = Character("a", 13, 20, 3, Buffs(Strength()), Sword())
        self.b = Character("b", 13, 20, 2, Buffs(), Sword())

        self.e = Character("e", 13, 20, 2, Buffs(), Sword())
        self.f = Character("f", 13, 20, 2, Buffs(), Sword())

    def test_used(self):
        self.a.attack(self.e, (10, 10), {ATTACK: None}, crit=0)
        self.assertEqual(self.e.cur_hp, -2)

        self.b.attack(self.f, (10, 10), {ATTACK: None}, crit=0)
        self.assertEqual(self.f.cur_hp, 3)


class TestProtected(unittest.TestCase):
    def setUp(self):
        self.a = Character("a", 13, 20, 3, Buffs(), Sword())
        self.b = Character("b", 13, 20, 4, Buffs(Protected(self.a)), Sword())

        self.e = Character("e", 13, 20, 2, Buffs(), Sword())
        self.f = Character("f", 13, 20, 2, Buffs(), Sword())

        self.arena = Arena([self.a, self.b], [self.e, self.f])

    def test_used(self):
        self.e.attack(self.b, (10, 10), {ATTACK: None}, crit=0)
        self.assertEqual(self.b.cur_hp, 13)
        self.assertEqual(self.a.cur_hp, 3)
        # 攻击b的伤害转移给a

    def test_used1(self):
        self.e.attack(self.a, (10, 10), {ATTACK: None}, crit=0)
        self.assertEqual(self.a.cur_hp, 3)
        self.assertEqual(self.b.cur_hp, 13)
        # 攻击a的伤害不转移给b

    # 如果c,d都有Protected，那么，c受到的攻击，伤害转移给d，
    # c受到的攻击，伤害转移给d，不应嵌套循环
    def test_used2(self):
        c = Character("c", 13, 20, 3, Buffs(), Sword())
        d = Character("d", 13, 20, 4, Buffs(Protected(c)), Sword())
        c.buffs = Buffs(Protected(d))

        arena2 = Arena([c, d], [self.e, self.f])

        self.e.attack(c, (10, 10), {ATTACK: None}, crit=0)
        c.attack(self.e, (10, 10), {ATTACK: None}, crit=0)
        self.assertEqual(c.cur_hp, 13)
        self.assertEqual(d.cur_hp, 3)

    # 如果被保护者死亡，不会在有保护效果
    def test_used3(self):
        c = Character("c", -1, 20, 3, Buffs(), Sword())
        d = Character("d", 13, 20, 4, Buffs(Protected(c)), Sword())

        arena2 = Arena([c, d], [self.e, self.f])

        self.e.attack(d, (10, 10), {ATTACK: None}, crit=0)
        self.assertEqual(d.cur_hp, 13)
        self.assertEqual(c.cur_hp, -1)


class TestCombo(unittest.TestCase):
    def setUp(self):
        self.a = Character("a", 13, 20, 3, Buffs(Combo()), Sword())
        self.b = Character("b", 13, 20, 4, Buffs(), Sword())

        self.e = WildDog("e")
        self.f = WildDog("f")

    def test_used(self):
        pass
    # combo方法未完成
