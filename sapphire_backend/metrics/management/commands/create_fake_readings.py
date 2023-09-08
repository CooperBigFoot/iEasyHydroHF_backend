from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from sapphire_backend.metrics.models import AirTemperature
from sapphire_backend.metrics.utils.fake_reading_generator import FakeReadingGenerator
from sapphire_backend.stations.models import Station


class Command(BaseCommand):
    help = "Create fake readings for testing purposes"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--station_id", type=int, help="IDs of the station for which to create fake readings.")
        parser.add_argument("--metric", type=str, help="For which metric should the readings be generated.")
        parser.add_argument("--year", type=int, help="For which year to generate readings.")
        parser.add_argument(
            "--step", type=int, required=False, default=60, help="Step (in minutes) between readings. Default is 60."
        )
        parser.add_argument("--unit", type=str, required=False, help="Unit of the measurements. Optional.")

    def handle(self, *args: Any, **options: Any) -> str | None:
        try:
            fake_generator = FakeReadingGenerator(options["metric"])
        except ValueError as e:
            raise CommandError(e)
        try:
            station = Station.objects.get(id=options["station_id"])
        except Station.DoesNotExist:
            raise CommandError("The station with the given ID doesn't exist.")

        if fake_generator.model == AirTemperature:
            fake_generator.generate_air_temperature_readings(
                station=station,
                year=options["year"],
                step=options["step"],
                unit=options["unit"] if options["unit"] else "°C",
            )

        return None
