from django.views.generic import TemplateView

from .forms import MailForm

from messenger.email_manager import SendGridEmailManager
from messenger.messsage_manager import HtmlMessageManager
from messenger.messager import ExcelMessenger


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

            message_manager = HtmlMessageManager(
                template_name='mailer/email_test.html',
                request=request,
                context=email_message_context
            )

            email_manager = SendGridEmailManager(
                api_key='',
                domain='example.com',
                sender=sender,
                debug=True,
                block_send=True,
                reply_email=reply_to
            )

            main_message = ExcelMessenger(
                start=start,
                stop=stop,
                file_path=file_path
            )
            main_message.set_email_manager(email_manager)
            main_message.set_message_manager(message_manager)

            main_message.start_process()

            obj.delete()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)
