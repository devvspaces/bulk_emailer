"""
Managers for email sending
"""

from typing import Optional


class BaseSenderManager:
    def __init__(
        self, sender: str, debug: bool = False,
        block_send: bool = False,
    ) -> None:
        self.__sender = sender
        self.__debug = debug
        self.__block_send = block_send

    def get_receipient_field(self) -> str:
        """
        Get receipient key
        """
        raise NotImplementedError('No receipient key')

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

    def get_sender(self) -> str:
        """
        Get sender info

        :return: sender info
        :rtype: str
        """
        return self.__sender

    def print_message(self, message: str) -> Optional[bool]:
        if self.get_debug():
            print(message)
            return True

    def send(self) -> bool:
        raise NotImplementedError('No send function')

    def send_message(
        self, message: str, fail: bool = False,
        **kwargs
    ) -> bool:
        self.print_message(message)

        if self.__block_send:
            return True

        try:
            kwargs['message'] = message
            return self.send(**kwargs)
        except Exception as e:
            if not fail:
                raise e
        return False
