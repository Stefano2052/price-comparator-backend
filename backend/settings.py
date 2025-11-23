"""
Django settings for backend project.
Production-ready, environment-driven.
"""

from pathlib import Path
import os
import dj_database_url
from datetime import timedelta
import json

BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------------------------------------------
# ✅ Sicurezza e variabili d'ambiente
# -------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "unsafe-default-key-change-this-in-env"
)

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    ".onrender.com,localhost,127.0.0.1"
).split(",")


# -------------------------------------------------------------------
# ✅ Applicazioni
# -------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'django_filters',
    'rest_framework',
    'djoser',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Local apps
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',            # CORS prima di CommonMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',       # Statici per Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True


ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# -------------------------------------------------------------------
# ✅ Database configurato da ENV (fallback su SQLite)
# -------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + str(BASE_DIR / "db.sqlite3")
)

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=os.getenv("DATABASE_SSL_REQUIRE", "false").lower() == "true"
    )
}


# -------------------------------------------------------------------
# ✅ Password & Auth
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
}


# -------------------------------------------------------------------
# ✅ Statici per Render
# -------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# -------------------------------------------------------------------
# ✅ Timezone e lingua
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True


# -------------------------------------------------------------------
# ✅ Firebase da variabile d’ambiente (niente file!)
# -------------------------------------------------------------------
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if FIREBASE_CREDENTIALS_JSON:
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS_JSON))
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Admin inizializzato correttamente")
    except Exception as e:
        print(f"⚠️ Firebase init failed: {e}")
else:
    print("⚠️ FIREBASE_SERVICE_ACCOUNT_JSON non impostato, Firebase non inizializzato")


# -------------------------------------------------------------------
# ✅ Default PK
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
