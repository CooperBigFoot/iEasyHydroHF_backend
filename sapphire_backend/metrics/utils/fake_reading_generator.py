import random
from datetime import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo

from tqdm import tqdm

from sapphire_backend.metrics.models import AirTemperature, WaterDischarge, WaterLevel, WaterTemperature, WaterVelocity


class FakeReadingGenerator:
    def __init__(self, metric: str):
        self.model = self._get_model_for_metric(metric)
        self.SEASON_STARTS = {
            "winter": 1,
            "spring": 80,  # This can be adjusted
            "summer": 172,  # This can be adjusted
            "autumn": 266,  # This can be adjusted
            "next_winter": 355,  # This can be adjusted
        }

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

    def _get_season(self, day_of_year):
        """Get the season for a given day of the year."""
        if self.SEASON_STARTS["spring"] <= day_of_year < self.SEASON_STARTS["summer"]:
            return "spring"
        elif self.SEASON_STARTS["summer"] <= day_of_year < self.SEASON_STARTS["autumn"]:
            return "summer"
        elif self.SEASON_STARTS["autumn"] <= day_of_year < self.SEASON_STARTS["next_winter"]:
            return "autumn"
        else:
            return "winter"

    @staticmethod
    def _get_next_season(season):
        """Return the next season."""
        if season == "winter":
            return "spring"
        elif season == "spring":
            return "summer"
        elif season == "summer":
            return "autumn"
        elif season == "autumn":
            return "next_winter"

    def _generate_air_temperature(self, day_of_year, previous_value=None):
        TEMP_MAPPING = {
            "winter": (-10, 10),
            "spring": (5, 25),
            "summer": (15, 40),
            "autumn": (5, 25),
        }

        return self._generic_value_generator(day_of_year, previous_value, TEMP_MAPPING)

    def _generate_water_temperature(self, day_of_year, previous_value=None):
        """Generate a realistic water temperature based on the day of the year."""
        TEMP_MAPPING = {
            "winter": (0, 7),
            "spring": (6, 15),
            "summer": (14, 22),
            "autumn": (10, 18),
        }

        return self._generic_value_generator(day_of_year, previous_value, TEMP_MAPPING)

    def _generate_water_discharge(self, day_of_year, previous_value=None):
        DISCHARGE_MAPPING = {
            "winter": (250, 450),
            "spring": (450, 700),
            "summer": (150, 400),
            "autumn": (200, 500),
        }

        return self._generic_value_generator(day_of_year, previous_value, DISCHARGE_MAPPING)

    def _generate_water_velocity(self, day_of_year, previous_value=None):
        VELOCITY_MAPPING = {
            "winter": (1.5, 2.5),
            "spring": (2.5, 3.5),
            "summer": (1.0, 2.0),
            "autumn": (1.2, 2.5),
        }

        return self._generic_value_generator(day_of_year, previous_value, VELOCITY_MAPPING)

    def _generate_water_level(self, day_of_year, previous_value=None):
        LEVEL_MAPPING = {
            "winter": (3, 4),
            "spring": (4, 6),
            "summer": (2, 3.5),
            "autumn": (3, 5),
        }

        return self._generic_value_generator(day_of_year, previous_value, LEVEL_MAPPING)

    def _generic_value_generator(self, day_of_year, previous_value, mapping):
        season = self._get_season(day_of_year)
        min_value, max_value = mapping[season]

        if previous_value is None:
            return random.uniform(min_value, max_value)

        if (day_of_year - self.SEASON_STARTS[season]) < 15:
            adjusted_value = previous_value + random.uniform(-1, 1)
        else:
            adjusted_value = previous_value + random.uniform(-3, 3)

        return max(min_value, min(max_value, adjusted_value))

    def generate_water_temperature_readings(self, station, year, step, unit):
        return self._generic_reading_generator(
            station, year, step, unit, self._generate_water_temperature, WaterTemperature
        )

    def generate_water_discharge_readings(self, station, year, step, unit):
        return self._generic_reading_generator(
            station, year, step, unit, self._generate_water_discharge, WaterDischarge
        )

    def generate_water_velocity_readings(self, station, year, step, unit):
        return self._generic_reading_generator(station, year, step, unit, self._generate_water_velocity, WaterVelocity)

    def generate_water_level_readings(self, station, year, step, unit):
        return self._generic_reading_generator(station, year, step, unit, self._generate_water_level, WaterLevel)

    def generate_air_temperature_readings(self, station, year, step, unit):
        return self._generic_reading_generator(
            station, year, step, unit, self._generate_air_temperature, AirTemperature
        )

    def _generic_reading_generator(self, station, year, step, unit, generator_function, model_class):
        start_date = dt(year, 1, 1, tzinfo=ZoneInfo("UTC"))
        end_date = dt(year + 1, 1, 1, tzinfo=ZoneInfo("UTC"))
        MISSING_VALUE_PROBABILITY = 0.01

        previous_value = None
        current_date = start_date
        total_minutes_in_year = (end_date - start_date).total_seconds() / 60
        total_iterations = int(total_minutes_in_year / step)

        consecutive_missing_count = 0
        with tqdm(total=total_iterations, desc=f"Generating {model_class.__name__} readings", unit="reading") as pbar:
            while current_date < end_date:
                if random.random() < MISSING_VALUE_PROBABILITY and consecutive_missing_count < 3:
                    consecutive_missing_count += 1
                else:
                    consecutive_missing_count = 0
                    day_of_year = current_date.timetuple().tm_yday
                    value = generator_function(day_of_year, previous_value)
                    reading = model_class(station=station, timestamp=current_date, value=value, unit=unit)
                    reading.save()
                    previous_value = value

                current_date += timedelta(minutes=step)
                pbar.update(1)
