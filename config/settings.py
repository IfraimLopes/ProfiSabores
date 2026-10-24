import dj_database_url
import os
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for env_linha in ENV_FILE.read_text().splitlines():
        env_linha = env_linha.strip()
        if env_linha and not env_linha.startswith("#") and "=" in env_linha:
            env_nome, env_valor = env_linha.split("=", 1)
            os.environ.setdefault(
                env_nome.strip(),
                env_valor.strip().strip('"').strip("'")
            )



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-local-development-only-key")



# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", 'localhost,127.0.0.1,192.168.1.101,192.168.1.100,10.27.0.194,172.20.10.2,metres-aerial-translation-scanners.trycloudflare.com,cleveland-human-jewish-balance.trycloudflare.com').split(",") if h.strip()]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "menu",
    "reservas",
    "funcionarios",
    "notificacoes",
    "cozinha",
    "utilizadores",
    "secretaria",
    "restaurante",
    "cloudinary_storage",
    "cloudinary",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'utilizadores.middleware.IdiomaPerfilMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'


TEMPLATES = [

    {

        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

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


WSGI_APPLICATION = 'config.wsgi.application'


# Database

# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.parse(
            os.environ["DATABASE_URL"],
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation

# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [

    {

        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',

    },

    {

        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',

    },

    {

        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',

    },

    {

        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',

    },

]


# Internationalization

# Internationalization

LANGUAGE_CODE = "pt-pt"

LANGUAGES = [
    ("pt-pt", "Português"),
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "Europe/Lisbon"

USE_I18N = True

USE_TZ = True

# Static files

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [

    BASE_DIR / 'static',

]


# Media files

MEDIA_URL = 'media/'

MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if os.environ.get("CLOUDINARY_CLOUD_NAME")
            and os.environ.get("CLOUDINARY_API_KEY")
            and os.environ.get("CLOUDINARY_API_SECRET")
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ==========================================
# SESSÕES PERSISTENTES DO PROFISABORES
# ==========================================

# Duração da sessão: 30 dias.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30

# Manter a sessão após fechar o navegador.
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Guardar as sessões na base de dados.
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Renovar a validade da sessão em cada pedido.
SESSION_SAVE_EVERY_REQUEST = True



# Email

MAILERS = {

    'default': {

        'BACKEND':
        'django.core.mail.backends.console.EmailBackend',

    },

}


# Web Push — notificações do navegador

WEBPUSH_VAPID_PUBLIC_KEY = (
    "BFuv64OJEM840lwvFNSUI2yhIE6jOJxUhPxZmL77y4gixRlOsD37oyQj7C4ZP-CCSWCCogtB4If_jXPoGNPp_jE"
)


WEBPUSH_VAPID_PRIVATE_KEY_PATH = Path(
    os.environ.get(
        "WEBPUSH_VAPID_PRIVATE_KEY_PATH",
        str(BASE_DIR / "private" / "vapid_private.pem")
    )
)

WEBPUSH_VAPID_SUBJECT = "mailto:0325065@alunos.profitecla.pt"

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", 'https://metres-aerial-translation-scanners.trycloudflare.com,https://cleveland-human-jewish-balance.trycloudflare.com,https://profisabores-web.onrender.com').split(",") if o.strip()]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
