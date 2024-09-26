import pytest

from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
    MeteorologicalMeasurementType,
    MeteorologicalMetricName,
)
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.telegrams.models import TelegramStored
from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.users.conftest import get_api_client_for_user
from sapphire_backend.utils.datetime_helper import SmartDatetime

INPUT_MULTIPLE_TELEGRAMS = [
    {
        "raw": "12345 01082 10251 20022 30249 45820 52020 51210 00100 "
        "96603 10150 23050 32521 40162 50313 "
        "96604 10250 22830 32436 52920 "
        "98805 111// 20013 30200="
    },
    {"raw": "12345 02082 10261 20010 30256 46822 51210 00100="},
    {"raw": "12346 01082 10151 20010 30149 45820 55008 00100 " "96607 10150 23050 32521 40162 50308="},
    {"raw": "12346 02082 10161 20010 30156 46822 52121 00100 " "98805 111// 20013 30300="},
]


class TestMultipleTelegramSaveGeneralAPI:
    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 201),
            ("organization_admin_kyrgyz_api_client", 201),
            ("superadmin_kyrgyz_api_client", 201),
            ("superadmin_uzbek_api_client", 201),
        ],
    )
    def test_save_input_multi_telegrams_status_code(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        client,
        expected_status_code,
        request,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        client = request.getfixturevalue(client)

        response = client.post(
            endpoint,
            data={"telegrams": INPUT_MULTIPLE_TELEGRAMS},
            content_type="application/json",
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        "user",
        [
            "regular_user_kyrgyz",
            "organization_admin_kyrgyz",
            "superadmin_kyrgyz",
            "superadmin_uzbek",
        ],
    )
    def test_save_input_telegrams_creates_telegram_stored(
        self,
        user,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        request,
    ):
        user = request.getfixturevalue(user)
        client = get_api_client_for_user(user)
        telegrams = INPUT_MULTIPLE_TELEGRAMS
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"

        assert TelegramStored.objects.all().count() == 0

        client.post(
            endpoint,
            data={"telegrams": INPUT_MULTIPLE_TELEGRAMS},
            content_type="application/json",
        )

        queryset = TelegramStored.objects.all()
        assert queryset.count() == len(telegrams)

        for telegram in telegrams:
            assert queryset.filter(telegram=telegram["raw"], stored_by=user).exists() is True


class TestMultipleTelegramSaveSectionOneAPI:
    def test_save_input_multi_telegrams_section_one_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        telegrams = INPUT_MULTIPLE_TELEGRAMS

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": INPUT_MULTIPLE_TELEGRAMS},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(
                decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=False
            )

            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
                    timestamp_local=telegram_day_smart.morning_local,
                    avg_value=float(decoded_data["section_one"]["morning_water_level"]),
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                    value_type=HydrologicalMeasurementType.MANUAL,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
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
                    station=parser.hydro_station,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    timestamp_local=telegram_day_smart.morning_local,
                    avg_value=float(decoded_data["section_one"]["water_temperature"]),
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.WATER_TEMPERATURE,
                    station=parser.hydro_station,
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
                    station=parser.hydro_station,
                ).exists()
                is True
            )

    def test_save_input_multi_telegrams_section_one_metrics_override_date(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"

        telegrams = [
            {
                "raw": "12345 01082 10251 20022 30249 45820 52020 51210 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200=",
                "override_date": "2019-06-10",
            },
            {"raw": "12345 02082 10261 20010 30256 46822 51210 00100=", "override_date": "2019-06-11"},
            {
                "raw": "12346 01082 10151 20010 30149 45820 55008 00100 " "96607 10150 23050 32521 40162 50308=",
                "override_date": "2019-06-10",
            },
            {
                "raw": "12346 02082 10161 20010 30156 46822 52121 00100 " "98805 111// 20013 30300=",
                "override_date": "2019-08-26",
            },
        ]

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(telegram["override_date"], parser.hydro_station, tz_included=False)
            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
                    timestamp_local=telegram_day_smart.morning_local,
                    avg_value=float(decoded_data["section_one"]["morning_water_level"]),
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                    value_type=HydrologicalMeasurementType.MANUAL,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
                    timestamp_local=telegram_day_smart.previous_evening_local,
                    avg_value=float(decoded_data["section_one"]["water_level_20h_period"]),
                    metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                    value_type=HydrologicalMeasurementType.MANUAL,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
                    timestamp_local=telegram_day_smart.morning_local,
                    avg_value=float(decoded_data["section_one"]["air_temperature"]),
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.AIR_TEMPERATURE,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
                    timestamp_local=telegram_day_smart.morning_local,
                    avg_value=float(decoded_data["section_one"]["water_temperature"]),
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.WATER_TEMPERATURE,
                ).exists()
                is True
            )

            assert (
                HydrologicalMetric.objects.filter(
                    station=parser.hydro_station,
                    timestamp_local=telegram_day_smart.previous_evening_local,
                    avg_value=float(decoded_data["section_one"]["daily_precipitation"]["precipitation"]),
                    value_code=decoded_data["section_one"]["daily_precipitation"]["duration_code"],
                    value_type=HydrologicalMeasurementType.MANUAL,
                    metric_name=HydrologicalMetricName.PRECIPITATION_DAILY,
                ).exists()
                is True
            )


