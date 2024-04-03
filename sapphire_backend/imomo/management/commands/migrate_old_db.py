from django.core.management.base import BaseCommand

# Configure SQLAlchemy connection to the old database
from sapphire_backend.imomo.migrate_old_db import migrate


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Add argument to include processed items
        parser.add_argument("--skip-structure", action="store_true", help="Include processed items")
        parser.add_argument("--skip-cleanup", action="store_true", help="Don't flag items as processed")
        parser.add_argument('--limiter', type=int, default=0, help='Set limiter value')


    def handle(self, **options):
        skip_structure= options["skip_structure"]
        skip_cleanup = options["skip_cleanup"]
        limiter = 0 - options["limiter"]

        # now do the things that you want with your models here
        migrate(skip_cleanup, skip_structure, limiter)
