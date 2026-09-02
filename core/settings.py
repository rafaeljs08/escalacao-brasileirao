"""Configurações do projeto Escalação Brasileirão."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Em produção, defina DJANGO_SECRET_KEY e DJANGO_DEBUG=0 no ambiente.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-troque-esta-chave-em-producao-0f2b7c9d4e1a',
)

DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

_hosts = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
if DEBUG and '*' not in _hosts:
    _hosts.append('*')
ALLOWED_HOSTS = _hosts


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'futebol',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


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


LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Chave em https://dash.api-futebol.com.br — o app funciona sem ela (catálogo local).
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    for _linha in _env_file.read_text(encoding='utf-8').splitlines():
        _linha = _linha.strip()
        if not _linha or _linha.startswith('#') or '=' not in _linha:
            continue
        _chave, _, _valor = _linha.partition('=')
        os.environ.setdefault(_chave.strip(), _valor.strip().strip('"').strip("'"))

API_FUTEBOL_KEY = os.environ.get('API_FUTEBOL_KEY', '').strip()
API_FUTEBOL_CAMPEONATO_ID = int(os.environ.get('API_FUTEBOL_CAMPEONATO_ID', '10'))

# Brasileirão Asset Manager — URLs/tokens só por ambiente.
CARTOLA_BASE_URL = os.environ.get('CARTOLA_BASE_URL', 'https://api.cartola.globo.com').rstrip('/')
CARTOLA_PHOTO_FORMAT = os.environ.get('CARTOLA_PHOTO_FORMAT', '220x220.png')
API_FOOTBALL_BASE_URL = os.environ.get('API_FOOTBALL_BASE_URL', 'https://v3.football.api-sports.io').rstrip('/')
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '').strip()
SPORTMONKS_BASE_URL = os.environ.get('SPORTMONKS_BASE_URL', 'https://api.sportmonks.com/v3/football').rstrip('/')
SPORTMONKS_TOKEN = os.environ.get('SPORTMONKS_TOKEN', '').strip()
ASSETS_DIR = Path(os.environ.get('ASSETS_DIR', BASE_DIR / 'assets'))
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE_DIR / 'data'))
ASSET_LOGS_DIR = Path(os.environ.get('ASSET_LOGS_DIR', BASE_DIR / 'logs'))
REQUEST_TIMEOUT = float(os.environ.get('REQUEST_TIMEOUT', '15'))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', '0.5'))
ASSET_SEASON = int(os.environ.get('ASSET_SEASON', '2026'))
ASSET_PROVIDERS = os.environ.get('ASSET_PROVIDERS', 'cartola,api_football,sportmonks,fallback')
ASSET_ALLOWED_HOSTS = os.environ.get('ASSET_ALLOWED_HOSTS', '')
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
