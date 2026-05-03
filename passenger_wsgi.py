import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coaching_erp.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
