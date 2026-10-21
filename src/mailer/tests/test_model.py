import pytest

from mailer.models import Job, Uploads


@pytest.mark.django_db
@pytest.mark.usefixtures('use_dummy_media_path')
def test_upload_new_file(uploaded_file_obj):
    obj = Uploads(
        file=uploaded_file_obj
    )
    obj.save()
    assert str(obj) == 'test_file.csv'
    assert obj.file.name == 'test_file.csv'


@pytest.mark.django_db
def test_job_properties():
    job = Job.objects.create(
        job_type=Job.JobType.EMAIL,
        start=1,
        stop=4,
    )
    assert job.total == 4
    assert job.processed == 0
    assert job.next_index == 1
    assert job.progress == 0
    assert job.is_active is True

    job.sent = 2
    job.failed = 1
    job.save()

    assert job.processed == 3
    assert job.next_index == 4
    assert job.progress == 75

