from typing import TypeVar

import pytest
from django.test.client import Client
from django.urls import reverse

T = TypeVar('T', bound=Client)


def test_view_dashboard(client: T):
    path = reverse('mailer:home')
    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures('use_dummy_media_path')
def test_send_messages(client: T, mail_form_data: dict):
    path = reverse('mailer:home')
    response = client.post(path, data=mail_form_data)
    assert response.status_code == 302
    messages = list(response.context['messages'])
    assert len(messages) == 1
    assert str(messages[0]) \
        == '1 messages sent, 0 messages failed'


def test_home_form_error(client: T, mail_form_data: dict):
    path = reverse('mailer:home')
    mail_form_data.pop('sender')
    response = client.post(path, data=mail_form_data)
    assert response.status_code == 200
    form = response.context['form']
    errors = form.errors.get('sender')
    assert errors.data[0].code == 'required'


@pytest.mark.django_db
@pytest.mark.usefixtures('use_dummy_media_path')
def test_home_exception_handler(
    client: T, uploaded_file_no_email_column,
    mail_form_data: dict
):
    path = reverse('mailer:home')
    mail_form_data['file'] = uploaded_file_no_email_column
    response = client.post(path, data=mail_form_data)
    assert response.status_code == 200
    messages = list(response.context['messages'])
    assert len(messages) == 1
    assert str(messages[0]) == 'Email column not in file'
