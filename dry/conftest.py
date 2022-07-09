from unittest import TestCase

import pytest


@pytest.fixture
def testcase():
    return TestCase()


@pytest.fixture
def excel_test_csv_path(settings):
    return settings.BASE_DIR / 'messenger/tests/files/test_excel.csv'


@pytest.fixture
def excel_test_csv_path_error(settings):
    return settings.BASE_DIR / 'messenger/tests/files/test_csv_no_email.csv'
