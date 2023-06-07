from __future__ import annotations

from abc import abstractmethod, ABC
from enum import Enum, IntFlag
from functools import singledispatchmethod
from random import Random
from typing import Optional, NoReturn, Sequence

from .rand import *
from .singleton import *

IGNORE_EVADE = "ignore evade"
IGNORE_SHIELD = "ignore shield"

ARENA_WIDTH = 4


class Timing(IntFlag):
    Healing = 0b000001
    Attack = 0b000010
    Defend = 0b000100
    Move = 0b001000
    Buffed = 0b010000


class FactorMixIn:
    def affect(self, timing: Timing, **kw) -> NoReturn:
        pass

    def may_affect(self, timing: Timing, **kw) -> bool:
        return False

    @staticmethod
    def priority(timing: Timing) -> int:
        """
        the higher the priority, the earlier it will be affected
        @rtype: int
        @param timing:
        @return:
        """
        return 0

    def after_affect(self, timing: Timing, **kw) -> NoReturn:
        pass


ITSELF = -1
EXCEPT_ITSELF = -2


class Position(tuple[bool, int, ...]):
    """
    first element is a bool, indicating whether its left or right
    rest elements are int, indicating the positions of the targets
    -1 means the caster itself
    -2 means everywhere but the caster itself
    """

    def include(self, pos: int) -> bool:
        return pos in self[1:]

    @property
    def left(self) -> bool:
        return self[0]


class TargetingError(ValueError):
    pass


class Targeting:
    """
    first element is a bool, indicating whether its ally or enemy
    second element is a bool, indicating whether its selective or aoe
    rest elements are int, indicating the positions of the targets
        -1 means the caster itself
    -2 means everywhere but the caster itself
    """

    def __init__(self, friendly: bool, selective: bool, *args: int):
        self.friendly = friendly
        self.selective = selective
        self.positions = args

    def __index__(self):
        return self.positions

    def __getitem__(self, item):
        return self.positions[item]

    def __sizeof__(self):
        return len(self.positions)

    def __len__(self):
        return len(self.positions)

    def __repr__(self):
        friendly = "ally" if self.friendly else "enemy"
        selective = "selective" if self.selective else "aoe"
        return f"Targeting({friendly}, {selective}, {self.positions})"

    @property
    def none(self) -> bool:
        return len(self) == 0

    @property
    def selfhood(self) -> bool:
        return len(self) == 1 and self[0] == ITSELF

    @property
    def selfless(self) -> bool:
        return len(self) == 1 and self[0] == EXCEPT_ITSELF

    def alt(self, position: Position) -> Targeting:
        if self.selfhood:
            return Targeting(self.friendly, self.selective, position[1])
        elif self.selfless:
            others = list(range(ARENA_WIDTH))
            others.remove(position[1])
            return Targeting(self.friendly, self.friendly, *others)
        else:
            return self

    def random_choose(self, rand: Random) -> Targeting:
        if not self.selective:
            return self
        else:
            return Targeting(self.friendly, self.selective, rand.choice(self))

    def choose(self, pos: int) -> Targeting:
        if pos >= ARENA_WIDTH:
            raise TargetingError("position out of range")
        if not self.selective:
            return self
        else:
            return Targeting(self.friendly, self.selective, pos)


