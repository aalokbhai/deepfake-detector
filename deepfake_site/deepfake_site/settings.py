"""
Django settings for deepfake_site project.
Production-ready version: secrets/config read from environment variables
so the same codebase works locally AND on a cloud host (Render, etc.)
without ever committing secrets to git.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(key, default=False):
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# SECURITY: secret key comes from the environment in production.
# The fallback below only fires for local `runserver` use and is not secret-safe.
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-local-dev-only-change-me-u#*8^9$n&o*7=25&uuowu0#^ezj",
)

# SECURITY: DEBUG must be False in production. On Render we set DEBUG=False
# via an environment variable; locally it defaults to True for convenience.
DEBUG = env_bool("DEBUG", default=True)

# Comma-separated list of hosts, e.g. "your-app.onrender.com,127.0.0.1"
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]

# Render (and most PaaS) put the app behind a reverse proxy that terminates TLS
# and forwards the original protocol in this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Trusted origins for CSRF (needed because the app sits behind HTTPS on a
# platform-provided subdomain). Set this env var to e.g.
# "https://your-app.onrender.com" once you know your deployed URL.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'detector',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'deepfake_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'deepfake_site.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---- Static files (served efficiently via WhiteNoise, no extra service needed) ----
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---- Media (uploaded photos + generated heatmaps) ----
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---- Upload limits (privacy + abuse protection on a free-tier server) ----
# Reject anything larger than 5 MB before it even touches disk/memory.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # used again in forms.py for a friendly error message

# ---- Hardened security headers, applied only when DEBUG is False ----
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 week to start; raise once confirmed working
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
