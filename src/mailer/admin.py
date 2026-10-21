from django.contrib import admin

from .models import EmailManager, Job, Uploads


@admin.register(Uploads)
class UploadsAdmin(admin.ModelAdmin):
    list_display = ["id", "file"]


@admin.register(EmailManager)
class EmailManagerAdmin(admin.ModelAdmin):
    list_display = ["id", "label", "mail_manager", "sender", "email_domain"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "job_type",
        "status",
        "subject",
        "sent",
        "failed",
        "created_at",
    ]
    list_filter = ["job_type", "status"]
