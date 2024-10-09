import datetime

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.metrics.management.metrics_data_anonymizer import MetricsDataAnonymizer
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.stations.models import HydrologicalStation
from sapphire_backend.telegrams.models import TelegramReceived


class TestMetricsDataAnonymizer:
    def test_init_for_invalid_station_type(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz
    ):
        with pytest.raises(ValueError, match="Unsupported station type: virtual. Expected hydro or meteo."):
            _ = MetricsDataAnonymizer(
                "virtual", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2015-01-01"
            )

    def test_init_for_non_existing_source_station(self, organization_kyrgyz, manual_hydro_station_kyrgyz):
        with pytest.raises(ValueError, match="HydrologicalStation with ID 22222 does not exist."):
            _ = MetricsDataAnonymizer("hydro", 22222, manual_hydro_station_kyrgyz.id, "2015-01-01")

    def test_init_for_non_existing_dest_station(self, organization_kyrgyz, manual_hydro_station_kyrgyz):
        with pytest.raises(ValueError, match="HydrologicalStation with ID 22222 does not exist."):
            _ = MetricsDataAnonymizer("hydro", manual_hydro_station_kyrgyz.id, 22222, "2015-01-01")

    def test_init_for_all_provided_arguments(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz
    ):
        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2015-01-01", "2024-12-31"
        )
        assert anonymizer.src_station == manual_hydro_station_kyrgyz
        assert anonymizer.dest_station == manual_second_hydro_station_kyrgyz
        assert anonymizer.station_cls == HydrologicalStation
        assert anonymizer.start_date == datetime.datetime(2015, 1, 1, 0, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert anonymizer.end_date == datetime.datetime(2024, 12, 31, 0, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

    def test_init_for_non_provided_end_date(
        self, mock_datetime, organization_kyrgyz, manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz
    ):
        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2015-01-01"
        )

        assert anonymizer.src_station == manual_hydro_station_kyrgyz
        assert anonymizer.dest_station == manual_second_hydro_station_kyrgyz
        assert anonymizer.station_cls == HydrologicalStation
        assert anonymizer.start_date == datetime.datetime(2015, 1, 1, 0, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert anonymizer.end_date == datetime.datetime(2024, 10, 8, 0, 0, 0, 0, tzinfo=ZoneInfo("UTC"))

    def test_copy_discharge_curves_when_source_doesnt_have_any(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz
    ):
        assert DischargeModel.objects.count() == 0
        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2015-01-01"
        )
        anonymizer.copy_discharge_curves()

        assert DischargeModel.objects.all().count() == 0

    def test_copy_discharge_curves_ignores_older(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_second_model_manual_hydro_station_kyrgyz,
    ):
        assert DischargeModel.objects.filter(station=manual_hydro_station_kyrgyz).count() == 2
        assert DischargeModel.objects.filter(station=manual_second_hydro_station_kyrgyz).count() == 0

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2020-02-01"
        )
        anonymizer.copy_discharge_curves()

        assert DischargeModel.objects.filter(station=manual_hydro_station_kyrgyz).count() == 2
        assert DischargeModel.objects.filter(station=manual_second_hydro_station_kyrgyz).count() == 1

        new_model = DischargeModel.objects.filter(station=manual_second_hydro_station_kyrgyz).first()

        assert new_model.param_a == discharge_second_model_manual_hydro_station_kyrgyz.param_a
        assert new_model.param_b == discharge_second_model_manual_hydro_station_kyrgyz.param_b
        assert float(new_model.param_c) == discharge_second_model_manual_hydro_station_kyrgyz.param_c
        assert new_model.valid_from_local == discharge_second_model_manual_hydro_station_kyrgyz.valid_from_local

    def test_copy_discharge_curves_across_organizations(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        discharge_model_manual_hydro_station_kyrgyz,
        discharge_model_manual_hydro_station_uzbek,
    ):
        assert DischargeModel.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert DischargeModel.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2020-01-01"
        )
        anonymizer.copy_discharge_curves()

        assert DischargeModel.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert DischargeModel.objects.filter(station=manual_hydro_station_uzbek).count() == 2

        new_model = DischargeModel.objects.filter(station=manual_hydro_station_uzbek).last()
        assert new_model.param_a == discharge_model_manual_hydro_station_kyrgyz.param_a
        assert new_model.param_b == discharge_model_manual_hydro_station_kyrgyz.param_b
        assert float(new_model.param_c) == discharge_model_manual_hydro_station_kyrgyz.param_c
        assert new_model.valid_from_local == discharge_model_manual_hydro_station_kyrgyz.valid_from_local

    def test_copy_telegrams_for_no_existing_telegrams(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz
    ):
        assert TelegramReceived.objects.count() == 0
        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2020-02-01"
        )
        anonymizer.copy_received_telegrams()
        assert TelegramReceived.objects.count() == 0

    def test_copy_telegrams_for_no_existing_telegram_for_source_station(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        telegram_received_manual_second_hydro_station_kyrgyz,
    ):
        assert TelegramReceived.objects.count() == 1

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_second_hydro_station_kyrgyz.id, "2020-02-01"
        )
        anonymizer.copy_received_telegrams()
        assert TelegramReceived.objects.count() == 1

    def test_copy_telegrams_ignores_older(
        self,
        datetime_mock_auto_now_add,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        telegram_received_manual_hydro_station_kyrgyz,
    ):
        assert TelegramReceived.objects.filter(station_code=manual_hydro_station_kyrgyz.station_code).count() == 1
        assert (
            TelegramReceived.objects.filter(station_code=manual_second_hydro_station_kyrgyz.station_code).count() == 0
        )

        anonymizer = MetricsDataAnonymizer(
            "hydro",
            manual_hydro_station_kyrgyz.id,
            manual_second_hydro_station_kyrgyz.id,
            "2024-09-01",  # datetime_mock_auto_now_add sets the created date to 2024-08-25T12:00:00
        )
        anonymizer.copy_received_telegrams()

        assert TelegramReceived.objects.filter(station_code=manual_hydro_station_kyrgyz.station_code).count() == 1
        assert (
            TelegramReceived.objects.filter(station_code=manual_second_hydro_station_kyrgyz.station_code).count() == 0
        )

    def test_copy_telegrams_across_organizations(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        telegram_received_manual_hydro_station_kyrgyz,
    ):
        assert TelegramReceived.objects.filter(station_code=manual_hydro_station_kyrgyz.station_code).count() == 1
        assert TelegramReceived.objects.filter(station_code=manual_hydro_station_uzbek.station_code).count() == 0
        assert (
            telegram_received_manual_hydro_station_kyrgyz.decoded_values["raw"]
            == telegram_received_manual_hydro_station_kyrgyz.telegram
        )
        assert (
            telegram_received_manual_hydro_station_kyrgyz.decoded_values["section_zero"]["station_name"]
            == manual_hydro_station_kyrgyz.name
        )
        assert (
            telegram_received_manual_hydro_station_kyrgyz.decoded_values["section_zero"]["station_code"]
            == manual_hydro_station_kyrgyz.station_code
        )

        anonymizer = MetricsDataAnonymizer(
            "hydro",
            manual_hydro_station_kyrgyz.id,
            manual_hydro_station_uzbek.id,
            "2024-08-01",  # datetime_mock_auto_now_add sets the created date to 2024-08-25T12:00:00
        )
        anonymizer.copy_received_telegrams()

        assert TelegramReceived.objects.filter(station_code=manual_hydro_station_kyrgyz.station_code).count() == 1
        assert TelegramReceived.objects.filter(station_code=manual_hydro_station_uzbek.station_code).count() == 1

        new_telegram = TelegramReceived.objects.filter(station_code=manual_hydro_station_uzbek.station_code).first()
        new_telegram_str = telegram_received_manual_hydro_station_kyrgyz.telegram.replace(
            telegram_received_manual_hydro_station_kyrgyz.station_code, manual_hydro_station_uzbek.station_code
        )

        assert new_telegram.telegram == new_telegram_str
        assert new_telegram.decoded_values["raw"] == new_telegram_str
        assert new_telegram.decoded_values["section_zero"]["station_code"] == manual_hydro_station_uzbek.station_code
        assert new_telegram.decoded_values["section_zero"]["station_name"] == manual_hydro_station_uzbek.name
        assert new_telegram.organization == organization_uzbek
        assert new_telegram.station_code == manual_hydro_station_uzbek.station_code

    def test_copy_metrics_for_no_existing_metrics(
        self, organization_kyrgyz, organization_uzbek, manual_hydro_station_kyrgyz, manual_hydro_station_uzbek
    ):
        assert HydrologicalMetric.objects.count() == 0

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WLD", "WDD"], ["M"])

        assert HydrologicalMetric.objects.count() == 0

    def test_copy_metrics_for_unknown_metric_name(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
        water_discharge_manual_hydro_station_kyrgyz,
        water_level_manual_hydro_station_uzbek,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 2
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["BBB"], ["M"])

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 2
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

    def test_copy_metrics_for_only_copies_specified_metrics(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
        water_level_manual_hydro_station_uzbek,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WDD"], ["M"])

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

    def test_copy_metrics_for_only_copies_specified_value_types(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
        water_level_manual_hydro_station_uzbek,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WLD"], ["M"])

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 2

    def test_copy_metrics_with_negative_offset_factor_decreases_value(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 0

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WLD"], ["M"], -0.1)

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        new_metric = HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).first()

        assert new_metric.station_id == manual_hydro_station_uzbek.id
        assert new_metric.avg_value == water_level_manual_hydro_station_kyrgyz.avg_value * 0.9

    def test_copy_metrics_with_positive_offset_factor_increases_value(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 0

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WLD"], ["M"], 0.2)

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        new_metric = HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).first()

        assert new_metric.station_id == manual_hydro_station_uzbek.id
        assert new_metric.avg_value == water_level_manual_hydro_station_kyrgyz.avg_value * 1.2

    def test_copy_metric_copies_ignores_metrics_outside_of_date_range(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 0

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-09-02"
        )
        anonymizer.copy_metrics(["WLD"], ["M"])

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 0

    def test_copy_metrics_copies_entire_metric(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_discharge_manual_hydro_station_kyrgyz,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 0

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WDD"], ["M"])

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 1
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        new_metric = HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).first()

        assert new_metric.station_id == manual_hydro_station_uzbek.id
        assert round(new_metric.avg_value, 2) == round(water_discharge_manual_hydro_station_kyrgyz.avg_value, 2)
        assert round(new_metric.min_value, 2) == round(water_discharge_manual_hydro_station_kyrgyz.min_value, 2)
        assert round(new_metric.max_value, 2) == round(water_discharge_manual_hydro_station_kyrgyz.max_value, 2)
        assert new_metric.value_code == water_discharge_manual_hydro_station_kyrgyz.value_code
        assert new_metric.timestamp_local == water_discharge_manual_hydro_station_kyrgyz.timestamp_local
        assert new_metric.timestamp == water_discharge_manual_hydro_station_kyrgyz.timestamp
        assert new_metric.sensor_identifier == water_discharge_manual_hydro_station_kyrgyz.sensor_identifier
        assert new_metric.sensor_type == water_discharge_manual_hydro_station_kyrgyz.sensor_type
        assert new_metric.source_type == water_discharge_manual_hydro_station_kyrgyz.source_type
        assert new_metric.source_id == water_discharge_manual_hydro_station_kyrgyz.source_id
        assert new_metric.unit == water_discharge_manual_hydro_station_kyrgyz.unit
        assert new_metric.value_type == water_discharge_manual_hydro_station_kyrgyz.value_type
        assert new_metric.metric_name == water_discharge_manual_hydro_station_kyrgyz.metric_name

    def test_copy_metrics_copies_multiple_metrics(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_hydro_station_kyrgyz,
        manual_hydro_station_uzbek,
        water_discharge_manual_hydro_station_kyrgyz,
        water_level_manual_hydro_station_uzbek,
        water_level_manual_hydro_station_kyrgyz,
    ):
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 2
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "hydro", manual_hydro_station_kyrgyz.id, manual_hydro_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["WDD", "WLD"], ["M"])

        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz).count() == 2
        assert HydrologicalMetric.objects.filter(station=manual_hydro_station_uzbek).count() == 3

    def test_copy_meteo_metrics_ignores_metrics_outside_of_date_range(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_meteo_station_kyrgyz,
        manual_meteo_station_uzbek,
        precipitation_meteo_station_kyrgyz,
        temperature_meteo_station_uzbek,
    ):
        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_kyrgyz).count() == 1
        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "meteo", manual_meteo_station_kyrgyz.id, manual_meteo_station_uzbek.id, "2024-09-03"
        )
        anonymizer.copy_metrics(["ATDCA", "PDCA"], ["M"])

        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_kyrgyz).count() == 1
        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_uzbek).count() == 1

    def test_copy_metrics_for_meteo_metrics(
        self,
        organization_kyrgyz,
        organization_uzbek,
        manual_meteo_station_kyrgyz,
        manual_meteo_station_uzbek,
        precipitation_meteo_station_kyrgyz,
        temperature_meteo_station_uzbek,
    ):
        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_kyrgyz).count() == 1
        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_uzbek).count() == 1

        anonymizer = MetricsDataAnonymizer(
            "meteo", manual_meteo_station_kyrgyz.id, manual_meteo_station_uzbek.id, "2024-08-01"
        )
        anonymizer.copy_metrics(["ATDCA", "PDCA"], ["M"])

        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_kyrgyz).count() == 1
        assert MeteorologicalMetric.objects.filter(station=manual_meteo_station_uzbek).count() == 2
