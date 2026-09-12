"""
One-shot, idempotent site bootstrap for hosts without shell access (e.g. Render free tier).

Runs at service start:  python manage.py migrate && python manage.py bootstrap_site && gunicorn ...

- seeds the catalogue, services, settings and legal pages (skips anything that already exists)
- attaches the catalogue photos
- creates the first admin user from DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD
  ONLY when no superuser exists yet, so a password changed later in the admin is never overwritten
"""
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed data, attach catalogue images and create the first admin user (idempotent)."

    def handle(self, *args, **options):
        call_command("seed_demo", verbosity=0)
        call_command("attach_catalogue_images", verbosity=0)
        self.stdout.write("Catalogue, services and pages are in place.")

        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Admin user already exists - leaving it unchanged.")
            return

        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        if not (username and password):
            self.stdout.write(self.style.WARNING(
                "No admin user created: set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD."
            ))
            return
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' created."))
