from __future__ import annotations

from .gameplay import *


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

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton: dict[str, Any]) -> Optional[
        dict[str, Any]]:
        targets = receiver.find_target(target)
        for aim in targets:
            if aim is not None:
                if self.baton is not None:
                    baton.update(self.baton)
                receiver.attack(aim, self.amount, baton)
        return baton


class MoveTo(Effect):
    def __init__(self, distance: int):
        super().__init__()
        self.distance = distance

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], baton) -> Optional[dict[str, Any]]:
        position = target[0]
        if position < 0 or position > 5:
            raise ValueError("Invalid position")
        if receiver.index - position > self.distance:
            raise ValueError("Too far")
        receiver.move(position)
        return baton


class AddSelfBuff(Effect):
    def __init__(self, buff: Buff):
        super().__init__()
        self.buff = buff

    def execute(self, receiver: CombatantMixIn, target: Optional[Targeting], **baton) -> Optional[dict[str, Any]]:
        receiver.add_buff(self.buff, baton)
        return baton
