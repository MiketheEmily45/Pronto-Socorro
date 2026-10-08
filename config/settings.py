"""
Configurações do projeto Fila de Pronto-Socorro.

Valores que mudam de uma máquina para outra (hosts, CORS, banco, chave secreta)
vêm de variáveis de ambiente. Veja o arquivo .env.example.
"""

import os
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(nome, padrao=False):
    return os.environ.get(nome, str(padrao)).strip().lower() in ("1", "true", "yes", "sim")


def env_lista(nome, padrao=""):
    return [item.strip() for item in os.environ.get(nome, padrao).split(",") if item.strip()]


# --- Segurança -------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "chave-insegura-apenas-para-desenvolvimento-troque-em-producao",
)
DEBUG = env_bool("DJANGO_DEBUG", True)

# Lista separada por vírgulas. Ex.: "localhost,127.0.0.1,192.168.0.10"
ALLOWED_HOSTS = env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

# --- Aplicações ------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # terceiros
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    # projeto
    "fila",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Banco de dados --------------------------------------------------------
# SQLite é o padrão. PostgreSQL configurável por variável de ambiente (DB_ENGINE=postgresql).

DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite3").lower()

if DB_ENGINE in ("postgres", "postgresql", "django.db.backends.postgresql"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "fila_ps"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Hasher rápido para suíte de testes (evita lentidão de PBKDF2 em dezenas de testes)
TESTING = "test" in sys.argv
if TESTING:
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]

# --- Internacionalização ---------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework -------------------------------------------------
# Por padrão tudo exige um administrador autenticado (is_staff).
# Só o endpoint do painel libera leitura pública, explicitamente.

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAdminUser",
    ],
}

# --- CORS ------------------------------------------------------------------
# Necessário se o painel (outra máquina) for uma página que chama a API pelo
# navegador. Ex.: CORS_ALLOWED_ORIGINS="http://192.168.0.20:8080"

CORS_ALLOWED_ORIGINS = env_lista("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CSRF_TRUSTED_ORIGINS = env_lista("CSRF_TRUSTED_ORIGINS")
