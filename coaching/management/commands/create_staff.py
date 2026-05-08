import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update a staff dashboard user from STAFF_USERNAME and STAFF_PASSWORD."

    def handle(self, *args, **options):
        username = os.environ.get("STAFF_USERNAME")
        email = os.environ.get("STAFF_EMAIL", "")
        password = os.environ.get("STAFF_PASSWORD")

        if not username or not password:
            self.stdout.write(
                "Skipping staff user creation: STAFF_USERNAME or STAFF_PASSWORD is not set."
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": False,
                "is_superuser": False,
            },
        )

        user.email = email
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} staff user '{username}'."))
