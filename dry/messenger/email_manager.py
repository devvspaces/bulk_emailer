"""
Managers for email sending
"""

from typing import Dict, Optional
import requests


class BaseEmailManager:
    def __init__(
        self, domain: str, sender: str,
        debug: bool = False, block_send: bool = False
    ) -> None:
        self.__domain = domain
        self.__sender = sender
        self.__debug = debug
        self.__block_send = block_send

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

    def print_message(self, message: str) -> Optional[bool]:
        if self.__debug:
            print(message)
            return True

    def send_email(self, message) -> bool:
        self.print_message(message)

        if self.__block_send:
            return True

        return False


class SendGridEmailManager(BaseEmailManager):
    def __init__(self, api_key: str, **kwargs) -> None:
        super().__init__(**kwargs)
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
            "subject": subject,
            "content": [{"type": "text/html", "value": message}]
        }
        return data

    def get_post_url(self) -> str:
        return 'https://api.sendgrid.com/v3/mail/send'

    def send_email(
        self, email: str, subject: str, message: str, fail: bool = True
    ):
        super().send_email(message)
        try:
            response = requests.post(
                url=self.get_post_url(),
                json=self.get_post_data(email, subject, message),
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            if not fail:
                raise e
        return False
