"""
Django settings for Smart EV Charging Slot Booking & Queue Scheduler.
"""

from pathlib import Path
import os
import socket

# PyMySQL installation for MySQL support without C++ compiler
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-smart-ev-slot-booking-scheduler-2026-mca-project')

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',

    # Custom Core Apps
    'accounts.apps.AccountsConfig',
    'stations.apps.StationsConfig',
    'vehicles.apps.VehiclesConfig',
    'bookings.apps.BookingsConfig',
    'charging.apps.ChargingConfig',
    'queue_management.apps.QueueManagementConfig',
    'notifications.apps.NotificationsConfig',
    'dashboard.apps.DashboardConfig',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notification_badge',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration
# Primary: MySQL (ev_charging_db)
# Auto-detects if MySQL port is reachable, falls back to SQLite for local development convenience if MySQL service is not running.
DB_NAME = os.getenv('DB_NAME', 'ev_charging_db')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
FORCE_SQLITE = os.getenv('FORCE_SQLITE', '0') == '1'

def is_mysql_available(host, port):
    if FORCE_SQLITE:
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((host, int(port)))
        s.close()
        return True
    except Exception:
        return False

if is_mysql_available(DB_HOST, DB_PORT):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            }
        }
    }
    print("[Smart EV] Connected to MySQL database:", DB_NAME)
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("[Smart EV] MySQL is not reachable on localhost:3306. Utilizing SQLite database for local fallback.")

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6}
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (QR codes, Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'role_redirect'
LOGOUT_REDIRECT_URL = 'landing'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
