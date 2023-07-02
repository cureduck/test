from .gameplay import *


class SelfPositionalRequirement(PreReqm):
    def __init__(self, position: Position):
        self.position = position

    def check(self, receiver: CombatantMixIn) -> bool:
        return self.position.include(receiver.index)

    def __repr__(self):
        return f"Need Self Position: {self.position}"


class ValidTargetRequirement(PreReqm):
    def __init__(self, target: Targeting):
        self.target = target

    def check(self, receiver: CombatantMixIn) -> bool:
        return any([x is not None for x in receiver.find_target(self.target)])

    def __repr__(self):
        return f"Need Valid Target: {self.target}"


class PosReqm(PostReqm):
    def __init__(self, target: Targeting):
        self.target = target

    def check(self, receiver: CombatantMixIn, targeting: Optional[Targeting]) -> Targeting:
        if targeting is None:
            return self.target.alt(receiver.position)
        else:
            return targeting

    def __repr__(self):
        return f"Need Targeting: {self.target}"


class DistanceLimitReqm(PostReqm):
    def __init__(self, distance: int):
        self.distance = distance

    def check(self, receiver: CombatantMixIn, targeting: Optional[Targeting]) -> Targeting:
        pos = receiver.position
        tar = targeting.alt(pos)
        poss = filter(lambda x: abs(x - pos[1]) <= self.distance, tar.positions)
        return Targeting(tar.friendly, tar.selective, *poss)


class TargetAliveReqm(PostReqm):
    def check(self, receiver: CombatantMixIn, targeting: Optional[Targeting]) -> Targeting:
        def alive(combatant: Optional[CombatantMixIn]) -> bool:
            if combatant is None:
                return False
            assert isinstance(combatant, CombatantMixIn)
            return not combatant.dead

        targets = receiver.find_target(targeting, alive)
        return Targeting(targeting.friendly, targeting.selective, *[target.index for target in targets])


class TargetHasBuffReqm(PreReqm):
    def __init__(self, buff: str):
        self.buff = buff

    def check(self, receiver: CombatantMixIn) -> bool:
        return any([x.name == self.buff for x in receiver.buffs])


class TargetHasComboReqm(TargetHasBuffReqm):
    def __init__(self):
        super().__init__("Combo")