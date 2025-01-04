"""
Managers for email sending
"""

from typing import Dict, overload

import requests
from django.conf import settings
from messenger.smtp import EmailConnection, get_connection
from utils.general import bytes_to_base64_str, is_success
from utils.loggers import logger

from .sender_manager import BaseSenderManager


class BaseEmailManager(BaseSenderManager):
    def __init__(self, reply_email: str = None, *args, **kwargs) -> None:
        self.__reply_email = reply_email
        super().__init__(*args, **kwargs)

    def get_recipient_field(self) -> str:
        return settings.RECEIPIENT_EMAIL_KEY

    def get_reply_email(self) -> str:
        """
        Get reply email address

        :return: reply email address
        :rtype: str
        """
        if self.__reply_email is None:
            return self.get_sender()
        return self.__reply_email


class SendGridEmailManager(BaseEmailManager):
    @overload
    def __init__(
        self, api_key: str, sender: str, debug: bool, block_send: bool, reply_email: str
    ) -> None: ...

    def __init__(self, api_key: str, *args, **kwargs) -> None:
        """
        SendGrid email manager

        :param api_key: api key
        :type api_key: str
        """
        super().__init__(*args, **kwargs)
        self.__api_key = api_key
        self.__headers: dict = self.set_headers()

    def get_api_key(self) -> str:
        """
        Get api key

        :return: api key
        :rtype: str
        """
        return self.__api_key

    def set_headers(self) -> dict:
        """
        Set headers for sendgrid

        :return: headers
        :rtype: dict
        """
        headers = {"Authorization": f"Bearer {self.get_api_key()}"}
        return headers

    def get_headers(self) -> dict:
        """
        Get headers

        :return: headers
        :rtype: dict
        """
        return self.__headers

    def get_post_data(self, email: str, subject: str, message: str) -> Dict[str, str]:
        """
        Get post data for sendgrid

        :param email: email of the receiver
        :type email: str
        :param subject: subject of the email
        :type subject: str
        :param message: message of the email
        :type message: str
        :return: post data
        :rtype: Dict[str, str]
        """
        data = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": self.get_sender()},
            "reply_to": {"email": self.get_reply_email()},
            "subject": subject,
            "content": [{"type": "text/html", "value": message}],
        }
        return data

    def get_post_url(self) -> str:
        """
        Get post url for sendgrid

        :return: post url
        :rtype: str
        """
        return "https://api.sendgrid.com/v3/mail/send"

    def send(self, recipient: str, subject: str, message: str, **kwargs):
        response = requests.post(
            url=self.get_post_url(),
            json=self.get_post_data(recipient, subject, message),
            headers=self.get_headers(),
        )
        stat = is_success(response.status_code)
        if not stat and self.get_debug():
            logger.debug(response.content)
            logger.debug(response.status_code)
        return stat


class ZeptoEmailManager(BaseEmailManager):
    @overload
    def __init__(
        self, api_key: str, sender: str, debug: bool, block_send: bool, reply_email: str
    ) -> None: ...

    def __init__(self, api_key: str, *args, **kwargs) -> None:
        """
        Zepto email manager

        :param api_key: api key
        :type api_key: str
        """
        super().__init__(*args, **kwargs)
        self.__api_key = api_key
        self.__headers: dict = self.set_headers()

    def get_api_key(self) -> str:
        """
        Get zeptomail token

        :return: api key
        :rtype: str
        """
        return self.__api_key

    def set_headers(self) -> dict:
        """
        Set headers for zeptomail

        :return: headers
        :rtype: dict
        """
        headers = {"Authorization": self.get_api_key()}
        return headers

    def get_headers(self) -> dict:
        """
        Get headers

        :return: headers
        :rtype: dict
        """
        return self.__headers

    def get_post_data(
        self, email: str, subject: str, message: str, **kwargs
    ) -> Dict[str, str]:
        """
        Get post data for zeptomail

        :param email: email of the receiver
        :type email: str
        :param subject: subject of the email
        :type subject: str
        :param message: message of the email
        :type message: str
        :return: post data
        :rtype: Dict[str, str]
        """
        attachments = kwargs.get("attachments", [])
        data = {
            "to": [{"email_address": {"address": email}}],
            "from": {"address": self.get_sender()},
            "subject": subject,
            "htmlbody": message,
            "attachments": [
                {
                    "name": _["filename"],
                    "content": bytes_to_base64_str(_["data"]),
                    "mime_type": _["mime_type"],
                }
                for _ in attachments
            ],
        }
        return data

    def get_post_url(self) -> str:
        """
        Get post url for zepto

        :return: post url
        :rtype: str
        """
        return "https://api.zeptomail.com/v1.1/email"

    def send(self, recipient: str, subject: str, message: str, **kwargs):
        response = requests.post(
            url=self.get_post_url(),
            json=self.get_post_data(recipient, subject, message, **kwargs),
            headers=self.get_headers(),
        )
        stat = is_success(response.status_code)
        if not stat and self.get_debug():
            logger.debug(response.content)
            logger.debug(response.status_code)
        return stat


class SmtpEmailManager(BaseEmailManager):
    @overload
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        debug: bool,
        block_send: bool,
        reply_email: str,
    ) -> None: ...

    def __init__(
        self, host: str, port: int, username: str, password: str, *args, **kwargs
    ) -> None:
        """
        SMTP email manager

        :param host: host
        :type host: str
        :param port: port
        :type port: int
        :param username: username
        :type username: str
        :param password: password
        :type password: str
        """
        super().__init__(*args, **kwargs)
        self.__host = host
        self.__port = port
        self.__username = username
        self.__password = password

    @property
    def conn(self) -> EmailConnection:
        """
        Get SMTP connection
        """
        return get_connection(
            host=self.__host,
            port=self.__port,
            username=self.__username,
            password=self.__password,
        )

    def send(
        self, recipient: str, subject: str, message: str, attachments=None, **kwargs
    ):
        try:
            self.conn.send(
                subject=subject,
                recipient=recipient,
                text=message,
                sender=self.get_sender(),
                html=message,
                attachments=attachments,
            )
        except Exception as e:
            logger.exception(e)
            return False
        return True
