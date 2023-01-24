from typing import Any, Dict, Type
from django.http.request import HttpRequest
from django.template.loader import get_template


class BaseMessageManager:
    def __init__(self) -> None:
        pass

    def render_message(self):
        raise NotImplementedError


class HtmlMessageManager(BaseMessageManager):
    def __init__(
        self, template_name: str,
        request: Type[HttpRequest] = None,
        context: dict = None
    ) -> None:
        self.__template = get_template(template_name)
        self.__request = request
        if context is None:
            context = {}
        self.__extra_context = context

    def get_context(self) -> Dict[str, Any]:
        return self.__extra_context

    def render_message(self, context: dict = None) -> str:
        if context is None:
            context = {}

        extra_context = self.get_context()
        extra_context.update(context)
        message = self.__template.render(extra_context, self.__request)
        return message
