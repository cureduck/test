import unittest
from unittest.mock import *
from PY.tests.basics.test_Test_ExtensionClass import *
from PY.python.basics import *


class Sword(OneHandWeapon):
    def __init__(self):
        super().__init__(10, (1, 2))

    def action(self) -> tuple[Action, ...]:
        return Bash(), Slash()

a = Character("a", 13, 20, 3, Buffs(), Sword())
b = Character("b", 13, 20, 4, Buffs(), Sword())

e = Character("e", 13, 20, 4, Buffs(Dodge()), Sword())

patcher = patch.object(random.Random(), 'random', return_value=0.0)
patcher.start()

a.new_TestUse_attack(e,(10,10),{ATTACK: Attack},acc = 1,crit=0)
print(e.cur_hp)
        
attack2 = Attack((10,10))
b.attack(a,(10,10),{ATTACK: attack2},crit=0)
print(a.cur_hp)

patcher.stop()
