import datetime as dt
from unittest.mock import patch

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.utils.datetime_helper import SmartDatetime


class TestTelegramsAPI:
    @patch("sapphire_backend.telegrams.parser.dt")
    def test_get_telegram_overview(
        self,
        mock_datetime,
        authenticated_regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        mock_datetime.now.return_value = dt.datetime(2020, 4, 15, tzinfo=manual_meteo_station_kyrgyz.timezone)
        mock_datetime.side_effect = lambda *args, **kw: dt.datetime(*args, **kw)

        station_code = manual_hydro_station_kyrgyz.station_code

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        input_telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        )

        parser = KN15TelegramParser(
            input_telegram,
            organization_kyrgyz.uuid,
        )
        decoded_data = parser.parse()

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": input_telegram}]},
            content_type="application/json",
        )
        res = response.json()
        expected_keys = {
            "daily_overview",
            "data_processing_overview",
            "save_data_overview",
            "reported_discharge_points",
            "discharge_codes",
            "meteo_codes",
            "errors",
        }

        actual_keys = set(res.keys())

        assert response.status_code == 200
        assert actual_keys == expected_keys, f"Expected keys {expected_keys}, but got {actual_keys}"

        # errors
        assert len(res["errors"]) == 0

        # daily_overview
        assert len(res["daily_overview"]) == 1
        assert res["daily_overview"][0]["station_code"] == manual_hydro_station_kyrgyz.station_code
        assert res["daily_overview"][0]["station_name"] == manual_hydro_station_kyrgyz.name
        assert res["daily_overview"][0]["telegram_day_date"] == "2020-04-01"
        assert res["daily_overview"][0]["previous_day_date"] == "2020-03-31"
        assert (
            res["daily_overview"][0]["section_one"]["morning_water_level"]
            == decoded_data["section_one"]["morning_water_level"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["water_level_20h_period"]
            == decoded_data["section_one"]["water_level_20h_period"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["water_temperature"]
            == decoded_data["section_one"]["water_temperature"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["air_temperature"]
            == decoded_data["section_one"]["air_temperature"]
        )
        assert len(res["daily_overview"][0]["section_one"]["ice_phenomena"]) == len(
            decoded_data["section_one"]["ice_phenomena"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["ice_phenomena"][0]["code"]
            == decoded_data["section_one"]["ice_phenomena"][0]["code"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["ice_phenomena"][0]["intensity"]
            == decoded_data["section_one"]["ice_phenomena"][0]["intensity"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["daily_precipitation"]["precipitation"]
            == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["daily_precipitation"]["duration_code"]
            == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
        )
        assert res["daily_overview"][0]["section_six"] == decoded_data["section_six"]
        assert res["daily_overview"][0]["section_eight"] == decoded_data["section_eight"]
        # data_processing_overview
        assert list(res["data_processing_overview"].keys()) == [station_code]
        assert len(res["data_processing_overview"][station_code]) == 2
        assert res["data_processing_overview"][station_code][0][0] == "2020-03-31"
        assert (
            res["data_processing_overview"][station_code][0][1]["evening"]["water_level_new"]
            == decoded_data["section_one"]["water_level_20h_period"]
        )
        assert res["data_processing_overview"][station_code][1][0] == "2020-04-01"
        assert (
            res["data_processing_overview"][station_code][1][1]["morning"]["water_level_new"]
            == decoded_data["section_one"]["morning_water_level"]
        )

        # save_data_overview
        assert len(res["save_data_overview"]) == 1
        assert res["save_data_overview"][0]["station_code"] == manual_hydro_station_kyrgyz.station_code
        assert res["save_data_overview"][0]["station_name"] == manual_hydro_station_kyrgyz.name
        assert res["save_data_overview"][0]["telegram_day_date"] == "2020-04-01"
        assert res["save_data_overview"][0]["previous_day_date"] == "2020-03-31"
        assert res["save_data_overview"][0]["type"] == "discharge / meteo"
        assert (
            res["save_data_overview"][0]["section_one"]["morning_water_level"]
            == decoded_data["section_one"]["morning_water_level"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["water_level_20h_period"]
            == decoded_data["section_one"]["water_level_20h_period"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["water_temperature"]
            == decoded_data["section_one"]["water_temperature"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["air_temperature"]
            == decoded_data["section_one"]["air_temperature"]
        )
        assert len(res["save_data_overview"][0]["section_one"]["ice_phenomena"]) == len(
            decoded_data["section_one"]["ice_phenomena"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["ice_phenomena"][0]["code"]
            == decoded_data["section_one"]["ice_phenomena"][0]["code"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["ice_phenomena"][0]["intensity"]
            == decoded_data["section_one"]["ice_phenomena"][0]["intensity"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["daily_precipitation"]["precipitation"]
            == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["daily_precipitation"]["duration_code"]
            == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
        )
        assert res["save_data_overview"][0]["section_six"] == decoded_data["section_six"]
        assert res["save_data_overview"][0]["section_eight"] == decoded_data["section_eight"]

        # reported_discharge_points
        assert list(res["reported_discharge_points"].keys()) == [station_code]
        for idx, section_six_entry in enumerate(decoded_data["section_six"]):
            assert res["reported_discharge_points"][station_code][idx]["date"] == section_six_entry["date"]
            assert res["reported_discharge_points"][station_code][idx]["h"] == float(section_six_entry["water_level"])
            assert res["reported_discharge_points"][station_code][idx]["q"] == float(section_six_entry["discharge"])

        # discharge_codes
        assert len(res["discharge_codes"]) == 1
        assert res["discharge_codes"][0] == [
            manual_hydro_station_kyrgyz.station_code,
            str(manual_hydro_station_kyrgyz.uuid),
        ]

        # meteo_codes
        assert len(res["meteo_codes"]) == 1
        assert res["meteo_codes"][0] == [
            manual_meteo_station_kyrgyz.station_code,
            str(manual_meteo_station_kyrgyz.uuid),
        ]

    @patch("sapphire_backend.telegrams.parser.dt")
    def test_save_input_telegrams(
        self,
        mock_datetime,
        authenticated_regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        dt_now = dt.datetime(2020, 4, 15, tzinfo=manual_meteo_station_kyrgyz.timezone)
        mock_datetime.now.return_value = dt_now
        mock_datetime.side_effect = lambda *args, **kw: dt.datetime(*args, **kw)

        station_code = manual_hydro_station_kyrgyz.station_code
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        input_telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        )

        parser = KN15TelegramParser(
            input_telegram,
            organization_kyrgyz.uuid,
        )
        decoded_data = parser.parse()

        telegram_day_smart = SmartDatetime(
            decoded_data["section_zero"]["date"], manual_hydro_station_kyrgyz, tz_included=False
        )

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": input_telegram}]},
            content_type="application/json",
        )
        res = response.json()

        assert response.status_code == 201
        assert res["code"] == "success"

        # section one metrics
        assert (
            HydrologicalMetric.objects.filter(
                station=manual_hydro_station_kyrgyz,
                timestamp_local=telegram_day_smart.morning_local,
                avg_value=float(decoded_data["section_one"]["morning_water_level"]),
                metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                value_type=HydrologicalMeasurementType.MANUAL,
            ).exists()
            is True
        )

        assert (
            HydrologicalMetric.objects.filter(
                station=manual_hydro_station_kyrgyz,
                timestamp_local=telegram_day_smart.previous_evening_local,
                avg_value=float(decoded_data["section_one"]["water_level_20h_period"]),
                metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                value_type=HydrologicalMeasurementType.MANUAL,
            ).exists()
            is True
        )

        assert (
            HydrologicalMetric.objects.filter(
                timestamp_local=telegram_day_smart.morning_local,
                avg_value=float(decoded_data["section_one"]["air_temperature"]),
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.AIR_TEMPERATURE,
                station=manual_hydro_station_kyrgyz,
            ).exists()
            is True
        )

        assert (
            HydrologicalMetric.objects.filter(
                timestamp_local=telegram_day_smart.morning_local,
                avg_value=float(decoded_data["section_one"]["water_temperature"]),
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.WATER_TEMPERATURE,
                station=manual_hydro_station_kyrgyz,
            ).exists()
            is True
        )

        assert (
            HydrologicalMetric.objects.filter(
                timestamp_local__date=telegram_day_smart.morning_local.date(),
                avg_value=float(decoded_data["section_one"]["ice_phenomena"][0]["intensity"]),
                value_code=decoded_data["section_one"]["ice_phenomena"][0]["code"],
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                station=manual_hydro_station_kyrgyz,
            ).exists()
            is True
        )

        assert (
            HydrologicalMetric.objects.filter(
                timestamp_local=telegram_day_smart.previous_evening_local,
                avg_value=float(decoded_data["section_one"]["daily_precipitation"]["precipitation"]),
                value_code=decoded_data["section_one"]["daily_precipitation"]["duration_code"],
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.PRECIPITATION_DAILY,
                station=manual_hydro_station_kyrgyz,
            ).exists()
            is True
        )

        # section six metrics
        for section_six_entry in decoded_data["section_six"]:
            timestamp_decoded = section_six_entry["date"]
            assert (
                HydrologicalMetric.objects.filter(
                    timestamp=timestamp_decoded,
                    avg_value=float(section_six_entry["water_level"]),
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DECADAL,
                    station=manual_hydro_station_kyrgyz,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    timestamp=timestamp_decoded,
                    avg_value=float(section_six_entry["discharge"]),
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                    station=manual_hydro_station_kyrgyz,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    timestamp=timestamp_decoded,
                    avg_value=float(section_six_entry["cross_section_area"]),
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.RIVER_CROSS_SECTION_AREA,
                    station=manual_hydro_station_kyrgyz,
                ).exists()
                is True
            )

            if section_six_entry["maximum_depth"] is not None:
                assert (
                    HydrologicalMetric.objects.filter(
                        timestamp=timestamp_decoded,
                        avg_value=float(section_six_entry["maximum_depth"]),
                        value_type=HydrologicalMeasurementType.MANUAL,
                        metric_name=HydrologicalMetricName.MAXIMUM_DEPTH,
                        station=manual_hydro_station_kyrgyz,
                    ).exists()
                    is True
                )

        # section eight metrics
        assert (
            MeteorologicalMetric.objects.filter(
                timestamp=decoded_data["section_eight"]["timestamp"],
                value=float(decoded_data["section_eight"]["precipitation"]),
                value_type=MeteorologicalMeasurementType.MANUAL,
                metric_name=MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE
                if decoded_data["section_eight"]["decade"] != 4
                else MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE,
                station=manual_meteo_station_kyrgyz,
            ).exists()
            is True
        )

        assert (
            MeteorologicalMetric.objects.filter(
                timestamp=decoded_data["section_eight"]["timestamp"],
                value=float(decoded_data["section_eight"]["temperature"]),
                value_type=MeteorologicalMeasurementType.MANUAL,
                metric_name=MeteorologicalMetricName.AIR_TEMPERATURE_DECADE_AVERAGE
                if decoded_data["section_eight"]["decade"] != 4
                else MeteorologicalMetricName.AIR_TEMPERATURE_MONTH_AVERAGE,
                station=manual_meteo_station_kyrgyz,
            ).exists()
            is True
        )
