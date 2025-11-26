from math_utils import multiply, is_even

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 10) == 0

def test_is_even():
    assert is_even(2) is True
    assert is_even(3) is False