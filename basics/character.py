from __future__ import annotations

from .operations import *


class Faith(FactorMixIn, ABC):
    pass


class Race(FactorMixIn, ABC):
    pass


# region combatants
class Brain(ABC):
    @abstractmethod
    def decide(self, caster: CombatantMixIn, arena: Arena) -> Decision:
        pass

    @staticmethod
    def get_castable_actions(caster: CombatantMixIn) -> list[Action, ...]:
        return list(filter(lambda x: x.check(caster), caster.get_actions()))

    @staticmethod
    def get_castable_targets(caster: CombatantMixIn, action: Action, targeting: Optional[Targeting]) -> Targeting:
        return action.check_target(caster, targeting)


class PlayerBrain(Brain, SingletonMixIn):
    async def decide(self, caster: CombatantMixIn, arena: Arena) -> Optional[Decision]:
        while True:
            try:
                actions = caster.get_actions()
                if len(actions) == 0:
                    print("no action available")
                    return None
                action_index = int(input("choose action:"))
                action = actions[action_index]
                if action.pre_reqm in (None, ()):
                    return Decision([action, None])
                legal_targets = action.check_target(caster)
                if len(legal_targets) == 0:
                    print("no legal target")
                    continue
                print(f"legal targets: {legal_targets}")
                if legal_targets.selective:
                    target_index = int(input("choose target:"))
                    if target_index in legal_targets:
                        targeting = legal_targets.choose(target_index)
                        return Decision([action, targeting])
                    else:
                        print("target index out of range, try again")
                        continue
                else:
                    return Decision([action, None])
            except IndexError:
                print("action index out of range, try again")
                continue
            except TargetingError as e:
                print(e)
                continue
            except Exception as e:
                print(e)
                continue


class AIBrain(Brain, SingletonMixIn):
    def __init__(self, rand: Random = None):
        if rand is None:
            return
        self.rand = rand

    def decide(self, caster: CombatantMixIn, arena: Arena) -> Optional[Decision]:
        actions = self.get_castable_actions(caster)

        while True:
            if len(actions) == 0:
                return None
            action = self.choose_preferred_action(actions, caster)
            if action.pre_reqm in (None, ()):
                return Decision([Action, None])
            try:
                targeting = self.choose_preferred_target(caster, action)
                return Decision([action, targeting])
            except TargetingError:
                actions.remove(action)

    def choose_preferred_action(self, actions: Sequence[Action, ...], caster: CombatantMixIn) -> Action:
        """
        temporary random choose
        """
        return self.rand.choice(actions)

    def choose_preferred_target(self, caster: CombatantMixIn, action: Action) -> Optional[Targeting]:
        """
        temporary random choose
        """
        if action.pre_reqm in (None, ()):
            return None
        targets = self.get_castable_targets(caster, action, None)
        return targets.random_choose(self.rand)


AIBrain(Random())

PlayerBrain()


class Character(CombatantMixIn, EquipageMixIn):
    async def get_decision(self) -> Decision:
        return await PlayerBrain().decide(self, Arena())

    def factors(self, timing: Timing, baton) -> Sequence[FactorMixIn, ...]:
        return list(filter(lambda x: x.may_affect(timing, baton), self.buffs + self.equipage.factors))

    def __init__(self, name: str, cur_hp: int, base_max_hp: int, base_speed: int, buffs: Buffs = None,
                 *equipment: Equipment):
        CombatantMixIn.__init__(self, name, cur_hp, base_max_hp, base_speed, buffs)
        EquipageMixIn.__init__(self, *equipment)

    def get_actions(self) -> tuple[Action, ...]:
        return self.equipage.get_actions() + self.basic_actions()

    @staticmethod
    def basic_actions() -> tuple[Action, ...]:
        return Move(2), Skip()


class Monster(CombatantMixIn):
    def factors(self, timing: Timing, baton) -> Sequence[FactorMixIn, ...]:
        return list(filter(lambda x: x.may_affect(timing, baton), self.buffs))

    def __init__(self, name: str, cur_hp: int, base_max_hp: int, base_speed: int, buffs: Buffs = None):
        CombatantMixIn.__init__(self, name, cur_hp, base_max_hp, base_speed, buffs)

    @property
    @abstractmethod
    def preference(self) -> tuple[str, ...]:
        pass

    async def get_decision(self) -> Decision:
        return AIBrain().decide(self, Arena())
        # return await PlayerBrain().decide(self, Arena())


# endregion


class WildDog(Monster):

    @property
    def preference(self) -> tuple[str, ...]:
        return ()

    def __init__(self, name: str, cur_hp: int = 24, base_max_hp: int = 24, base_speed: int = 9):
        super().__init__(name, cur_hp, base_max_hp, base_speed)
        self.buffs = Buffs(Dodge())

    def get_actions(self) -> (Action, ...):
        return (Bite(),)


class Robber(Monster):

    @property
    def preference(self) -> tuple[str, ...]:
        return ()

    def __init__(self, name: str, cur_hp: int = 24, base_max_hp: int = 24, base_speed: int = 9):
        super().__init__(name, cur_hp, base_max_hp, base_speed)
        self.buffs = Buffs()

    def get_actions(self) -> (Action, ...):
        return (Bite(),)