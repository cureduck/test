from __future__ import annotations

from .gameplay import *
from .KEYWORDS import *

class Heal(Effect):
    def __init__(self, amount: tuple[int, int]):
        super().__init__()
        self.amount = amount

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], **passed):
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                aim.heal(self.amount, **passed)


class Damage(Effect):
    def __init__(self, amount: tuple[int, int], **passing):
        super().__init__()
        self.amount = amount
        self.passing = passing

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], **passed) -> Optional[dict[str, Any]]:
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                passed.update(self.passing)
                return receiver.attack(aim, self.amount, **passed)


class MoveTo(Effect):
    def __init__(self, distance: int):
        super().__init__()
        self.distance = distance

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], **passed) -> Optional[dict[str, Any]]:
        position = target[0]
        if position < 0 or position > 5:
            raise ValueError("Invalid position")
        if receiver.index - position > self.distance:
            raise ValueError("Too far")
        receiver.move(position)
        return passed


class AddSelfBuff(Effect):
    def __init__(self, buff: Buff):
        super().__init__()
        self.buff = buff

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], **passed) -> Optional[dict[str, Any]]:
        receiver.add_buff(self.buff, **passed)
        return passed