class TestMultipleTelegramSaveSectionOneIcePhenomenaAPI:
    def test_save_input_multi_telegrams_section_one_ice_phenomena_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"

        telegrams = [
            {
                "raw": "12345 01082 10251 20022 30249 45820 55008 51210 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": "12345 02082 10261 20010 30256 46822 51210 00100="},
            {"raw": "12346 01082 10151 20010 30149 45820 55008 00100 " "96607 10150 23050 32521 40162 50308="},
            {"raw": "12346 02082 10161 20010 30156 46822 52121 00100 " "98805 111// 20013 30300="},
        ]

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(
                decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=False
            )
            for ice_ph_entry in decoded_data["section_one"]["ice_phenomena"]:
                assert (
                    HydrologicalMetric.objects.filter(
                        timestamp_local__date=telegram_day_smart.morning_local.date(),
                        avg_value=ice_ph_entry["intensity"] if ice_ph_entry["intensity"] else -1,
                        value_code=ice_ph_entry["code"],
                        value_type=HydrologicalMeasurementType.MANUAL,
                        metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                        station=parser.hydro_station,
                    ).exists()
                    is True
                )

    def test_save_input_multi_telegrams_section_one_ice_phenomena_metrics_override_date(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"

        telegrams = [
            {
                "raw": "12345 01082 10251 20022 30249 45820 55008 51210 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200=",
                "override_date": "2019-06-10",
            },
            {"raw": "12345 02082 10261 20010 30256 46822 51210 00100=", "override_date": "2019-06-11"},
            {
                "raw": "12346 01082 10151 20010 30149 45820 55008 00100 " "96607 10150 23050 32521 40162 50308=",
                "override_date": "2019-06-10",
            },
            {
                "raw": "12346 02082 10161 20010 30156 46822 52121 00100 " "98805 111// 20013 30300=",
                "override_date": "2019-08-26",
            },
        ]

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(telegram["override_date"], parser.hydro_station, tz_included=False)
            for ice_ph_entry in decoded_data["section_one"]["ice_phenomena"]:
                assert (
                    HydrologicalMetric.objects.filter(
                        timestamp_local__date=telegram_day_smart.morning_local.date(),
                        avg_value=ice_ph_entry["intensity"] if ice_ph_entry["intensity"] else -1,
                        value_code=ice_ph_entry["code"],
                        value_type=HydrologicalMeasurementType.MANUAL,
                        metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                        station=parser.hydro_station,
                    ).exists()
                    is True
                )


class TestMultipleTelegramSaveSectionTwoAPI:
    def test_save_input_multi_telegrams_section_two_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        telegrams = [
            {
                "raw": "12345 20082 10572 20000 30575 "
                "92219 10582 20022 30586 45820 51209 52020 00011 "
                "92218 10554 20011 30558 "
                "92217 10524 20011 30555 40162 00003 "
                "96603 10150 23050 32521 46830 51308 00011 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {
                "raw": "12346 20082 10672 20000 30675 00003 "
                "92219 10682 20022 30686 40192 52020 00011 "
                "92218 10654 20011 30658 00100 "
                "92217 10624 20011 30666="
            },
        ]

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            for section_data in decoded_data["section_two"]:
                section_date = section_data["date"]
                section_date_smart = SmartDatetime(section_date, parser.hydro_station, tz_included=False)

                assert (
                    HydrologicalMetric.objects.filter(
                        station=parser.hydro_station,
                        timestamp_local=section_date_smart.morning_local,
                        avg_value=float(section_data["morning_water_level"]),
                        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                        value_type=HydrologicalMeasurementType.MANUAL,
                    ).exists()
                    is True
                )

                assert (
                    HydrologicalMetric.objects.filter(
                        station=parser.hydro_station,
                        timestamp_local=section_date_smart.previous_evening_local,
                        avg_value=float(section_data["water_level_20h_period"]),
                        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                        value_type=HydrologicalMeasurementType.MANUAL,
                    ).exists()
                    is True
                )

                if section_data["air_temperature"] is not None:
                    assert (
                        HydrologicalMetric.objects.filter(
                            timestamp_local=section_date_smart.morning_local,
                            avg_value=float(section_data["air_temperature"]),
                            value_type=HydrologicalMeasurementType.MANUAL,
                            metric_name=HydrologicalMetricName.AIR_TEMPERATURE,
                            station=parser.hydro_station,
                        ).exists()
                        is True
                    )

                    assert (
                        HydrologicalMetric.objects.filter(
                            timestamp_local=section_date_smart.morning_local,
                            avg_value=float(section_data["water_temperature"]),
                            value_type=HydrologicalMeasurementType.MANUAL,
                            metric_name=HydrologicalMetricName.WATER_TEMPERATURE,
                            station=parser.hydro_station,
                        ).exists()
                        is True
                    )
                if section_data["daily_precipitation"] is not None:
                    assert (
                        HydrologicalMetric.objects.filter(
                            timestamp_local=section_date_smart.previous_evening_local,
                            avg_value=float(section_data["daily_precipitation"]["precipitation"]),
                            value_code=section_data["daily_precipitation"]["duration_code"],
                            value_type=HydrologicalMeasurementType.MANUAL,
                            metric_name=HydrologicalMetricName.PRECIPITATION_DAILY,
                            station=parser.hydro_station,
                        ).exists()
                        is True
                    )

    def test_save_input_multi_telegrams_section_two_ice_phenomena(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"
        telegrams = [
            {
                "raw": "12345 20082 10572 20000 30575 "
                "92219 10582 20022 30586 45820 51209 52020 00011 "
                "92218 10554 20011 30558 "
                "92217 10524 20011 30555 40162 51308 00003 "
                "96603 10150 23050 32521 46830 51308 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {
                "raw": "12346 20082 10672 20000 30675 00003 "
                "92219 10682 20022 30686 40192 51610 00011 "
                "92218 10654 20011 30658 54141 00100 "
                "92217 10624 20011 30666="
            },
        ]

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            for section_data in decoded_data["section_two"]:
                section_date = section_data["date"]
                section_date_smart = SmartDatetime(section_date, parser.hydro_station, tz_included=False)
                for ice_ph_entry in section_data["ice_phenomena"]:
                    assert (
                        HydrologicalMetric.objects.filter(
                            timestamp_local__date=section_date_smart.morning_local.date(),
                            avg_value=ice_ph_entry["intensity"] if ice_ph_entry["intensity"] else -1,
                            value_code=ice_ph_entry["code"],
                            value_type=HydrologicalMeasurementType.MANUAL,
                            metric_name=HydrologicalMetricName.ICE_PHENOMENA_OBSERVATION,
                            station=parser.hydro_station,
                        ).exists()
                        is True
                    )


class TestMultipleTelegramSaveSectionSixAPI:
    def test_save_input_multi_telegrams_section_six_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"

        telegrams = INPUT_MULTIPLE_TELEGRAMS

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            for section_six_entry in decoded_data.get("section_six", []):
                timestamp_decoded = section_six_entry["date"]
                assert (
                    HydrologicalMetric.objects.filter(
                        timestamp=timestamp_decoded,
                        avg_value=float(section_six_entry["water_level"]),
                        value_type=HydrologicalMeasurementType.MANUAL,
                        metric_name=HydrologicalMetricName.WATER_LEVEL_DECADAL,
                        station=parser.hydro_station,
                    ).exists()
                    is True
                )

                assert (
                    HydrologicalMetric.objects.filter(
                        timestamp=timestamp_decoded,
                        avg_value=float(section_six_entry["discharge"]),
                        value_type=HydrologicalMeasurementType.MANUAL,
                        metric_name=HydrologicalMetricName.WATER_DISCHARGE_DAILY,
                        station=parser.hydro_station,
                    ).exists()
                    is True
                )

                assert (
                    HydrologicalMetric.objects.filter(
                        timestamp=timestamp_decoded,
                        avg_value=float(section_six_entry["cross_section_area"]),
                        value_type=HydrologicalMeasurementType.MANUAL,
                        metric_name=HydrologicalMetricName.RIVER_CROSS_SECTION_AREA,
                        station=parser.hydro_station,
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
                            station=parser.hydro_station,
                        ).exists()
                        is True
                    )


class TestMultipleTelegramSaveSectionEightAPI:
    def test_save_input_multi_telegrams_section_eight_metrics(
        self,
        datetime_kyrgyz_mock,
        regular_user_kyrgyz_api_client,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams"

        telegrams = INPUT_MULTIPLE_TELEGRAMS

        regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )
        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            if decoded_data.get("section_eight", False):
                assert (
                    MeteorologicalMetric.objects.filter(
                        timestamp=decoded_data["section_eight"]["timestamp"],
                        value=float(decoded_data["section_eight"]["precipitation"]),
                        value_type=MeteorologicalMeasurementType.MANUAL,
                        metric_name=MeteorologicalMetricName.PRECIPITATION_DECADE_AVERAGE
                        if decoded_data["section_eight"]["decade"] != 4
                        else MeteorologicalMetricName.PRECIPITATION_MONTH_AVERAGE,
                        station=parser.meteo_station,
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
                        station=parser.meteo_station,
                    ).exists()
                    is True
                )
