from modpipe import SkipTo


def f(x):
    return x + 1


def g(x):
    # This is before in the linearized pipeline!
    return SkipTo(f, x)
