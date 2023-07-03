from __future__ import annotations


class RandomStub:
    def randint(self, a, b):
        return a

    def randrange(self, a, b):
        return a

    def choice(self, seq):
        return seq[0]

    def shuffle(self, seq):
        return seq

    def sample(self, seq, k):
        return seq[:k]

    def choices(self, seq, k):
        return seq[:k]

    def uniform(self, a, b):
        return a

    def triangular(self, low, high, mode):
        return low

    def random(self):
        return .5


# game_random = random.Random()
game_random = RandomStub()
