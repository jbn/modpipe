from modpipe import Result


def f(s):
    tok = s.upper().strip()
    return tok if tok else Result(None)  # or Done(None)
