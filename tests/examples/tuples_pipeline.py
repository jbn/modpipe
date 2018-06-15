def f(x):
    return x, -x  # i.e. add(x, -x)


def g(x, y):
    return x + y, x * y  # i.e. h(x + y, x * y)


def h(items):
    return sum(items)
