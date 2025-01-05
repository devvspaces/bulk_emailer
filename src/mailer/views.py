import json
import os
from typing import Any
from django.conf import settings

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView
from mailer.mail_manager import MANAGER_CONFIG
from mailer.models import EmailManager
from messenger.sms_manager import SmsManager
from messenger.messager import ExcelMessenger
from messenger.messsage_manager import HtmlMessageManager
from utils.general import count_true_in_iter
from utils.loggers import err_logger  # noqa

from .forms import EmailManagerConfigForm, MailForm


class Dashboard(TemplateView):
    """
    Email Sender Dashboard
    """

    template_name = "mailer/index.html"
    message_template = "mailer/email_templates/template1.html"
    extra_context = {
        "title": "Email Sender",
        "page": "home",
    }
    form_class = MailForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = MailForm()
        return context

    def get_message_context(self, data: dict):
        """
        Get message context

        :param data: form cleaned data
        :type data: dict
        :return: message context
        :rtype: dict
        """
        return {"reply_to": data.get("reply_to")}

    def create_message_manager(self, data: dict):
        """
        Create message manager

        :param data: form cleaned data
        :type data: dict
        :return: message manager
        :rtype: HtmlMessageManager
        """
        return HtmlMessageManager(
            template_name=self.message_template,
            request=self.request,
            context=self.get_message_context(data),
        )

    def create_sender_manager(self, data: dict):
        """
        Create sender manager

        :param data: form cleaned data
        :type data: dict
        :return: sender manager
        :rtype: Email manager
        """
        sender = data.get("sender")
        reply_to = data.get("reply_to")
        email_domain = data.get("email_domain")
        mail_manager = data.get("mail_manager")
        return mail_manager.get_email_manager(sender, email_domain, reply_to)

    def create_messenger(self, file_path: str, data: dict):
        """
        Create messenger

        :param file_path: path to excel file
        :type file_path: str
        :param data: form cleaned data
        :type data: dict
        :return: messenger
        :rtype: ExcelMessenger
        """
        start = data.get("start")
        stop = data.get("stop")
        messenger = ExcelMessenger(
            start=start,
            stop=stop,
            file_path=file_path,
            recipient_field=data.get("email_key"),
        )
        messenger.set_sender_manager(self.create_sender_manager(data))
        messenger.set_message_manager(self.create_message_manager(data))
        return messenger

    def post(self, request, **kwargs):
        """
        Post request, save form for uploaded file
        and start sending emails
        """
        form = self.form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save()

            subject = form.cleaned_data.get("subject")
            message = json.loads(form.cleaned_data.get("content")).get("html")
            start = form.cleaned_data.get("start")
            stop = form.cleaned_data.get("stop")

            attachments = []
            files = request.FILES.getlist("attachments")
            for file in files:
                attachments.append(
                    {
                        "filename": file.name,
                        "data": file.read(),
                        "mime_type": file.content_type,
                    }
                )

            file_path = obj.file.path
            messages_to_be_sent = stop - start + 1

            completed = False
            
            try:
                messenger = self.create_messenger(file_path, form.cleaned_data)

                sents_fails = messenger.start_process(
                    subject=subject, message=message, attachments=attachments
                )
                sents = count_true_in_iter(sents_fails)
                fails = messages_to_be_sent - sents

                response_message = "{} messages sent, {} messages failed".format(
                    sents, fails
                )

                messages.success(request, response_message)
                completed = True
            except Exception as e:
                err_logger.exception(e)
                messages.warning(request, e)

            obj.delete()
            os.remove(file_path)
            if completed:
                return redirect(self.request.get_full_path())

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class SmsDashboard(Dashboard):
    """
    SMS Sender Dashboard
    """

    template_name = "mailer/sms.html"
    message_template = "mailer/sms_templates/template1.html"
    extra_context = {
        "title": "SMS Sender",
        "page": "phone",
    }

    def get_message_context(self, data: dict):
        return {
            "subject": data.get("subject"),
        }

    def create_sender_manager(self, data: dict):
        """
        Create sender manager

        :param data: form cleaned data
        :type data: dict
        :return: sender manager
        :rtype: SmsManager
        """
        sender = data.get("sender")
        return SmsManager(
            sid=settings.TWILIO_SID,
            token=settings.TWILIO_TOKEN,
            sender=sender,
            block_send=False and settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
        )


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
        context["form"] = EmailManagerConfigForm()
        forms_dict = {
            manager: MANAGER_CONFIG[manager]["form"](manager=manager, prefix=manager)
            for manager in MANAGER_CONFIG.keys()
        }
        context["forms"] = list(forms_dict.values())
        context["managers"] = {"managers": list(MANAGER_CONFIG.keys())}
        return context

    def post(self, request, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        form = EmailManagerConfigForm(data=request.POST)
        if form.is_valid():
            manager = form.cleaned_data.get("mail_manager")
            manager_form = MANAGER_CONFIG[manager]["form"](data=request.POST, prefix=manager, manager=manager)
            if manager_form.is_valid():
                config = manager_form.cleaned_data
                form.save(config)
                messages.success(request, "Manager added successfully")
                return redirect("mailer:settings")
            else:
                messages.error(request, "Invalid form data")
            forms_dict = {
                manager: MANAGER_CONFIG[manager]["form"](manager=manager, prefix=manager)
                for manager in MANAGER_CONFIG.keys()
            }
            forms_dict[manager] = manager_form
            context["forms"] = list(forms_dict.values())
        context["form"] = form
        return self.render_to_response(context)
