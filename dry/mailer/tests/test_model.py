import pytest

from mailer.models import Uploads


@pytest.mark.django_db
@pytest.mark.usefixtures('use_dummy_media_path')
def test_upload_new_file(uploaded_file_obj):
    obj = Uploads(
        file=uploaded_file_obj
    )
    obj.save()
    assert str(obj) == 'test_file.csv'
    assert obj.file.name == 'test_file.csv'
