import pytest
from modpipe.helpers import is_simple_callable, iter_defined_in, iter_pipelineable, is_pseudo_private, \
    remove_from_pipeline_seq, sequence_objects, compile_signatures, load_pipeline_seq
from tests.examples import math_mod
from collections import OrderedDict


def test_defined_in():
    res = {k for k, v in iter_defined_in(math_mod)}
    assert res == {'normed', 'rot90', 'times_ten', 'ScaleAll', '_is_zero'}


def test_class_constructors_arent_simple_callables():
    class MyClass:
        pass

    assert not is_simple_callable(MyClass)


def test_iter_pipelineable():
    res = {k for k, v in iter_pipelineable(iter_defined_in(math_mod))}
    assert res == {'normed', 'rot90', 'times_ten', '_is_zero'}


def test_underscores_are_pseudo_private():
    assert is_pseudo_private('_name', None)
    assert not is_pseudo_private('name', None)


def test_remove_from_pipeline_seq():
    pipeline_seq = OrderedDict(iter_pipelineable(iter_defined_in(math_mod)))
    remove_from_pipeline_seq(pipeline_seq, is_pseudo_private)
    assert set(pipeline_seq.keys()) == {'normed', 'rot90', 'times_ten'}


def test_sequence_objects():
    pairs = iter_pipelineable(iter_defined_in(math_mod))
    res = [k for k, v in sequence_objects(math_mod, pairs)]
    assert res == ['_is_zero', 'normed', 'rot90', 'times_ten']

    pairs = list(iter_pipelineable(iter_defined_in(math_mod)))
    class MissingClass: pass
    pairs.append(('zed', MissingClass))

    with pytest.raises(RuntimeError):
        sequence_objects(math_mod, pairs)



def test_compile_signatures():

    def f(x, y):
        pass

    def g(x, y):
        pass

    def h(x):
        pass

    def f_prime(a, b):
        pass

    # Only one callable.
    res = compile_signatures({'f': f})
    assert list(res[f].parameters) == ['x', 'y']

    # Two callables with the same signature.
    tbl = {func.__name__: func for func in [f, g]}
    res = compile_signatures(tbl)
    assert list(res[f].parameters) == ['x', 'y']
    assert list(res[g].parameters) == ['x', 'y']

    # Two callables with the same signature different names.
    tbl = {func.__name__: func for func in [f, f_prime]}
    res = compile_signatures(tbl)
    assert list(res[f].parameters) == ['x', 'y']
    assert list(res[f_prime].parameters) == ['a', 'b']

    # Two callables with the same signature different names.
    with pytest.raises(RuntimeError):
        compile_signatures(tbl, assert_unif=True, ignore_names=False)

    # Three with a heterogeneous signature.
    with pytest.raises(RuntimeError) as e:
        tbl = OrderedDict([(func.__name__, func) for func in [h, f, g]])
        compile_signatures(tbl, assert_unif=True)

    e.match(r"Signature for f is \(x, y\) which doesn't match \(x\)")


def test_load_pipeline_seq():
    def starts_with_rot(k, _):
        return k.startswith('rot')

    pipeline_seq = load_pipeline_seq(math_mod, True, starts_with_rot)

    assert list(pipeline_seq) == ['normed', 'times_ten']