# region Buffs
class Buff(FactorMixIn, ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    def __init__(self, stack: int, duration: int):
        self.stack = stack
        self.duration = duration

    def after_affect(self, timing: Timing, **kw):
        self.stack -= 1
        self.on_expire()

    def on_expire(self) -> NoReturn:
        pass

    def __repr__(self):
        return f"{self.name}({self.stack}, {self.duration})"

    def clone(self) -> Buff:
        return self.__class__(self.stack, self.duration)


class PositiveBuff(Buff, ABC):
    def __init__(self, stack: int = 1, duration: int = 1):
        super().__init__(stack, duration)


class NegativeBuff(Buff, ABC):
    def __init__(self, stack: int = 1, duration: int = 1):
        super().__init__(stack, duration)


class Buffs(list[Buff]):
    def __init__(self, *args: Buff):
        super().__init__(args)
        for buff in self:
            buff.on_expire = self.check_expire

    def add(self, buff: Buff):
        for b in self:
            if b.name == buff.name:
                b.stack += buff.stack
                b.duration = max(b.duration, buff.duration)
                return
        self.append(buff)

    def check_expire(self):
        for buff in self:
            if buff.stack <= 0 or buff.duration <= 0:
                self.remove(buff)

    def turn_end(self):
        for buff in self:
            buff.duration -= 1
        self.check_expire()

    def _group_by_name(self) -> dict[str, Buff]:
        """
        return a dict, with buff name as key, and add the value of the same name
        """
        d = {}
        for buff in self:
            if buff.name not in d:
                d[buff.name] = buff.clone()
            else:
                d[buff.name].stack += buff.stack
                d[buff.name].duration = max(d[buff.name].duration, buff.duration)
        return d

    def __repr__(self):
        return ",".join([f"{v}:{v.stack}" for v in self._group_by_name().values()])


class BuffMixIn:
    def __init__(self, *args: Buff):
        self.buffs = Buffs(*args)


# endregion


class StatusMetaClass(type):
    def __new__(cls, name, bases, attrs):
        """
        Add slots and to the class.
        """
        slots = attrs.get("__slots__", ())
        if slots != ():
            slots += ("cur_hp", "max_hp", "cur_mp", "speed")
            attrs["__slots__"] = slots
        return super().__new__(cls, name, bases, attrs)


class StatusMixIn(metaclass=StatusMetaClass):
    __slots__ = ("cur_hp", "max_hp", "speed")

    def __init__(self, cur_hp: int, max_hp: int, speed: int):
        self.cur_hp = cur_hp
        self.max_hp = max_hp
        self.speed = speed

    @property
    def dead(self) -> bool:
        return self.cur_hp <= 0

    def suffer(self, attack: Attack) -> NoReturn:
        if attack.missed:
            return
        if not attack.critted:
            attack.critted = game_random.random() < attack.crit
        if attack.critted:
            dmg = int(attack.min * attack.mag * 1.5)
        else:
            dmg = int(game_random.random(attack.min, attack.max) * attack.mag)
        self.cur_hp -= dmg

    @property
    def hp(self) -> str:
        return f"{self.cur_hp}/{self.max_hp}"


class Attack:
    def __init__(self, amount: tuple[int, int], kw: str = "", mag: float = 1.0, acc: float = 1.0, crit=0,
                 missed=False, critted=False):
        self.amount = amount
        self.kw = kw
        self.mag = mag
        self.acc = acc
        self.crit = crit
        self.missed = missed
        self.critted = critted

    def miss_check(self) -> bool:
        self.missed = game_random.random() < self.acc
        return self.missed

    def contains_kw(self, kw: str) -> bool:
        if self.kw is None:
            return False
        return kw in self.kw.split('|')

    def add_kw(self, kw: str):
        if self.kw is None:
            self.kw = kw
        else:
            self.kw += f"|{kw}"

    def set_kws(self, kws: list[str]):
        self.kw = '|'.join(kws)

    @property
    def min(self) -> int:
        return self.amount[0]

    @property
    def max(self) -> int:
        return self.amount[1]


class CombatantMixIn(StatusMixIn, BuffMixIn):
    def __init__(self, cur_hp: int, max_hp: int, speed: int, buffs: Buffs = None):
        super().__init__(cur_hp, max_hp, speed)
        if buffs is None:
            self.buffs = Buffs()
        else:
            self.buffs = buffs

    @abstractmethod
    def factors(self, timing: Timing, **kw) -> tuple[FactorMixIn, ...]:
        pass

    def attack(self, enemy: CombatantMixIn, amount: tuple[int, int], kw: str) -> NoReturn:
        if enemy is None or enemy.dead:
            return
        attack = Attack(amount, kw)
        factors = self.modify(Timing.Attack, attack=attack, enemy=enemy, kw=kw)
        self.after_affect(Timing.Attack, factors, attack=attack, enemy=enemy, kw=kw)
        attack.miss_check()
        if attack.missed:
            return
        attack = enemy.defend(attack, self, kw)
        enemy.suffer(attack)

    def forge_attack(self, enemy: CombatantMixIn, amount: tuple[int, int], kw: str) -> Optional[Attack]:
        if enemy is None or enemy.dead:
            return
        attack = Attack(amount, kw)
        self.modify(Timing.Attack, attack=attack, enemy=enemy, kw=kw)
        return attack

    def defend(self, attack: Attack, enemy: CombatantMixIn, kw: str) -> Attack:
        factors = self.modify(Timing.Defend, attack=attack, enemy=enemy, kw=kw)
        self.after_affect(Timing.Defend, factors, attack=attack, enemy=enemy, kw=kw)
        return attack

    def moved(self, target: int):
        factors = self.modify(Timing.Move, target=target)
        self.after_affect(Timing.Move, factors, target=target)

    def move(self, target: int):
        factors = self.modify(Timing.Move, target=target)
        Arena.Instance.move(self, target)
        self.after_affect(Timing.Move, factors, target=target)

    def add_buff(self, buff: Buff):
        factors = self.modify(Timing.Buffed, buff=buff)
        self.buffs.add(buff)
        self.after_affect(Timing.Buffed, factors, buff=buff)

    def die(self):
        pass

    def modify(self, timing: Timing, **kw) -> Sequence[FactorMixIn]:
        factors = self.factors(timing, **kw)
        for factor in factors:
            factor.affect(timing, **kw)
        return factors

    @staticmethod
    def after_affect(timing: Timing, factors: Sequence[FactorMixIn], **kw) -> NoReturn:
        for factor in factors:
            factor.after_affect(timing, **kw)

    def heal(self, amount):
        pass

    def healed(self, amount):
        pass

    def find_target(self, target: Targeting) -> tuple[Optional[CombatantMixIn], ...]:
        return Arena.Instance.find_target(self, target)

    @property
    def index(self) -> int:
        return Arena.Instance.find_index(self)

    @property
    def position(self) -> Position:
        return Arena.Instance.find_position(self)

    def take(self, action: Action, target: Optional[Targeting]):
        action.execute(self, target)

    def execute(self, decision: Decision) -> NoReturn:
        if decision is None or decision[0] is None:
            return
        self.take(*decision)

    @abstractmethod
    def get_actions(self) -> tuple[Action, ...]:
        pass

    @abstractmethod
    async def get_decision(self) -> Decision:
        pass


class Arena(SingletonMixIn):
    Instance = None

    def __init__(self, left: list[Optional[CombatantMixIn], ...], right: list[Optional[CombatantMixIn], ...]):
        self._current = None
        self._round = 0
        self.left = left
        self.right = right
        self.action_order: list[CombatantMixIn] = []

    def move(self, combatant: CombatantMixIn, target: int):
        """
        Move the combatant to the target position.
        and the combatants that changed position will call moved method.
        """
        if combatant in self.left:
            previous_position = self.left.index(combatant)  # 3
            forward = previous_position > target  # True
            offset = -1 if forward else 1  # -1
            for i in range(previous_position, target, offset):
                print(i)
                self.left[i] = self.left[i + offset]
                if self.left[i] is not None:
                    self.left[i].moved(i)
            self.left[target] = combatant
        elif combatant in self.right:
            previous_position = self.right.index(combatant)
            forward = previous_position > target
            offset = -1 if forward else 1
            for i in range(previous_position, target, offset):
                self.right[i] = self.right[i + offset]
                if self.right[i] is not None:
                    self.right[i].moved(i)

            self.right[target] = combatant

    def get_current_actions(self) -> tuple[Action, ...]:
        return self.current.get_actions()

    def get_current_actions_description(self) -> str:
        return '\n'.join([f"{i}: {action}" for i, action in enumerate(self.get_current_actions())])

    def get_arena_info(self) -> str:
        return f"Round {self._round}\n" \
               f"Left: {[combatant for combatant in self.left]}\n" \
               f"Right: {[combatant for combatant in self.right]}\n" \
               f"Current: {self.current}"

    async def run(self):
        while True:
            if not self.action_order:
                self.action_order = self.get_action_order()
                self._round += 1
            combatant = self.action_order.pop(-1)
            self._current = combatant
            if combatant.dead or combatant not in self.left and combatant not in self.right:
                continue
            if combatant in self.left:
                print(self.get_arena_info())
                print("order:" + self.action_order.__str__())
                print()
                print(self.get_current_actions_description())

            decision = await combatant.get_decision()
            print(f"{combatant} decided to {decision}\n\n")
            combatant.execute(decision)
            self.clean_dead_in_order()
            if self.is_over():
                print("End")
                break

    def find_position(self, combatant: CombatantMixIn) -> Position:
        if combatant in self.left:
            return Position([True, self.left.index(combatant)])
        if combatant in self.right:
            return Position([False, self.right.index(combatant)])
        raise ValueError("Combatant not in arena")

    def find_index(self, combatant: CombatantMixIn) -> int:
        if combatant in self.left:
            return self.left.index(combatant)
        if combatant in self.right:
            return self.right.index(combatant)
        raise ValueError("Combatant not in arena")

    def find_target(self, combatant: CombatantMixIn, target: Targeting) -> tuple[Optional[CombatantMixIn], ...]:
        def find(li: list[CombatantMixIn], index: int):
            return li[index] if index != -1 else combatant

        pos = self.find_position(combatant)

        if target.selfhood:
            return (combatant,)
        elif target.selfless:
            if pos.left:
                return tuple(self.left[:pos[1]] + self.left[pos[1] + 1:])
            else:
                return tuple(self.right[:pos[1]] + self.right[pos[1] + 1:])

        friendly, selective = target.friendly, target.selective
        targets = target.positions
        if friendly ^ (pos.left):
            candi = self.right  # -1 means combatant himself
            return tuple(find(candi, i) for i in targets)
        else:
            candi = self.left
            return tuple(find(candi, i) for i in targets)

    def get_action_order(self) -> list[CombatantMixIn]:
        def not_none(c: CombatantMixIn) -> bool:
            return c is not None and not c.dead

        return sorted(filter(not_none, self.left + self.right), key=lambda c: c.speed, reverse=True)

    def start(self):
        self.action_order = self.get_action_order()

    @property
    def round_over(self) -> bool:
        return len(self.action_order) == 0

    def new_round(self):
        self.action_order = self.get_action_order()
        self._round += 1

    @property
    def current(self) -> CombatantMixIn:
        return self._current

    def clean_dead_in_order(self):
        for combatant in self.action_order:
            if combatant.dead:
                self.action_order.remove(combatant)

    @property
    def turn(self) -> int:
        return self._round

    def is_over(self) -> bool:
        def is_none_or_dead(c: CombatantMixIn) -> bool:
            return c is None or c.dead

        return all(map(is_none_or_dead, self.left)) or all(map(is_none_or_dead, self.right))


class Requirement(ABC):
    def __repr__(self):
        return self.__class__.__name__


class PreReqm(Requirement, ABC):
    @abstractmethod
    def check(self, receiver: CombatantMixIn) -> bool:
        pass


class PostReqm(Requirement, ABC):
    @abstractmethod
    def check(self, receiver: CombatantMixIn, targeting: Optional[Targeting]) -> Targeting:
        """
        filter out invalid targets
        @param receiver:
        @param targeting:
        @return:
        """
        pass


class SelfPositionalRequirement(PreReqm):
    def __init__(self, position: Position):
        self.position = position

    def check(self, receiver: CombatantMixIn) -> bool:
        return self.position.include(receiver.index)

    def __repr__(self):
        return f"Need Self Position: {self.position}"


class ValidTargetRequirement(PreReqm):
    def __init__(self, target: Targeting):
        self.target = target

    def check(self, receiver: CombatantMixIn) -> bool:
        return any([x is not None for x in receiver.find_target(self.target)])

    def __repr__(self):
        return f"Need Valid Target: {self.target}"


class PosReqm(PostReqm):
    def __init__(self, target: Targeting):
        self.target = target

    def check(self, receiver: CombatantMixIn, targeting: Optional[Targeting]) -> Targeting:
        if targeting is None:
            return self.target.alt(receiver.position)
        else:
            return targeting

    def __repr__(self):
        return f"Need Targeting: {self.target}"


class DistanceLimitReqm(PostReqm):
    def __init__(self, distance: int):
        self.distance = distance

    def check(self, receiver: CombatantMixIn, targeting: Optional[Targeting]) -> Targeting:
        pos = receiver.position
        tar = targeting.alt(pos)
        poss = filter(lambda x: abs(x - pos[1]) <= self.distance, tar[2:])
        return Targeting(tar[0], tar[1], *poss)


class Action:
    def __init__(self, exe_reqm: tuple[PreReqm, ...], tar_reqm: tuple[PostReqm, ...],
                 effects: tuple[tuple[Targeting, Effect], ...]):
        self.exe_reqm = exe_reqm
        self.tar_reqm = tar_reqm
        self.effects = effects

    def check(self, receiver: CombatantMixIn) -> bool:
        return all(req.check(receiver) for req in self.exe_reqm)

    def check_target(self, receiver: CombatantMixIn, target: Optional[Targeting] = None) -> Targeting:
        for req in self.tar_reqm:
            target = req.check(receiver, target)
            if target.none:
                raise TargetingError("No valid target")
        return target

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting]):
        for tar_eff in self.effects:
            tar, eff = tar_eff
            if tar.selective and target is None:
                raise TargetingError("Selective target required")
            if not tar.selective and target is not None:
                raise TargetingError("Aoe target not allowed")

            if tar.selective:
                tar = target
            eff.execute(receiver, tar)

    def __repr__(self):
        return f"{self.__class__.__name__}"


