import os
from django.conf import settings

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView
from messenger.email_manager import SendGridEmailManager
from messenger.messager import ExcelMessenger
from messenger.messsage_manager import HtmlMessageManager
from utils.general import count_true_in_iter
from utils.loggers import err_logger, logger  # noqa

from .forms import MailForm


class Dashboard(TemplateView):
    template_name = 'mailer/index.html'

    def post(self, request, **kwargs):
        form = MailForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save()

            reply_to = form.cleaned_data.get('reply_to')
            sender = form.cleaned_data.get('sender')
            subject = form.cleaned_data.get('subject')
            message = form.cleaned_data.get('message')
            start = form.cleaned_data.get('start')
            stop = form.cleaned_data.get('stop')

            file_path = obj.file.path
            email_message_context = {
                'reply_to': reply_to
            }

            messages_to_be_sent = stop - start + 1

            completed = False

            try:
                message_manager = HtmlMessageManager(
                    template_name='mailer/email_test.html',
                    request=request,
                    context=email_message_context
                )

                email_manager = SendGridEmailManager(
                    api_key=settings.SEND_GRID,
                    domain=settings.EMAIL_DOMAIN,
                    sender=sender,
                    block_send=settings.BLOCK_EMAIL,
                    debug=settings.DEBUG_EMAIL,
                    reply_email=reply_to
                )

                main_message = ExcelMessenger(
                    start=start,
                    stop=stop,
                    file_path=file_path
                )
                main_message.set_email_manager(email_manager)
                main_message.set_message_manager(message_manager)

                sents_fails = main_message.start_process(
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
