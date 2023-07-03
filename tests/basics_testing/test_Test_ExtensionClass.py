from basics import *


class CombatantMixInExtension:
    def new_TestUse_attack(self, enemy: CombatantMixIn, amount: tuple[int, int], baton: dict[str, Any], crit=.15,
                           acc=1.0) -> None:

        if enemy is None or enemy.dead:
            return
        attack = Attack(amount, crit=crit, acc=acc)
        attack.missed = baton.get(MISSED, None)
        attack.critted = baton.get(CRITTED, None)
        baton.update({ATTACKER: self, ATTACK: attack, DEFENDER: enemy})
        factors = self.modify(Timing.Attack, baton)
        self.after_affect(Timing.Attack, factors, baton)
        if attack.missed is None:
            baton[MISSED] = attack.miss_check()
        if attack.missed is True:
            return
        another = enemy.mislead(attack, self, baton)
        attack = another.defend(attack, self, baton)
        if attack.missed is False:
            baton[MISSED] = attack.miss_check()
        another.suffer(attack)


CombatantMixIn.__bases__ += (CombatantMixInExtension,)


class NewAttack(Attack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def miss_check(self):
        1.0 > self.acc
        self.acc = 1.0
        return self.missed
