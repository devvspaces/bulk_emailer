from .base import *

LOGGING['handlers']['basic_h']['filename'] = BASE_DIR / 'logs/test_debug.log'
LOGGING['handlers']['basic_e']['filename'] = BASE_DIR / 'logs/test_error.log'

SEND_GRID = 'test_api_key'
EMAIL_DOMAIN = 'example.com'
BLOCK_EMAIL = True
DEBUG_EMAIL = True
