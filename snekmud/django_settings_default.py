from django.conf.global_settings import *

# Change this to False in production.
DEBUG = True

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "server/snekmud.sqlite",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

# CHANGE THIS IN PRODUCTION!
SECRET_KEY = "snek"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.flatpages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "idmap",
    "snekmud.db.accounts",
    "snekmud.db.players"
]

AUTH_USER_MODEL = "accounts.Account"

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]