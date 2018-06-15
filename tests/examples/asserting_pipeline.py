def sqrt(x):
    return type(x)(x ** 0.5)


assert sqrt(1776) != 42, "Uh oh!"
