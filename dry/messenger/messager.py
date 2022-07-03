"""
Module for email messenger
"""

import pathlib
from typing import Optional, Type

import pandas as pd
from pandas.core.frame import DataFrame

from .email_manager import BaseEmailManager
from .messsage_manager import BaseMessageManager


class Managers:
    def __init__(self) -> None:
        self.__email: Type[BaseEmailManager] = None
        self.__message: Type[BaseMessageManager] = None
        # TODO: self.__report: Type[BaseMessageManager] = None

    def set_email_manager(self, manager: Type[BaseEmailManager]) -> None:
        self.__email = manager

    @property
    def email_manager(self) -> Type[BaseEmailManager]:
        return self.__email

    def set_message_manager(self, manager: Type[BaseMessageManager]) -> None:
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

    def run_checks(self) -> None:
        raise NotImplementedError

    def set_manager(self) -> None:
        self.__manager = Managers()

    def set_email_manager(self, manager: Type[BaseEmailManager]) -> None:
        self.__manager.set_email_manager(manager)

    def set_message_manager(self, manager: Type[BaseMessageManager]) -> None:
        self.__manager.set_message_manager(manager)

    def get_message(self, message: str, data: dict = None) -> str:
        if data is None:
            data = {}
        for key, value in data.items():
            message = message.replace(key, value)
        return message

    def start_process(self) -> None:
        self.__manager.run_checks()
        return self.__send_messages()

    def __send_messages(self) -> None:
        raise NotImplementedError('No private send_messages \
method implemented')


class ExcelMessenger(BaseMessenger):
    """
    CSV and Excel manager for loading and sending messages to
    receiver data placed in csv or excel files.
    Files supported: xls, xlsx, csv, csv.gz
    """
    def __init__(self, file_path: str, **kwargs) -> None:
        self.__file_path = pathlib.Path(file_path)
        self.__supported_read_map = {
            'xls': pd.read_excel, 'xlsx': pd.read_excel,
            'csv': pd.read_csv, 'gz': pd.read_csv
        }
        self.__read_map = None
        self.__dataframe: Optional[DataFrame] = None
        super().__init__(**kwargs)

    def get_supported_exts(self) -> str:
        return ', '.join(self.__supported_read_map.keys())

    def set_ext_read_map(self, ext: str) -> bool:
        read_map = self.__supported_read_map.get(ext)
        if read_map is not None:
            self.__read_map = read_map
            return True
        raise TypeError(f"File is not in correct format, \
must be {self.get_supported_exts()}. Current format {ext}")

    def validate_ext(self) -> Optional[bool]:
        splits = self.__file_path.name('.')
        if splits:
            ext = splits[-1]
            return self.set_ext_read_map(ext)
        raise TypeError('File does not have an extension')

    def run_checks(self) -> None:
        if not self.__file_path.is_absolute():
            raise TypeError('File path is not absolute')
        if not self.__file_path.exists():
            raise TypeError('File does not exist')
        if not self.__file_path.is_file():
            raise TypeError('Path provided is not a file')
        self.validate_ext()

    def get_str_path(self) -> str:
        return str(self.__file_path)

    def load_data(self):
        self.__dataframe: Type[DataFrame] = self.__read_map(
            self.get_str_path())

    def get_data(self) -> Type[DataFrame]:
        return self.__dataframe

    def __send_messages(self) -> None:
        pass
