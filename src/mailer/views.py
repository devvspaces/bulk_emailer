import json
import os
import shutil
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, ListView

from mailer.mail_manager import MANAGER_CONFIG
from mailer.models import EmailManager, Job

from .forms import EmailManagerConfigForm, MailForm, SmsForm
from .jobs import request_cancel, resume_orphaned_jobs, save_attachments, start_job


class Dashboard(TemplateView):
    """
    Email Sender Dashboard
    """

    template_name = "mailer/index.html"
    extra_context = {
        "title": "Email Sender",
        "page": "home",
    }
    form_class = MailForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("form", self.form_class())
        context["email_managers"] = [
            {
                "id": m.pk,
                "label": m.label,
                "mail_manager": m.mail_manager,
                "sender": m.sender,
                "reply_to": m.reply_to,
                "email_domain": m.email_domain,
            }
            for m in EmailManager.objects.all()
        ]
        return context

    def _get_message(self, form):
        return json.loads(form.cleaned_data.get("content")).get("html")

    def _build_job(self, form, obj, message):
        mail_manager = form.cleaned_data.get("mail_manager")
        return Job(
            job_type=Job.JobType.EMAIL,
            subject=form.cleaned_data.get("subject"),
            sender=f"{form.cleaned_data.get('sender')}@{form.cleaned_data.get('email_domain')}",
            reply_to=form.cleaned_data.get("reply_to") or "",
            email_domain=form.cleaned_data.get("email_domain") or "",
            manager_label=mail_manager.label,
            manager_type=mail_manager.mail_manager,
            manager_config=mail_manager.config,
            recipient_field=form.cleaned_data.get("email_key"),
            message=message,
            start=form.cleaned_data.get("start"),
            stop=form.cleaned_data.get("stop"),
            upload=obj,
        )

    def post(self, request, **kwargs):
        """
        Post request, save the uploaded file, queue a job and redirect
        to the jobs list for progress tracking.
        """
        form = self.form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save()
            job = self._build_job(form, obj, self._get_message(form))
            job.save()
            save_attachments(job, request.FILES.getlist("attachments"))
            start_job(job)
            messages.success(request, f"Job #{job.pk} queued")
            return redirect("mailer:jobs")

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class SmsDashboard(Dashboard):
    """
    SMS Sender Dashboard
    """

    template_name = "mailer/sms.html"
    form_class = SmsForm
    extra_context = {
        "title": "SMS Sender",
        "page": "phone",
    }

    def _get_message(self, form):
        return form.cleaned_data.get("message")

    def _build_job(self, form, obj, message):
        return Job(
            job_type=Job.JobType.SMS,
            subject=form.cleaned_data.get("subject"),
            sender=form.cleaned_data.get("sender"),
            recipient_field=settings.RECEIPIENT_SMS_KEY,
            message=message,
            start=form.cleaned_data.get("start"),
            stop=form.cleaned_data.get("stop"),
            upload=obj,
        )


class Help(TemplateView):
    """
    Help and guides page
    """

    template_name = "mailer/help.html"
    extra_context = {
        "title": "Help",
        "page": "help",
    }


class JobsView(TemplateView):
    """
    List of executed/queued send jobs with live progress.
    """

    template_name = "mailer/jobs.html"
    extra_context = {
        "title": "Jobs",
        "page": "jobs",
    }

    def get(self, request, *args, **kwargs):
        resume_orphaned_jobs()
        return super().get(request, *args, **kwargs)


def jobs_data(request):
    payload = [
        {
            "id": j.pk,
            "type": j.get_job_type_display(),
            "status": j.status,
            "status_display": j.get_status_display(),
            "subject": j.subject,
            "sender": j.sender,
            "manager_label": j.manager_label,
            "total": j.total,
            "sent": j.sent,
            "failed": j.failed,
            "processed": j.processed,
            "progress": j.progress,
            "error": j.error,
            "is_active": j.is_active,
            "created_at": j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else "",
            "started_at": j.started_at.strftime("%Y-%m-%d %H:%M") if j.started_at else "",
            "finished_at": j.finished_at.strftime("%Y-%m-%d %H:%M") if j.finished_at else "",
        }
        for j in Job.objects.all()
    ]
    return JsonResponse({"jobs": payload})


