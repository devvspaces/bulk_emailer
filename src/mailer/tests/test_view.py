from typing import TypeVar

import pytest
from django.test.client import Client
from django.urls import reverse

from mailer.models import Job

T = TypeVar('T', bound=Client)


@pytest.mark.django_db
def test_view_dashboard(client: T):
    path = reverse('mailer:home')
    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures('use_dummy_media_path')
def test_send_messages(client: T, mail_form_data: dict, settings):
    settings.BLOCK_EMAIL = True
    path = reverse('mailer:home')
    response = client.post(path, data=mail_form_data)
    assert response.status_code == 302
    assert response.url == reverse('mailer:jobs')

    job = Job.objects.get()
    assert job.job_type == Job.JobType.EMAIL
    assert job.total == 1
    assert job.sender == 'test@example.com'
    assert job.subject == 'test subject'
    assert job.recipient_field == 'email'


@pytest.mark.django_db
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
def test_queue_job_with_bad_file(
    client: T, uploaded_file_no_email_column,
    mail_form_data: dict
):
    path = reverse('mailer:home')
    mail_form_data['file'] = uploaded_file_no_email_column
    response = client.post(path, data=mail_form_data)
    assert response.status_code == 302
    assert response.url == reverse('mailer:jobs')
    assert Job.objects.count() == 1


@pytest.mark.django_db
def test_settings_edit_manager(client: T, email_manager):
    response = client.get(reverse('mailer:settings') + f'?edit={email_manager.pk}')
    assert response.status_code == 200
    assert b'Edit email manager' in response.content

    response = client.post(reverse('mailer:settings'), {
        'manager_id': str(email_manager.pk),
        'label': 'Updated',
        'mail_manager': 'smtp',
        'sender': 'newprefix',
        'reply_to': 'new@example.com',
        'email_domain': 'new.example.com',
        'smtp-host': 'localhost',
        'smtp-port': '587',
        'smtp-username': 'user',
        'smtp-password': 'pass',
    })
    assert response.status_code == 302

    email_manager.refresh_from_db()
    assert email_manager.label == 'Updated'
    assert email_manager.sender == 'newprefix'
    assert email_manager.email_domain == 'new.example.com'

