import re
from importlib import import_module, reload
from inspect import getmodule, getsourcelines, getsource, signature
from collections import OrderedDict


def _defined_in(module):
    pairs = vars(module).items()
    return (pair for pair in pairs if getmodule(pair[1]) == module)


def _is_simple_callable(obj):
    return callable(obj) and not isinstance(obj, type)


def _pipelineable(pairs):
    return (pair for pair in pairs if _is_simple_callable(pair[1]))


def _is_pseudo_private(name, obj):
    return name.startswith('_')


def _remove_from_pipeline_seq(pipeline_seq, predicate):
    """
    Remove items that match the predicate *in place*.
    """
    remove_ks = [k for k, v in pipeline_seq.items() if predicate(k, v)]

    for k in remove_ks:
        del pipeline_seq[k]


def _sequence_objects(module, items):
    """
    :returns: a list of (name, callable) pairs sorted by source line number
    """
    items, linenos, missing = list(items), {}, set()

    # First try to get the line numbers via getsourcelines.
    for k, obj in items:
        try:
            linenos[k] = getsourcelines(obj)[-1]
        except TypeError:
            missing.add(k)  # i.e. class instance

    # Now find any instantiated objects.
    missing_re = re.compile("^({})".format("|".join(missing)))
    for lineno, line in enumerate(getsource(module).splitlines()):
        match = missing_re.match(line)
        if match:
            linenos[match.group(0)] = lineno

    # Verify all objects found.
    still_missing = missing - set(linenos)
    if still_missing:
        raise RuntimeError("Unable to resolve: {}".format(still_missing))

    return sorted(items, key=lambda p: linenos[p[0]])


def _compile_signatures(pipeline_seq, assert_uniform=False):
    """
    :param assert_uniform: if True raises a runtime if all the functions
        don't share the same signature.
    :return: a map from the callable to the Signature for each item
    """
    signatures = [(f, signature(f)) for f in pipeline_seq.values()]

    last = None
    for f, sig in signatures:
        # The order is important! It's easier to debug with the first
        # inconsistency than an arbitrary one.
        if last is not None and last != sig:
            msg = "Signature for {} is {} which doesn't match {}"
            raise RuntimeError(msg.format(f.__name__, sig, last))
        last = sig

    return dict(signatures)


def _load_pipeline_seq(module, elide_helpers=True):
    """
    :param elide_helpers: if True, remove all conventionally-designated
        helper functions.
    :return: an OrderedDict mapping name to callable.
    """
    pairs = _sequence_objects(module, _pipelineable(_defined_in(module)))
    pipeline_seq = OrderedDict(pairs)

    if elide_helpers:
        _remove_from_pipeline_seq(pipeline_seq, _is_pseudo_private)

    return pipeline_seq


def call_reconciled(n, f, args):
    # XXX: Ugly.
    if isinstance(args, tuple):
        k = len(args)

        if n == k:
            return f(*args)
        elif k == 0:
            return f()
        else:
            return f(args)
    elif args is None:
        return f()
    else:
        return f(args)


class ModPipe:

    @classmethod
    def on(cls, module_dot_path, ensure_uniform_sigs=False):
        return ModPipe(module_dot_path, ensure_uniform_sigs)

    def __init__(self, module_dot_path, ensure_uniform_sigs=False):
        self._module = import_module(module_dot_path)
        self._ensure_uniform_sigs = ensure_uniform_sigs

        self.reload()

    def reload(self):
        self._module = reload(self._module)
        self._pipeline = _load_pipeline_seq(self._module)

        assert len(self._pipeline) > 0

        self._signatures = _compile_signatures(self._pipeline,
                                               self._ensure_uniform_sigs)
        self._expected_args = {k: len(sig.parameters)
                               for k, sig in self._signatures.items()}

    def __delitem__(self, k):
        f = self._pipeline[k]
        del self._pipeline[k]
        del self._signatures[f]
        del self._expected_args[f]

    def __getitem__(self, k):
        return self._pipeline[k]

    def _ipython_key_completions_(self):
        return list(self._pipeline.keys())

    def __repr__(self):
        return "ModPipe({})".format(self._module.__name__)

    def __enter__(self):
        self.reload()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False   # Don't swallow.

    def __call__(self, *args):
        skip_until = None

        res = args
        for k, f in self._pipeline.items():

            if skip_until is not None:
                if f is not skip_until.f:
                    continue
                else:
                    res, skip_until = skip_until.args, None

            res = call_reconciled(self._expected_args[f], f, res)

            # Done as a monad?
            if isinstance(res, Done):
                if isinstance(res.args, tuple) and len(res.args) == 1:
                    return res.args[0]
                else:
                    return res.args
            elif isinstance(res, SkipTo):
                skip_until = res

        return res


class Result:

    def __init__(self, *args):
        self.args = args


class Done(Result):
    pass


class SkipTo(Result):

    def __init__(self, f, *args):
        super().__init__(*args)
        self.f = f
