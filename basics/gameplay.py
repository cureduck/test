from __future__ import annotations

import copy
from abc import abstractmethod, ABC
from enum import Enum
from functools import singledispatchmethod
from random import Random
from typing import Optional, NoReturn, Sequence, Any, Callable

from .KEYWORDS import *
from .rand import *
from .singleton import *
from .timing import *

ARENA_WIDTH = 4


class FactorMixIn(ABC):
    def affect(self, timing: Timing, baton) -> NoReturn:
        pass

    def may_affect(self, timing: Timing, baton: dict[str, Any]) -> bool:
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

    def after_affect(self, timing: Timing, baton: dict[str, Any]) -> NoReturn:
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
        selective = "single" if self.selective else "aoe"
        pos = ",".join([str(x) for x in self.positions])
        return f"{friendly}, {selective}, {pos}"

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

    def __repr__(self):
        return f"{self.name}"

    @abstractmethod
    def add(self, buff: Buff) -> NoReturn:
        pass

    @property
    @abstractmethod
    def expire(self) -> bool:
        pass

    stackable = True

    def on_turn_end(self):
        pass

    def on_expire(self):
        pass

    def clone(self):
        return copy.deepcopy(self)


class Timer(list[int, int]):
    def __init__(self, duration: int, stack: int = 1):
        super().__init__([duration, stack])

    def tick(self):
        self[0] -= 1


class IndBuff(Buff, ABC):  # independent refresh time buff
    def __init__(self, duration: int = 3, stack: int = 1):
        self.timers = [Timer(duration, stack)]

    def add(self, ind_buff: IndBuff):
        self.timers.append(ind_buff.timers[0])

    def on_turn_end(self):
        for timer in self.timers:
            timer.tick()
        filter(lambda t: t[0] > 0, self.timers)

    @property
    def expire(self) -> bool:
        return len(self.timers) == 0

    def after_affect(self, timing: Timing, baton: dict[str, Any]) -> NoReturn:
        def find_shortest() -> Timer:
            shortest = self.timers[0]
            for timer in self.timers:
                if timer[0] < shortest[0]:
                    shortest = timer
            return shortest

        self.timers.remove(find_shortest())
        self.on_expire()


class RefBuff(Buff, ABC):  # refresh time buff
    def __init__(self, duration: int = 3, stack: int = 1):
        self.duration = duration
        self.stack = stack

    def add(self, ref_buff: RefBuff):
        if self.stackable:
            self.stack += ref_buff.stack
            self.duration = max(self.duration, ref_buff.duration)
        else:
            self.stack = 1
            self.duration = ref_buff.duration

    @property
    def expire(self) -> bool:
        return self.duration <= 0 or self.stack <= 0

    def after_affect(self, timing: Timing, baton: dict[str, Any]) -> NoReturn:
        self.stack -= 1
        self.on_expire()


class Buffs(list[Buff]):
    def __init__(self, *args: Buff):
        super().__init__(args)
        for buff in self:
            buff.on_expire = self.check_expire

    def add(self, buff: Buff):
        for b in self:
            if b.name == buff.name:
                b.add(buff)
                return

        self.append(buff)
        buff.on_expire = self.check_expire

    def check_expire(self):
        buffs_to_remove = []
        for buff in self:
            if buff.expire:
                buffs_to_remove.append(buff)
        for buff in buffs_to_remove:
            self.remove(buff)

    def turn_end(self):
        for buff in self:
            buff.on_turn_end()
        self.check_expire()

    def __repr__(self):
        return ",".join([str(buff) for buff in self])


