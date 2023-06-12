import pytest
from unittest.mock import MagicMock, patch, call
from basics import Character, Buffs, Equipment, Move, Skip, Decision, Timing, Sword


class TestCharacter:
    @pytest.fixture
    def character(self) -> Character:
        buffs = Buffs()
        equipment = Sword()
        return Character("player", 100, 100, 10, buffs, equipment)

    def test_init(self, character: Character) -> None:
        assert character.name == "player"
        assert character.cur_hp == 100
        assert character.base_max_hp == 100
        assert character.base_speed == 10

    def test_basic_actions(self, character: Character) -> None:
        move2, skip2 = Move(2), Skip()
        actions = character.basic_actions()
        assert len(actions) == 2
        assert move2 in actions
        assert skip2 in actions

    def test_factors(self, character: Character) -> None:
        timing = Timing.BeforeRound
        baton = MagicMock()
        buff = MagicMock()
        buff.may_affect = MagicMock(return_value=True)
        character.buffs = [buff]
        equip_factor = MagicMock()
        equip_factor.may_affect = MagicMock(return_value=True)
        character.equipage.factors = [equip_factor]
        factors = character.factors(timing, baton)
        assert len(factors) == 2  # Buffs+Equipage
        assert equip_factor in factors
        assert buff in factors

    def test_get_decision(self, character: Character) -> None:
        with patch("PlayerBrain.decide") as decide_mock:
            decision = Decision.Attack
            decide_mock.return_value = decision
            arena_mock = MagicMock()
            res = character.get_decision()

        assert res == decision
        decide_mock.assert_called_once_with(character, arena_mock)
