import smtplib
import ssl
from contextlib import ContextDecorator
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
import logging


class EmailConnection(ContextDecorator):
    """
    This class is responsible for connecting to the
    email server and sending the email.
    """

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.context = ssl.create_default_context()

    def __enter__(self):
        logging.info("Connecting to the email server")
        if self.port == 465:
            self.connection = smtplib.SMTP_SSL(
                self.host, self.port, context=self.context
            )
        else:
            self.connection = smtplib.SMTP(self.host, self.port)
            self.connection.starttls(context=self.context)
        logging.info("Logging into the email server")
        self.connection.login(self.username, self.password)
        logging.info("Successfully logged in")
        return self

    def __exit__(self, *exc):
        logging.info("Disconnecting from the email server")
        self.connection.quit()

    def send(
        self,
        subject: str,
        recipient: str,
        text: str,
        sender: str,
        html: str = None,
        attachments: list[dict[str, bytes | str]] = None,
    ):
        """
        Send email

        :param subject: Email subject
        :type subject: str
        :param recipient: Email recipient
        :type recipient: str
        :param text: Email text
        :type text: str
        :param sender: Email sender
        :type sender: str
        :param html: Email html, defaults to None
        :type html: str, optional
        :param attachments: Email attachments in the form of a list of dictionaries of the form {"filename": str, "data": bytes}, defaults to None
        :type attachments: list[dict[str, bytes  |  str]], optional
        :return: True if email is sent successfully else raise exception
        :rtype: bool
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = recipient

        message.attach(MIMEText(text, "plain"))
        if html is not None:
            message.attach(MIMEText(html, "html"))

        if attachments is not None:
            for attachment in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment["data"])
                encoders.encode_base64(part)
                filename = attachment["filename"]
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                message.attach(part)

        try:
            self.connection.sendmail(self.username, recipient, message.as_string())
            return True
        except Exception as e:
            logging.error(f"Failed to send email: {e}")
            raise e


connection: EmailConnection = None


def get_connection(host: str, port: int, username: str, password: str):
    global connection
    if connection is None:
        connection = EmailConnection(host, port, username, password)
    return connection
