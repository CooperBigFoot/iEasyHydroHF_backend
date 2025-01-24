from datetime import datetime
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
        parser.add_argument('--start-date', type=str, default="", help='Start date for migration (YYYY-MM-DD)')
        parser.add_argument('--end-date', type=str, default="", help='End date for migration (YYYY-MM-DD)')

    def handle(self, **options):
        start_date = None
        end_date = None

        if options["start_date"]:
            start_date = datetime.strptime(options["start_date"], "%Y-%m-%d")
        if options["end_date"]:
            end_date = datetime.strptime(options["end_date"], "%Y-%m-%d")

        migrate(
            skip_cleanup=options["skip_cleanup"],
            skip_structure=options["skip_structure"],
            target_station=options["station"],
            target_organization=options["organization"],
            limiter=options["limiter"],
            start_date=start_date,
            end_date=end_date
        )
