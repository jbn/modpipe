def f(x):
    return {'value': x}


def g(src):
    return src, {}


def h(src, dst):
    dst['computation'] = src['value'] * 2


def last_one(src, dst):
    return dst
