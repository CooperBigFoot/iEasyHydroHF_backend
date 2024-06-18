from datetime import date

import pytest
from django.db.models import Avg

from sapphire_backend.estimations.models import (
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterDischargeFivedayAverage,
)
from sapphire_backend.utils.rounding import custom_round


class TestHydroStationWaterDischargeFivedayAverageFirstFivePentads:
    start_date = date(2020, 2, 1)
    end_date = date(2020, 2, 29)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_first_fiveday_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        first_fiveday_avg_date = date(2020, 2, 3)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 1), date(2020, 2, 5)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=first_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_second_fiveday_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        second_fiveday_avg_date = date(2020, 2, 8)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 6), date(2020, 2, 10)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=second_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_third_fiveday_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        third_fiveday_avg_date = date(2020, 2, 13)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 11), date(2020, 2, 15)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=third_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_fourth_fiveday_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        fourth_fiveday_avg_date = date(2020, 2, 18)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 16), date(2020, 2, 20)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=fourth_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("water_level_metrics_daily_generator", [(start_date, end_date)], indirect=True)
    def test_water_discharge_fifth_fiveday_average(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        fifth_fiveday_avg_date = date(2020, 2, 23)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 21), date(2020, 2, 25)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=fifth_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)


class TestHydroStationWaterDischargeFivedayAverageSixthPentad:
    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2021, 2, 1), date(2021, 3, 10))], indirect=True
    )
    def test_fiveday_sixth_pentad_february_28_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        sixth_fiveday_avg_date = date(2021, 2, 28)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2021, 2, 26), date(2021, 2, 28)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=sixth_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 2, 1), date(2020, 3, 10))], indirect=True
    )
    def test_fiveday_sixth_pentad_february_29_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        sixth_fiveday_avg_date = date(2020, 2, 28)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 2, 26), date(2020, 2, 29)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=sixth_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 3, 1), date(2020, 4, 10))], indirect=True
    )
    def test_fiveday_sixth_pentad_march_31_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        sixth_fiveday_avg_date = date(2020, 3, 28)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 3, 26), date(2020, 3, 31)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=sixth_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "water_level_metrics_daily_generator", [(date(2020, 4, 1), date(2020, 5, 10))], indirect=True
    )
    def test_fiveday_sixth_pentad_april_30_days(
        self,
        discharge_model_manual_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        water_level_metrics_daily_generator,
    ):
        sixth_fiveday_avg_date = date(2020, 4, 28)
        wdda_queryset_agg = EstimationsWaterDischargeDailyAverage.objects.filter(
            station_id=manual_hydro_station_kyrgyz.id,
            timestamp_local__date__range=(date(2020, 4, 26), date(2020, 4, 30)),
        ).aggregate(avg_total=Avg("avg_value"))

        wdfa_expected = wdda_queryset_agg["avg_total"]

        wdfa_estimated = EstimationsWaterDischargeFivedayAverage.objects.get(
            station_id=manual_hydro_station_kyrgyz.id, timestamp_local__date=sixth_fiveday_avg_date
        ).avg_value

        assert custom_round(wdfa_estimated, 6) == custom_round(wdfa_expected, 6)
