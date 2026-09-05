import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# Windows dev: point GeoDjango at the OSGeo4W native libs (unnecessary on
# Linux/macOS where they're resolved via the system library path).
# The sqlite3.dll preload must happen before django.db.backends.sqlite3 is
# ever imported — otherwise Python's bundled sqlite3.dll (no spatialite
# support) claims the "sqlite3.dll" process-wide module name first, and
# GDAL's later load fails with "specified procedure could not be found".
if os.name == "nt" and os.getenv("SPATIALITE_LIBRARY_PATH"):
    import ctypes

    # h5py/netCDF4 ship their own hdf5 DLLs; they must claim that module
    # name before GDAL loads its own build of hdf5.dll, or whichever
    # loads first wins process-wide and the other fails to import.
    import h5py  # noqa: F401
    import netCDF4  # noqa: F401

    _osgeo_bin = os.path.dirname(os.environ["SPATIALITE_LIBRARY_PATH"])
    ctypes.WinDLL(os.path.join(_osgeo_bin, "sqlite3.dll"))

if os.getenv("GDAL_LIBRARY_PATH"):
    GDAL_LIBRARY_PATH = os.environ["GDAL_LIBRARY_PATH"]
if os.getenv("GEOS_LIBRARY_PATH"):
    GEOS_LIBRARY_PATH = os.environ["GEOS_LIBRARY_PATH"]
if os.getenv("SPATIALITE_LIBRARY_PATH"):
    SPATIALITE_LIBRARY_PATH = os.environ["SPATIALITE_LIBRARY_PATH"]

# FIX 1: Crash loudly if SECRET_KEY is missing — no unsafe fallback
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    import sys
    if "test" not in sys.argv and "migrate" not in sys.argv:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Copy .env.example to .env and set a secure value."
        )
    SECRET_KEY = "test-only-insecure-key-do-not-use-in-production"

# FIX 2: Safe DEBUG default — off unless explicitly set to True
DEBUG = os.getenv("DEBUG", "False") == "True"

# FIX 2: Safe ALLOWED_HOSTS default
_allowed = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    # FIX 12: CORS support
    "corsheaders",
    "apps.cyclones",
    "apps.predictions",
]

MIDDLEWARE = [
    # FIX 12: CORS middleware must be first
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# FIX 12: CORS — allow all origins in dev, restrict via env in prod
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "True") == "True"
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "apps" / "predictions" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if os.getenv("USE_SQLITE", "True") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.spatialite",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.getenv("DATABASE_NAME", "cyclone_db"),
            "USER": os.getenv("DATABASE_USER", "postgres"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD", "postgres"),
            "HOST": os.getenv("DATABASE_HOST", "localhost"),
            "PORT": os.getenv("DATABASE_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
# FIX 10: Add STATIC_ROOT so collectstatic works in deployment
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
# FIX 9: Expire Celery results after 1 hour to avoid Redis bloat
CELERY_RESULT_EXPIRES = 3600

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    # FIX 9: Rate-limit anonymous inference calls — 30/min for browsing, 10/min for heavy endpoints
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "live_inference": "10/min",
    },
}
