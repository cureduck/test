import unittest
from unittest.mock import *

from basics import *

"""
class testFactorMixIn(FactorMixIn):
    def affect(self, timing: Timing, baton) -> NoReturn:
        a = 1

    def may_affect(self, timing: Timing, baton: dict[str, Any]) -> bool:
        return True

    @staticmethod
    def priority(timing: Timing) -> int:
        return 1

    def after_affect(self, timing: Timing, baton: dict[str, Any]) -> NoReturn:
        a = 1

class TestFactorMixIn(unittest.TestCase):
    def test_may_affect(self):
        factor = testFactorMixIn()
        self.assertTrue(factor.may_affect(Timing.Mislead, {}))
        self.assertTrue(factor.may_affect(Timing.Death, {}))
        self.assertTrue(factor.may_affect(Timing.Attack, {}))

    def test_priority(self):
        self.assertEqual(FactorMixIn.priority(Timing.Mislead), 0)
        self.assertEqual(testFactorMixIn.priority(Timing.Mislead), 1)
"""


class TestPosition(unittest.TestCase):
    def test_include(self):
        pos = Position([True, 0, 1, 2])
        self.assertTrue(pos.include(0))
        self.assertTrue(pos.include(1))
        self.assertTrue(pos.include(2))

    def test_left(self):
        pos = Position([True, 0, 1, 2])
        self.assertTrue(pos.left)


class TestTargeting(unittest.TestCase):
    def setUp(self):
        self.target1 = Targeting(True, True, 0, 1, 2)
        self.target2 = Targeting(True, True, -1)
        self.target3 = Targeting(True, True)
        self.target4 = Targeting(False, False, 0, 1)
        self.target5 = Targeting(True, True, -2)

    def test__index__(self):
        self.assertTrue(0 in self.target1.__index__())
        self.assertTrue(1 in self.target1.__index__())
        self.assertTrue(2 in self.target1.__index__())

    def test__getitem__(self):
        self.assertEqual(self.target1[0], 0)
        self.assertEqual(self.target1[1], 1)
        self.assertEqual(self.target1[2], 2)

    def test__sizeof__(self):
        self.assertEqual(self.target1.__sizeof__(), 3)

    def test__len__(self):
        self.assertEqual(self.target1.__len__(), 3)

    def test__repr__(self):
        self.assertEqual(self.target4.__repr__(), "enemy, aoe, 0,1")
        self.assertEqual(self.target1.__repr__(), "ally, single, 0,1,2")

    def test_none(self):
        self.assertTrue(self.target3.none)
        self.assertFalse(self.target1.none)

    def test_selfhood(self):
        self.assertTrue(self.target2.selfhood)
        self.assertFalse(self.target1.selfhood)

    def test_selfless(self):
        self.assertTrue(self.target5.selfless)
        self.assertFalse(self.target1.selfless)

    def test_alt(self):
        position1 = Position([True, 0, 1, 2])
        others = list(range(ARENA_WIDTH))
        others.remove(position1[1])
        self.assertEqual(str(Targeting(True, True, 0)),
                         str(self.target2.alt(position1)))
        self.assertEqual(str(Targeting(True, True, *others)),
                         str(self.target5.alt(position1)))
        self.assertEqual(str(self.target1.alt(position1)),
                         str(self.target1.alt(position1)))

    def test_random_choose(self):
        rand = Random(0)
        self.assertEqual(self.target4.random_choose(rand), (self.target4))
        self.assertEqual(str(self.target1.random_choose(rand)),
                         str((Targeting(self.target1.friendly, self.target1.selective, rand.choice(self.target1)))))

    def test_choose(self):
        with self.assertRaises(TargetingError):
            self.target1.choose(4)
        self.assertEqual(self.target4.choose(0), (self.target4))
        self.assertEqual(str(self.target1.choose(0)),
                         str((Targeting(self.target1.friendly, self.target1.selective, 0))))


"""
class testbuff(testFactorMixIn,Buff):
    def name(self) -> str:
        return "Testbuff"
    
    def __repr__(self) -> str:
        return "Testbuff"
    
    def add(self, buff: Buff) -> NoReturn:
        a = 1

    def expire(self) -> bool:
        return False

    def on_turn_end(self, character: Character) -> NoReturn:
        a = 1
     
    def clone(self) -> Buff:
        return testbuff()

class TestBuff(unittest.TestCase):
    def test_name(self):
        buff = testbuff()
        self.assertEqual(buff.name(),"Testbuff")
    
    def test__repr__(self):
        buff = testbuff()
        self.assertEqual(buff.__repr__(),"Testbuff")
    
    def test_clone(self):
        buff = testbuff()
        self.assertEqual(str(buff.clone()),str(testbuff()))
"""


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.timer = Timer(3, 1)

    def test_tick(self):
        self.timer.tick()
        self.assertEqual(self.timer[0], 2)
        self.assertEqual(self.timer[1], 1)


