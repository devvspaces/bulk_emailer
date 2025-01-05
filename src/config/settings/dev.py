# flake8: noqa

from .base import *

ALLOWED_HOSTS = ["*"]

BLOCK_EMAIL = config('BLOCK_EMAIL', default=False, cast=bool)
DEBUG_EMAIL = config('DEBUG_EMAIL', default=False, cast=bool)
