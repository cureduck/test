from __future__ import annotations

from .character import *
from .operations import *
from .KEYWORDS import *

class Sword(OneHandWeapon):
    def __init__(self):
        super().__init__(10, (1, 2))

    def action(self) -> tuple[Action, ...]:
        return Bash(), Slash()


class Shield(OffHand):
    def __init__(self):
        super().__init__()

    def action(self) -> tuple[Action, ...]:
        return (Defend(),)

    def may_affect(self, timing: Timing, **kw) -> bool:
        if timing == Timing.Defend:
            return True
        return False

    def affect(self, timing: Timing, **kw: dict[str, Union[Character, Attack]]):
        if timing == Timing.Defend:
            attack = kw[ATTACK]
            assert isinstance(attack, Attack)
            attack.crit /= 2
