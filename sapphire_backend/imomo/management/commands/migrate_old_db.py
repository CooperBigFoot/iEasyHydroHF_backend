from django.core.management.base import BaseCommand

# Configure SQLAlchemy connection to the old database

from sapphire_backend.imomo.migrate_old_db import migrate
class Command(BaseCommand):
    def handle(self, **options):
        # now do the things that you want with your models here
        migrate()
