from django.core.management.base import BaseCommand

# Configure SQLAlchemy connection to the old database
from sapphire_backend.imomo.migrate_old_db import migrate


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Add argument to include processed items
        parser.add_argument("--skip-structure", action="store_true", default=False, help="Skip building organizations, sites, stations")
        parser.add_argument("--skip-cleanup", action="store_true", default=False, help="Skip cleaning up all the objects")
        parser.add_argument('--limiter', type=int, default=0, help='Set limiter value')
        parser.add_argument('--station', type=str, default="", help='Specify which station code to migrate only')
        parser.add_argument('--organization', type=str, default="", help='Specify which organization code to migrate only')

    def handle(self, **options):
        skip_structure = options["skip_structure"]
        skip_cleanup = options["skip_cleanup"]
        limiter = options["limiter"]
        target_station = options["station"]
        target_organization = options["organization"]
        # now do the things that you want with your models here
        migrate(skip_cleanup, skip_structure, target_station, target_organization, limiter)
