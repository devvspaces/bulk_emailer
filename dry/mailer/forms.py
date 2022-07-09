from django import forms
from django.forms import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator

from .models import Uploads


validator_file_ext = FileExtensionValidator(
    allowed_extensions=['xls', 'gz', 'csv', 'xlsx']
)
validator_start_min = MinValueValidator(limit_value=1)
validator_stop_min = MinValueValidator(limit_value=1)


class MailForm(forms.Form):
    file = forms.FileField(validators=[validator_file_ext])
    sender = forms.CharField()
    reply_to = forms.EmailField()
    subject = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)
    start = forms.IntegerField(validators=[validator_start_min])
    stop = forms.IntegerField(validators=[validator_stop_min])

    def clean(self):
        cleaned = super().clean()

        # Validate stop is greater than start
        start = cleaned.get('start')
        stop = cleaned.get('stop')
        if (start is not None and stop is not None) and (start > stop):
            error = ValidationError(
                'Start must not be greater that stop',
                code='start_stop_error')
            self.add_error('start', error)

        return cleaned

    def save(self, commit=True):
        file = self.cleaned_data.get('file')
        obj = Uploads(file=file)
        if commit:
            obj.save()
        return obj
