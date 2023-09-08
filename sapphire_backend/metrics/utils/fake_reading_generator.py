import math
import random
from datetime import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo

from tqdm import tqdm

from sapphire_backend.metrics.models import AirTemperature, WaterDischarge, WaterLevel, WaterTemperature, WaterVelocity


class FakeReadingGenerator:
    def __init__(self, metric: str):
        self.model = self._get_model_for_metric(metric)

    @staticmethod
    def _get_model_for_metric(metric: str):
        metric_str_to_model_mappings = {
            "water_level": WaterLevel,
            "water_discharge": WaterDischarge,
            "water_velocity": WaterVelocity,
            "water_temp": WaterTemperature,
            "air_temp": AirTemperature,
        }

        try:
            return metric_str_to_model_mappings[metric]
        except KeyError:
            raise ValueError(
                "Invalid metric. Supported metrics are:\n"
                "\t-water_discharge\n"
                "\t-water_level\n"
                "\t-water_velocity\n"
                "\t-water_temp\n"
                "\t-air_temp"
            )

    @staticmethod
    def _generate_air_temperature(day_of_year, previous_value=None):
        # Constants for tweaking the simulation
        AMPLITUDE = 10  # This will determine the max difference from the seasonal baseline
        ANOMALY_CHANCE = 0.02  # 2% chance for an anomaly
        ANOMALY_AMPLITUDE = 30  # How much an anomaly might deviate from the expected value
        MISSING_VALUE_CHANCE = 0.4  # 4% chance for a missing value

        if random.random() < MISSING_VALUE_CHANCE:
            return None

        # Determine the seasonal baseline using a sine wave
        # This simulates the cyclical nature of seasonal temperatures
        baseline = AMPLITUDE * math.sin(2 * math.pi * day_of_year / 365.25)

        # Random daily variation
        variation = random.uniform(-3, 3)  # Change this for larger/smaller daily variations

        # Calculate expected value for this day
        expected_value = baseline + variation

        # Introduce potential anomalies
        if random.random() < ANOMALY_CHANCE:
            expected_value += random.uniform(-ANOMALY_AMPLITUDE, ANOMALY_AMPLITUDE)

        # Make sure the next value is not drastically different from the previous value (if given)
        if previous_value is not None:
            expected_value = (expected_value + previous_value) / 2

        return expected_value

    def generate_air_temperature_readings(self, station, year, step, unit):
        start_date = dt(year, 1, 1, tzinfo=ZoneInfo("UTC"))
        end_date = dt(year + 1, 1, 1, tzinfo=ZoneInfo("UTC"))

        previous_value = None
        current_date = start_date

        total_minutes_in_year = (end_date - start_date).total_seconds() / 60
        total_iterations = int(total_minutes_in_year / step)

        with tqdm(total=total_iterations, desc="Generating air temperature readings", unit="reading") as pbar:
            while current_date < end_date:
                day_of_year = current_date.timetuple().tm_yday
                value = self._generate_air_temperature(day_of_year, previous_value)
                reading = AirTemperature(station=station, timestamp=current_date, value=value, unit=unit)
                reading.save()

                previous_value = value if value else previous_value
                current_date += timedelta(minutes=step)
                pbar.update(1)
