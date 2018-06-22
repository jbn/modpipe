import pytest
from modpipe.modpipe_impl import (_defined_in,
                                  _pipelineable,
                                  _is_simple_callable,
                                  _is_pseudo_private,
                                  _remove_from_pipeline_seq,
                                  _sequence_objects,
                                  _compile_signatures,
                                  _load_pipeline_seq)
from tests.examples import math_mod
from collections import OrderedDict


def test_defined_in():
    res = {k for k, v in _defined_in(math_mod)}
    assert res == {'normed', 'rot90', 'times_ten', 'ScaleAll', '_is_zero'}


def test_class_constructors_arent_simple_callables():
    class MyClass:
        pass

    assert not _is_simple_callable(MyClass)


def test_pipelineable():
    res = {k for k, v in _pipelineable(_defined_in(math_mod))}
    assert res == {'normed', 'rot90', 'times_ten', '_is_zero'}


def test_underscores_are_pseudo_private():
    assert _is_pseudo_private('_name', None)
    assert not _is_pseudo_private('name', None)


def test_remove_from_pipeline_seq():
    pipeline_seq = OrderedDict(_pipelineable(_defined_in(math_mod)))
    _remove_from_pipeline_seq(pipeline_seq, _is_pseudo_private)
    assert set(pipeline_seq.keys()) == {'normed', 'rot90', 'times_ten'}


def test_sequence_objects():
    pairs = _pipelineable(_defined_in(math_mod))
    res = [k for k, v in _sequence_objects(math_mod, pairs)]
    assert res == ['_is_zero', 'normed', 'rot90', 'times_ten']


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
    _compile_signatures({'f': f})

    # Two callables with the same signature.
    tbl = {func.__name__: func for func in [f, g]}
    _compile_signatures(tbl)

    # Two callables with the same signature different names.
    tbl = {func.__name__: func for func in [f, f_prime]}
    _compile_signatures(tbl)

    # Two callables with the same signature different names.
    with pytest.raises(RuntimeError):
        _compile_signatures(tbl, assert_unif=True, ignore_names=False)

    # Three with a heterogeneous signature.
    with pytest.raises(RuntimeError) as e:
        tbl = OrderedDict([(func.__name__, func) for func in [h, f, g]])
        _compile_signatures(tbl, assert_unif=True)

    e.match("Signature for f is \(x, y\) which doesn't match \(x\)")


def test_load_pipeline_seq():
    pipeline_seq = _load_pipeline_seq(math_mod)

    assert list(pipeline_seq) == ['normed', 'rot90', 'times_ten']
