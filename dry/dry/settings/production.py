from .base import *  # noqa

ALLOWED_HOSTS = []

STATIC_ROOT = BASE_DIR / "static"  # noqa

SEND_GRID = config('SEND_GRID')  # noqa
EMAIL_DOMAIN = config('EMAIL_DOMAIN')  # noqa
BLOCK_EMAIL = config('BLOCK_EMAIL', default=False, cast=bool)  # noqa
DEBUG_EMAIL = config('DEBUG_EMAIL', default=False, cast=bool)  # noqa
