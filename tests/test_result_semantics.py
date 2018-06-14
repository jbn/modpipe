import pytest
from modpipe.modpipe_impl import Result, Done, SkipTo


def test_single_arg_result():
    res_0 = Result(1)
    assert res_0.args == 1

    def f(x):
        assert x == 1
        return 1

    res_1 = res_0.apply_to(f, 1)
    assert res_1.args == 1


def test_tuple_arg_result():
    res_0 = Result(1, 2)
    assert res_0.args == (1, 2)

    def f(x, y):
        assert x == 1
        assert y == 2
        return x + 1, y + 1

    res_1 = res_0.apply_to(f, 2)
    assert res_1.args == (2, 3)


def test_triple_arg_result():
    res_0 = Result(1, 2, 3)
    assert res_0.args == (1, 2, 3)

    def f(items):
        assert len(items) == 3
        return sum(items)

    res_1 = res_0.apply_to(f, 1)
    assert res_1.args == 6


def test_list_arg_result():
    res_0 = Result([1, 2])
    assert res_0.args == [1, 2]

    def f(items):
        assert items == [1, 2]
        return sum(items)

    res_1 = res_0.apply_to(f, 1)
    assert res_1.args == 3


def test_done_args():
    res = Done(1, 2)
    assert res.args == (1, 2)


def test_done_fails_loudly_on_apply_to():
    with pytest.raises(RuntimeError):
        Done(1, 2).apply_to(lambda x: x, 1)


def test_skip_to():
    def f(a, b):
        assert False  # Not called

    def g(a, b):
        assert a == 1
        assert b == 2
        return a + b

    res_0 = SkipTo(g, 1, 2)

    assert res_0.args == (1, 2)
    assert res_0.apply_to(f, 2) is res_0
    assert res_0.apply_to(g, 2).args == 3
