from __future__ import annotations

from .KEYWORDS import *
from .gameplay import *


class Dodge(PositiveBuff):
    def may_affect(self, timing: Timing, baton) -> bool:
        if timing == Timing.Defend:
            return True
        return False

    def affect(self, timing: Timing, baton):
        if timing == Timing.Defend:
            attack = baton[ATTACK]
            assert isinstance(attack, Attack)
            if baton.get(IGNORE_EVADE, False):
                pass
            else:
                attack.acc /= 2

    @property
    def name(self) -> str:
        return "Dodge"

    def __repr__(self):
        return "D"


class Strength(PositiveBuff):
    def may_affect(self, timing: Timing, baton) -> bool:
        if timing == Timing.Attack:
            return True
        return False

    def affect(self, timing: Timing, baton):
        if timing == Timing.Attack:
            attack = baton[ATTACK]
            assert isinstance(attack, Attack)
            attack.mag += .5

    @property
    def name(self) -> str:
        return "Strength"

    def __repr__(self):
        return "S"


class Protected(PositiveBuff):
    @property
    def name(self) -> str:
        return 'Protected'

    def __init__(self, protector):
        super().__init__()
        self.protector = protector

    def may_affect(self, timing: Timing, baton) -> bool:
        if timing == Timing.Mislead:
            return True
        return False

    def affect(self, timing: Timing, baton):
        if timing == Timing.Mislead:
            defender = baton[DEFENDER]
            assert isinstance(defender, CombatantMixIn)
            pos = Arena().find_position(defender)
            another_pos = Targeting(True, True, 0)
            another = defender.find_target(another_pos)
            baton[MISLEAD_TARGET] = self.protector
            print(f"mislead to {self.protector}")

    def __repr__(self):
        return "P"
