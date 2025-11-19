"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# 👇 IMPORT PER IL COMANDO
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# 👇 BLOCCO TEMPORANEO: crea superuser admin se non esiste
try:
    call_command("createsu")
except Exception as e:
    print(f"Auto createsu skipped/failed: {e}")

application = get_wsgi_application()