class Attack:
    def __init__(self, amount: tuple[int, int], mag: float = 1.0, acc: float = 1.0, crit: float = 0,
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
        self.acc = 1.0
        return self.missed

    @property
    def min(self) -> int:
        return self.amount[0]

    @property
    def max(self) -> int:
        return self.amount[1]


class CombatantMixIn(ABC):
    def __init__(self, name: str, cur_hp: int, base_max_hp: int, base_speed: int, buffs: Buffs = None):
        self.name = name
        self.cur_hp = cur_hp
        self.base_max_hp = base_max_hp
        self.base_speed = base_speed
        self.buffs = buffs or Buffs()

        self.cache_max_hp = None
        self.cache_speed = None

    def _set_speed(self):
        self.cache_speed = self.base_speed
        kwargs = {THIS: self}
        self.modify(timing=Timing.GetSpeed, **kwargs)

    def _set_max_hp(self):
        self.cache_max_hp = self.base_max_hp
        kwargs = {THIS: self}
        self.modify(timing=Timing.GetMaxHp, baton=kwargs)

    @property
    def dead(self) -> bool:
        return self.cur_hp <= 0

    def suffer(self, attack: Attack) -> NoReturn:
        if attack.missed:
            print(f"{self.name} missed")
            return
        if attack.critted is None:
            attack.critted = game_random.random() < attack.crit
        if attack.critted:
            dmg = int(attack.min * attack.mag * 1.5)
        else:
            dmg = int(game_random.randint(attack.min, attack.max) * attack.mag)
        self.cur_hp -= dmg
        critted_str = "critted" if attack.critted else ""
        print(f"{self.name} suffer {dmg} damage, {self.hp} left {critted_str}")

    @property
    def max_hp(self) -> int:
        self._set_max_hp()
        return self.cache_max_hp

    @property
    def speed(self) -> int:
        self._set_speed()
        return self.cache_speed

    @property
    def hp(self) -> str:
        return f"{self.cur_hp}/{self.max_hp}"

    @abstractmethod
    def factors(self, timing: Timing, baton: dict[str, Any]) -> Sequence[FactorMixIn, ...]:
        pass

    def attack(self, enemy: CombatantMixIn, amount: tuple[int, int], baton: dict[str, Any], crit=.15) -> None:
        """
        Attack the enemy.
        @param crit:
        @param enemy:
        @param amount:
        @param baton: passed to factors
        @return:
        """
        if enemy is None or enemy.dead:
            return
        attack = Attack(amount, crit=crit)
        attack.missed = baton.get(MISSED, None)
        attack.critted = baton.get(CRITTED, None)
        baton.update({ATTACKER: self, ATTACK: attack, DEFENDER: enemy})
        factors = self.modify(Timing.Attack, baton)
        self.after_affect(Timing.Attack, factors, baton)
        if attack.missed is None:
            baton[MISSED] = attack.miss_check()
        if attack.missed is True:
            return
        another = enemy.mislead(attack, self, baton)
        attack = another.defend(attack, self, baton)
        if attack.missed is False:
            baton[MISSED] = attack.miss_check()
        another.suffer(attack)

    def mislead(self, attack: Attack, attacker: CombatantMixIn, baton: dict[str, Any]) -> CombatantMixIn:
        """
        when a target is going to be attacked by someone else, mislead will try someone else to
        take the attack for me.
        @param attack:
        @param attacker:
        @param baton:
        @return:
        """
        factors = self.modify(Timing.Mislead, baton)
        self.after_affect(Timing.Mislead, factors, baton)
        return baton.get(MISLEAD_TARGET, self)

    def defend(self, attack: Attack, enemy: CombatantMixIn, baton: dict[str, Any]) -> Attack:
        factors = self.modify(Timing.Defend, baton)
        self.after_affect(Timing.Defend, factors, baton)
        return attack

    def moved(self, target: int):
        kws = {TARGET_POSITION: target}
        factors = self.modify(Timing.Move, **kws)
        self.after_affect(Timing.Move, factors, **kws)

    def move(self, target: int):
        kws = {TARGET_POSITION: target}
        factors = self.modify(Timing.Move, **kws)
        Arena().move(self, target)
        self.after_affect(Timing.Move, factors, **kws)

    def add_buff(self, buff: Buff, baton):
        b = buff.clone()
        baton.update({BUFF: b})
        factors = self.modify(Timing.Buffed, baton)
        self.buffs.add(b)
        self.after_affect(Timing.Buffed, factors, baton)

    def die(self):
        pass

    def modify(self, timing: Timing, baton: dict[str, Any]) -> Sequence[FactorMixIn]:
        factors = self.factors(timing, baton)
        for factor in factors:
            factor.affect(timing, baton)
        return factors

    @staticmethod
    def after_affect(timing: Timing, factors: Sequence[FactorMixIn], baton: dict[str, Any]) -> NoReturn:
        for factor in factors:
            factor.after_affect(timing, baton)

    def heal(self, amount, baton):
        pass

    def find_target(self, target: Targeting, filtor: Callable[[CombatantMixIn], bool] = None) -> \
            Sequence[Optional[CombatantMixIn], ...]:
        return Arena().find_target(self, target, filtor)

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

    def __repr__(self):
        return f"{self.name} {self.hp} {self.buffs}"

    @max_hp.setter
    def max_hp(self, value):
        self.cache_max_hp = value


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
        def get_info(combatant: Optional[CombatantMixIn]):
            if combatant is None:
                return "None".ljust(30, ' ')
            else:
                if combatant.dead:
                    return f"{combatant} (dead)".ljust(30, '-')
                else:
                    return f"{combatant}".ljust(30, ' ')

        return f"Round {self._round}\n" \
               f"Left : {[get_info(combatant) for combatant in self.left]}\n" \
               f"Right: {[get_info(combatant) for combatant in self.right]}\n"

    async def run(self):
        while True:
            if not self.action_order:
                self.action_order = self.get_action_order()
                self._round += 1
            combatant = self.action_order.pop(-1)
            self._current = combatant
            print(f"{combatant}".ljust(143, '-'))
            if combatant.dead or combatant not in self.left and combatant not in self.right:
                continue
            if combatant in self.left:
                print(self.get_arena_info())
                print(self.get_current_actions_description())

            decision = await combatant.get_decision()
            print(f"{combatant} decided to {decision}\n")
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
                    filtor: Callable[[CombatantMixIn], bool] = None) -> Sequence[Optional[CombatantMixIn], ...]:
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
        if filtor is not None:
            candidates = list(filter(filtor, candidates))
            return candidates
        else:
            return candidates

    def get_action_order(self) -> list[CombatantMixIn]:
        def not_none(c: CombatantMixIn) -> bool:
            return c is not None and not c.dead

        return sorted(filter(not_none, self.left + self.right), key=lambda c: c.base_speed, reverse=True)

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

    def execute(self, receiver: CombatantMixIn, selected_target: Optional[Targeting]):
        """

        @param receiver:
        @param selected_target: selected target can be None if the action is not selective
        @return:
        """
        baton = dict()
        for tar_eff in self.effects:
            tar, eff = tar_eff
            if tar.selective and selected_target is None:
                raise TargetingError("Selective target required")
            if not tar.selective and selected_target is not None:
                raise TargetingError("Aoe target not allowed")

            if tar.selective:
                tar = selected_target
            eff.execute(receiver, tar, baton)

    def __repr__(self):
        return f"{self.__class__.__name__}"


class Decision(tuple[Optional[Action], Optional[Targeting]]):
    def __repr__(self):
        if self[1] is None:
            return f"{self[0]}"
        else:
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
    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton: dict[str, Any]) -> NoReturn:
        """

        @param receiver:
        @param target:
        @param baton: the keywords passed from previous effect
        @return:
        """
        pass