def _delete_job(job):
    upload = job.upload
    if upload:
        if upload.file:
            try:
                upload.file.delete(save=False)
            except Exception:
                pass
        upload.delete()
    folder = os.path.join(settings.MEDIA_ROOT, "jobs", str(job.pk))
    shutil.rmtree(folder, ignore_errors=True)
    job.delete()


@require_POST
def job_stop(request, pk):
    request_cancel(pk)
    messages.info(request, f"Stop requested for job #{pk}")
    return redirect("mailer:jobs")


@require_POST
def job_stop_all(request):
    for job in Job.objects.filter(
        status__in=[Job.Status.PENDING, Job.Status.RUNNING]
    ):
        request_cancel(job.pk)
    messages.info(request, "All running jobs stopped")
    return redirect("mailer:jobs")


@require_POST
def job_clear(request):
    finished = Job.objects.filter(
        status__in=[
            Job.Status.COMPLETED,
            Job.Status.PARTIAL,
            Job.Status.FAILED,
            Job.Status.CANCELLED,
        ]
    )
    for job in finished:
        _delete_job(job)
    messages.info(request, "Finished jobs cleared")
    return redirect("mailer:jobs")


@require_POST
def job_clear_all(request):
    for job in Job.objects.filter(
        status__in=[Job.Status.PENDING, Job.Status.RUNNING]
    ):
        request_cancel(job.pk)
    for job in Job.objects.all():
        _delete_job(job)
    messages.info(request, "All jobs cleared")
    return redirect("mailer:jobs")


class Settings(ListView):
    """
    Email Sender Settings
    """

    template_name = "mailer/settings.html"
    extra_context = {
        "title": "Settings",
        "page": "settings",
    }
    model = EmailManager
    context_object_name = "email_managers"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        edit_manager = self._get_edit_manager()
        form = EmailManagerConfigForm(
            instance=edit_manager,
            initial={"mail_manager": edit_manager.mail_manager}
            if edit_manager
            else None,
        )
        context["form"] = form
        context["forms"] = list(self._manager_forms(edit_manager).values())
        context["managers"] = {"managers": list(MANAGER_CONFIG.keys())}
        context["edit_manager"] = edit_manager
        return context

    def _get_edit_manager(self):
        pk = self.request.GET.get("edit") or self.request.POST.get("manager_id")
        if pk:
            return EmailManager.objects.filter(pk=pk).first()
        return None

    def _manager_forms(self, edit_manager=None):
        forms_dict = {}
        for manager_key in MANAGER_CONFIG.keys():
            initial = None
            if edit_manager and edit_manager.mail_manager == manager_key:
                initial = edit_manager.config
            forms_dict[manager_key] = MANAGER_CONFIG[manager_key]["form"](
                manager=manager_key, prefix=manager_key, initial=initial
            )
        return forms_dict

    def post(self, request, **kwargs):
        self.object_list = self.get_queryset()
        edit_manager = self._get_edit_manager()
        context = self.get_context_data()
        form = EmailManagerConfigForm(data=request.POST, instance=edit_manager)
        if form.is_valid():
            manager = form.cleaned_data.get("mail_manager")
            manager_form = MANAGER_CONFIG[manager]["form"](data=request.POST, prefix=manager, manager=manager)
            if manager_form.is_valid():
                config = manager_form.cleaned_data
                form.save(config)
                messages.success(
                    request,
                    "Manager updated successfully"
                    if edit_manager
                    else "Manager added successfully",
                )
                return redirect("mailer:settings")
            else:
                messages.error(request, "Invalid form data")
            forms_dict = self._manager_forms(edit_manager)
            forms_dict[manager] = manager_form
            context["forms"] = list(forms_dict.values())
        context["form"] = form
        context["edit_manager"] = edit_manager
        return self.render_to_response(context)
