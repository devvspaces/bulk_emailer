from pathlib import Path
from typing import TypeVar

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

T = TypeVar('T', bound=Path)


@pytest.fixture
def use_dummy_media_path(settings, tmp_path):
    settings.MEDIA_ROOT = settings.BASE_DIR / tmp_path


@pytest.fixture
def uploaded_file_obj(excel_test_csv_path: T):
    return SimpleUploadedFile(
        "test_file.csv", excel_test_csv_path.read_bytes())


@pytest.fixture
def uploaded_file_no_email_column(excel_test_csv_path_error: T):
    return SimpleUploadedFile(
        "test_file.csv", excel_test_csv_path_error.read_bytes())


@pytest.fixture
def wrong_extention_file_obj(tmp_path: T):
    tmp_file_path: T = tmp_path / 'test_file'
    with tmp_file_path.open(mode='w') as file:
        file.write('file content here')
    return SimpleUploadedFile(
        "test_file.wrong_extension", tmp_file_path.read_bytes())


@pytest.fixture
def mail_form_data(uploaded_file_obj):
    data = {
        'sender': 'test',
        'reply_to': 'test@reply.to',
        'subject': 'test subject',
        'message': 'test message',
        'start': 1,
        'stop': 1,
        'file': uploaded_file_obj
    }
    return data
