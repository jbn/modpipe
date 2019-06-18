import re
from collections import OrderedDict
from inspect import getmodule, getsourcelines, getsource, signature, Signature
from typing import Mapping, Callable
from types import ModuleType
from typing import Iterator, Tuple

BindingSeq = Iterator[Tuple[str, object]]


def is_simple_callable(obj) -> bool:
    """
    :param obj: Any object
    :return: true if the object is callable but class constructor.
    """
    return callable(obj) and not isinstance(obj, type)


def iter_defined_in(module: ModuleType) -> BindingSeq:
    """
    Iterate over all objects defined in a particular module.

    This does not include builtins or anything it imports.

    :param module: A loaded module
    :type module: ModuleType
    :return: A generator of the binding and the bound object for all objects
        defined in a module.
    """
    pairs = vars(module).items()
    return (pair for pair in pairs if getmodule(pair[1]) == module)


def iter_pipelineable(pairs: BindingSeq) -> BindingSeq:
    """
    Iterate over every pair that has an object that is a simple callable.

    :param module: pairs of names to objects.
    :type module: Iterator[Tuple[str, object]]
    :return: A generator of the binding and the bound object for all objects
        that are simple callables.
    """
    return (pair for pair in pairs if is_simple_callable(pair[1]))


def is_pseudo_private(name, _) -> bool:
    return name.startswith('_')


def remove_from_pipeline_seq(pipeline_seq: Mapping[str, object], predicate: Callable[[str, object], bool]):
    """

    :param pipeline_seq: A Mapping (albeit ordered) of bindings to objects.
    :type pipeline_seq: Mapping[str, object]
    :param predicate: A callable that filters out entries that should not
        be retained in a pipeline.
    :type predicate: Callable[[str, object], bool])
    :return: None
    """
    remove_ks = [k for k, v in pipeline_seq.items() if predicate(k, v)]

    for k in remove_ks:
        del pipeline_seq[k]


def sequence_objects(module: ModuleType, items: BindingSeq) -> BindingSeq:
    """
    :param module: The module to extract callable definitions from.
    :type module: ModuleType
    :param items: The callables and bindings for extraction.
    :type items: Iterator[Tuple[str, object]]
    :returns: a list of (name, callable) pairs sorted by source line number
    """
    items, linenos, missing = list(items), {}, set()

    # First try to get the line numbers via getsourcelines.
    for k, obj in items:
        try:
            if obj.__module__ == module.__name__:
                linenos[k] = getsourcelines(obj)[-1]
            else:
                missing.add(k)  # Not in module
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


def sigs_equal_case_insensitive(a, b):
    a_ = [p.kind for p in a.parameters.values()]
    b_ = [p.kind for p in b.parameters.values()]
    return a_ == b_


def sigs_equal_case_sensitive(a, b):
    return a == b


# XXX: TODO: WRONG SIGNATURE!
def compile_signatures(pipeline_seq: BindingSeq, assert_unif=False, ignore_names=True) -> Mapping[str, Signature]:
    """
    :param pipeline_seq: The sequence of name to object bindings.
    :param assert_unif: if True raises a RuntimeError if all the functions
        don't share the same signature.
    :param ignore_names: if True, then the uniform assertion ignores name
        differences
    :return: a map from the callable to the Signature for each item
    """
    signatures = [(f, signature(f)) for f in pipeline_seq.values()]

    equal_sigs = sigs_equal_case_sensitive
    if ignore_names:
        equal_sigs = sigs_equal_case_insensitive

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


def load_pipeline_seq(module: ModuleType, elide_helpers=True, *predicates) -> BindingSeq:
    """
    :param module: The module to load from
    :param elide_helpers: if True, remove all conventionally-designated
        helper functions.
    :param predicates: Predicates to remove_from_pipeline_seq
    :return: an OrderedDict mapping name to callable.
    """
    pairs = sequence_objects(module, iter_pipelineable(iter_defined_in(module)))
    pipeline_seq = OrderedDict(pairs)

    if elide_helpers:
        remove_from_pipeline_seq(pipeline_seq, is_pseudo_private)

    for predicate in predicates:
        remove_from_pipeline_seq(pipeline_seq, predicate)

    return pipeline_seq
