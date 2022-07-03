from django.test import SimpleTestCase

from messenger.messager import Managers
from messenger.email_manager import BaseEmailManager
from messenger.messsage_manager import BaseMessageManager


class TestManagers(SimpleTestCase):
    def setUp(self) -> None:
        self.managers = Managers()

    def test_set_email_manager(self):
        email = BaseEmailManager(
            domain='example.com',
            sender='test',
        )
        self.managers.set_email_manager(email)
        self.assertIs(email, self.managers.email_manager)

    def test_email_manager(self):
        pass

    def test_set_message_manager(self):
        pass

    def test_message_manager(self):
        pass

    def test_run_checks(self):
        pass
