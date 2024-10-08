import os
from django.conf import settings

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView
from messenger.email_manager import ZeptoEmailManager
from messenger.sms_manager import SmsManager
from messenger.messager import ExcelMessenger
from messenger.messsage_manager import HtmlMessageManager
from utils.general import count_true_in_iter
from utils.loggers import err_logger, logger  # noqa

from .forms import MailForm


class Dashboard(TemplateView):
    """
    Email Sender Dashboard
    """
    template_name = 'mailer/index.html'
    message_template = 'mailer/email_templates/template1.html'
    extra_context = {
        'title': 'Email Sender',
        'page': 'home',
    }
    form_class = MailForm

    def get_message_context(self, data: dict):
        """
        Get message context

        :param data: form cleaned data
        :type data: dict
        :return: message context
        :rtype: dict
        """
        return {
            'reply_to': data.get('reply_to')
        }

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
            context=self.get_message_context(data)
        )

    def create_sender_manager(self, data: dict):
        """
        Create sender manager

        :param data: form cleaned data
        :type data: dict
        :return: sender manager
        :rtype: Email manager
        """
        sender = data.get('sender')
        reply_to = data.get('reply_to')
        return ZeptoEmailManager(
            api_key=settings.ZEPTOTOKEN,
            sender=f"{sender}@{settings.EMAIL_DOMAIN}",
            block_send=settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
            reply_email=reply_to
        )

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
        start = data.get('start')
        stop = data.get('stop')
        messenger = ExcelMessenger(
            start=start,
            stop=stop,
            file_path=file_path
        )
        messenger.set_sender_manager(
            self.create_sender_manager(data)
        )
        messenger.set_message_manager(
            self.create_message_manager(data)
        )
        return messenger

    def post(self, request, **kwargs):
        """
        Post request, save form for uploaded file
        and start sending emails
        """
        form = self.form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save()

            subject = form.cleaned_data.get('subject')
            message = form.cleaned_data.get('message')
            start = form.cleaned_data.get('start')
            stop = form.cleaned_data.get('stop')

            file_path = obj.file.path
            messages_to_be_sent = stop - start + 1

            completed = False

            try:
                messenger = self.create_messenger(file_path, form.cleaned_data)

                message = message.replace('\n', '<br>')
                print(message)

                sents_fails = messenger.start_process(
                    subject=subject,
                    message=message
                )
                sents = count_true_in_iter(sents_fails)
                fails = messages_to_be_sent - sents

                response_message = "{} messages sent, {} messages failed"\
                    .format(sents, fails)

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
    template_name = 'mailer/sms.html'
    message_template = 'mailer/sms_templates/template1.html'
    extra_context = {
        'title': 'SMS Sender',
        'page': 'phone',
    }

    def get_message_context(self, data: dict):
        return {
            'subject': data.get('subject'),
        }

    def create_sender_manager(self, data: dict):
        """
        Create sender manager

        :param data: form cleaned data
        :type data: dict
        :return: sender manager
        :rtype: SmsManager
        """
        sender = data.get('sender')
        return SmsManager(
            sid=settings.TWILIO_SID,
            token=settings.TWILIO_TOKEN,
            sender=sender,
            block_send=False and settings.BLOCK_EMAIL,
            debug=settings.DEBUG_EMAIL,
        )
