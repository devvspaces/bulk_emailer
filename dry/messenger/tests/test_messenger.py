from typing import Type
from unittest import TestCase
from pandas import DataFrame
import pytest
from pathlib import Path
from messenger.messager import Managers, BaseMessenger, ExcelMessenger
from messenger.email_manager import BaseEmailManager
from messenger.messsage_manager import BaseMessageManager


E = Type[BaseEmailManager]
T = Type[BaseMessageManager]
M = Type[Managers]
B = Type[BaseMessenger]
G = Type[ExcelMessenger]
U = Type[TestCase]


def test_set_email_manager(managers: M, email_manager: E):
    managers.set_email_manager(email_manager)
    assert email_manager is managers.email_manager


def test_set_email_manager_error(managers: M):
    with pytest.raises(TypeError):
        managers.set_email_manager('wrong type')


def test_email_manager(managers: M):
    assert managers.email_manager is None


def test_set_message_manager(managers: M, message_manager: T):
    managers.set_message_manager(message_manager)
    assert message_manager is managers.message_manager


def test_set_message_manager_error(managers: M):
    with pytest.raises(TypeError):
        managers.set_message_manager('wrong type')


def test_message_manager(managers: M):
    assert managers.message_manager is None


def test_run_checks_email(managers: M):
    """
    raise error for email manager check
    """
    with pytest.raises(NotImplementedError):
        managers.run_checks()


def test_run_checks_message(managers: M, email_manager: E):
    """
    raise error for message manager check
    """
    with pytest.raises(NotImplementedError):
        managers.set_email_manager(email_manager)
        managers.run_checks()


def test_create_base_manager():
    BaseMessenger(
        start=10,
        stop=20
    )


def test_base_manager_get_start(messenger: B):
    assert messenger.get_start() == 9


def test_base_manager_get_stop(messenger: B):
    assert messenger.get_stop() == 19


@pytest.mark.parametrize(
    'start, stop',
    [
        ('20', 10), (20, '10'), (20, 10),
    ]
)
def test_base_manager_error_check(start, stop):
    with pytest.raises(TypeError):
        BaseMessenger(start=start, stop=stop)


def test_base_manager_set_manager(messenger: B):
    messenger.set_manager()
    assert isinstance(messenger.get_manager(), Managers)


def test_base_manager_get_manager(messenger: B):
    assert isinstance(messenger.get_manager(), Managers)


def test_base_manager_set_message_manager(messenger: B, message_manager):
    messenger.set_message_manager(message_manager)


def test_base_manager_set_email_manager(messenger: B, email_manager):
    messenger.set_email_manager(email_manager)


def test_base_manager_get_message_without_data(messenger: B):
    message = """
    hi i want _first_name_ to know that i _fiRst_namE_ love to meet you.
    with the presence of _last_
    """
    computed = messenger.get_message(message)
    assert computed == message


def test_base_manager_get_message_data(messenger: B):
    data = {
        'first_name': 'Test',
        'fiRst_namE': 'Pytest',
        'last': 'Python',
    }
    message = """
    hi i want _first_name_ to know that i _fiRst_namE_ love to meet you.
    with _last_ presence of _last_.
    """
    computed = messenger.get_message(message, data)
    expected = """
    hi i want Test to know that i Pytest love to meet you.
    with Python presence of Python.
    """
    assert computed == expected


def test_base_manager_start_process_without_managers(messenger: B):
    with pytest.raises(NotImplementedError, match=r'No \w+ manager provided'):
        messenger.start_process(
            subject='test',
            message='test'
        )


def test_base_manager_start_process_with_managers(messenger_with_managers: B):
    with pytest.raises(NotImplementedError, match='No send_messages'):
        messenger_with_managers.start_process(
            subject='test',
            message='test'
        )


def test_excel_messenger(excel_test_csv_path):
    ExcelMessenger(
        start=0,
        stop=4,
        file_path=excel_test_csv_path
    )


def test_excel_messenger_error_index_start(excel_test_csv_path):
    with pytest.raises(
        TypeError, match='Start index is greater than file max index'
    ):
        ExcelMessenger(
            start=7,
            stop=40,
            file_path=excel_test_csv_path
        )


def test_excel_messenger_error_index_stop(excel_test_csv_path):
    with pytest.raises(
        TypeError, match='Stop index is greater than file max index'
    ):
        ExcelMessenger(
            start=0,
            stop=40,
            file_path=excel_test_csv_path
        )


def test_excel_messenger_get_supported_exts(excel_messenger: G):
    computed = excel_messenger.get_supported_exts()
    expected = 'xls, xlsx, csv and gz'
    assert computed == expected


@pytest.mark.parametrize(
    'path, match',
    [
        ('test/path', 'is not absolute'),
        (Path().resolve() / 'not_exist', 'does not exist'),
        (Path().resolve(), 'is not a file'),
        (
            Path().resolve() / 'messenger/tests/files/no_ext',
            'does not have an extension'),
        (__file__, 'not in correct format'),
    ]
)
def test_excel_messenger_error_checks(path, match):
    with pytest.raises(TypeError, match=match):
        ExcelMessenger(
            start=10,
            stop=20,
            file_path=path
        )


def test_excel_messenger_get_file_path(excel_messenger: G):
    computed = excel_messenger.get_file_path()
    assert isinstance(computed, Path)


def test_excel_messenger_data(excel_messenger: G):
    computed = excel_messenger.data
    assert isinstance(computed, DataFrame)


def test_excel_messenger_get_range(excel_messenger: G):
    computed = excel_messenger.get_range()
    assert isinstance(computed, range)
    assert computed[0] == 0
    assert computed[-1] == 2


def test_excel_messenger_get_index_dict(excel_messenger: G, testcase: U):
    computed: dict = excel_messenger.get_index_dict(0)
    computed_keys = list(computed.keys())
    expected_keys = ['first_name', 'last_name', 'email']
    testcase.assertListEqual(computed_keys, expected_keys)

    computed_values = list(computed.values())
    expected_values = ['ayo', 'israel', 'ayo@testing.com']
    testcase.assertListEqual(computed_values, expected_values)


def test_excel_messenger_get_email_from_data(excel_messenger: G):
    computed = excel_messenger.get_email_from_data(
        excel_messenger.get_index_dict(0))
    expected = 'ayo@testing.com'
    assert expected == computed


def test_excel_messenger_get_email_from_data_error(excel_messenger_error: G):
    with pytest.raises(TypeError, match='column not in file'):
        excel_messenger_error.get_email_from_data(
            excel_messenger_error.get_index_dict(0))


def test_excel_messenger_send_messages(excel_messenger: G):
    sents = excel_messenger.send_messages(
        subject='Testing',
        message="""hi i want _first_name_ to know that i _last_name_ love to meet you.
        with _first_name_ presence of _last_name_."""
    )
    assert 3 == len(list(sents))
