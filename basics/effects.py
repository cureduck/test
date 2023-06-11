from __future__ import annotations

from .buffs import Protected
from .reqirements import *


class Heal(Effect):
    def __init__(self, amount: tuple[int, int]):
        super().__init__()
        self.amount = amount

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                aim.heal(self.amount, baton)


class Damage(Effect):
    def __init__(self, amount: tuple[int, int], baton: dict[str, Any] = None):
        super().__init__()
        self.amount = amount
        self.baton = baton

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton: dict[str, Any]):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                if self.baton is not None:
                    baton.update(self.baton)
                receiver.attack(aim, self.amount, baton)


class MoveTo(Effect):
    def __init__(self, distance: int):
        super().__init__()
        self.distance = distance

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        position = target[0]
        if position < 0 or position > 5:
            raise ValueError("Invalid position")
        if receiver.index - position > self.distance:
            raise ValueError("Too far")
        receiver.move(position)


class AddSelfBuff(Effect):
    def __init__(self, buff: Buff):
        super().__init__()
        self.buff = buff

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        receiver.add_buff(self.buff, baton)


class AddProtected(Effect):
    def __init__(self):
        super().__init__()

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        client = receiver.find_target(target)[0]
        client.add_buff(Protected(receiver), baton)


class ApplyTargetBuff(Effect):
    def __init__(self, buff: Buff):
        super().__init__()
        self.buff = buff

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                aim.add_buff(self.buff, baton)


class ProtectTarget(Effect):
    def __init__(self, stack: int = 3):
        super().__init__()
        self.stack = stack

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                aim.add_buff(Protected(receiver, self.stack), baton)


class ConditionalEffect(Effect):
    def __init__(self, condition: PreReqm, effect1: Effect, effect2: Effect):
        super().__init__()
        self.condition = condition
        self.effect1 = effect1
        self.effect2 = effect2

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        if self.condition.check(receiver):
            self.effect1.execute(receiver, target, baton)
        else:
            self.effect2.execute(receiver, target, baton)


class ComboConditionEffect(ConditionalEffect):
    def __init__(self, effect1: Effect, effect2: Effect):
        super().__init__(TargetHasComboReqm(), effect1, effect2)

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton):
        baton[COMBO] = True
        if self.condition.check(receiver):
            self.effect1.execute(receiver, target, baton)
        else:
            self.effect2.execute(receiver, target, baton)
