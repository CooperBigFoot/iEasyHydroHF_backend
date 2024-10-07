from django.core.management.base import BaseCommand, CommandError

from sapphire_backend.metrics.management.metrics_data_anonymizer import MetricsDataAnonymizer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--src", type=int, help="ID of the source station", required=True)
        parser.add_argument("--dest", type=int, help="ID of the destination station", required=True)
        parser.add_argument("--station_type", type=str, help="Type of station", required=True)
        parser.add_argument(
            "--start_date",
            type=str,
            help="Starting date of the copied metrics, requires YYYY-MM-DD format",
            required=True,
        )
        parser.add_argument(
            "--end_date", type=str, help="Ending date of the copied metrics, requires YYYY-MM-DD format"
        )
        parser.add_argument("--metrics", type=str, nargs="+", help="List of metrics to copy")
        parser.add_argument("--value_types", type=str, nargs="+", help="Types of metrics to copy")
        parser.add_argument("--offset_factor", type=float, default=0.0, help="Offset factor for the metrics value")
        parser.add_argument("--copy_metrics", action="store_true", default=False, help="Copy metrics")
        parser.add_argument("--copy_curves", action="store_true", default=False, help="Copy discharge curves")
        parser.add_argument("--copy_telegrams", action="store_true", default=False, help="Copy telegrams")

    def handle(self, **options):
        anonymizer = MetricsDataAnonymizer(
            station_type=options["station_type"],
            src_id=options["src"],
            dest_id=options["dest"],
            start_date_str=options["start_date"],
            end_date_str=options["end_date"],
        )

        if options["copy_metrics"]:
            if not options["metrics"] or not options["value_types"]:
                raise CommandError("'metrics' and 'value_types' options are required when copying metrics")
            anonymizer.copy_metrics(
                metric_names=options["metrics"],
                value_types=options["value_types"],
                offset_factor=options["offset_factor"],
            )

        if options["copy_curves"]:
            anonymizer.copy_discharge_curves()

        if options["copy_telegrams"]:
            anonymizer.copy_received_telegrams()
