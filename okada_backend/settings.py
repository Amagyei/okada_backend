# settings.py

from decimal import Decimal
from pathlib import Path
from datetime import timedelta
import os
import json # For parsing Firebase credentials from environment variable (even if not used in local dev)
import dj_database_url # For parsing DATABASE_URL (useful if you set it locally)
from dotenv import load_dotenv # Crucial for loading .env file locally

# Load environment variables from .env file.
# This makes variables in your .env file available via os.getenv()
# This line is essential for your local macOS setup.
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# Core Django Settings
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-insecure-development-key-here-for-local-use-ONLY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS for local development.
# APP_DOMAIN and CUSTOM_DOMAINS are not relevant for local development.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# ==============================================================================
# Database Configuration (PostgreSQL with PostGIS for local)
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Explicitly set for PostGIS
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        # DigitalOcean Managed PostgreSQL usually requires SSL.
        # For local, if your PostgreSQL is not configured with SSL, remove this.
        # If your local PostgreSQL uses SSL, uncomment this.
        # 'OPTIONS': {'sslmode': 'require'},
    }
}

# ==============================================================================
# Installed Applications
# ==============================================================================

INSTALLED_APPS = [
    # Local apps 
    'users',
    'authentication',
    'rides',
    'payments',
    'notifications',

    # Django core and contrib apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # Required for PostGIS
    'django_celery_beat',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'channels',
    'channels_redis',  # For Redis channel layer
    'whitenoise.runserver_nostatic',  # For serving static files in development with `runserver`
    # 'storages', # Only needed if you plan to use DigitalOcean Spaces for media locally
]

# ==============================================================================
# Middleware Configuration
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================================================================
# URL Configuration
# ==============================================================================

ROOT_URLCONF = 'okada_backend.urls'

# ==============================================================================
# Templates Configuration
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.backends.django.DjangoTemplates', # This line is usually not a context processor
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==============================================================================
# ASGI & WSGI Applications
# ==============================================================================

ASGI_APPLICATION = 'okada_backend.asgi.application'
WSGI_APPLICATION = 'okada_backend.wsgi.application'

# ==============================================================================
# Geospatial Libraries (GDAL, GEOS, PROJ) for macOS Homebrew
# ==============================================================================
if DEBUG:
    # Attempt to dynamically find Homebrew paths or use common defaults
    try:
        GDAL_LIBRARY_PATH = os.popen("brew --prefix gdal").read().strip() + "/lib/libgdal.dylib"
    except Exception:
        GDAL_LIBRARY_PATH = "/opt/homebrew/opt/gdal/lib/libgdal.dylib" # Fallback for M1 Mac or common Intel

    try:
        GEOS_LIBRARY_PATH = os.popen("brew --prefix geos").read().strip() + "/lib/libgeos_c.dylib"
    except Exception:
        GEOS_LIBRARY_PATH = "/opt/homebrew/opt/geos/lib/libgeos_c.dylib" # Fallback for M1 Mac or common Intel

    try:
        PROJ_LIB = os.path.join(os.popen("brew --prefix proj").read().strip(), "share/proj")
    except Exception:
        PROJ_LIB = "/opt/homebrew/share/proj" # Fallback for M1 Mac or common Intel

    # Ensure these are actually set if the dynamic lookup fails, you can set them in .env
    GDAL_LIBRARY_PATH = os.environ.get("GDAL_LIBRARY_PATH", GDAL_LIBRARY_PATH)
    GEOS_LIBRARY_PATH = os.environ.get("GEOS_LIBRARY_PATH", GEOS_LIBRARY_PATH)
    PROJ_LIB = os.environ.get("PROJ_LIB", PROJ_LIB)

    print(f"DEBUG GEOS_LIBRARY_PATH: {GEOS_LIBRARY_PATH}")
    print(f"DEBUG GDAL_LIBRARY_PATH: {GDAL_LIBRARY_PATH}")
    print(f"DEBUG PROJ_LIB: {PROJ_LIB}")

