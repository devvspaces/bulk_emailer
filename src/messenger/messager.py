"""
Module for email messenger
"""

from pathlib import Path
import time
from typing import Optional, Sequence, Type

import pandas as pd
from pandas import DataFrame

from .messsage_manager import BaseMessageManager
from .sender_manager import BaseSenderManager


class Managers:
    def __init__(self) -> None:
        self.__sender: Type[BaseSenderManager] = None
        self.__message: Type[BaseMessageManager] = None
        # TODO: report manager for sending websocket
        # updates on message sending progress

    def set_sender_manager(self, manager: Type[BaseSenderManager]) -> None:
        if not isinstance(manager, BaseSenderManager):
            raise TypeError('Manager must be an instance of an Sender Manager')
        self.__sender = manager

    @property
    def sender_manager(self) -> Type[BaseSenderManager]:
        return self.__sender

    def set_message_manager(self, manager: Type[BaseMessageManager]) -> None:
        if not isinstance(manager, BaseMessageManager):
            raise TypeError('Manager must be an instance \
of an Message Manager')
        self.__message = manager

    @property
    def message_manager(self) -> BaseMessageManager:
        return self.__message

    def run_checks(self):
        if self.sender_manager is None:
            raise NotImplementedError("""No Sender manager provided,
            specify one by calling set_sender_manager method on your
            Messenger object""")

        if self.message_manager is None:
            raise NotImplementedError("""No Message manager provided,
            specify one by calling set_message_manager method on your
            Messenger object""")


class BaseMessenger:
    def __init__(
        self, start: int = 0, stop: int = 0,
        recipient_field: str = None
    ) -> None:
        self.__start = start
        self.__stop = stop
        self.__manager: Type[Managers] = None
        self.__recipient_field = recipient_field
        self.set_manager()
        self.run_checks()

    def get_start(self) -> int:
        """
        Get value to start sending messages

        :return: start value
        :rtype: int
        """
        return self.__start - 1

    def get_stop(self) -> int:
        """
        Get value to stop sending messages

        :return: stop value
        :rtype: int
        """
        return self.__stop - 1

    def get_recipient_field(self) -> str:
        """
        Get receipeint field key

        :return: receipeint field key
        :rtype: str
        """
        if self.__recipient_field is None:
            return self.get_manager().sender_manager.get_recipient_field()
        return self.__recipient_field

    def run_checks(self) -> None:
        if not isinstance(self.__start, int):
            raise TypeError('Start value must be an integer')

        if not isinstance(self.__stop, int):
            raise TypeError('Stop value must be an integer')

        if self.get_start() > self.get_stop():
            raise TypeError('Start cannot be greater that stop')

    def set_manager(self) -> None:
        self.__manager = Managers()

    def get_manager(self) -> Type[Managers]:
        return self.__manager

    def set_sender_manager(self, manager: Type[BaseSenderManager]) -> None:
        """
        Sets the sender manager to be used by the messenger to send messages

        :param manager: sender manager to be used
        :type manager: Type[BaseSenderManager]
        """
        self.get_manager().set_sender_manager(manager)

    def set_message_manager(self, manager: Type[BaseMessageManager]) -> None:
        """
        Sets the message manager to be used by the messenger to render messages

        :param manager: message manager to be used
        :type manager: Type[BaseMessageManager]
        """
        self.get_manager().set_message_manager(manager)

    def get_message(self, message: str, data: dict = None) -> str:
        """
        Formats the message with the data provided, it replaces the
        keys in the message with the values provided in the data

        :param message: message to be sent
        :type message: str
        :param data: data to format message with, defaults to None
        :type data: dict, optional
        :return: formatted message
        :rtype: str
        """
        if data is None:
            data = {}
        for key, value in data.items():
            replace_key = f'_{key}_'
            message = message.replace(replace_key, str(value))
        return message

    def start_process(self, subject: str, message: str, **kwargs) -> None:
        """
        Starts the process of sending messages to receivers

        :param subject: subject of the message
        :type subject: str
        :param message: message to be formatted and sent
        :type message: str
        :return: None
        :rtype: None
        """
        self.__manager.run_checks()
        return self.send_messages(subject, message, **kwargs)

    def send_messages(self, subject: str, message: str, **kwargs) -> None:
        """
        Sends messages to receivers

        :param subject: subject of the message
        :type subject: str
        :param message: message to be formatted and sent
        :type message: str
        :raises NotImplementedError: No send_messages method implemented
        """
        raise NotImplementedError('No send_messages \
method implemented')


