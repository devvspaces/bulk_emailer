"""
Module for email messenger
"""

from pathlib import Path
from typing import Optional, Sequence, Type

import pandas as pd
from pandas import DataFrame

from .email_manager import BaseEmailManager
from .messsage_manager import BaseMessageManager


class Managers:
    def __init__(self) -> None:
        self.__email: Type[BaseEmailManager] = None
        self.__message: Type[BaseMessageManager] = None
        # TODO: self.__report: Type[BaseMessageManager] = None

    def set_email_manager(self, manager: Type[BaseEmailManager]) -> None:
        if not isinstance(manager, BaseEmailManager):
            raise TypeError('Manager must be an instance of an Email Manager')
        self.__email = manager

    @property
    def email_manager(self) -> Type[BaseEmailManager]:
        return self.__email

    def set_message_manager(self, manager: Type[BaseMessageManager]) -> None:
        if not isinstance(manager, BaseMessageManager):
            raise TypeError('Manager must be an instance \
of an Message Manager')
        self.__message = manager

    @property
    def message_manager(self) -> Type[BaseMessageManager]:
        return self.__message

    def run_checks(self):
        if self.email_manager is None:
            raise NotImplementedError("""No Email manager provided,
            specify one by calling set_email_manager method on your
            Messenger object""")

        if self.message_manager is None:
            raise NotImplementedError("""No Message manager provided,
            specify one by calling set_message_manager method on your
            Messenger object""")


class BaseMessenger:
    def __init__(self, start: int = 0, stop: int = 0) -> None:
        self.__start = start
        self.__stop = stop
        self.__manager: Type[Managers] = None
        self.set_manager()
        self.run_checks()

    def get_start(self) -> int:
        return self.__start

    def get_stop(self) -> int:
        return self.__stop

    def run_checks(self) -> None:
        if not isinstance(self.get_start(), int):
            raise TypeError('Start value must be an integer')

        if not isinstance(self.get_stop(), int):
            raise TypeError('Stop value must be an integer')

        if self.get_start() > self.get_stop():
            raise TypeError('Start cannot be greater that stop')

    def set_manager(self) -> None:
        self.__manager = Managers()

    def get_manager(self) -> Type[Managers]:
        return self.__manager

    def set_email_manager(self, manager: Type[BaseEmailManager]) -> None:
        self.get_manager().set_email_manager(manager)

    def set_message_manager(self, manager: Type[BaseMessageManager]) -> None:
        self.get_manager().set_message_manager(manager)

    def get_message(self, message: str, data: dict = None) -> str:
        if data is None:
            data = {}
        for key, value in data.items():
            replace_key = f'_{key}_'
            message = message.replace(replace_key, value)
        return message

    def start_process(self, subject: str, message: str, **kwargs) -> None:
        self.__manager.run_checks()
        return self.send_messages(subject, message, **kwargs)

    def send_messages(self, subject: str, message: str, **kwargs) -> None:
        raise NotImplementedError('No send_messages \
method implemented')


class ExcelMessenger(BaseMessenger):
    """
    CSV and Excel manager for loading and sending messages to
    receiver data placed in csv or excel files.
    Files supported: xls, xlsx, csv, csv.gz
    """
    def __init__(self, file_path: str, **kwargs) -> None:
        self.__file_path = Path(file_path)
        self.__supported_read_map = {
            'xls': pd.read_excel, 'xlsx': pd.read_excel,
            'csv': pd.read_csv, 'gz': pd.read_csv
        }
        self.__read_map = None
        self.__dataframe: Optional[DataFrame] = None
        super().__init__(**kwargs)
        self.load_data()

    def get_supported_exts(self) -> str:
        keys = list(self.__supported_read_map.keys())
        part1 = ', '.join(keys[:-1])
        all_part = f"{part1} and {keys[-1]}"
        return all_part

    def set_ext_read_map(self, ext: str) -> None:
        read_map = self.__supported_read_map.get(ext)
        if read_map is None:
            raise TypeError(f"File is not in correct format, \
must be {self.get_supported_exts()}. Current format {ext}")
        self.__read_map = read_map

    def validate_ext(self) -> None:
        ext = self.get_file_path().suffix[1:].lower()
        if not ext:
            raise TypeError('File does not have an extension')
        self.set_ext_read_map(ext)

    def run_checks(self) -> None:
        super().run_checks()
        if not self.get_file_path().is_absolute():
            raise TypeError('File path is not absolute')
        if not self.get_file_path().exists():
            raise TypeError('File does not exist')
        if not self.get_file_path().is_file():
            raise TypeError('Path provided is not a file')
        self.validate_ext()

    def get_file_path(self) -> Type[Path]:
        return self.__file_path

    def load_data(self):
        self.__dataframe: Type[DataFrame] = self.__read_map(
            self.get_file_path())

    @property
    def data(self) -> Type[DataFrame]:
        return self.__dataframe

    def get_range(self) -> Sequence[int]:
        return range(self.get_start(), self.get_stop() + 1)

    def get_index_dict(self, index: int) -> dict:
        return self.data.loc[index].to_dict()

    def get_email_from_data(self, data: dict) -> str:
        email = data.get('email')
        if email is None:
            raise TypeError('Email column not in file')
        return email

    def send_messages(
        self, subject: str, message: str,
        context: dict = None
    ) -> None:
        if context is None:
            context = {}

        for index in self.get_range():
            data = self.get_index_dict(index)
            _message = self.get_message(message, data)
            context['message'] = _message
            _message = self.get_manager()\
                .message_manager.render_message(context)
            email = self.get_email_from_data(data)
            self.get_manager().email_manager.send_email(
                email=email, subject=subject,
                message=message
            )
