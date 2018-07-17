import re
from importlib import import_module
from inspect import getmodule, getsourcelines, getsource, getfile
from collections import OrderedDict

try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except ImportError:
        pass  # Assuming 2.7


def _defined_in(module):
    pairs = vars(module).items()
    return (pair for pair in pairs if getmodule(pair[1]) == module)


try:
    from inspect import signature

    def _is_simple_callable(obj):
        return callable(obj) and not isinstance(obj, type)
except ImportError:
    from funcsigs import signature as _signature
    from types import TypeType, ClassType, InstanceType

    def _is_simple_callable(obj):
        return callable(obj) and not isinstance(obj, (TypeType, ClassType))

    def signature(f):
        return _signature(f.__call__ if isinstance(f, InstanceType) else f)


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


def _compile_signatures(pipeline_seq, assert_unif=False, ignore_names=True):
    """
    :param assert_unif: if True raises a runtime if all the functions
        don't share the same signature.
    :param ignore_names: if True, then the uniform assertion ignores name
        differences
    :return: a map from the callable to the Signature for each item
    """
    signatures = [(f, signature(f)) for f in pipeline_seq.values()]

    if ignore_names:
        def equal_sigs(a, b):
            a_ = [p.kind for p in a.parameters.values()]
            b_ = [p.kind for p in b.parameters.values()]
            return a_ == b_
    else:
        def equal_sigs(a, b):
            return a == b

    if assert_unif:
        last = None
        for f, sig in signatures:
            # The order is important! It's easier to debug with the first
            # inconsistency than an arbitrary one.
            if last is not None and not equal_sigs(last, sig):
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


class ModPipe:

    @classmethod
    def on(cls, module_dot_path, unif_sigs=False, ignore_names=True):
        return ModPipe(module_dot_path, unif_sigs, ignore_names)

    def __init__(self, module_dot_path, unif_sigs=False, ignore_names=True):
        self._module_dot_path = module_dot_path
        self._unif_sigs = unif_sigs
        self._ignore_names = ignore_names

        self.reload()

    @property
    def module_name(self):
        return self._module_name

    @property
    def abs_module_path(self):
        return self._module_path

    def reload(self):
        # Don't save a ref to module. It's not picklable.
        module = reload(import_module(self._module_dot_path))
        self._module_name = module.__name__
        self._module_path = getfile(module)
        self._pipeline = _load_pipeline_seq(module)

        assert len(self._pipeline) > 0

        self._signatures = _compile_signatures(self._pipeline,
                                               self._unif_sigs,
                                               self._ignore_names)
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
        res = Result(args)

        for k, f in self._pipeline.items():

            res = res.apply_to(f, self._expected_args[f])

            if isinstance(res, Done):
                break

        if isinstance(res, SkipTo):
            msg = "Pipeline ended before encountering {}"
            raise RuntimeError(msg.format(res.target_f.__name__))

        return res.args


class Result(object):

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args, tuple):
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
