from __future__ import annotations

import asyncio

from basics import *

a = Character("a", 13, 17, 3, Buffs(Dodge(), Strength()), Sword())
b = Character("b", 13, 13, 7, Buffs(Strength()), Sword(), Shield())
c = Character("c", 12, 12, 9, Buffs(), Sword())
d = Character("d", 18, 18, 2, Buffs(), Sword())

e = WildDog("e")
f = WildDog("f")
g = WildDog("g")

Arena([a, b, c, d], [e, f, None, g])

# a.get_actions()
# print(a.position)
# a_decision = (a.get_actions()[0], Targeting([False, False, 2]))

# if a.get_actions()[0].check(a):
#     a.take(a.get_actions()[0], None)  # a takes Slash

# monster_brain = AIBrain(Random())
# decision = monster_brain.decide(e, Arena.Instance)
# # e.take(e.get_actions()[0], target=Targeting([False, False, 2]))
# e.execute(decision)

Arena().start()

loop = asyncio.get_event_loop()
loop.run_until_complete(Arena().run())
loop.close()

# while True:
#     print(a.hp, b.hp, c.hp, d.hp)
#     print(e.hp, f.hp, g.hp)
#     decision = pi.get_input()
#     Arena.Instance.current_execute(decision)
