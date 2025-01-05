from django import forms
from django.forms import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django_quill.forms import QuillFormField

from mailer.mail_manager import MAIL_MANAGERS

from .models import EmailManager, Uploads


validator_file_ext = FileExtensionValidator(
    allowed_extensions=["xls", "gz", "csv", "xlsx"]
)
validator_start_min = MinValueValidator(limit_value=1)
validator_stop_min = MinValueValidator(limit_value=1)


class MailForm(forms.Form):
    file = forms.FileField(validators=[validator_file_ext])
    sender = forms.CharField()
    reply_to = forms.EmailField(required=False)
    subject = forms.CharField()
    content = QuillFormField()
    email_key = forms.CharField()
    start = forms.IntegerField(validators=[validator_start_min])
    stop = forms.IntegerField(validators=[validator_stop_min])
    attachments = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}), required=False
    )
    mail_manager = forms.ModelChoiceField(
        queryset=EmailManager.objects.all(),
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    def clean(self):
        cleaned = super().clean()

        # Validate stop is greater than start
        start = cleaned.get("start")
        stop = cleaned.get("stop")
        if (start is not None and stop is not None) and (start > stop):
            error = ValidationError(
                "Start must not be greater that stop", code="start_stop_error"
            )
            self.add_error("start", error)

        return cleaned

    def save(self, commit=True):
        file = self.cleaned_data.get("file")
        obj = Uploads(file=file)
        if commit:
            obj.save()
        return obj


class EmailManagerConfigForm(forms.ModelForm):
    label = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Enter a label for this email manager",
    )
    mail_manager = forms.ChoiceField(
        choices=MAIL_MANAGERS,
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Select the email manager",
    )

    class Meta:
        model = EmailManager
        fields = ["label", "mail_manager"]

    def save(self, config, *args, **kwargs):
        self.instance.config = config
        return super().save(*args, **kwargs)
