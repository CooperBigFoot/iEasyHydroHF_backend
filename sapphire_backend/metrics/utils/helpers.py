from sapphire_backend.metrics.models import (
    AirTemperature,
    Precipitation,
    WaterDischarge,
    WaterLevel,
    WaterTemperature,
    WaterVelocity,
)


def get_metric_model(
    metric: str
) -> WaterDischarge | WaterLevel | WaterTemperature | WaterVelocity | AirTemperature | Precipitation | None:
    metric_str_model_mapping = {
        "water_discharge": WaterDischarge,
        "water_level": WaterLevel,
        "water_velocity": WaterVelocity,
        "water_temp": WaterTemperature,
        "air_temp": AirTemperature,
        "precipitation": Precipitation,
    }

    return metric_str_model_mapping.get(metric)
