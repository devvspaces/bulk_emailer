# flake8: noqa

from .base import *

ALLOWED_HOSTS = ["*"]

SEND_GRID = config('SEND_GRID', default='test')
ZEPTOTOKEN = config('ZEPTOTOKEN', default='test')
EMAIL_DOMAIN = config('EMAIL_DOMAIN', default='test')
BLOCK_EMAIL = config('BLOCK_EMAIL', default=True, cast=bool)
DEBUG_EMAIL = config('DEBUG_EMAIL', default=True, cast=bool)


EMAIL_USER = config('EMAIL_USER', default='test')
EMAIL_PASSWORD = config('EMAIL_PASSWORD', default='test')
EMAIL_HOST = config('EMAIL_HOST', default='test')
EMAIL_PORT = config('EMAIL_PORT', default='test', cast=int)
