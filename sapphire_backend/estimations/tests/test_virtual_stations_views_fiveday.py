from datetime import date
from decimal import Decimal

import pytest
from django.db.models import Avg

from sapphire_backend.estimations.models import (
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterDischargeFivedayAverageVirtual,
)
from sapphire_backend.utils.rounding import custom_round, hydrological_round


class TestVirtualStationWaterDischargeFivedayMetrics:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 2, 5)
    wdfa_date = date(2020, 2, 3)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator_second_station", [(start_date, end_date)], indirect=True
    )
    def test_water_discharge_fiveday_average(
        self,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
        water_level_metrics_daily_generator_second_station,
    ):
        wdda_station1_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station=manual_hydro_station_kyrgyz,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).aggregate(avg_total=Avg("avg_value"))

        wdda_station2_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station=manual_second_hydro_station_kyrgyz,
            timestamp_local__date__range=(self.start_date, self.end_date),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_station1_expected = hydrological_round(wdda_station1_agg["avg_total"])
        wdfa_station2_expected = hydrological_round(wdda_station2_agg["avg_total"])

        wdfa_virtual_expected = hydrological_round(
            wdfa_station1_expected * virtual_station_association_one.weight / Decimal("100")
            + wdfa_station2_expected * virtual_station_association_two.weight / Decimal("100")
        )

        wdfa_virtual_estimated = EstimationsWaterDischargeFivedayAverageVirtual.objects.get(
            station=virtual_station, timestamp_local__date=self.wdfa_date
        ).avg_value

        assert custom_round(wdfa_virtual_estimated, 6) == custom_round(wdfa_virtual_expected, 6)