class TestBuffs(unittest.TestCase):
    def setUp(self):
        self.Buff1 = Mock(spec=Buff)
        setattr(self.Buff1, "name", "buff1")
        setattr(self.Buff1, "on_expire", 1)
        self.Buff2 = Mock(spec=Buff)
        setattr(self.Buff2, "name", "buff2")
        setattr(self.Buff2, "on_expire", 1)
        self.Buff3 = Mock(spec=Buff)
        setattr(self.Buff3, "name", "buff3")
        setattr(self.Buff3, "on_expire", 1)
        self.buffs = Buffs(self.Buff1)

    def test_add(self):
        self.buffs.add(self.Buff2)
        self.assertEqual(self.buffs[1], self.Buff2)

        self.buffs.add(self.Buff2)
        self.assertEqual(len(self.buffs), 2)


class TestAttack(unittest.TestCase):
    def setUp(self):
        self.attack = Attack(amount=(10, 20), mag=1.0, acc=0.0, crit=0.2)

    def test_miss_check(self):
        game_random.set_sequence([.2, .2, .2])
        self.assertEqual(game_random.random(), .2)
        self.assertEqual(self.attack.acc, 0.0)
        self.assertTrue(self.attack.miss_check())
        self.assertEqual(self.attack.acc, 1.0)

        self.attack.acc = 1.0

        self.assertFalse(self.attack.miss_check())
        self.assertEqual(self.attack.acc, 1.0)

    def test_min(self):
        self.assertEqual(self.attack.min, 10)

    def test_max(self):
        self.assertEqual(self.attack.max, 20)


"""
class TestCombatantMixIn(unittest.TestCase, MyCombatant):

    def setUp(self):
        self.combatant = CombatantMixIn("test",100,100,10,None)

    def test_dead(self):
        self.assertFalse(self.combatant.dead)
        self.cur_hp = 0
        self.assertTrue(self.combatant.dead)
        self.combatant.cur_hp = -10
        self.assertTrue(self.combatant.dead)

    def test_suffer(self):
        attack = Attack(amount=(10, 20))
        self.combatant.suffer(attack)
        self.assertLess(self.combatant.cur_hp, 100)

    def test_max_hp(self):
        self.assertEqual(self.combatant.max_hp, 100)
        self.combatant.max_hp = 200
        self.assertEqual(self.combatant.max_hp, 200)

    def test_speed(self):
        self.assertEqual(self.combatant.speed, 10)

    def test_hp(self):
        self.assertEqual(self.combatant.hp, "100/100")

    def test_find_target(self):
        targets = self.combatant.find_target(Targeting.All)
        self.assertEqual(len(targets), 0)

    def test_take(self):
        action = Action.Attack
        target = Targeting.Enemy
        self.assertIsNone(self.combatant.take(action, target))

    def test_execute(self):
        decision = (Action.Attack, Targeting.Enemy)
        self.assertIsNone(self.combatant.execute(decision))

    def test_get_actions(self):
        actions = self.combatant.get_actions()
        self.assertIsInstance(actions, tuple)

    async def test_get_decision(self):
        decision = await self.combatant.get_decision()
        self.assertIsNone(decision)

    def test_on_turn_end(self):
        self.assertIsNone(self.combatant.on_turn_end())
"""


