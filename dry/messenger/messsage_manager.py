from typing import Any, Dict, Type
from django.http.request import HttpRequest
from django.template.loader import render_to_string


class BaseMessageManager:
    def __init__(self) -> None:
        pass

    def render_message(self):
        raise NotImplementedError


class HtmlMessageManager(BaseMessageManager):
    def __init__(self, template: str, request: Type[HttpRequest]) -> None:
        self.__template = template
        self.__request = request
        self.__extra_context = self.get_extra_context()

    def get_extra_context(self) -> Dict[str, Any]:
        extra_context = {
            "request": self.__request
        }
        return extra_context

    def render_message(self, context: dict) -> str:
        if not self.__template:
            raise TypeError('Must provide a template name')

        context.update(self.__extra_context)
        message = render_to_string(self.__template, context)
        return message