class Decision(tuple[Optional[Action], Optional[Targeting]]):
    def __repr__(self):
        return f"{self[0]} on {self[1]}"


# Decision = tuple[Optional[Action], Optional[Targeting]]


# region Equipment
class Equipment(FactorMixIn, ABC):
    @property
    @abstractmethod
    def occupation(self) -> tuple[Slot, ...]:
        pass

    @abstractmethod
    def action(self) -> tuple[Action, ...]:
        pass


class Slot(Enum):
    MainHand = 0
    OffHand = 1
    Amulet = 2
    Armor = 3


class Weapon(Equipment, ABC):
    def __init__(self, atk: int, band: tuple[int, int]):
        self.atk = atk
        self.band = band


class OneHandWeapon(Weapon, ABC):
    @property
    def occupation(self) -> tuple[Slot, ...]:
        return (Slot.MainHand,)


class TwoHandWeapon(Weapon, ABC):
    @property
    def occupation(self) -> tuple[Slot, ...]:
        return Slot.MainHand, Slot.OffHand


class OffHand(Equipment, ABC):
    @property
    def occupation(self) -> tuple[Slot, ...]:
        return (Slot.OffHand,)


class Amulet(Equipment, ABC):
    @property
    def occupation(self) -> tuple[Slot, ...]:
        return (Slot.Amulet,)


