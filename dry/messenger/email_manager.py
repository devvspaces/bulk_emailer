"""
Managers for email sending
"""

from typing import Dict, Optional
import requests
from utils.loggers import logger
from utils.general import is_success


class BaseEmailManager:
    def __init__(
        self, domain: str, sender: str,
        debug: bool = False, block_send: bool = False,
        reply_email: str = None
    ) -> None:
        self.__domain = domain
        self.__sender = sender
        self.__debug = debug
        self.__block_send = block_send
        self.__reply_email = reply_email

    def set_debug(self) -> None:
        self.__debug = True

    def get_debug(self) -> bool:
        return self.__debug

    def unset_debug(self) -> None:
        self.__debug = False

    def unblock_send(self) -> None:
        self.__block_send = False

    def block_send(self) -> None:
        self.__block_send = True

    def get_block_send(self) -> bool:
        return self.__block_send

    def get_sender_email(self) -> str:
        return f"{self.__sender}@{self.__domain}"

    def get_reply_email(self) -> str:
        if self.__reply_email is None:
            return self.get_sender_email()
        return self.__reply_email

    def print_message(self, message: str) -> Optional[bool]:
        if self.__debug:
            print(message)
            return True

    def send_mail(self) -> bool:
        raise NotImplementedError('No send mail function')

    def send_email(
        self, message: str, fail: bool = True,
        **kwargs
    ) -> bool:
        self.print_message(message)

        if self.__block_send:
            return True

        try:
            kwargs['message'] = message
            return self.send_mail(**kwargs)
        except Exception as e:
            if not fail:
                raise e
        return False


class SendGridEmailManager(BaseEmailManager):
    def __init__(
        self, api_key: str, domain: str, sender: str, debug: bool = False,
        block_send: bool = False, reply_email: str = None
    ) -> None:
        super().__init__(domain, sender, debug, block_send, reply_email)
        self.__api_key = api_key
        self.__headers: dict = self.set_headers()

    def get_api_key(self) -> str:
        return self.__api_key

    def set_headers(self) -> dict:
        headers = {
            'Authorization': f'Bearer {self.get_api_key()}'
        }
        return headers

    def get_headers(self) -> dict:
        return self.__headers

    def get_post_data(
        self, email: str, subject: str, message: str
    ) -> Dict[str, str]:
        data = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": self.get_sender_email()},
            "reply_to": {"email": self.get_reply_email()},
            "subject": subject,
            "content": [{"type": "text/html", "value": message}]
        }
        return data

    def get_post_url(self) -> str:
        return 'https://api.sendgrid.com/v3/mail/send'

    def send_mail(
        self, email: str, subject: str, message: str, **kwargs
    ):
        response = requests.post(
            url=self.get_post_url(),
            json=self.get_post_data(email, subject, message),
            headers=self.get_headers()
        )
        stat = is_success(response.status_code)
        if not stat:
            logger.debug(response.content)
            logger.debug(response.status_code)
        return stat
