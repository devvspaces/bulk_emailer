"""
Background job execution for bulk email/SMS sending.

Sending runs in a daemon thread. Progress is persisted to the ``Job`` model
after each recipient using short, atomic ``F()`` updates so the UI can poll it
and so the job can be resumed if the app is restarted mid-send.
"""

import os
import threading

from django.conf import settings
from django.db.models import F
from django.utils import timezone

from mailer.mail_manager import MANAGER_CONFIG
from mailer.models import Job
from messenger.messager import ExcelMessenger
from messenger.messsage_manager import HtmlMessageManager
from messenger.sms_manager import SmsManager
from utils.loggers import err_logger

_cancel_events = {}
_running = set()
_registry_lock = threading.Lock()


def _get_event(job_id):
    with _registry_lock:
        if job_id not in _cancel_events:
            _cancel_events[job_id] = threading.Event()
        return _cancel_events[job_id]


def request_cancel(job_id):
    """Persistently flag a job for cancellation and signal its thread."""
    Job.objects.filter(pk=job_id).update(stop_requested=True)
    _get_event(job_id).set()


def build_messenger(job):
    """
    Reconstruct a fully-configured messenger from a Job's stored snapshot.
    """
    if job.job_type == Job.JobType.EMAIL:
        manager_cls = MANAGER_CONFIG[job.manager_type]["manager"]
        sender_manager = manager_cls(
            **job.manager_config,
            sender=job.sender,
            block_send=settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
            reply_email=job.reply_to or None,
        )
        message_manager = HtmlMessageManager(
            template_name="mailer/email_templates/template1.html",
            request=None,
            context={"reply_to": job.reply_to or None},
        )
    else:
        sender_manager = SmsManager(
            sid=settings.TWILIO_SID,
            token=settings.TWILIO_TOKEN,
            sender=job.sender,
            block_send=settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
        )
        message_manager = HtmlMessageManager(
            template_name="mailer/sms_templates/template1.html",
            request=None,
            context={"subject": job.subject},
        )

    file_path = job.upload.file.path
    messenger = ExcelMessenger(
        start=job.next_index,
        stop=job.stop,
        file_path=file_path,
        recipient_field=job.recipient_field,
    )
    messenger.set_sender_manager(sender_manager)
    messenger.set_message_manager(message_manager)
    return messenger


def save_attachments(job, files):
    """Persist uploaded attachments next to the job so they survive restarts."""
    entries = []
    if files:
        folder = os.path.join(settings.MEDIA_ROOT, "jobs", str(job.pk), "attachments")
        os.makedirs(folder, exist_ok=True)
        for f in files:
            path = os.path.join(folder, os.path.basename(f.name))
            with open(path, "wb") as out:
                for chunk in f.chunks():
                    out.write(chunk)
            entries.append(
                {
                    "filename": f.name,
                    "path": path,
                    "mime_type": f.content_type or "application/octet-stream",
                }
            )
    job.attachment_paths = entries
    job.save(update_fields=["attachment_paths"])


def load_attachments(job):
    attachments = []
    for entry in job.attachment_paths or []:
        path = entry.get("path")
        if path and os.path.exists(path):
            with open(path, "rb") as fh:
                data = fh.read()
            attachments.append(
                {
                    "filename": entry.get("filename", os.path.basename(path)),
                    "data": data,
                    "mime_type": entry.get("mime_type", "application/octet-stream"),
                }
            )
    return attachments


def _run_job(job_id):
    from django.db import connection

    with _registry_lock:
        if job_id in _running:
            return
        _running.add(job_id)

    try:
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return

        if job.status not in (Job.Status.PENDING, Job.Status.RUNNING):
            return

        Job.objects.filter(pk=job_id).update(
            status=Job.Status.RUNNING,
            stop_requested=False,
            started_at=timezone.now(),
        )

        event = _get_event(job_id)
        messenger = build_messenger(job)
        attachments = load_attachments(job)

        try:
            results = messenger.start_process(
                subject=job.subject,
                message=job.message,
                attachments=attachments,
            )
            for sent in results:
                if event.is_set():
                    Job.objects.filter(pk=job_id).update(
                        status=Job.Status.CANCELLED,
                        finished_at=timezone.now(),
                    )
                    return
                if sent:
                    Job.objects.filter(pk=job_id).update(sent=F("sent") + 1)
                else:
                    Job.objects.filter(pk=job_id).update(failed=F("failed") + 1)
        except Exception as e:
            err_logger.exception("Job %s failed", job_id)
            Job.objects.filter(pk=job_id).update(
                status=Job.Status.FAILED,
                error=str(e)[:2000],
                finished_at=timezone.now(),
            )
            return

        job.refresh_from_db()
        if job.failed == 0 and job.processed >= job.total:
            Job.objects.filter(pk=job_id).update(
                status=Job.Status.COMPLETED,
                finished_at=timezone.now(),
            )
        else:
            Job.objects.filter(pk=job_id).update(
                status=Job.Status.PARTIAL,
                finished_at=timezone.now(),
            )
    finally:
        with _registry_lock:
            _running.discard(job_id)
        connection.close()


def start_job(job):
    """Spawn the background thread that executes a pending job."""
    thread = threading.Thread(target=_run_job, args=(job.pk,), daemon=True)
    thread.start()
    return job


def resume_orphaned_jobs():
    """
    Resume jobs left in a pending/running state by a previous shutdown.
    Idempotent and safe to call multiple times.
    """
    from django.db import connection

    try:
        orphans = Job.objects.filter(
            status__in=[Job.Status.PENDING, Job.Status.RUNNING]
        )
        for job in orphans:
            if job.pk in _running:
                continue
            if job.stop_requested:
                Job.objects.filter(pk=job.pk).update(
                    status=Job.Status.CANCELLED,
                    finished_at=timezone.now(),
                )
                continue
            if job.upload is None or not job.upload.file:
                Job.objects.filter(pk=job.pk).update(
                    status=Job.Status.FAILED,
                    error="Recipient file is missing.",
                    finished_at=timezone.now(),
                )
                continue
            start_job(job)
    except Exception as e:  # noqa: BLE001 - table may not exist yet on startup
        err_logger.exception("Failed to resume orphaned jobs: %s", e)
    finally:
        connection.close()