class ExcelMessenger(BaseMessenger):
    """
    CSV and Excel manager for loading and sending messages to
    receiver data placed in csv or excel files.
    Files supported: xls, xlsx, csv, csv.gz
    """

    def __init__(self, file_path: str, **kwargs) -> None:
        """
        Set up excel manager with file path to the accepted readable file,
        This sets up the neccessary properties before calling parent class
        init setup to run checks.

        :param str file_path: path to file
        """
        self.__file_path = Path(file_path)
        self.__supported_read_map = {
            'xls': pd.read_excel, 'xlsx': pd.read_excel,
            'csv': pd.read_csv, 'gz': pd.read_csv
        }
        self.__read_map = None
        self.__dataframe: Optional[DataFrame] = None
        super().__init__(**kwargs)
        self.load_data()
        self.validate_data()

    def get_supported_exts(self) -> str:
        """
        Returns a string of all the supported file extensions

        :return: supported file extensions
        :rtype: str
        """
        keys = list(self.__supported_read_map.keys())
        part1 = ', '.join(keys[:-1])
        all_part = f"{part1} and {keys[-1]}"
        return all_part

    def set_ext_read_map(self, ext: str) -> None:
        """
        Sets the read function to be used to read the file
        using the read map dict.

        :param ext: file extension
        :type ext: str
        :raises TypeError: File is not in correct format
        """
        read_map = self.__supported_read_map.get(ext)
        if read_map is None:
            raise TypeError(f"File is not in correct format, \
must be {self.get_supported_exts()}. Current format {ext}")
        self.__read_map = read_map

    def validate_ext(self) -> None:
        """
        Validates the file extension and sets the read map to be used

        :raises TypeError: File does not have an extension
        """
        ext = self.get_file_path().suffix[1:].lower()
        if not ext:
            raise TypeError('File does not have an extension')
        self.set_ext_read_map(ext)

    def run_checks(self) -> None:
        """
        Runs checks on the file path provided to ensure it is a valid file

        :raises TypeError: File path is not absolute
        :raises TypeError: File does not exist
        :raises TypeError: Path provided is not a file
        """
        super().run_checks()
        if not self.get_file_path().is_absolute():
            raise TypeError('File path is not absolute')
        if not self.get_file_path().exists():
            raise TypeError('File does not exist')
        if not self.get_file_path().is_file():
            raise TypeError('Path provided is not a file')
        self.validate_ext()

    def get_file_path(self) -> Type[Path]:
        """
        Returns the file path

        :return: file path
        :rtype: Type[Path]
        """
        return self.__file_path

    def validate_data(self):
        """
        Validates the data loaded from the file

        :raises TypeError: Start index is greater than file max index
        :raises TypeError: Stop index is greater than file max index
        """
        row = self.data.shape[0] - 1
        if self.get_start() > row:
            raise TypeError('Start index is greater than file max index')
        if self.get_stop() > row:
            raise TypeError('Stop index is greater than file max index')

    def load_data(self):
        """
        Loads the data from the file into a pandas dataframe
        """
        self.__dataframe: Type[DataFrame] = self.__read_map(
            self.get_file_path(), dtype=str)

    @property
    def data(self) -> Type[DataFrame]:
        """
        Returns the data loaded from the file

        :return: data loaded from file
        :rtype: Type[DataFrame]
        """
        return self.__dataframe

    def get_range(self) -> Sequence[int]:
        """
        Returns a range of indexes to be used to get data from the file

        :return: range of indexes
        :rtype: Sequence[int]
        """
        return range(self.get_start(), self.get_stop() + 1)

    def get_index_dict(self, index: int) -> dict:
        """
        Returns a dictionary of the data at the index

        :param index: index of data
        :type index: int
        :return: data at index
        :rtype: dict
        """
        return self.data.loc[index].to_dict()

    def get_recipient_from_data(self, data: dict) -> str:
        key = self.get_recipient_field()
        value = data.get(key)
        if value is None:
            raise TypeError(f'{key.capitalize()} column not in file')
        return value

    def send_messages(
        self, subject: str, message: str,
        context: dict = None
    ):
        if context is None:
            context = {}
        for index in self.get_range():
            data = self.get_index_dict(index)
            _message = self.get_message(message, data)
            context['message'] = _message
            _message = self.get_manager()\
                .message_manager.render_message(context)
            recipient = self.get_recipient_from_data(data)
            sent = self.get_manager().sender_manager.send_message(
                _message, subject=subject,
                recipient=recipient
            )
            yield sent
