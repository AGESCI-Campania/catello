from catello.settings.base import *

ALLOWED_HOSTS = ["*"]

LOGLEVELDEBUG=True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'catello_bot',
        'USER': 'bruand',
        'PASSWORD': None,
        'HOST': 'localhost',
        'PORT': 5432,
    }
}