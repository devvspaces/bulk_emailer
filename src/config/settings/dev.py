# flake8: noqa

from .base import *

ALLOWED_HOSTS = ["*"]

SEND_GRID = config('SEND_GRID')
EMAIL_DOMAIN = config('EMAIL_DOMAIN')
BLOCK_EMAIL = config('BLOCK_EMAIL', default=True, cast=bool)
DEBUG_EMAIL = config('DEBUG_EMAIL', default=True, cast=bool)
