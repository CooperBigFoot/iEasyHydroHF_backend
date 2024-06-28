from datetime import date

import pytest
from django.db.models import Avg

from sapphire_backend.estimations.models import (
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterDischargeDecadeAverage,
)
from sapphire_backend.utils.rounding import custom_round


class TestHydroStationWaterDischargeDecadeAverageFirstTwoDecades:
    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 2, 1), date(2020, 2, 29))], indirect=True
    )
    def test_water_discharge_first_decade_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        first_decade_avg_date = date(2020, 2, 5)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 1), date(2020, 2, 10)),
        ).aggregate(avg_total=Avg("avg_value"))

        wddca_expected = wdda_queryset_agg["avg_total"]

        wddca_estimated = EstimationsWaterDischargeDecadeAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=first_decade_avg_date
        ).avg_value

        assert custom_round(wddca_estimated, 6) == custom_round(wddca_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 2, 1), date(2020, 2, 29))], indirect=True
    )
    def test_water_discharge_second_decade_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        second_decade_avg_date = date(2020, 2, 15)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 11), date(2020, 2, 20)),
        ).aggregate(avg_total=Avg("avg_value"))

        wddca_expected = wdda_queryset_agg["avg_total"]

        wddca_estimated = EstimationsWaterDischargeDecadeAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=second_decade_avg_date
        ).avg_value

        assert custom_round(wddca_estimated, 6) == custom_round(wddca_expected, 6)


class TestHydroStationWaterDischargeDecadeAverageThirdDecade:
    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2021, 2, 1), date(2021, 3, 10))], indirect=True
    )
    def test_third_decade_february_28_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        third_decade_avg_date = date(2021, 2, 25)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2021, 2, 21), date(2021, 2, 28)),
        ).aggregate(avg_total=Avg("avg_value"))

        wddca_expected = wdda_queryset_agg["avg_total"]

        wddca_estimated = EstimationsWaterDischargeDecadeAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=third_decade_avg_date
        ).avg_value

        assert custom_round(wddca_estimated, 6) == custom_round(wddca_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 2, 1), date(2020, 3, 10))], indirect=True
    )
    def test_third_decade_february_29_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        third_decade_avg_date = date(2020, 2, 25)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 21), date(2020, 2, 29)),
        ).aggregate(avg_total=Avg("avg_value"))

        wddca_expected = wdda_queryset_agg["avg_total"]

        wddca_estimated = EstimationsWaterDischargeDecadeAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=third_decade_avg_date
        ).avg_value

        assert custom_round(wddca_estimated, 6) == custom_round(wddca_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 3, 1), date(2020, 4, 10))], indirect=True
    )
    def test_third_decade_march_31_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        third_decade_avg_date = date(2020, 3, 25)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 3, 21), date(2020, 3, 31)),
        ).aggregate(avg_total=Avg("avg_value"))

        wddca_expected = wdda_queryset_agg["avg_total"]

        wddca_estimated = EstimationsWaterDischargeDecadeAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=third_decade_avg_date
        ).avg_value

        assert custom_round(wddca_estimated, 6) == custom_round(wddca_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 4, 1), date(2020, 5, 10))], indirect=True
    )
    def test_third_decade_april_30_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        third_decade_avg_date = date(2020, 4, 25)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 4, 21), date(2020, 4, 30)),
        ).aggregate(avg_total=Avg("avg_value"))

        wddca_expected = wdda_queryset_agg["avg_total"]

        wddca_estimated = EstimationsWaterDischargeDecadeAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=third_decade_avg_date
        ).avg_value

        assert custom_round(wddca_estimated, 6) == custom_round(wddca_expected, 6)
