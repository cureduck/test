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


class PlayerBrain(Brain):
    async def decide(self, caster: CombatantMixIn, arena: Arena) -> Optional[Decision]:
        while True:
            try:
                actions = caster.get_actions()
                if len(actions) == 0:
                    print("no action available")
                    return None
                action_index = int(input("choose action:"))
                action = actions[action_index]
                if action.tar_reqm in (None, ()):
                    return Decision([action, None])
                legal_targets = action.check_target(caster)
                print(f"legal targets: {legal_targets}")
                target_index = int(input("choose target:"))
                if target_index in legal_targets:
                    targeting = action.check_target(caster).choose(target_index)
                    return Decision([action, targeting])
                else:
                    print("target index out of range, try again")
                    continue
            except IndexError:
                print("action index out of range, try again")
                continue
            except TargetingError as e:
                print(e)
                continue
            except Exception as e:
                print(e)
                continue


class AIBrain(Brain):
    def __init__(self, rand: Random):
        self.rand = rand

    def decide(self, caster: CombatantMixIn, arena: Arena) -> Optional[Decision]:
        actions = self.get_castable_actions(caster)

        while True:
            if len(actions) == 0:
                return None
            action = self.choose_preferred_action(actions, caster)
            if action.tar_reqm in (None, ()):
                return Decision([Action, None])
            try:
                targeting = self.choose_preferred_target(caster, action, arena)
                return Decision([action, targeting])
            except TargetingError:
                actions.remove(action)

    def choose_preferred_action(self, actions: Sequence[Action, ...], caster: CombatantMixIn) -> Action:
        """
        temporary random choose
        """
        return self.rand.choice(actions)

    def choose_preferred_target(self, caster: CombatantMixIn, action: Action, arena: Arena) -> Optional[Targeting]:
        """
        temporary random choose
        """
        if action.tar_reqm in (None, ()):
            return None
        targets = self.get_castable_targets(caster, action, None)
        return targets.random_choose(self.rand)


monster_brain = AIBrain(Random())

player_brain = PlayerBrain()


class Character(CombatantMixIn, EquipageMixIn):
    async def get_decision(self) -> Decision:
        return await player_brain.decide(self, Arena())

    def factors(self, timing: Timing, **kw) -> Sequence[FactorMixIn, ...]:
        return list(filter(lambda x: x.may_affect(timing, **kw), self.buffs + self.equipage.factors))

    def __init__(self, name: str, cur_hp: int, max_hp: int, speed: int, buffs: Buffs = None, *equipment: Equipment):
        CombatantMixIn.__init__(self, cur_hp, max_hp, speed, buffs)
        EquipageMixIn.__init__(self, *equipment)
        self.name = name

    def get_actions(self) -> tuple[Action, ...]:
        return self.equipage.get_actions() + self.basic_actions()

    def __repr__(self):
        return f"{self.name} {self.hp} {self.buffs}"

    @staticmethod
    def basic_actions() -> tuple[Action, ...]:
        return Move(2), Skip()


class Monster(CombatantMixIn):
    def factors(self, timing: Timing, **kw) -> Sequence[FactorMixIn, ...]:
        return list(filter(lambda x: x.may_affect(timing, **kw), self.buffs))

    def __init__(self, name: str, cur_hp: int, max_hp: int, speed: int, buffs: Buffs = None):
        CombatantMixIn.__init__(self, cur_hp, max_hp, speed, buffs)
        self.name = name

    @property
    @abstractmethod
    def preference(self) -> tuple[str, ...]:
        pass

    async def get_decision(self) -> Decision:
        return monster_brain.decide(self, Arena())

    def __repr__(self):
        return f"{self.__class__.__name__} {self.name} {self.hp} {self.buffs}"


# endregion


class WildDog(Monster):

    @property
    def preference(self) -> tuple[str, ...]:
        return ()

    def __init__(self, name: str, cur_hp: int = 24, max_hp: int = 24, speed: int = 9):
        super().__init__(name, cur_hp, max_hp, speed)
        self.buffs = Buffs(Dodge())

    def get_actions(self) -> (Action, ...):
        return Bite(), Move(1)
