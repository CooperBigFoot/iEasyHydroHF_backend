from datetime import date

import pytest

from sapphire_backend.estimations.models import EstimationsWaterLevelDailyAverage
from sapphire_backend.utils.aggregations import custom_average
from sapphire_backend.utils.rounding import custom_ceil, custom_round


class TestHydroStationWaterDischargeDailyAverage:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 2, 15)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_level_daily_average(
        self,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        wlda_estimated_queryset = EstimationsWaterLevelDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).order_by("timestamp_local")

        wlda_estimated_list = list(wlda_estimated_queryset.values_list("avg_value", flat=True))
        for wlda_estimated, wld_pair in zip(wlda_estimated_list, water_level_metrics_daily_generator):
            wl_morning, wl_evening = wld_pair
            wlda_expected = custom_ceil(custom_average([wl_morning.avg_value, wl_evening.avg_value]))

            assert custom_round(wlda_estimated, 6) == custom_round(wlda_expected, 6)
