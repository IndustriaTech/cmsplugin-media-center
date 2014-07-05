import sys

from .common import *


SECRET_KEY = 'secret cms3.0.x key'

DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS += (
    'djangocms_admin_style',
    'djangocms_text_ckeditor',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if len(sys.argv) > 1 and 'test' in sys.argv[1]:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'SUPPORTS_TRANSACTIONS': True,
        },
    }

    SOUTH_TESTS_MIGRATE = False
    SKIP_SOUTH_TESTS = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'example/media/')
