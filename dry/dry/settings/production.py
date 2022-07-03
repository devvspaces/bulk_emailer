from .base import *

ALLOWED_HOSTS = []

WSGI_APPLICATION = 'leapfund.wsgi.base.application'
ASGI_APPLICATION = 'leapfund.asgi.base.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config("DB_NAME"),
        'USER': config("DB_USER"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': 'localhost',
        'PORT': '',
    }
}


STATIC_ROOT = os.path.join(BASE_DIR, "static")

PRINT_LOG = False
OFF_EMAIL = False


LOAN_COMPANY = {
    '1': {
        'link': 'https://harvestfinancialloan.com/',
        'name': 'Harvest Financial Loan',
    },
    '2': {
        'link': 'https://fountainbusinessloan.com/',
        'name': 'Fountain Business Loan',
    }
}