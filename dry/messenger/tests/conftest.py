from pathlib import Path
from typing import Type
from unittest import TestCase

import pytest
from messenger.email_manager import BaseEmailManager
from messenger.messager import BaseMessenger, ExcelMessenger, Managers
from messenger.messsage_manager import BaseMessageManager, HtmlMessageManager

T = Type[Path]
M = Type[HtmlMessageManager]


@pytest.fixture
def testcase():
    return TestCase()


@pytest.fixture
def use_dummy_template_backend(settings, tmp_path):
    test_template_dir: T = tmp_path
    test_path: T = test_template_dir / 'test.html'
    with test_path.open(mode='w') as f:
        f.write('hello world {{ message }} {{ name }}')

    settings.TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [test_template_dir],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]


@pytest.fixture
def create_manager(use_dummy_template_backend):
    return HtmlMessageManager(
        template_name='test.html',
        context={
            'name': 'testing'
        }
    )


@pytest.fixture
def email_manager():
    manager = BaseEmailManager(
        domain='example.com',
        sender='test',
    )
    return manager


@pytest.fixture
def message_manager():
    manager = BaseMessageManager()
    return manager


@pytest.fixture
def managers():
    return Managers()


@pytest.fixture
def messenger():
    return BaseMessenger(
        start=10,
        stop=20
    )


@pytest.fixture
def messenger_with_managers(email_manager, message_manager):
    messenger = BaseMessenger(
        start=10,
        stop=20
    )
    messenger.set_email_manager(email_manager)
    messenger.set_message_manager(message_manager)
    return messenger


@pytest.fixture
def excel_test_csv_path(settings):
    return settings.BASE_DIR / 'messenger/tests/files/test_excel.csv'


@pytest.fixture
def excel_test_csv_path_error(settings):
    return settings.BASE_DIR / 'messenger/tests/files/test_csv_no_email.csv'


@pytest.fixture
def excel_messenger(excel_test_csv_path, create_manager, email_manager):
    messenger = ExcelMessenger(
        start=1,
        stop=3,
        file_path=excel_test_csv_path
    )
    messenger.set_message_manager(create_manager)
    messenger.set_email_manager(email_manager)
    return messenger


@pytest.fixture
def excel_messenger_error(
    excel_test_csv_path_error, create_manager,
    email_manager
):
    messenger = ExcelMessenger(
        start=1,
        stop=3,
        file_path=excel_test_csv_path_error
    )
    messenger.set_message_manager(create_manager)
    messenger.set_email_manager(email_manager)
    return messenger
