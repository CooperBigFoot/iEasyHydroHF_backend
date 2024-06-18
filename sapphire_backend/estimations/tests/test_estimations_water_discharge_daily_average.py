from datetime import date

import pytest

from sapphire_backend.estimations.models import (
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterLevelDailyAverage,
)
from sapphire_backend.utils.rounding import custom_round


class TestHydroStationWaterDischargeDailyAverage:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 2, 15)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_daily_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        wlda_queryset = EstimationsWaterLevelDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        wlda_values = list(wlda_queryset.values_list("avg_value", flat=True))
        discharge_average_expected = [
            discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(wla) for wla in wlda_values
        ]

        wdda_queryset = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        discharge_average_estimated = list(wdda_queryset.values_list("avg_value", flat=True))
        for wdda_estimated, wdda_expected in zip(discharge_average_estimated, discharge_average_expected):
            assert custom_round(wdda_estimated, 6) == custom_round(wdda_expected, 6)
