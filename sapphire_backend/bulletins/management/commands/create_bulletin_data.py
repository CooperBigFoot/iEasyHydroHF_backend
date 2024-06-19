import os.path
from typing import Any

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from sapphire_backend.bulletins.choices import BulletinTagType, BulletinType
from sapphire_backend.bulletins.models import BulletinTemplate, BulletinTemplateTag


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--skip_tags", action="store_true", default=False, help="Skip the creation of template tags."
        )
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

    def handle(self, *args: Any, **options: Any) -> str | None:
        skip_tags = options["skip_tags"]
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

        if skip_tags:
            return

        self.stdout.write("Creating the default template tags...")

        date = BulletinTemplateTag.objects.create(
            name="DATE", type=BulletinTagType.GENERAL, description="Formatted value of the chosen date"
        )
        date.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{date.name} {date.type.label} tag created!"))

        today = BulletinTemplateTag.objects.create(
            name="TODAY", type=BulletinTagType.GENERAL, description="Formatted value of the current date"
        )
        today.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{today.name} {today.type.label} tag created!"))

        decade = BulletinTemplateTag.objects.create(
            name="DECADE_PERIOD", type=BulletinTagType.GENERAL, description="Formatted value decade's period"
        )
        decade.bulletins.add(default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{decade.name} {decade.type.label} tag created!"))

        site_basin_header = BulletinTemplateTag.objects.create(
            name="SITE_BASIN", type=BulletinTagType.HEADER, description="Site basin"
        )
        site_basin_header.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{site_basin_header.name} {site_basin_header.type.label} tag created!"))

        site_region_header = BulletinTemplateTag.objects.create(
            name="SITE_REGION", type=BulletinTagType.HEADER, description="Site region"
        )
        site_region_header.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{site_region_header.name} {site_region_header.type.label} tag created!")
        )

        site_basin_data = BulletinTemplateTag.objects.create(
            name="SITE_BASIN", type=BulletinTagType.DATA, description="Site basin"
        )
        site_basin_data.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{site_basin_data.name} {site_basin_data.type.label} tag created!"))

        site_region_data = BulletinTemplateTag.objects.create(
            name="SITE_REGION", type=BulletinTagType.DATA, description="Site region"
        )
        site_region_data.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{site_region_data.name} {site_region_data.type.label} tag created!"))

        site_name = BulletinTemplateTag.objects.create(
            name="SITE_NAME", type=BulletinTagType.DATA, description="Site name"
        )
        site_name.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{site_name.name} {site_name.type.label} tag created!"))

        site_code = BulletinTemplateTag.objects.create(
            name="SITE_CODE", type=BulletinTagType.DATA, description="Site code"
        )
        site_code.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{site_code.name} {site_code.type.label} tag created!"))

        discharge_morning = BulletinTemplateTag.objects.create(
            name="DISCHARGE_MORNING",
            type=BulletinTagType.DATA,
            description="Morning (8 AM at local time) discharge estimation for the selected date",
        )
        discharge_morning.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_morning.name} {discharge_morning.type.label} tag created!"))

        discharge_morning_1 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_MORNING_1",
            type=BulletinTagType.DATA,
            description="Morning (8 AM at local time) discharge estimation for day before the selected day",
        )
        discharge_morning_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_morning_1.name} {discharge_morning_1.type.label} tag created!")
        )

        discharge_morning_2 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_MORNING_2",
            type=BulletinTagType.DATA,
            description="Morning (8 AM at local time) discharge estimation for 2 days before the selected day",
        )
        discharge_morning_2.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_morning_2.name} {discharge_morning_2.type.label} tag created!")
        )

        discharge_evening = BulletinTemplateTag.objects.create(
            name="DISCHARGE_EVENING",
            type=BulletinTagType.DATA,
            description="Evening (8 PM at local time) discharge estimation for the selected date",
        )
        discharge_evening.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_evening.name} {discharge_evening.type.label} tag created!"))

        discharge_evening_1 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_EVENING_1",
            type=BulletinTagType.DATA,
            description="Evening (8 PM at local time) discharge estimation for day before the selected date",
        )
        discharge_evening_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_evening_1.name} {discharge_evening_1.type.label} tag created!")
        )

        discharge_evening_2 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_EVENING_2",
            type=BulletinTagType.DATA,
            description="Evening (8 PM at local time) discharge estimation for 2 days before the selected date",
        )
        discharge_evening_2.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_evening_2.name} {discharge_evening_2.type.label} tag created!")
        )

        discharge_daily = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DAILY",
            type=BulletinTagType.DATA,
            description="Discharge daily average estimation for the selected date",
        )
        discharge_daily.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_daily.name} {discharge_daily.type.label} tag created!"))

        discharge_daily_1 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DAILY_1",
            type=BulletinTagType.DATA,
            description="Discharge daily average estimation for day before the selected date",
        )
        discharge_daily_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_daily_1.name} {discharge_daily_1.type.label} tag created!"))

        discharge_daily_2 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DAILY_2",
            type=BulletinTagType.DATA,
            description="Discharge daily average estimation for 2 days before the selected date",
        )
        discharge_daily_2.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_daily_2.name} {discharge_daily_2.type.label} tag created!"))

        discharge_fiveday = BulletinTemplateTag.objects.create(
            name="DISCHARGE_FIVEDAY",
            type=BulletinTagType.DATA,
            description="Discharge average for pentad (5 day) period of the selected date",
        )
        discharge_fiveday.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_fiveday.name} {discharge_fiveday.type.label} tag created!"))

        discharge_fiveday_1 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_FIVEDAY_1",
            type=BulletinTagType.DATA,
            description="Discharge average for the previous pentad (5 day) period of the selected date",
        )
        discharge_fiveday_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_fiveday_1.name} {discharge_fiveday_1.type.label} tag created!")
        )

        discharge_decade = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DECADE",
            type=BulletinTagType.DATA,
            description="Discharge average for decade (10 day) period of the selected date",
        )
        discharge_decade.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_decade.name} {discharge_decade.type.label} tag created!"))

        discharge_decade_1 = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DECADE_1",
            type=BulletinTagType.DATA,
            description="Discharge average for the previous decade (10 day) period of the selected date",
        )
        discharge_decade_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_decade_1.name} {discharge_decade_1.type.label} tag created!")
        )

        discharge_measurement = BulletinTemplateTag.objects.create(
            name="DISCHARGE_MEASUREMENT",
            type=BulletinTagType.DATA,
            description="Discharge measurement on the selected date",
        )
        discharge_measurement.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_measurement.name} {discharge_measurement.type.label} tag created!")
        )

        discharge_max = BulletinTemplateTag.objects.create(
            name="DISCHARGE_MAX", type=BulletinTagType.DATA, description="Site's discharge maximum recommendation"
        )
        discharge_max.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_max.name} {discharge_max.type.label} tag created!"))

        discharge_norm = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DECADE_NORM",
            type=BulletinTagType.DATA,
            description="Discharge decade norm on the selected day",
        )
        discharge_norm.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{discharge_norm.name} {discharge_norm.type.label} tag created!"))

        water_level_morning = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_MORNING",
            type=BulletinTagType.DATA,
            description="Morning (8 AM at local time) water level measurement for the selected date",
        )
        water_level_morning.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_morning.name} {water_level_morning.type.label} tag created!")
        )

        water_level_morning_1 = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_MORNING_1",
            type=BulletinTagType.DATA,
            description="Morning (8 AM at local time) water level measurement for day before the selected day",
        )
        water_level_morning_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_morning_1.name} {water_level_morning_1.type.label} tag created!")
        )

        water_level_morning_2 = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_MORNING_2",
            type=BulletinTagType.DATA,
            description="Morning (8 AM at local time) water level measurement for 2 days before the selected day",
        )
        water_level_morning_2.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_morning_2.name} {water_level_morning_2.type.label} tag created!")
        )

        water_level_evening = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_EVENING",
            type=BulletinTagType.DATA,
            description="Evening (8 PM at local time) water level measurement for the selected date",
        )
        water_level_evening.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_evening.name} {water_level_evening.type.label} tag created!")
        )

        water_level_evening_1 = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_EVENING_1",
            type=BulletinTagType.DATA,
            description="Evening (8 PM at local time) water level measurement for day before the selected date",
        )
        water_level_evening_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_evening_1.name} {water_level_evening_1.type.label} tag created!")
        )

        water_level_evening_2 = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_EVENING_2",
            type=BulletinTagType.DATA,
            description="Evening (8 PM at local time) water level measurement for 2 days before the selected date",
        )
        water_level_evening_2.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_evening_2.name} {water_level_evening_2.type.label} tag created!")
        )

        water_level_daily = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_DAILY",
            type=BulletinTagType.DATA,
            description="Water level daily average for the selected date",
        )
        water_level_daily.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{water_level_daily.name} {water_level_daily.type.label} tag created!"))

        water_level_daily_1 = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_DAILY_1",
            type=BulletinTagType.DATA,
            description="Water level daily average for day before the selected date",
        )
        water_level_daily_1.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_daily_1.name} {water_level_daily_1.type.label} tag created!")
        )

        water_level_daily_2 = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_DAILY_2",
            type=BulletinTagType.DATA,
            description="Water level daily average for 2 days before the selected date",
        )
        water_level_daily_2.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_daily_2.name} {water_level_daily_2.type.label} tag created!")
        )

        water_level_decadal = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_DECADAL_MEASUREMENT",
            type=BulletinTagType.DATA,
            description="Water level decadal measurement",
        )
        water_level_decadal.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_decadal.name} {water_level_decadal.type.label} tag created!")
        )

        water_level_morning_trend = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_MORNING_TREND",
            type=BulletinTagType.DATA,
            description="Water level morning (8 AM at local time) trend: selected date - previous day value",
        )
        water_level_morning_trend.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_morning_trend.name} {water_level_morning_trend.type.label} tag created!")
        )

        water_level_evening_trend = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_EVENING_TREND",
            type=BulletinTagType.DATA,
            description="Water level evening (8 PM at local time) trend: selected date - previous day value",
        )
        water_level_evening_trend.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_evening_trend.name} {water_level_evening_trend.type.label} tag created!")
        )

        water_level_daily_trend = BulletinTemplateTag.objects.create(
            name="WATER_LEVEL_DAILY_TREND",
            type=BulletinTagType.DATA,
            description="Water level daily trend: selected date - previous day value",
        )
        water_level_daily_trend.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{water_level_daily_trend.name} {water_level_daily_trend.type.label} tag created!")
        )

        discharge_morning_trend = BulletinTemplateTag.objects.create(
            name="DISCHARGE_MORNING_TREND",
            type=BulletinTagType.DATA,
            description="Discharge morning (8 AM at local time) trend: selected date - previous day value",
        )
        discharge_morning_trend.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_morning_trend.name} {discharge_morning_trend.type.label} tag created!")
        )

        discharge_evening_trend = BulletinTemplateTag.objects.create(
            name="DISCHARGE_EVENING_TREND",
            type=BulletinTagType.DATA,
            description="Discharge evening (8 PM at local time) trend: selected date - previous day value",
        )
        discharge_evening_trend.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_evening_trend.name} {discharge_evening_trend.type.label} tag created!")
        )

        discharge_daily_trend = BulletinTemplateTag.objects.create(
            name="DISCHARGE_DAILY_TREND",
            type=BulletinTagType.DATA,
            description="Discharge daily trend: selected date - previous day value",
        )
        discharge_daily_trend.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(
            self.style.SUCCESS(f"{discharge_daily_trend.name} {discharge_daily_trend.type.label} tag created!")
        )

        ice_phenomena = BulletinTemplateTag.objects.create(
            name="ICE_PHENOMENA",
            type=BulletinTagType.DATA,
            description="Ice phenomena text value on the requested date",
        )
        ice_phenomena.bulletins.add(default_daily_template, default_decadal_template)
        self.stdout.write(self.style.SUCCESS(f"{ice_phenomena.name} {ice_phenomena.type.label} tag created!"))
