from __future__ import annotations

from .buffs import Strength
from .gameplay import *


class Bash(Action):
    """
    A simple attack.
    deal 10-15 damage to the target in position 1 and 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__(
            (SelfPositionalRequirement(Position([True, 0, 1, 2])),),
            (),
            ((Targeting([False, False, 1, 2]), Damage((10, 15))),)
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
            (PosReqm(Targeting([False, True, 1, 2])),),
            ((Targeting([False, True, 1, 2]), Damage((15, 20))),)
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
                ValidTargetRequirement(Targeting([False, True, 0, 1, 2]))
            ),
            (PosReqm(Targeting([False, True, 0, 1, 2])),),
            ((Targeting([False, True, 0, 1, 2]), Damage((4, 7))),)
        )


class Defend(Action):
    """
    Defend the caster.
    """

    def __init__(self):
        super().__init__(
            (),
            (),
            ((Targeting([True, False, ITSELF]), AddSelfBuff(Strength())),)
        )


class Move(Action):
    """
    Move to the target position.
    distance is the max distance the caster can move.
    """

    def __init__(self, distance: int):
        super().__init__(
            (),
            (PosReqm(Targeting([True, True, EXCEPT_ITSELF])),),
            ((Targeting([True, True, EXCEPT_ITSELF]), MoveTo(distance)),)
        )


class Skip(Action):
    def __init__(self):
        super().__init__(
            (),
            (PosReqm(Targeting([True, True, ITSELF])),),
            ()
        )
