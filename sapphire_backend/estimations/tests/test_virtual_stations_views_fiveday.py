import math

import pytest
from django.db import connection

from sapphire_backend.estimations.query import EstimationsViewQueryManager
from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.utils.aggregations import custom_average
from sapphire_backend.utils.datetime_helper import SmartDatetime


class TestVirtualStationWaterDischargeFivedayMetrics:
    morning_water_levels_station1 = [100, 110, 120, 130, 140]
    evening_water_levels_station1 = [105, 115, 125, 135, 145]

    morning_water_levels_station2 = [200, 210, 220, 230, 240]
    evening_water_levels_station2 = [205, 215, 225, 235, 245]

    dates = ["2020-02-01", "2020-02-02", "2020-02-03", "2020-02-04", "2020-02-05"]

    def calculate_water_level_daily_averages(self, morning_water_levels, evening_water_levels):
        daily_averages = []
        for morning, evening in zip(morning_water_levels, evening_water_levels):
            daily_average = math.ceil((morning + evening) / 2)
            daily_averages.append(daily_average)

        return daily_averages

    def save_water_levels_to_db(self, morning_water_levels, evening_water_levels, dates, station, model):
        for wl_morning, wl_evening, date in zip(morning_water_levels, evening_water_levels, dates):
            smart_dt = SmartDatetime(date, station=station, tz_included=False)
            water_level_morning = HydrologicalMetric(
                timestamp_local=smart_dt.morning_local,
                avg_value=wl_morning,
                unit=MetricUnit.WATER_LEVEL,
                metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                value_type=HydrologicalMeasurementType.MANUAL,
                station=station,
            )
            water_level_morning.save()

            water_level_evening = HydrologicalMetric(
                timestamp_local=smart_dt.evening_local,
                avg_value=wl_evening,
                unit=MetricUnit.WATER_LEVEL,
                metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                value_type=HydrologicalMeasurementType.MANUAL,
                station=station,
            )
            water_level_evening.save()

    @pytest.mark.django_db(transaction=True)
    def test_water_discharge_fiveday_average(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_second_hydro_station_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
    ):
        wlda_station1 = self.calculate_water_level_daily_averages(
            self.morning_water_levels_station1, self.evening_water_levels_station1
        )
        wlda_station2 = self.calculate_water_level_daily_averages(
            self.morning_water_levels_station2, self.evening_water_levels_station2
        )

        wdda_station1_expected = [
            discharge_model_manual_hydro_station_kyrgyz.estimate_discharge(wlda) for wlda in wlda_station1
        ]
        wdda_station2_expected = [
            discharge_model_manual_second_hydro_station_kyrgyz.estimate_discharge(wlda) for wlda in wlda_station2
        ]

        wdfa_station1_expected = custom_average(wdda_station1_expected)
        wdfa_station2_expected = custom_average(wdda_station2_expected)
        wdfa_timestamp = SmartDatetime(
            "2020-02-03", station=manual_hydro_station_kyrgyz, tz_included=False
        ).midday_local
        wdfa_virtual_expected = (
            wdfa_station1_expected * virtual_station_association_one.weight / 100.0
            + wdfa_station2_expected * virtual_station_association_two.weight / 100.0
        )
        self.save_water_levels_to_db(
            self.morning_water_levels_station1,
            self.evening_water_levels_station1,
            self.dates,
            manual_hydro_station_kyrgyz,
            discharge_model_manual_hydro_station_kyrgyz,
        )
        self.save_water_levels_to_db(
            self.morning_water_levels_station2,
            self.evening_water_levels_station2,
            self.dates,
            manual_second_hydro_station_kyrgyz,
            discharge_model_manual_second_hydro_station_kyrgyz,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "CALL refresh_continuous_aggregate('test_sapphire_backend.public.estimations_water_level_daily_average', '2015-01-01', '2025-04-10')"
            )
        wdfa_virtual_estimated = EstimationsViewQueryManager(
            model="estimations_water_discharge_fiveday_average_virtual",
            filter_dict={"station_id": virtual_station.id, "timestamp_local": wdfa_timestamp},
        ).execute_query()[0]["avg_value"]

        assert round(float(wdfa_virtual_estimated), 6) == round(float(wdfa_virtual_expected), 6)
