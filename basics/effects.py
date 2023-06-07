from __future__ import annotations

from .gameplay import *


class Heal(Effect):
    def __init__(self, amount: tuple[int, int]):
        super().__init__()
        self.amount = amount

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting]):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                aim.heal(self.amount)


class Damage(Effect):
    def __init__(self, amount: tuple[int, int], keywords: str = None):
        super().__init__()
        self.amount = amount
        self.keywords = keywords

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting]):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                receiver.attack(aim, self.amount, self.keywords)


class MoveTo(Effect):
    def __init__(self, distance: int):
        super().__init__()
        self.distance = distance

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting]):
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

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting]):
        receiver.add_buff(self.buff)
