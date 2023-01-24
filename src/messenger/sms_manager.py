"""
Managers for email sending
"""

from typing import overload

from django.conf import settings
from twilio.rest import Client

from .sender_manager import BaseSenderManager


class SmsManager(BaseSenderManager):

    @overload
    def __init__(
        self, sid: str, token: str, sender: str,
        debug: bool, block_send: bool
    ) -> None:
        ...

    def __init__(
        self, sid: str, token: str,
        *args, **kwargs
    ) -> None:
        """
        Twilio SMS manager

        :param sid: twilio sid
        :type sid: str
        :param token: twilio token
        :type token: str
        :param sender: sender phone number for twilio (e.g. +1234567890)
        :type sender: str
        """
        super().__init__(*args, **kwargs)
        self.client = Client(sid, token)

    def get_receipient_field(self) -> str:
        return settings.RECEIPIENT_SMS_KEY

    def send(
        self, receipient: str, message: str, **kwargs
    ) -> bool:
        """
        Send SMS message to receipient using Twilio

        :param receipient: receipient phone number (e.g. +1234567890)
        :type receipient: str
        :param message: message to send
        :type message: str
        :return: success of sending message
        :rtype: bool
        """
        message = self.client.messages.create(
            body=message,
            from_=self.get_sender(),
            to=receipient
        )
        return True
