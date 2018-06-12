

def _helper(x, y):
    return x + y


def h(x, y):
    return x / y


assert h(2, 2) == 1


def f(x, y):
    return _helper(x, y)


assert f(1, 2) == 3


def g(x, y):
    return x * y


assert g(1, 2) == 2


class Something:
    def __call__(self, x, y):
        return x**2 + y**2
    
something = Something()

assert something(1, 2) == 5