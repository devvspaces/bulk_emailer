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
    sender = models.CharField(max_length=255, blank=True)
    reply_to = models.CharField(max_length=255, blank=True)
    email_domain = models.CharField(max_length=255, blank=True)

    @property
    def config_json(self):
        return json.dumps(
            {
                "label": self.label,
                "mail_manager": self.get_mail_manager_display(),
                "sender": self.sender,
                "reply_to": self.reply_to,
                "email_domain": self.email_domain,
                **self.config,
            }
        )

    def get_email_manager(self, sender: str, email_domain: str, reply_to: str) -> BaseEmailManager:
        email_manager: BaseEmailManager = MANAGER_CONFIG.get(self.mail_manager).get(
            "manager"
        )
        return email_manager(
            **self.config,
            sender=f"{sender}@{email_domain}",
            block_send=settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
            reply_email=reply_to,
        )

    def __str__(self):
        return f"{self.label} - {self.get_mail_manager_display()}"


class Job(models.Model):
    """
    A bulk email/SMS send job with progress tracking.
    """

    class JobType(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    job_type = models.CharField(max_length=10, choices=JobType.choices)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    subject = models.CharField(max_length=255, blank=True)
    sender = models.CharField(max_length=255, blank=True)
    reply_to = models.CharField(max_length=255, blank=True)
    email_domain = models.CharField(max_length=255, blank=True)
    manager_label = models.CharField(max_length=255, blank=True)
    manager_type = models.CharField(max_length=10, blank=True)
    manager_config = models.JSONField(default=dict, blank=True)
    recipient_field = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    attachment_paths = models.JSONField(default=list, blank=True)
    start = models.PositiveIntegerField(default=1)
    stop = models.PositiveIntegerField(default=1)
    sent = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    stop_requested = models.BooleanField(default=False)
    upload = models.ForeignKey(
        Uploads, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total(self):
        return self.stop - self.start + 1

    @property
    def processed(self):
        return self.sent + self.failed

    @property
    def next_index(self):
        return self.start + self.processed

    @property
    def progress(self):
        total = self.total
        if total <= 0:
            return 100 if self.status == self.Status.COMPLETED else 0
        return min(100, round(self.processed / total * 100))

    @property
    def is_active(self):
        return self.status in (self.Status.PENDING, self.Status.RUNNING)

    def __str__(self):
        return f"Job #{self.pk} - {self.get_job_type_display()} ({self.get_status_display()})"
