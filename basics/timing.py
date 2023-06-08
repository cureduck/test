from enum import IntFlag


class Timing(IntFlag):
    Healing = 0b000001
    Attack = 0b000010
    Defend = 0b000100
    Move = 0b001000
    Buffed = 0b010000
    GetSpeed = 0b100000
    Equip = 0b1000000
    Unequip = 0b10000000
    GetMaxHp = 0b100000000
