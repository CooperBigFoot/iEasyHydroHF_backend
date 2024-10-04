from django.core.management.base import BaseCommand

from sapphire_backend.metrics.management.metrics_data_anonymizer import MetricsDataAnonymizer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--src_id", type=int, help="ID of the source station")
        parser.add_argument("--dest_id", type=int, help="ID of the destination station")
        parser.add_argument("--type", type=int, help="Type of station")
        parser.add_argument(
            "--start_date", type=str, help="Starting date of the copied metrics, requires YYYY-MM-DD format"
        )
        parser.add_argument(
            "--end_date", type=str, help="Ending date of the copied metrics, requires YYYY-MM-DD format"
        )

    def handle(self, **options):
        _ = MetricsDataAnonymizer(
            station_type=options["type"],
            src_id=options["src_id"],
            dest_id=options["dest_id"],
        )
