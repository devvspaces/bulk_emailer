from pathlib import Path
from typing import TypeVar
from unittest import TestCase
import pytest
from messenger.messsage_manager import BaseMessageManager, HtmlMessageManager
from django.template.exceptions import TemplateDoesNotExist


T = TypeVar('T', bound=Path)
M = TypeVar('M', bound=HtmlMessageManager)
U = TypeVar('U', bound=TestCase)


def test_base_message_manager():
    manager = BaseMessageManager()
    with pytest.raises(NotImplementedError):
        manager.render_message()


def test_html_manager_creation(use_dummy_template_backend):
    HtmlMessageManager(
        template_name='test.html'
    )


def test_html_manager_template_error():
    with pytest.raises(TemplateDoesNotExist):
        HtmlMessageManager(
            template_name='notexist'
        )


def test_html_manager_get_context(create_manager: M, testcase: U):
    computed = create_manager.get_context()
    expected = {
        'name': 'testing'
    }
    testcase.assertDictEqual(computed, expected)


def test_html_manager_render_message(create_manager: M):
    computed: str = create_manager.render_message()
    assert computed == 'hello world  testing'


def test_html_manager_render_message_with_context(create_manager: M):
    context = {
        'message': 'python'
    }
    computed: str = create_manager.render_message(context)
    assert computed == 'hello world python testing'
