from typing import TypeVar
from unittest import TestCase

import pytest
from utils.general import (count_true_in_iter, count_value_in_iter,
                           filter_value_iter, is_success)

X = TypeVar('X', bound=TestCase)


@pytest.mark.parametrize(
    'text, value, result',
    [
        ('testmyname', 't', 'tt'),
        ('testmyname', 's', 's'),
        ('testmyname', 'm', 'mm'),
        ('testmyname', 'e', 'ee'),
    ]
)
def test_filter_value_iter(testcase: X, text, value, result):
    test_iter = iter(text)
    expected_iter = list(result)
    computed_iter = list(filter_value_iter(test_iter, value))
    testcase.assertListEqual(expected_iter, computed_iter)


@pytest.mark.parametrize(
    'text, value, result',
    [
        ('testmyname', 't', 2),
        ('testmyname', 's', 1),
        ('testmyname', 'm', 2),
        ('testmyname', 'e', 2),
    ]
)
def test_count_value_in_iter(text, value, result):
    test_iter = iter(text)
    computed_result = count_value_in_iter(test_iter, value)
    assert computed_result == result


@pytest.mark.parametrize(
    'iter, result',
    [
        ([True, False, True, True], 3),
        ([True, True, True, True], 4),
        ([True, False, False, True], 2),
        ([True, False, False, False], 1),
        ([False, False, False, False], 0),
    ]
)
def test_count_true_in_iter(iter, result):
    computed_result = count_true_in_iter(iter)
    assert computed_result == result


@pytest.mark.parametrize(
    'code, expected',
    [
        (200, True),
        (201, True),
        (299, True),
        (101, False),
        (301, False),
    ]
)
def test_is_success(code, expected):
    computed_result = is_success(code)
    assert computed_result == expected
