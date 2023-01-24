"""General python utilities to be used in project"""


from typing import Any, Iterable


def filter_value_iter(iter, value) -> Iterable[Any]:
    return filter(lambda x: x == value, iter)


def count_value_in_iter(iter, value):
    return len(list(filter_value_iter(iter, value)))


def count_true_in_iter(iter):
    return count_value_in_iter(iter, True)


def is_success(code):
    return 200 <= code <= 299
