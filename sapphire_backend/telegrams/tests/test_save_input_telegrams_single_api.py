from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.utils.datetime_helper import SmartDatetime

INPUT_SINGLE_TELEGRAM = (
    "{station_code} 01082 10251 20022 30249 45820 51209 00100 "
    "96603 10150 23050 32521 40162 50313 "
    "96604 10250 22830 32436 52920 "
    "98805 111// 20013 30200="
)


class TestSingleTelegramSaveGeneralAPI:
    def test_save_input_telegrams_status_code(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_SINGLE_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert response.status_code == 201
        assert res["code"] == "success"


class TestSingleTelegramSaveSectionOneAPI:
    def test_save_input_telegrams_section_one_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_SINGLE_TELEGRAM.format(station_code=station_code)

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()

        telegram_day_smart = SmartDatetime(
            decoded_data["section_zero"]["date"], manual_hydro_station_kyrgyz, tz_included=False
        )

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
                timestamp_local=telegram_day_smart.previous_evening_local,
                avg_value=float(decoded_data["section_one"]["daily_precipitation"]["precipitation"]),
                value_code=decoded_data["section_one"]["daily_precipitation"]["duration_code"],
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.PRECIPITATION_DAILY,
                station=manual_hydro_station_kyrgyz,
            ).exists()
            is True
        )

    def test_save_input_telegrams_section_one_metrics_override_date(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        override_date = "2019-06-01"

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_SINGLE_TELEGRAM.format(station_code=station_code)

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram, "override_date": override_date}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()

        telegram_day_smart = SmartDatetime(override_date, manual_hydro_station_kyrgyz, tz_included=False)

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
                timestamp_local=telegram_day_smart.previous_evening_local,
                avg_value=float(decoded_data["section_one"]["daily_precipitation"]["precipitation"]),
                value_code=decoded_data["section_one"]["daily_precipitation"]["duration_code"],
                value_type=HydrologicalMeasurementType.MANUAL,
                metric_name=HydrologicalMetricName.PRECIPITATION_DAILY,
                station=manual_hydro_station_kyrgyz,
            ).exists()
            is True
        )


class TestSingleTelegramSaveSectionOneIcePhenomenaAPI:
    def test_save_input_telegrams_section_one_ice_phenomena_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station1_code = manual_hydro_station_kyrgyz.station_code

        telegram = {
            "raw": f"{station1_code} 01082 10251 20022 30249 45820 55008 51210 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        }

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [telegram]},
            content_type="application/json",
        )

        parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
        decoded_data = parser.parse()
        telegram_day_smart = SmartDatetime(
            decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=False
        )
        # in case of multiple ice phenomenas
        for ice_ph_entry in decoded_data["section_one"]["ice_phenomena"]:
            assert (
                HydrologicalMetric.objects.filter(
                    timestamp_local__date=telegram_day_smart.morning_local.date(),
                    avg_value=ice_ph_entry["intensity"] if ice_ph_entry["intensity"] else -1,
                    value_code=ice_ph_entry["code"],
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                    station=manual_hydro_station_kyrgyz,
                ).exists()
                is True
            )

    def test_save_input_telegrams_section_one_ice_phenomena_metrics_override_date(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        override_date = "2019-06-01"

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_SINGLE_TELEGRAM.format(station_code=station_code)

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram, "override_date": override_date}]},
            content_type="application/json",
        )
        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()

        telegram_day_smart = SmartDatetime(override_date, manual_hydro_station_kyrgyz, tz_included=False)

        for ice_ph_entry in decoded_data["section_one"]["ice_phenomena"]:
            assert (
                HydrologicalMetric.objects.filter(
                    timestamp_local__date=telegram_day_smart.morning_local.date(),
                    avg_value=ice_ph_entry["intensity"] if ice_ph_entry["intensity"] else -1,
                    value_code=ice_ph_entry["code"],
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                    station=manual_hydro_station_kyrgyz,
                ).exists()
                is True
            )


class TestSingleTelegramSaveSectionSixAPI:
    def test_save_input_telegrams_section_six_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_SINGLE_TELEGRAM.format(station_code=station_code)

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )
        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()

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


class TestSingleTelegramSaveSectionEightAPI:
    def test_save_input_telegrams_section_eight_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_SINGLE_TELEGRAM.format(station_code=station_code)

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )
        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()

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
