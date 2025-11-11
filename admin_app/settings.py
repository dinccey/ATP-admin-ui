import os

# NOTE: This is an excerpt intended to be added to the standard Django-generated settings.py
# Use the default `django-admin startproject admin_app` to get the rest of the settings file.

INSTALLED_APPS = [
    # ... keep the defaults from Django's generated file
    'videos',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'alltdjli_pas'),
        'USER': os.environ.get('DB_USER', 'alltdjli'),
        'PASSWORD': os.environ.get('DB_PASS', 'Um+2W=$-N_b+'),
        'HOST': os.environ.get('DB_HOST', '192.168.100.149'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# If you need the custom template filter available on all templates, ensure
# 'django.template.context_processors.request' is in TEMPLATES context_processors in the generated settings.
