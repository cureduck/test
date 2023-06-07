from __future__ import annotations
from typing import Union

from .gameplay import *


class Dodge(PositiveBuff):
    def may_affect(self, timing: Timing) -> bool:
        if timing == Timing.Defend:
            return True
        return False

    def affect(self, timing: Timing, **kw: dict[str, Union[CombatantMixIn, Attack]]):
        if timing == Timing.Defend:
            attack = kw["attack"]
            assert isinstance(attack, Attack)
            if not attack.contains_kw(IGNORE_EVADE):
                attack.acc /= 2

    @property
    def name(self) -> str:
        return "Dodge"

    def __repr__(self):
        return "D"


class Strength(PositiveBuff):
    def may_affect(self, timing: Timing) -> bool:
        if timing == Timing.Attack:
            return True
        return False

    def affect(self, timing: Timing, **kw: dict[str, Union[CombatantMixIn, Attack]]):
        if timing == Timing.Attack:
            attack = kw["attack"]
            assert isinstance(attack, Attack)
            attack.mag += .5

    @property
    def name(self) -> str:
        return "Strength"

    def __repr__(self):
        return "S"
