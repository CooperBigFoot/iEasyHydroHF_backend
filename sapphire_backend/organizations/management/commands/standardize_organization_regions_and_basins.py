from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--organization", "-o", action="store", help="Organization ID")
        parser.add_argument("--skip_regions", "-rs", action="store_true", default=False, help="Region ID")
        parser.add_argument("--skip_basins", "-bs", action="store_true", default=False, help="Region ID")

    def handle(self, **options):
        pass