class Equipage(dict[Slot, Optional[Equipment]]):
    def __init__(self, *equipment: Optional[Equipment]):
        super().__init__()
        for slot in Slot:
            self[slot] = None
        for item in equipment:
            self.equip(item)

    def get_actions(self) -> tuple[Action, ...]:
        actions = []
        for item in self.values():
            if item is not None:
                actions.extend(item.action())
        return tuple(actions)

    @property
    def factors(self) -> Sequence[FactorMixIn, ...]:
        """
        just get all equipments, not including None, no repeat
        @return:
        """
        return list(set(filter(lambda x: x is not None, self.values())))

    def equip(self, equipment: Equipment):
        for slot in equipment.occupation:
            if self[slot]:
                raise ValueError("Slot already occupied")
            else:
                self[slot] = equipment

    @singledispatchmethod
    def unequip(self, slot: [Slot, Equipment]):
        pass

    @unequip.register
    def _(self, equipment: Equipment):
        for slot in equipment.occupation:
            self._ueq(slot)

    @unequip.register
    def _ueq(self, slot: Slot):
        if self[slot]:
            slots = self[slot].occupation
            for s in slots:
                self.pop(s)
                self[s] = None
        else:
            raise ValueError("Slot is empty")


class EquipageMixIn:
    def __init__(self, *equipment: Equipment):
        self.equipage = Equipage(*equipment)


# endregion


class Effect(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting]):
        pass
