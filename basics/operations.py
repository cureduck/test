from __future__ import annotations

from .buffs import *
from .effects import *
from .reqirements import *


class Bash(Action):
    """
    A simple attack.
    deal 10-15 damage to the target in position 1 and 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__(
            (SelfPositionalRequirement(Position([True, 0, 1, 2])),),
            (PosReqm(Targeting(False, False, 0, 1, 2)), TargetAliveReqm(),),
            (
                (Targeting(False, False, 0, 1, 2), Damage((2, 4), {IGNORE_EVADE: True})),
                (Targeting(False, False, 0, 1, 2), ApplyTargetBuff(Combo())),
            )
        )


class Slash(Action):
    """
    A simple attack.
    deal 15-20 damage to the target in position 1 or 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__(
            (SelfPositionalRequirement(Position([True, 0, 1, 2])),),
            (
                PosReqm(Targeting(False, True, 0, 1, 2)),
                TargetAliveReqm()
            ),
            (
                (Targeting(False, True, 1, 2), ComboConditionEffect(Damage((4, 6)), Damage((6, 9)), )),
            )
        )


class Bite(Action):
    """
    A simple attack.
    deal 4-7 damage to the target in position 1 or 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__(
            (
                SelfPositionalRequirement(Position([True, 0, 1, 2])),
                ValidTargetRequirement(Targeting(False, True, 0, 1, 2))
            ),
            (PosReqm(Targeting(False, True, 0, 1, 2)),),
            ((Targeting(False, True, 0, 1, 2), Damage((3, 7))),)
        )


class Defend(Action):
    """
    Defend the caster.
    """

    def __init__(self):
        super().__init__(
            (),
            (),
            ((Targeting(True, False, ITSELF), AddSelfBuff(Strength())),)
        )


class Move(Action):
    """
    Move to the target position.
    distance is the max distance the caster can move.
    """

    def __init__(self, distance: int):
        super().__init__(
            (),
            (PosReqm(Targeting(True, True, EXCEPT_ITSELF)), DistanceLimitReqm(distance)),
            ((Targeting(True, True, EXCEPT_ITSELF), MoveTo(distance)),)
        )


class Skip(Action):
    def __init__(self):
        super().__init__(
            (),
            (),
            ()
        )


class Protect(Action):
    def __init__(self):
        super().__init__(
            (),
            (),
            (
                (Targeting(True, True, EXCEPT_ITSELF), AddSelfBuff(Strength())),
                (Targeting(True, True, ITSELF), AddSelfBuff(Strength())),
            )
        )
