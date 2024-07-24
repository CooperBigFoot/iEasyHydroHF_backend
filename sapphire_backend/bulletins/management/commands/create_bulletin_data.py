import os.path
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from sapphire_backend.bulletins.choices import BulletinType
from sapphire_backend.bulletins.models import BulletinTemplate


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--organization_uuid",
            type=str,
            required=True,
            help="UUID of the organization for which the objects are created.",
        )

    @staticmethod
    def get_static_file_path(static_path: str):
        static_file_path = os.path.join(settings.STATIC_ROOT, static_path)
        if not os.path.exists(static_file_path):
            # If the file does not exist in STATIC_ROOT, try the development static folder
            static_file_path = os.path.join(settings.APPS_DIR, "static", static_path)
        return static_file_path

    def handle(self, *args: Any, **options: Any):
        organization_uuid = options["organization_uuid"]

        daily_static_path = "bulletins/daily_bulletin.xlsx"
        decadal_static_path = "bulletins/decadal_bulletin.xlsx"

        daily_file_path = self.get_static_file_path(daily_static_path)
        decadal_file_path = self.get_static_file_path(decadal_static_path)

        with open(daily_file_path, "rb") as f:
            daily_file = File(f, name="daily_bulletin.xlsx")
            default_daily_template, _ = BulletinTemplate.objects.get_or_create(
                organization_id=organization_uuid,
                user=None,
                name="Daily bulletin",
                type=BulletinType.DAILY,
                is_default=True,
                defaults={"filename": daily_file},
            )

        with open(decadal_file_path, "rb") as f:
            decadal_file = File(f, name="decadal_bulletin.xlsx")
            default_decadal_template, _ = BulletinTemplate.objects.get_or_create(
                organization_id=organization_uuid,
                user=None,
                name="Decadal bulletin",
                type=BulletinType.DECADAL,
                is_default=True,
                defaults={"filename": decadal_file},
            )

        self.stdout.write(self.style.SUCCESS("Default bulletin templates created!"))
