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
        """Generate a realistic air temperature based on the day of the year."""
        # Define temperature bounds
        WINTER_TEMP = (-10, 10)
        SPRING_TEMP = (5, 25)
        SUMMER_TEMP = (15, 40)
        AUTUMN_TEMP = (5, 25)

        season = self._get_season(day_of_year)

        # Define a mapping of seasons to their respective temperature bounds
        temp_mapping = {"winter": WINTER_TEMP, "spring": SPRING_TEMP, "summer": SUMMER_TEMP, "autumn": AUTUMN_TEMP}

        min_temp, max_temp = temp_mapping[season]

        # If it's the first value, or no previous value provided, select randomly from the range
        if previous_value is None:
            return random.uniform(min_temp, max_temp)

        # Adjust based on transition phase: the first 15 days of the season
        # will have a more limited change from the previous day's value.
        if (day_of_year - self.SEASON_STARTS[season]) < 15:
            adjusted_temp = previous_value + random.uniform(-1, 1)
        else:
            adjusted_temp = previous_value + random.uniform(-3, 3)

        return max(min_temp, min(max_temp, adjusted_temp))

    def generate_air_temperature_readings(self, station, year, step, unit):
        start_date = dt(year, 1, 1, tzinfo=ZoneInfo("UTC"))
        end_date = dt(year + 1, 1, 1, tzinfo=ZoneInfo("UTC"))
        MISSING_VALUE_PROBABILITY = 0.01  # 1% chance of a missing value

        previous_value = None
        current_date = start_date

        total_minutes_in_year = (end_date - start_date).total_seconds() / 60
        total_iterations = int(total_minutes_in_year / step)

        consecutive_missing_count = 0
        with tqdm(total=total_iterations, desc="Generating readings", unit="reading") as pbar:
            while current_date < end_date:
                # Check for missing value
                if random.random() < MISSING_VALUE_PROBABILITY and consecutive_missing_count < 3:
                    consecutive_missing_count += 1
                else:
                    consecutive_missing_count = 0
                    day_of_year = current_date.timetuple().tm_yday
                    value = self._generate_air_temperature(day_of_year, previous_value)
                    reading = AirTemperature(station=station, timestamp=current_date, value=value, unit=unit)
                    reading.save()
                    previous_value = value

                current_date += timedelta(minutes=step)
                pbar.update(1)
