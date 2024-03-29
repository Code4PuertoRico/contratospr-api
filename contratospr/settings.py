"""
Django settings for contratospr project.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
import logging.config
import os

import structlog
from configurations import Configuration, values

LOGGING_CONFIG = None
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "loggers": {
            "": {"level": "WARNING", "handlers": ["console"], "formatter": "default"},
            "contratospr": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "requests": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "celery": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
    }
)


class Common(Configuration):
    # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = values.SecretValue()

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = values.BooleanValue(False)

    ALLOWED_HOSTS = values.ListValue([])

    # Application definition
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.humanize",
        "whitenoise.runserver_nostatic",
        "django.contrib.staticfiles",
        "django_extensions",
        "debug_toolbar",
        "django_s3_storage",
        "django_filters",
        "crispy_forms",
        "rest_framework",
        "corsheaders",
        "contratospr.users",
        "contratospr.contracts",
        "contratospr.api",
        "contratospr.utils",
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]

    ROOT_URLCONF = "contratospr.urls"
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ]
            },
        }
    ]

    WSGI_APPLICATION = "contratospr.wsgi.application"

    # Database
    # https://docs.djangoproject.com/en/2.1/ref/settings/#databases
    DATABASES = values.DatabaseURLValue(
        "sqlite:///{}".format(os.path.join(BASE_DIR, "db.sqlite3"))
    )

    # Password validation
    # https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        },
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/2.1/topics/i18n/
    LANGUAGE_CODE = "en-us"

    TIME_ZONE = "UTC"

    USE_I18N = True

    USE_L10N = True

    USE_TZ = True

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.1/howto/static-files/
    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    STATICFILES_DIRS = []
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

    AUTH_USER_MODEL = "users.User"

    REDIS_URL = values.Value(environ_prefix=None)
    AUX_REDIS_URL = values.Value(environ_prefix=None)

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": "contratospr.utils.debug_toolbar.show_toolbar"
    }

    CONTRACTS_DOCUMENT_STORAGE = "django.core.files.storage.FileSystemStorage"

    REST_FRAMEWORK = {
        "DEFAULT_PAGINATION_CLASS": "contratospr.api.pagination.PageNumberPagination",
        "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.AnonRateThrottle",),
        "DEFAULT_THROTTLE_RATES": {"anon": "5000/hour"},
        "COERCE_DECIMAL_TO_STRING": False,
    }

    API_CACHE_TIMEOUT = values.IntegerValue(60 * 60 * 24, environ_prefix=None)

    @property
    def CELERY_BROKER_URL(self):
        return f"{self.REDIS_URL}/0"

    CELERY_BROKER_TRANSPORT_OPTIONS = {
        "fanout_prefix": True,
        "fanout_patterns": True,
        "visibility_timeout": 3600,
        "max_connections": 15,
    }

    CELERY_BROKER_POOL_LIMIT = None
    CELERY_TASK_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_ACKS_LATE = True
    CELERY_TASK_IGNORE_RESULT = True
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1

    CORS_ORIGIN_ALLOW_ALL = True


class Development(Common):
    """
    The in-development settings and the default configuration.
    """

    DEBUG = True

    ALLOWED_HOSTS = ["*"]

    INTERNAL_IPS = ["127.0.0.1"]

    AWS_S3_BUCKET_NAME = "pdfs.contratospr.com"

    CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}


class Production(Common):
    """
    The in-production settings.
    """

    # Security
    SESSION_COOKIE_SECURE = values.BooleanValue(True)
    SECURE_BROWSER_XSS_FILTER = values.BooleanValue(True)
    SECURE_CONTENT_TYPE_NOSNIFF = values.BooleanValue(True)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = values.BooleanValue(True)
    SECURE_HSTS_SECONDS = values.IntegerValue(31_536_000)
    SECURE_REDIRECT_EXEMPT = values.ListValue([])
    SECURE_SSL_HOST = values.Value(None)
    SECURE_SSL_REDIRECT = values.BooleanValue(True)
    SECURE_PROXY_SSL_HEADER = values.TupleValue(("HTTP_X_FORWARDED_PROTO", "https"))

    AWS_REGION = values.Value("us-east-1", environ_prefix=None)
    AWS_ACCESS_KEY_ID = values.SecretValue(environ_prefix=None)
    AWS_SECRET_ACCESS_KEY = values.SecretValue(environ_prefix=None)
    AWS_S3_BUCKET_NAME = values.Value(environ_prefix=None)

    CONTRACTS_DOCUMENT_STORAGE = "django_s3_storage.storage.S3Storage"

    @property
    def CACHES(self):
        caches = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": f"{self.REDIS_URL}/1",
                "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            }
        }

        if self.AUX_REDIS_URL:
            caches["aux"] = {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": f"{self.AUX_REDIS_URL}/1",
                "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            }

        return caches


class Testing(Common):
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

    CELERY_TASK_IGNORE_RESULT = True
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

    SECRET_KEY = "dont-tell-eve"
    AWS_ACCESS_KEY_ID = ""
    AWS_S3_BUCKET_NAME = "pdfs.contratospr.com"
    AWS_SECRET_ACCESS_KEY = ""


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.KeyValueRenderer(),
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
