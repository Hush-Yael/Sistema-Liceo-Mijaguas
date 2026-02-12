import os
from pathlib import Path
import sys
from dotenv import dotenv_values
from django.contrib.messages import constants as messages
from .config_unfold import CONFIG as CONFIG_UNFOLD


BASE_DIR = Path(__file__).resolve().parent.parent

secretos = dotenv_values(".env")
SECRET_KEY = secretos["SECRET_KEY"]

DEV = True
DEBUG = DEV

ALLOWED_HOSTS = ["*"]


INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_group_model",
    "widget_tweaks",
    "sekizai",
    "template_partials",
    "usuarios",
    "estudios",
    "django_cleanup.apps.CleanupConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.middleware.StaticUnCachingMiddleware",
]

if DEBUG:
    INSTALLED_APPS.append("django_browser_reload")
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
                "app.context_processors.contexto",
            ],
            "libraries": {
                "utilidades": "templatetags.utilidades",
                "grupos_variantes": "templatetags.grupos_variantes.tags",
            },
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"

if DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "null": {
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "django.server": {
                "handlers": ["null"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = (
    []
    if DEV
    else [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]
)

LANGUAGE_CODE = "es-VE"
ADMIN_LANGUAGE_CODE = "es"

TIME_ZONE = "America/Caracas"

USE_I18N = True
USE_L10N = False
USE_THOUSAND_SEPARATOR = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGOUT_URL = "logout"

AUTH_USER_MODEL = "usuarios.Usuario"
AUTH_GROUP_MODEL = "usuarios.Grupo"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

UNFOLD = CONFIG_UNFOLD

MESSAGE_TAGS = {
    messages.DEBUG: "ui-msg/debug",
    messages.INFO: "ui-msg/info",
    messages.SUCCESS: "ui-msg/exito",
    messages.WARNING: "ui-msg/advertencia",
    messages.ERROR: "ui-msg/peligro",
}

MIGRANDO = "makemigrations" in sys.argv or "migrate" in sys.argv


EMAIL_BACKEND = (
    "django.core.mail.backends.filebased.EmailBackend"
    if DEV
    else "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_FILE_PATH = BASE_DIR / "correos"
