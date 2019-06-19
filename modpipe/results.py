class Result:

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args, tuple):
            # Unpack a single element tuple.
            self.args = args[0]
        else:
            self.args = args

    def apply_to(self, f, arity):
        res = None

        if isinstance(self.args, tuple) and arity == len(self.args):
            res = f(*self.args)
        else:
            res = f(self.args)

        if isinstance(res, Result):
            return res
        elif res is not None:
            return Result(res)
        else:
            return Result(self.args)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.args)


class Done(Result):

    def apply_to(self, f, arity):
        raise RuntimeError("Calling apply to on a completed result.")


class SkipTo(Result):

    def __init__(self, target_f, *args):
        super(SkipTo, self).__init__(*args)
        self.target_f = target_f

    def apply_to(self, f, arity):
        if f != self.target_f:
            return self
        else:
            return Result.apply_to(self, f, arity)
