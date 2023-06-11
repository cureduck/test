from __future__ import annotations

import asyncio

from basics import *

a = Character("a", 13, 20, 3, Buffs(Dodge(), Strength()), Sword())
b = Character("b", 13, 20, 7, Buffs(Strength(), ), Sword(), Shield())
c = Character("c", 12, 20, 9, Buffs(), Sword(), MagicBook())
d = Character("d", 18, 20, 2, Buffs(), Bow())

e = WildDog("e")
f = WildDog("f")
g = WildDog("g")
h = WildDog("h")

Arena([a, b, c, d], [e, f, h, g])

Arena().start()

loop = asyncio.get_event_loop()
loop.run_until_complete(Arena().run())
loop.close()
