from django import forms
import socket

from messenger.email_manager import SendGridEmailManager, SmtpEmailManager, ZeptoEmailManager


class ManagerForm(forms.Form):
    manager = None

    def __init__(self, manager: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager


class SMTPForm(ManagerForm):
    host = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    port = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean_host(self):
        host = self.cleaned_data.get("host")
        try:
            # Validate the host by resolving it
            socket.gethostbyname(host)
        except socket.error:
            raise forms.ValidationError(
                "Invalid host. Please enter a valid hostname or IP address."
            )
        return host

    def clean_port(self):
        port = self.cleaned_data.get("port")
        if port < 1 or port > 65535:
            raise forms.ValidationError("Port must be between 1 and 65535.")
        return port


class ApiKeyForm(ManagerForm):
    api_key = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))


MAIL_MANAGERS = (
    ("sendgrid", "Sendgrid"),
    ("zepto", "ZeptoMail"),
    ("smtp", "SMTP Server"),
)

MANAGER_CONFIG = {
    "sendgrid": {
        "form": ApiKeyForm,
        "manager": SendGridEmailManager,
    },
    "zepto": {
        "form": ApiKeyForm,
        "manager": ZeptoEmailManager,
    },
    "smtp": {
        "form": SMTPForm,
        "manager": SmtpEmailManager
    },
}
