from modpipe import Done, SkipTo


def _is_zero(x, y):
    return x == 0 and y == 0


def normed(x, y):
    if _is_zero(x, y):
        return Done(0, 0)
    elif x == 42 and y == 42:
        return SkipTo(times_ten, x, y)
    elif x == 1j or y == 1j:
        return Done(None)

    a = (x**2 + y**2) ** -0.5
    return a * x, a * y


assert abs(sum(x ** 2 for x in normed(3, 4)) - 1.0) < 0.0001


ROT = [[0, 1], [-1, 0]]


def rot90(x, y):
    return tuple(x * a + y * b for a, b in ROT)


class ScaleAll:

    def __init__(self, a):
        self.a = a

    def __call__(self, x, y):
        return x * self.a, y * self.a


times_ten = ScaleAll(10)
