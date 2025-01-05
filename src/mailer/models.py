import json
from django.db import models

from mailer.mail_manager import MAIL_MANAGERS, MANAGER_CONFIG
from messenger.email_manager import BaseEmailManager
from django.conf import settings


class Uploads(models.Model):
    """
    Model to save files uploaded to storage

    :param models: Model
    :type models: models.Model
    :return: Uploads
    :rtype: models.Model
    """

    file = models.FileField()

    def __str__(self):
        return self.file.name


class EmailManager(models.Model):
    label = models.CharField(max_length=255)
    mail_manager = models.CharField(max_length=10, choices=MAIL_MANAGERS)
    config = models.JSONField()

    @property
    def config_json(self):
        return json.dumps(
            {
                "label": self.label,
                "mail_manager": self.get_mail_manager_display(),
                **self.config,
            }
        )

    def get_email_manager(self, sender: str, reply_to: str) -> BaseEmailManager:
        email_manager: BaseEmailManager = MANAGER_CONFIG.get(self.mail_manager).get(
            "manager"
        )
        return email_manager(
            **self.config,
            sender=f"{sender}@{settings.EMAIL_DOMAIN}",
            block_send=settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
            reply_email=reply_to,
        )

    def __str__(self):
        return f"{self.label} - {self.get_mail_manager_display()}"
