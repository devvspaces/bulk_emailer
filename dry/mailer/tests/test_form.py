import pytest
from mailer.forms import MailForm
from mailer.models import Uploads


@pytest.mark.parametrize(
    'field',
    [
        'sender',
        'reply_to',
        'subject',
        'message',
        'start',
        'stop',
        'file',
    ]
)
def test_form_required_errors(mail_form_data: dict, field):
    mail_form_data.pop(field)
    if 'file' in mail_form_data.keys():
        files = {
            'file': mail_form_data.pop('file')
        }
        form = MailForm(data=mail_form_data, files=files)
    else:
        form = MailForm(data=mail_form_data)
    valid = form.is_valid()
    errors = form.errors.get(field)
    assert valid is False
    assert errors.data[0].code == 'required'


@pytest.mark.parametrize(
    'field, value, code',
    [
        ('reply_to', 'not_an_email', 'invalid'),
        (
            'file',
            pytest.lazy_fixture('wrong_extention_file_obj'),
            'invalid_extension'
        ),
        ('start', 0, 'min_value'),
        ('stop', 0, 'min_value'),
        ('start', 2, 'start_stop_error'),
    ]
)
def test_form_file_field_error(field, value, code, mail_form_data: dict):
    mail_form_data[field] = value

    files = {
        'file': mail_form_data.pop('file')
    }
    form = MailForm(data=mail_form_data, files=files)
    valid = form.is_valid()
    errors = form.errors.get(field)
    assert valid is False
    assert errors.data[0].code == code


@pytest.mark.django_db
@pytest.mark.usefixtures('use_dummy_media_path')
def test_save_files(mail_form_data: dict):
    files = {
        'file': mail_form_data.pop('file')
    }
    form = MailForm(data=mail_form_data, files=files)
    valid = form.is_valid()
    assert valid is True
    obj = form.save()
    assert obj.file.name == 'test_file.csv'
