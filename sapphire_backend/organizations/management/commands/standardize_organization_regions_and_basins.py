from django.core.management.base import BaseCommand

from ..basin_region_standardizer import BasinRegionStandardizer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--organization", "-o", action="store", help="Organization ID")
        parser.add_argument("--skip_regions", "-rs", action="store_true", default=False, help="Region ID")
        parser.add_argument("--skip_basins", "-bs", action="store_true", default=False, help="Region ID")

    def handle(self, **options):
        organization = options["organization"]

        standardizer = BasinRegionStandardizer(organization)

        if not options["skip_basins"]:
            standardizer.standardize_basins_for_sites()
            standardizer.standardize_basins_for_virtual_stations()
            standardizer.cleanup_empty_basins()

        if not options["skip_regions"]:
            standardizer.standardize_regions_for_sites()
            standardizer.standardize_regions_for_virtual_stations()
            standardizer.cleanup_empty_regions()
