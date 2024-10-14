import logging

from django.core.management.base import BaseCommand

from sapphire_backend.metrics.management.automatic_data_simulator import AutomaticDataSimulator


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--src_id", type=int, required=True, help="ID of source manual station")
        parser.add_argument("--dest_id", type=int, required=True, help="ID of the target automatic station")
        parser.add_argument("--metrics", type=str, nargs="+", required=True, help="List of metrics to simulate")
        parser.add_argument("--offset_value", type=float, default=0.0, help="Offset factor for the metrics value")

    def handle(self, *args, **options):
        data_simulator = AutomaticDataSimulator(src_id=options["src_id"], dest_id=options["dest_id"])

        for metric in options["metrics"]:
            new_metric = data_simulator.create_simulated_measurement(metric, options["offset_value"])
            if new_metric:
                logging.info(
                    f"{new_metric.avg_value} {new_metric.unit} value successfully created for station {data_simulator.dest_station.station_code}"
                )
            else:
                logging.error(f"{metric} not created for stations {data_simulator.dest_station.station_code}.")
