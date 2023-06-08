from __future__ import annotations

from abc import abstractmethod, ABC
from enum import Enum, IntFlag
from functools import singledispatchmethod
from random import Random
from typing import Optional, NoReturn, Sequence, Any, Callable

from .KEYWORDS import *
from .rand import *
from .singleton import *

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

    def __getitem__(self, item) -> int:
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
        if attack.critted is None:
            attack.critted = game_random.random() < attack.crit
        if attack.critted:
            dmg = int(attack.min * attack.mag * 1.5)
        else:
            dmg = int(game_random.randint(attack.min, attack.max) * attack.mag)
        self.cur_hp -= dmg

    @property
    def hp(self) -> str:
        return f"{self.cur_hp}/{self.max_hp}"


class Attack:
    def __init__(self, amount: tuple[int, int], mag: float = 1.0, acc: float = 1.0, crit=0,
                 missed: Optional[bool] = None, critted: Optional[bool] = None):
        """

        @param amount: min and max damage
        @param mag: magnification, 1 means normal, 0 means no damage, 2 means double damage
        @param acc: chance to hit, 0 means can't hit, between 0 and 1 means can hit
        @param crit: chance to crit, 0 means can't crit, between 0 and 1 means can crit
        @param missed: None means haven't checked yet, True means missed, False means not missed
        @param critted: None means haven't checked yet, True means critted, False means not critted
        """
        self.amount = amount
        self.mag = mag
        self.acc = acc
        self.crit = crit
        self.missed = missed
        self.critted = critted

    def miss_check(self) -> bool:
        self.missed = game_random.random() > self.acc
        return self.missed

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

    def attack(self, enemy: CombatantMixIn, amount: tuple[int, int], **passed) -> Optional[dict[str, Any]]:
        """
        Attack the enemy.
        @param enemy:
        @param amount:
        @param passed: passed to factors
        @return:
        """
        if enemy is None or enemy.dead:
            return passed
        attack = Attack(amount)
        attack.missed = passed.get(MISSED, None)
        attack.critted = passed.get(CRITTED, None)
        factors = self.modify(Timing.Attack, attack=attack, enemy=enemy, **passed)
        self.after_affect(Timing.Attack, factors, attack=attack, enemy=enemy, **passed)
        if attack.missed is None:
            attack.miss_check()
        if attack.missed:
            passed[MISSED] = True
        attack = enemy.defend(attack, self, **passed)
        enemy.suffer(attack)
        return passed

    def defend(self, attack: Attack, enemy: CombatantMixIn, **passed) -> Attack:
        factors = self.modify(Timing.Defend, attack=attack, enemy=enemy, **passed)
        self.after_affect(Timing.Defend, factors, attack=attack, enemy=enemy, **passed)
        return attack

    def moved(self, target: int):
        factors = self.modify(Timing.Move, target=target)
        self.after_affect(Timing.Move, factors, target=target)

    def move(self, target: int):
        factors = self.modify(Timing.Move, target=target)
        Arena().move(self, target)
        self.after_affect(Timing.Move, factors, target=target)

    def add_buff(self, buff: Buff, **kw):
        factors = self.modify(Timing.Buffed, buff=buff, **kw)
        self.buffs.add(buff)
        self.after_affect(Timing.Buffed, factors, buff=buff, **kw)

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

    def heal(self, amount, **passed):
        pass

    def find_target(self, target: Targeting, term: Callable[[CombatantMixIn], bool] = None) -> \
            Sequence[Optional[CombatantMixIn], ...]:
        return Arena().find_target(self, target, term)

    @property
    def index(self) -> int:
        return Arena().find_index(self)

    @property
    def position(self) -> Position:
        return Arena().find_position(self)

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
    def __init__(self, left: list[Optional[CombatantMixIn], ...] = None,
                 right: list[Optional[CombatantMixIn], ...] = None):
        """
        create a new arena or load from the previous one if left and right are None.
        @param left:
        @param right:
        """
        if left is None and right is None:
            return
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

    def find_target(self, combatant: CombatantMixIn, target: Targeting,
                    term: Callable[[CombatantMixIn], bool] = None) -> Sequence[Optional[CombatantMixIn], ...]:
        def find(li: list[CombatantMixIn], index: int) -> Optional[CombatantMixIn]:
            return li[index]

        pos = self.find_position(combatant)

        if target.selfhood:
            candidates = [combatant]
        elif target.selfless:
            if pos.left:
                candidates = self.left[:pos[1]] + self.left[pos[1] + 1:]
            else:
                candidates = self.right[:pos[1]] + self.right[pos[1] + 1:]
        else:
            friendly, selective = target.friendly, target.selective
            targets = target.positions
            if friendly ^ pos.left:
                candi = self.right  # -1 means combatant himself
                candidates = [find(candi, i) for i in targets]
            else:
                candi = self.left
                candidates = [find(candi, i) for i in targets]
        if term is not None:
            candidates = list(filter(term, candidates))
            return candidates
        else:
            return candidates

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
        @param receiver: the combatant who is executing the action
        @param targeting:
        @return:
        """
        pass


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
        result = None
        for tar_eff in self.effects:
            tar, eff = tar_eff
            if tar.selective and target is None:
                raise TargetingError("Selective target required")
            if not tar.selective and target is not None:
                raise TargetingError("Aoe target not allowed")

            if tar.selective:
                tar = target
            if result is None:
                result = eff.execute(receiver, tar)
            else:
                result = eff.execute(receiver, tar, **result)

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
    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], **passed: dict) -> dict:
        """

        @param receiver:
        @param target:
        @param passed: the keywords passed from previous effect
        @return:
        """
        pass
