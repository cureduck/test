from __future__ import annotations

from .gameplay import *


class Dodge(IndBuff):
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


class Strength(IndBuff):
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


class Protected(IndBuff):
    @property
    def name(self) -> str:
        return 'Protected'

    def __init__(self, protector: CombatantMixIn):
        super().__init__()
        self.protector = protector

    def may_affect(self, timing: Timing, baton) -> bool:
        if timing == Timing.Mislead:
            return True
        elif timing == Timing.Death:
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

    def expire(self) -> bool:
        if super().expire:
            return self.protector.dead


class Combo(RefBuff):
    stackable = False

    def may_affect(self, timing: Timing, baton) -> bool:
        if timing == Timing.Defend and COMBO in baton.keys():
            return True
        return False

    def affect(self, timing: Timing, baton):
        pass

    @property
    def name(self) -> str:
        return "Combo"

    def __repr__(self):
        return "C"
