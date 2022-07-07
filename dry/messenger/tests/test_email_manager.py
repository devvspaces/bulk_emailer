from contextlib import redirect_stdout
from io import StringIO

import pytest

from django.test import SimpleTestCase
from messenger.email_manager import BaseEmailManager, SendGridEmailManager


class TestManager(SimpleTestCase):
    """
    Test BaseEmailManager
    """

    def setUp(self) -> None:
        manager = BaseEmailManager(
            domain='example.com',
            sender='test',
        )
        self.manager = manager

    def test_get_debug(self):
        self.assertFalse(self.manager.get_debug())

    def test_get_block_send(self):
        self.assertFalse(self.manager.get_block_send())

    def test_set_debug(self):
        self.manager.set_debug()
        self.assertTrue(self.manager.get_debug())

    def test_unset_debug(self):
        self.manager.unset_debug()
        self.assertFalse(self.manager.get_debug())

    def test_unblock_send(self):
        self.manager.unblock_send()
        self.assertFalse(self.manager.get_block_send())

    def test_block_send(self):
        self.manager.block_send()
        self.assertTrue(self.manager.get_block_send())

    def test_get_sender_email(self):
        computed = self.manager.get_sender_email()
        self.assertEqual(computed, 'test@example.com')

    def test_get_reply_email_returns_sender(self):
        computed = self.manager.get_reply_email()
        self.assertEqual(computed, 'test@example.com')

    def test_get_reply_email(self):
        manager = BaseEmailManager(
            domain='example.com',
            sender='test',
            reply_email='noreplytest@gmail.com'
        )
        computed = manager.get_reply_email()
        self.assertEqual(computed, 'noreplytest@gmail.com')

    def test_print_message_without_debug(self):
        with redirect_stdout(StringIO()) as f:
            computed = self.manager.print_message('hello world')
        computed2 = f.getvalue()
        self.assertEqual(computed2, '')
        self.assertIsNone(computed)

    def test_print_message_with_debug(self):
        self.manager.set_debug()
        with redirect_stdout(StringIO()) as f:
            computed = self.manager.print_message('hello world')
        computed2 = f.getvalue()
        self.assertEqual(computed2, 'hello world\n')
        self.assertTrue(computed)

    def test_send_email_with_debug(self):
        self.manager.set_debug()
        with redirect_stdout(StringIO()) as f:
            computed = self.manager.send_email('hello world')
        computed2 = f.getvalue()
        self.assertEqual(computed2, 'hello world\n')
        self.assertFalse(computed)

    def test_send_email_without_debug(self):
        with redirect_stdout(StringIO()) as f:
            computed = self.manager.send_email('hello world')
        computed2 = f.getvalue()
        self.assertEqual(computed2, '')
        self.assertFalse(computed)

    def test_send_email_with_block_send(self):
        self.manager.block_send()
        with redirect_stdout(StringIO()) as f:
            computed = self.manager.send_email('hello world')
        computed2 = f.getvalue()
        self.assertEqual(computed2, '')
        self.assertTrue(computed)

    def test_send_mail(self):
        with self.assertRaises(NotImplementedError):
            self.manager.send_mail()


class TestSendGridManager(SimpleTestCase):
    """
    Test SendGridEmailManager
    """

    def setUp(self) -> None:
        manager = SendGridEmailManager(
            domain='example.com',
            sender='test',
            api_key='test_key',
            reply_email='noreply@test.io'
        )
        self.manager = manager

    def test_get_api_key(self):
        api_key = self.manager.get_api_key()
        self.assertEqual(api_key, 'test_key')

    def test_set_headers(self):
        computed = self.manager.set_headers()
        expected = {
            'Authorization': 'Bearer test_key'
        }
        self.assertEqual(computed, expected)

    def test_get_headers(self):
        computed = self.manager.get_headers()
        expected = {
            'Authorization': 'Bearer test_key'
        }
        self.assertEqual(computed, expected)

    def test_get_post_data(self):
        computed = self.manager.get_post_data(
            email='me@gmail.com',
            subject='testings',
            message='hello world',
        )
        expected = {
            "personalizations": [{"to": [{"email": 'me@gmail.com'}]}],
            "from": {"email": 'test@example.com'},
            "reply_to": {"email": 'noreply@test.io'},
            "subject": 'testings',
            "content": [{"type": "text/html", "value": 'hello world'}]
        }
        self.assertEqual(computed, expected)

    def test_get_post_url(self):
        computed = self.manager.get_post_url()
        self.assertEqual(computed, 'https://api.sendgrid.com/v3/mail/send')

    @pytest.mark.xfail
    def test_send_email(self):
        computed = self.manager.send_email(
            email='me@gmail.com',
            subject='testings',
            message='hello world',
        )
        self.assertFalse(computed)

    def test_send_email_fail_silently(self):
        computed = self.manager.send_email(
            subject='testings',
            message='hello world',
        )
        self.assertFalse(computed)

    def test_send_email_not_fail_silently(self):
        with self.assertRaises(Exception):
            self.manager.send_email(
                subject='testings',
                message='hello world',
                fail=False
            )
