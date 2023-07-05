from __future__ import annotations

from .buffs import *
from .effects import *
from .gameplay import Targeting as Tar
from .reqirements import *


class Bash(Action):
    """
    A simple attack.
    deal 10-15 damage to the target in position 1 and 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__(
            pre_reqm=(
                SelfPositionalRequirement(Position([True, 0, 1, 2])),
            ),
            post_reqm=(
                PosReqm(Tar.aoe_enemy(0, 1, 2)),
                TargetAliveReqm(),
            ),
            effects=(
                (Tar.aoe_enemy(0, 1, 2), Damage((2, 4))),
                (Tar.aoe_enemy(0, 1, 2), ApplyTargetBuff(Combo())),
            ),
            baton={IGNORE_EVADE: True}
        )


class Slash(Action):
    """
    A simple attack.
    deal 15-20 damage to the target in position 1 or 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__(
            (
                SelfPositionalRequirement(Position([True, 0, 1, 2])),
            ),
            (
                PosReqm(Targeting(False, True, 0, 1, 2)),
                TargetAliveReqm()
            ),
            (
                (Targeting(False, True, 1, 2), ComboConditionEffect(Damage((4, 6)), Damage((6, 9)), )),
            ))


class Bite(Action):
    """
    A simple attack.
    deal 4-7 damage to the target in position 1 or 2
    requires the caster to be in position 1 or 2
    """

    def __init__(self):
        super().__init__((
            SelfPositionalRequirement(Position([True, 0, 1, 2])),
            ValidTargetRequirement(Targeting(False, True, 0, 1, 2))
        ), (PosReqm(Targeting(False, True, 0, 1, 2)),), ((Targeting(False, True, 0, 1, 2), Damage((3, 7))),))


class Defend(Action):
    """
    Defend the caster.
    """

    def __init__(self):
        super().__init__((), (), ((Targeting(True, False, ONLY_SELF), AddSelfBuff(Strength())),))


class Move(Action):
    """
    Move to the target position.
    distance is the max distance the caster can move.
    """

    def __init__(self, distance: int):
        super().__init__(
            (),
            (PosReqm(Targeting.except_self()), DistanceLimitReqm(distance)),
            ((Targeting.except_self(), MoveTo(distance)),)
        )


class Skip(Action):
    def __init__(self):
        super().__init__((), (), ())


class Protect(Action):
    def __init__(self):
        super().__init__(
            (),
            (
                PosReqm(Targeting(True, True, EXCEPT_SELF)),
            ),
            (
                (Targeting(True, True, EXCEPT_SELF), ProtectTarget()),
                (Targeting(True, False, ONLY_SELF), ApplyTargetBuff(Block(3, 3)))
            )
        )


class Aiming(Action):
    def __init__(self):
        super().__init__(
            (
                SelfPositionalRequirement(Position([True, 1, 2, 3])),
            ),
            (
                PosReqm(Targeting(False, True, 1, 2, 3)),
                TargetAliveReqm()
            ),
            (
                (Targeting(False, True, 0, 1, 2, 3), ApplyTargetBuff(Combo())),
                (Targeting(False, True, 0, 1, 2, 3), ApplyTargetBuff(Combo())),
            ),
            {IGNORE_EVADE: True}
        )


class Shot(Action):
    def __init__(self):
        super().__init__(
            (
                SelfPositionalRequirement(Position([True, 1, 2, 3])),
            ),
            (
                PosReqm(Targeting(False, True, 1, 2, 3)),
                TargetAliveReqm()
            ),
            (
                (Targeting(False, True, 1, 2, 3),
                 ComboConditionEffect(Damage((6, 9)), Damage((12, 16), {IGNORE_EVADE: True}))),
            ),
        )


class Heal(Action):
    def __init__(self, amount: (int, int)):
        super().__init__(
            (),
            (
                PosReqm(Targeting(True, True, 0, 1, 2, 3)),
                TargetAliveReqm()
            ),
            (
                (Targeting(True, True, 0, 1, 2, 3), HealTarget(amount)),
            ),
        )