# ==============================================================================
# Password Validation
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==============================================================================
# Internationalization
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# Static and Media Files Configuration (Local Dev)
# ==============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DO_SPACES_ENDPOINT_URL = os.environ.get('DO_SPACES_ENDPOINT_URL')
# DO_SPACES_KEY = os.environ.get('DO_SPACES_KEY')
# DO_SPACES_SECRET = os.environ.get('DO_SPACES_SECRET')
# DO_SPACES_NAME = os.environ.get('DO_SPACES_NAME')
# DO_SPACES_REGION = os.environ.get('DO_SPACES_REGION')
# DO_SPACES_CUSTOM_DOMAIN = os.environ.get('DO_SPACES_CUSTOM_DOMAIN')
#
# if DO_SPACES_KEY and DO_SPACES_SECRET and DO_SPACES_NAME and DO_SPACES_ENDPOINT_URL:
#     AWS_S3_ENDPOINT_URL = DO_SPACES_ENDPOINT_URL
#     AWS_ACCESS_KEY_ID = DO_SPACES_KEY
#     AWS_SECRET_ACCESS_KEY = DO_SPACES_SECRET
#     AWS_STORAGE_BUCKET_NAME = DO_SPACES_NAME
#     AWS_S3_FILE_OVERWRITE = False
#     AWS_DEFAULT_ACL = 'public-read'
#     AWS_S3_REGION_NAME = DO_SPACES_REGION
#     DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#     if DO_SPACES_CUSTOM_DOMAIN:
#         MEDIA_URL = f'https://{DO_SPACES_CUSTOM_DOMAIN}/{MEDIA_URL.strip("/")}/'
#     else:
#         MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_ENDPOINT_URL.split("//")[1]}/{MEDIA_URL.strip("/")}/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# Custom User Model
# ==============================================================================

AUTH_USER_MODEL = 'users.User'

# ==============================================================================
# REST Framework Settings
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'authentication.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

# ==============================================================================
# JWT Settings
# ==============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# ==============================================================================
# CORS Settings
# ==============================================================================

# CORS_ALLOW_ALL_ORIGINS = True is safe for local development with DEBUG=True
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        # In production, list your frontend origins specifically for security
        # "https://your-frontend-domain.com",
    ]
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# Email Settings
# ==============================================================================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend') # Default to console for local
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# ==============================================================================
# SMS Service Config
# ==============================================================================
ARKESEL_USERNAME = os.environ.get('ARKESEL_USERNAME')
ARKESEL_API_KEY = os.environ.get('ARKESEL_API_KEY')
SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'OkadaApp')

# ==============================================================================
# Flutterwave settings
# ==============================================================================
FLUTTERWAVE_SECRET_KEY = os.getenv('FLUTTERWAVE_SECRET_KEY')
FLUTTERWAVE_PUBLIC_KEY = os.getenv('FLUTTERWAVE_PUBLIC_KEY')
FLUTTERWAVE_BASE_URL = os.getenv('FLUTTERWAVE_BASE_URL', 'https://api.flutterwave.com/v3')

# ==============================================================================
# RIDE FARE PARAMETERS
# ==============================================================================
RIDE_BASE_FARE = Decimal('5.00')
RIDE_PRICE_PER_KM = Decimal('1.50')
RIDE_PRICE_PER_MINUTE = Decimal('0.20')
RIDE_MINIMUM_FARE = Decimal('10.00')

# ==============================================================================
# Logging Configuration
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ==============================================================================
# Firebase Admin SDK Settings
# ==============================================================================
import firebase_admin
from firebase_admin import credentials

if DEBUG:
    FIREBASE_ADMIN_SDK_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'okada_backend/okada-457703-firebase-adminsdk-fbsvc-9202cfff43.json')
    if os.path.exists(FIREBASE_ADMIN_SDK_CREDENTIALS_PATH):
        if not firebase_admin._apps: # Check if Firebase Admin SDK is already initialized
            try:
                cred = credentials.Certificate(FIREBASE_ADMIN_SDK_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully from local file (DEBUG mode).")
            except Exception as e:
                print(f"ERROR: Firebase initialization failed from local file: {e}")
        else:
            print("Firebase Admin SDK already initialized.")
    else:
        print(f"WARNING: Firebase Admin SDK credentials file not found at {FIREBASE_ADMIN_SDK_CREDENTIALS_PATH}. Push notifications may not work in DEBUG mode.")
else:
    FIREBASE_CREDENTIALS_JSON = os.environ.get('FIREBASE_CREDENTIALS_JSON')
    if FIREBASE_CREDENTIALS_JSON:
        try:
            cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully from environment variable (PRODUCTION).")
            else:
                print("Firebase Admin SDK already initialized (PRODUCTION).")
        except json.JSONDecodeError:
            print("ERROR: Invalid Firebase credentials JSON in FIREBASE_CREDENTIALS_JSON environment variable (PRODUCTION).")
        except Exception as e:
            print(f"ERROR: Firebase initialization failed from environment variable (PRODUCTION): {e}")
    else:
        print("WARNING: FIREBASE_CREDENTIALS_JSON environment variable not found. Push notifications will not work in production.")


# ==============================================================================
# Channel Layer Settings (for Django Channels with Redis)
# =============================================================================
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0') # Default to local Redis for dev

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}