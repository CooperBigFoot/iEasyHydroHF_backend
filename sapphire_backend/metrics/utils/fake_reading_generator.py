import random
from datetime import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo

from tqdm import tqdm

from sapphire_backend.metrics.models import (
    AirTemperature,
    Precipitation,
    WaterDischarge,
    WaterLevel,
    WaterTemperature,
    WaterVelocity,
)


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
            "precipitation": Precipitation,
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
                "\t-air_temp\n"
                "\t-precipitation"
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

    def _generate_air_temperature(self, day_of_year, previous_avg=None):
        TEMP_MAPPING = {
            "winter": (-10, 10),
            "spring": (5, 25),
            "summer": (15, 40),
            "autumn": (5, 25),
        }

        return self._generic_value_generator(day_of_year, previous_avg, TEMP_MAPPING)

    def _generate_water_temperature(self, day_of_year, previous_avg=None):
        """Generate a realistic water temperature based on the day of the year."""
        TEMP_MAPPING = {
            "winter": (0, 7),
            "spring": (6, 15),
            "summer": (14, 22),
            "autumn": (10, 18),
        }

        return self._generic_value_generator(day_of_year, previous_avg, TEMP_MAPPING)

    def _generate_water_discharge(self, day_of_year, previous_avg=None):
        DISCHARGE_MAPPING = {
            "winter": (250, 450),
            "spring": (450, 700),
            "summer": (150, 400),
            "autumn": (200, 500),
        }

        return self._generic_value_generator(day_of_year, previous_avg, DISCHARGE_MAPPING)

    def _generate_water_velocity(self, day_of_year, previous_avg=None):
        VELOCITY_MAPPING = {
            "winter": (1.5, 2.5),
            "spring": (2.5, 3.5),
            "summer": (1.0, 2.0),
            "autumn": (1.2, 2.5),
        }

        return self._generic_value_generator(day_of_year, previous_avg, VELOCITY_MAPPING)

    def _generate_water_level(self, day_of_year, previous_avg=None):
        LEVEL_MAPPING = {
            "winter": (3, 4),
            "spring": (4, 6),
            "summer": (2, 3.5),
            "autumn": (3, 5),
        }

        return self._generic_value_generator(day_of_year, previous_avg, LEVEL_MAPPING)

    def _generate_precipitation(self, day_of_year, previous_avg=None):
        PRECIPITATION_MAPPING = {
            "winter": (0, 7),
            "spring": (1, 15),
            "summer": (1, 10),
            "autumn": (1, 12),
        }

        return self._generic_value_generator(day_of_year, previous_avg, PRECIPITATION_MAPPING)

    def _generic_value_generator(self, day_of_year, previous_avg, mapping):
        season = self._get_season(day_of_year)
        min_bound, max_bound = mapping[season]

        if previous_avg is None:
            avg_value = random.uniform(min_bound, max_bound)
        else:
            if (day_of_year - self.SEASON_STARTS[season]) < 15:
                avg_value = previous_avg + random.uniform(-1, 1)
            else:
                avg_value = previous_avg + random.uniform(-3, 3)

        avg_value = max(min_bound, min(max_bound, avg_value))
        min_value = max(min_bound, avg_value - random.uniform(0.5, 2))
        max_value = min(max_bound, avg_value + random.uniform(0.5, 2))

        return min_value, max_value, avg_value

    def generate_water_temperature_readings(self, sensor, year, step, unit):
        return self._generic_reading_generator(
            sensor, year, step, unit, self._generate_water_temperature, WaterTemperature
        )

    def generate_water_discharge_readings(self, sensor, year, step, unit):
        return self._generic_reading_generator(
            sensor, year, step, unit, self._generate_water_discharge, WaterDischarge
        )

    def generate_water_velocity_readings(self, sensor, year, step, unit):
        return self._generic_reading_generator(sensor, year, step, unit, self._generate_water_velocity, WaterVelocity)

    def generate_water_level_readings(self, sensor, year, step, unit):
        return self._generic_reading_generator(sensor, year, step, unit, self._generate_water_level, WaterLevel)

    def generate_air_temperature_readings(self, sensor, year, step, unit):
        return self._generic_reading_generator(
            sensor, year, step, unit, self._generate_air_temperature, AirTemperature
        )

    def generate_precipitation_readings(self, sensor, year, step, unit):
        return self._generic_reading_generator(sensor, year, step, unit, self._generate_precipitation, Precipitation)

    @staticmethod
    def _generic_reading_generator(sensor, year, step, unit, generator_function, model_class):
        start_date = dt(year, 1, 1, tzinfo=ZoneInfo("UTC"))
        end_date = dt(year + 1, 1, 1, tzinfo=ZoneInfo("UTC"))
        MISSING_VALUE_PROBABILITY = 0.01

        previous_avg = None
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
                    min_value, max_value, avg_value = generator_function(day_of_year, previous_avg)
                    reading = model_class(
                        sensor=sensor,
                        timestamp=current_date,
                        average_value=avg_value,
                        maximum_value=max_value,
                        minimum_value=min_value,
                        unit=unit,
                    )
                    reading.save()
                    previous_avg = avg_value
                current_date += timedelta(minutes=step)
                pbar.update(1)