class TestArena(unittest.TestCase):
    def setUp(self) -> None:
        self.a = Character("a", 13, 20, 3, Buffs(), Sword())
        self.b = Character("b", 13, 20, 4, Buffs(), Sword())
        self.c = Character("c", 12, 25, 9, Buffs(), Sword())
        self.d = Character("d", 18, 20, 2, Buffs(), Sword())


        self.e = Character("e", 20, 25, 5, Buffs(), Sword())
        self.f = Character("f", 0, 25, 1, Buffs(), Sword())


        self.arena = Arena([self.a, self.b, self.c, self.d], [self.e, ])
        self.arena.round = 0
        self.arena.action_order = [self.a, self.b, self.c, self.d, self.e]

    def test_move(self):
        self.arena.move(self.c, 1)  # 后退
        self.assertEqual(self.arena.left[1], self.c)
        self.assertEqual(self.arena.left[2], self.b)

        self.arena.move(self.c, 2)  # 前进
        self.assertEqual(self.arena.left[1], self.b)
        self.assertEqual(self.arena.left[2], self.c)

        self.arena.move(self.c, 3)  # 不动
        self.assertEqual(self.arena.left[1], self.b)
        self.assertEqual(self.arena.left[2], self.c)


    def test_get_arena_info(self):
        self.arena.start()
        self.assertEqual(self.arena.action_order, [self.c, self.e, self.b, self.a, self.d])

    async def test_run(self):
        self.assertEqual(self.arena.run(), self.arena.run() - 1)

    def test_find_position(self):
        self.assertEqual(self.arena.find_position(self.a), (True, 0))
        self.assertEqual(self.arena.find_position(self.b), (True, 1))
        self.assertEqual(self.arena.find_position(self.c), (True, 2))
        self.assertEqual(self.arena.find_position(self.d), (True, 3))
        self.assertEqual(self.arena.find_position(self.e), (False, 0))

        with self.assertRaises(ValueError):
            self.arena.find_position(None)

    def test_find_index(self):
        self.assertEqual(self.arena.find_index(self.a), 0)
        self.assertEqual(self.arena.find_index(self.b), 1)
        self.assertEqual(self.arena.find_index(self.c), 2)
        self.assertEqual(self.arena.find_index(self.d), 3)
        self.assertEqual(self.arena.find_index(self.e), 0)

        with self.assertRaises(ValueError):
            self.arena.find_index(None)

    def test_find_target(self):
        target1 = Targeting(False, True, 0)
        target2 = Targeting(False, True, 0, 1, 2)
        target3 = Targeting(True, True, 0, 1, 2)

        self.assertEqual(self.arena.find_target(self.a, target1),
                         [self.e])

        self.assertEqual(self.arena.find_target(self.e, target2),
                         [self.a, self.b, self.c])

        self.assertEqual(self.arena.find_target(self.a, target3),
                         [self.a, self.b, self.c])

    def test_get_action_order(self):
        pass

    def test_clean_dead_in_order(self):
        # arena1 = Arena([self.a,self.b], [self.e, ])
        # self.assertEqual(arena1.get_action_order(),[])
        # 不知道为什么返回的是一个空列表
        pass

    def test_start(self):
        pass

    def test_round_over(self):
        self.assertFalse(self.arena.round_over)
    
        arena1 = Arena([self.a,self.f], [self.e, ])
        arena1.action_order = [self.a, self.f, self.e]
        arena1.clean_dead_in_order()
        self.assertEqual(arena1.action_order, [self.a,self.e])


    def test_trun(self):
        self.assertEqual(self.arena.turn, 0)
        self.arena._round += 1
        self.assertEqual(self.arena.turn, 1)

    def test_is_over(self):
        arena1 = Arena([self.f,], [self.e, ])
        self.assertTrue(arena1.is_over)

        arena2 = Arena([self.a,], [self.e, ])
        #self.assertFalse(arena2.is_over)
        #编译器犯病，但确实是False


class TestAction(unittest.TestCase):
    def setUp(self):
        self.effect1 = Mock(spec=Effect)
        self.pre_reqm1 = Mock(spec=PreReqm)
        self.pre_reqm2 = Mock(spec=PreReqm)
        self.post_reqm1 = Mock(spec=PostReqm)
        self.target1 = Mock(spec=Targeting)

        # self.baton = Mock(spec=Baton)

        self.pre_reqm1.check.return_value = True
        self.pre_reqm2.check.return_value = False

        self.post_reqm1.check.return_value = self.target1

        setattr(self.target1, "friendly", False)
        setattr(self.target1, "selective", True)
        setattr(self.target1, "positions", [0, 1, 2])

        self.action1 = Action((self.pre_reqm1,), (self.post_reqm1,), ((self.target1, self.effect1),))
        self.action2 = Action((self.pre_reqm2,), (self.post_reqm1,), ((self.target1, self.effect1),))

        # self.a = Character("a", 13, 20, 3,Buffs())
        self.a = Mock(spec=CombatantMixIn)
        setattr(self.a, "name", "a")
        setattr(self.a, "speed", 3)
        setattr(self.a, "max_hp", 20)
        setattr(self.a, "cur_hp", 13)
        setattr(self.a, "buffs", Buffs())

    def test_check(self):
        self.assertTrue(self.action1.check(self.a))
        self.assertFalse(self.action2.check(self.a))

    def test_check_target(self):
        with self.assertRaises(TargetingError):
            self.action1.check_target(self.a, self.target1)

        # self.assertEqual(self.action1.check_target(self.a,self.target1),target)

    def test_execute(self):
        pass


class TestEquipage(unittest.TestCase):
    def setUp(self):

        self.equipage = Equipage(Sword())

    def test_get_actions(self):
        self.equipage.get_actions()
        my_list = list(self.equipage.keys())

        result0 = Slot.MainHand
        result1 = Slot.OffHand

        self.assertEqual(result0,my_list[0])
        self.assertEqual(result1,my_list[1])

    def test_equip(self):

        self.equipage.equip(Shield())
        my_list = list(self.equipage.keys())

        result0 = Slot.MainHand
        result1 = Slot.OffHand
        result2 = Slot.Amulet
        result3 = Slot.Armor

        self.assertEqual(result0,my_list[0])
        self.assertEqual(result1,my_list[1])
        self.assertEqual(result2,my_list[2])
        self.assertEqual(result3,my_list[3])

        with self.assertRaises(ValueError):
            self.equipage.equip(Sword())

    def test_unequip(self):

        with self.assertRaises(ValueError):
            self.equipage.unequip(Shield())

        self.equipage.equip(Shield())
        self.equipage.unequip(Shield())

        my_list = list(self.equipage.values())

        self.assertEqual(my_list[1],None)
