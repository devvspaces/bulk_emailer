"""
Module for email messenger
"""

from typing import Type
from .messsage_manager import BaseMessageManager
from .email_manager import BaseEmailManager


class Messenger:
    def __init__(self, sender: str, message: str) -> None:
        self.email_manager: Type[BaseEmailManager] = None
        self.message_manager: Type[BaseMessageManager] = None

    def get_message(self, message: str, data: dict = None) -> str:
        if data is None:
            data = {}
        for key, value in data.items():
            message = message.replace(key, value)
        return message
