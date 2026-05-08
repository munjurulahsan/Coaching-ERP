import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coaching_erp.settings")

import django
from django.core.management import call_command


django.setup()

call_command("migrate")
call_command("collectstatic", interactive=False)
call_command("create_admin")
call_command("create_staff")
