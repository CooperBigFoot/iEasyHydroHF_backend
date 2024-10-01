import datetime as dt

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.estimations.models import (
    DischargeModel,
    EstimationsWaterDischargeDaily,
    EstimationsWaterDischargeDailyAverage,
    EstimationsWaterLevelDailyAverage,
)
from sapphire_backend.metrics.choices import (
    HydrologicalMeasurementType,
    HydrologicalMetricName,
)
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.telegrams.utils import custom_ceil, custom_round
from sapphire_backend.utils.aggregations import custom_average
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.db_helper import refresh_continuous_aggregate


class TestGetTelegramOverviewDataProcessingOverviewAPI:
    def test_get_telegram_overview_data_processing_overview(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        )

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

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

    def test_get_multiple_telegram_overview_data_processing_overview_keys(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station1_code = manual_hydro_station_kyrgyz.station_code
        station2_code = manual_second_hydro_station_kyrgyz.station_code

        # to simplify the test logic, make sure the telegrams are ordered by station code
        telegrams = [
            {
                "raw": f"{station1_code} 01082 10251 20022 30249 45820 52020 51210 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{station1_code} 02082 10261 20010 30256 46822 51210 00100="},
            {
                "raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100 "
                f"96607 10150 23050 32521 40162 50308="
            },
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100 " f"98805 111// 20013 30300="},
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert set(res["data_processing_overview"].keys()) == {station1_code, station2_code}

    def test_multi_telegram_consecutive_dates_single_station(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code = manual_hydro_station_kyrgyz.station_code

        telegrams = [
            {"raw": f"{station_code} 01082 10251 20022 30249="},
            {"raw": f"{station_code} 02082 10261 20010 30259="},
            {"raw": f"{station_code} 03082 10271 20010 30269="},
        ]

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        EXPECTED_DATES = ["2020-03-31", "2020-04-01", "2020-04-02", "2020-04-03"]

        assert dp_overview[station_code][0][0] == EXPECTED_DATES[0]
        assert dp_overview[station_code][1][0] == EXPECTED_DATES[1]
        assert dp_overview[station_code][2][0] == EXPECTED_DATES[2]
        assert dp_overview[station_code][3][0] == EXPECTED_DATES[3]

    def test_multi_telegram_non_consecutive_dates_single_station(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code = manual_hydro_station_kyrgyz.station_code

        telegrams = [
            {"raw": f"{station_code} 01082 10251 20022 30249="},
            {"raw": f"{station_code} 05082 10261 20010 30259="},
        ]
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        EXPECTED_DATES = ["2020-03-31", "2020-04-01", "2020-04-04", "2020-04-05"]

        assert dp_overview[station_code][0][0] == EXPECTED_DATES[0]
        assert dp_overview[station_code][1][0] == EXPECTED_DATES[1]
        assert dp_overview[station_code][2][0] == EXPECTED_DATES[2]
        assert dp_overview[station_code][3][0] == EXPECTED_DATES[3]

    def test_multi_telegram_mix_dates_multi_station(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code1 = manual_hydro_station_kyrgyz.station_code
        station_code2 = manual_second_meteo_station_kyrgyz.station_code

        # mix of consecutive and non-consecutive telegrams
        telegrams = [
            {"raw": f"{station_code1} 01082 10251 20022 30249="},
            {"raw": f"{station_code1} 02082 10261 20010 30259="},
            {"raw": f"{station_code1} 03082 10271 20010 30269="},
            {"raw": f"{station_code1} 04082 10181 20010 30279="},
            {"raw": f"{station_code2} 01082 10151 20010 30149="},
            {"raw": f"{station_code2} 02082 10161 20010 30159="},
            {"raw": f"{station_code2} 10082 10171 20010 30169="},
            {"raw": f"{station_code2} 13082 10181 20010 30179="},
        ]

        EXPECTED_DATES_STATION_1 = ["2020-03-31", "2020-04-01", "2020-04-02", "2020-04-03", "2020-04-04"]
        EXPECTED_DATES_STATION_2 = [
            "2020-03-31",
            "2020-04-01",
            "2020-04-02",
            "2020-04-09",
            "2020-04-10",
            "2020-04-12",
            "2020-04-13",
        ]

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        for idx, expected_date in enumerate(EXPECTED_DATES_STATION_1):
            assert dp_overview[station_code1][idx][0] == expected_date

        for idx, expected_date in enumerate(EXPECTED_DATES_STATION_2):
            assert dp_overview[station_code2][idx][0] == expected_date

    def test_multi_telegram_mix_dates_multi_station_section_two(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code1 = manual_hydro_station_kyrgyz.station_code
        station_code2 = manual_second_meteo_station_kyrgyz.station_code

        # mix of consecutive and non-consecutive telegrams
        telegrams = [
            {
                "raw": f"{station_code1} 11082 10172 20000 30175 92210 10172 20022 30176 92209 10174 20011 30178 92202 10174 20011 30178="
            },
            {
                "raw": f"{station_code2} 20082 10272 20000 30275 92219 10282 20022 30286 92218 10254 20011 30258 92217 10124 20011 30248="
            },
        ]

        EXPECTED_DATES_STATION_1 = ["2020-04-01", "2020-04-02", "2020-04-08", "2020-04-09", "2020-04-10", "2020-04-11"]
        EXPECTED_DATES_STATION_2 = [
            "2020-03-16",
            "2020-03-17",
            "2020-03-18",
            "2020-03-19",
            "2020-03-20",
        ]

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        for idx, expected_date in enumerate(EXPECTED_DATES_STATION_1):
            assert dp_overview[station_code1][idx][0] == expected_date

        for idx, expected_date in enumerate(EXPECTED_DATES_STATION_2):
            assert dp_overview[station_code2][idx][0] == expected_date

    def test_single_telegram_morning_evening_new_metrics(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code = manual_hydro_station_kyrgyz.station_code

        telegram = f"{station_code} 01082 10251 20022 30249="

        discharge_model = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model.save()

        parser = KN15TelegramParser(telegram, organization_kyrgyz.uuid)
        decoded_data = parser.parse()
        telegram_day_smart = SmartDatetime(
            decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=False
        )

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        assert len(dp_overview[station_code]) == 2
        assert dp_overview[station_code][0][0] == telegram_day_smart.previous_local.date().isoformat()
        assert (
            dp_overview[station_code][0][1]["evening"]["water_level_new"]
            == decoded_data["section_one"]["water_level_20h_period"]
        )
        assert dp_overview[station_code][0][1]["evening"]["discharge_new"] == custom_round(
            discharge_model.estimate_discharge(decoded_data["section_one"]["water_level_20h_period"]), 1
        )

        assert dp_overview[station_code][1][0] == telegram_day_smart.local.date().isoformat()
        assert (
            dp_overview[station_code][1][1]["morning"]["water_level_new"]
            == decoded_data["section_one"]["morning_water_level"]
        )
        assert dp_overview[station_code][1][1]["morning"]["discharge_new"] == custom_round(
            discharge_model.estimate_discharge(decoded_data["section_one"]["morning_water_level"]), 1
        )

    def test_multi_telegram_single_station_new_metrics(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code = manual_hydro_station_kyrgyz.station_code

        discharge_model = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model.save()
        # telegrams must be ordered by date ASC in order to simplify the test logic
        telegrams = [
            {"raw": f"{station_code} 01082 10251 20022 30249="},
            {"raw": f"{station_code} 02082 10261 20010 30259="},
            {"raw": f"{station_code} 03082 10271 20010 30269="},
            {"raw": f"{station_code} 04082 10281 20010 30279="},
        ]

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        expected_evening_water_level_new = {}
        expected_evening_discharge_new = {}
        expected_morning_water_level_new = {}
        expected_morning_discharge_new = {}

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(
                decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=False
            )
            telegram_date = telegram_day_smart.local.date().isoformat()
            telegram_previous_date = telegram_day_smart.previous_local.date().isoformat()

            expected_morning_water_level_new[telegram_date] = decoded_data["section_one"]["morning_water_level"]
            expected_morning_discharge_new[telegram_date] = custom_round(
                discharge_model.estimate_discharge(decoded_data["section_one"]["morning_water_level"]), 1
            )

            expected_evening_water_level_new[telegram_previous_date] = decoded_data["section_one"][
                "water_level_20h_period"
            ]
            expected_evening_discharge_new[telegram_previous_date] = custom_round(
                discharge_model.estimate_discharge(decoded_data["section_one"]["water_level_20h_period"]), 1
            )

        for date, metrics in dp_overview[station_code]:
            expected_average_water_level_new = custom_ceil(
                custom_average(
                    [
                        expected_morning_water_level_new.get(date, None),
                        expected_evening_water_level_new.get(date, None),
                    ]
                )
            )
            expected_average_discharge_new = custom_round(
                discharge_model.estimate_discharge(expected_average_water_level_new), 1
            )

            assert metrics["morning"]["water_level_new"] == expected_morning_water_level_new.get(date, None)
            assert metrics["morning"]["discharge_new"] == expected_morning_discharge_new.get(date, None)
            assert metrics["evening"]["water_level_new"] == expected_evening_water_level_new.get(date, None)
            assert metrics["evening"]["discharge_new"] == expected_evening_discharge_new.get(date, None)
            assert metrics["average"]["water_level_new"] == expected_average_water_level_new
            assert metrics["average"]["discharge_new"] == expected_average_discharge_new

    def test_single_telegram_single_station_section_two(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code = manual_hydro_station_kyrgyz.station_code

        discharge_model = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model.save()
        INPUT_TELEGRAM = f"{station_code} 11082 10215 20100 30210 92210 10205 20100 30200 92209 10195 20100 30190 92208 10185 20100 30180="

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": INPUT_TELEGRAM}]},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        expected_evening_water_level_new = {}
        expected_evening_discharge_new = {}
        expected_morning_water_level_new = {}
        expected_morning_discharge_new = {}

        parser = KN15TelegramParser(INPUT_TELEGRAM, organization_kyrgyz.uuid)
        decoded_data = parser.parse()
        section_one_two = sorted([decoded_data["section_one"]] + decoded_data["section_two"], key=lambda x: x["date"])

        for decoded_entry in section_one_two:
            day_smart = SmartDatetime(decoded_entry["date"], parser.hydro_station, tz_included=False)
            section_date = day_smart.local.date().isoformat()
            section_previous_date = day_smart.previous_local.date().isoformat()

            expected_morning_water_level_new[section_date] = decoded_entry["morning_water_level"]
            expected_morning_discharge_new[section_date] = custom_round(
                discharge_model.estimate_discharge(decoded_entry["morning_water_level"]), 1
            )

            expected_evening_water_level_new[section_previous_date] = decoded_entry["water_level_20h_period"]
            expected_evening_discharge_new[section_previous_date] = custom_round(
                discharge_model.estimate_discharge(decoded_entry["water_level_20h_period"]), 1
            )

        for date, metrics in dp_overview[station_code]:
            expected_average_water_level_new = custom_ceil(
                custom_average(
                    [
                        expected_morning_water_level_new.get(date, None),
                        expected_evening_water_level_new.get(date, None),
                    ]
                )
            )
            expected_average_discharge_new = custom_round(
                discharge_model.estimate_discharge(expected_average_water_level_new), 1
            )

            assert metrics["morning"]["water_level_new"] == expected_morning_water_level_new.get(date, None)
            assert metrics["morning"]["discharge_new"] == expected_morning_discharge_new.get(date, None)
            assert metrics["evening"]["water_level_new"] == expected_evening_water_level_new.get(date, None)
            assert metrics["evening"]["discharge_new"] == expected_evening_discharge_new.get(date, None)
            assert metrics["average"]["water_level_new"] == expected_average_water_level_new
            assert metrics["average"]["discharge_new"] == expected_average_discharge_new

    def test_multi_telegram_single_station_section_two(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        station_code = manual_hydro_station_kyrgyz.station_code

        discharge_model = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model.save()
        telegrams = [
            {
                "raw": f"{station_code} 11082 10215 20100 30210 92210 10205 20100 30200 92209 10195 20100 30190 92208 10185 20100 30180="
            },
            {
                "raw": f"{station_code}  20082 10272 20000 30275 00003 92219 10282 20022 30286 00011 92218 10254 20011 30258 92217 10124 20011 30248="
            },
        ]

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        expected_evening_water_level_new = {}
        expected_evening_discharge_new = {}
        expected_morning_water_level_new = {}
        expected_morning_discharge_new = {}

        for telegram_entry in telegrams:
            parser = KN15TelegramParser(telegram_entry["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            section_one_two = sorted(
                [decoded_data["section_one"]] + decoded_data["section_two"], key=lambda x: x["date"]
            )

            for decoded_entry in section_one_two:
                day_smart = SmartDatetime(decoded_entry["date"], parser.hydro_station, tz_included=False)
                section_date = day_smart.local.date().isoformat()
                section_previous_date = day_smart.previous_local.date().isoformat()

                expected_morning_water_level_new[section_date] = decoded_entry["morning_water_level"]
                expected_morning_discharge_new[section_date] = custom_round(
                    discharge_model.estimate_discharge(decoded_entry["morning_water_level"]), 1
                )

                expected_evening_water_level_new[section_previous_date] = decoded_entry["water_level_20h_period"]
                expected_evening_discharge_new[section_previous_date] = custom_round(
                    discharge_model.estimate_discharge(decoded_entry["water_level_20h_period"]), 1
                )

        for date, metrics in dp_overview[station_code]:
            expected_average_water_level_new = custom_ceil(
                custom_average(
                    [
                        expected_morning_water_level_new.get(date, None),
                        expected_evening_water_level_new.get(date, None),
                    ]
                )
            )
            expected_average_discharge_new = custom_round(
                discharge_model.estimate_discharge(expected_average_water_level_new), 1
            )

            assert metrics["morning"]["water_level_new"] == expected_morning_water_level_new.get(date, None)
            assert metrics["morning"]["discharge_new"] == expected_morning_discharge_new.get(date, None)
            assert metrics["evening"]["water_level_new"] == expected_evening_water_level_new.get(date, None)
            assert metrics["evening"]["discharge_new"] == expected_evening_discharge_new.get(date, None)
            assert metrics["average"]["water_level_new"] == expected_average_water_level_new
            assert metrics["average"]["discharge_new"] == expected_average_discharge_new

    def test_multi_telegram_multi_station_check_new_metrics(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        """
        Test data processing overview _new metrics for new telegram candidates.
        """

        station_code1 = manual_hydro_station_kyrgyz.station_code
        station_code2 = manual_second_meteo_station_kyrgyz.station_code
        discharge_model = {}

        discharge_model[station_code1] = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model[station_code1].save()

        discharge_model[station_code2] = DischargeModel(
            name="Test discharge curve",
            param_a=20,
            param_b=2,
            param_c=0.002,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_second_hydro_station_kyrgyz,
        )
        discharge_model[station_code2].save()

        # telegrams must be ordered by date ASC in order to simplify the test logic
        telegrams = [
            {"raw": f"{station_code1} 01082 10251 20022 30249="},
            {"raw": f"{station_code1} 02082 10261 20010 30259="},
            {"raw": f"{station_code1} 03082 10271 20010 30269="},
            {"raw": f"{station_code1} 04082 10281 20010 30279="},
            {"raw": f"{station_code2} 01082 10151 20010 30149="},
            {"raw": f"{station_code2} 02082 10161 20010 30159="},
            {"raw": f"{station_code2} 10082 10171 20010 30169="},
            {"raw": f"{station_code2} 13082 10181 20010 30179="},
        ]
        stations = [manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz]
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        expected_evening_water_level_new = {station_code1: {}, station_code2: {}}
        expected_evening_discharge_new = {station_code1: {}, station_code2: {}}
        expected_morning_water_level_new = {station_code1: {}, station_code2: {}}
        expected_morning_discharge_new = {station_code1: {}, station_code2: {}}

        for telegram in telegrams:
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            s_code = decoded_data["section_zero"]["station_code"]

            telegram_day_smart = SmartDatetime(
                decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=False
            )
            telegram_date = telegram_day_smart.local.date().isoformat()
            telegram_previous_date = telegram_day_smart.previous_local.date().isoformat()

            expected_morning_water_level_new[s_code][telegram_date] = decoded_data["section_one"][
                "morning_water_level"
            ]
            expected_morning_discharge_new[s_code][telegram_date] = custom_round(
                discharge_model[s_code].estimate_discharge(decoded_data["section_one"]["morning_water_level"]), 1
            )

            expected_evening_water_level_new[s_code][telegram_previous_date] = decoded_data["section_one"][
                "water_level_20h_period"
            ]
            expected_evening_discharge_new[s_code][telegram_previous_date] = custom_round(
                discharge_model[s_code].estimate_discharge(decoded_data["section_one"]["water_level_20h_period"]), 1
            )

        for station in stations:
            station_code = station.station_code
            for date, metrics in dp_overview[station_code]:
                expected_average_water_level_new = custom_ceil(
                    custom_average(
                        [
                            expected_morning_water_level_new[station_code].get(date, None),
                            expected_evening_water_level_new[station_code].get(date, None),
                        ]
                    )
                )
                expected_average_discharge_new = custom_round(
                    discharge_model[station_code].estimate_discharge(expected_average_water_level_new), 1
                )

                assert metrics["morning"]["water_level_new"] == expected_morning_water_level_new[station_code].get(
                    date, None
                )
                assert metrics["morning"]["discharge_new"] == expected_morning_discharge_new[station_code].get(
                    date, None
                )
                assert metrics["evening"]["water_level_new"] == expected_evening_water_level_new[station_code].get(
                    date, None
                )
                assert metrics["evening"]["discharge_new"] == expected_evening_discharge_new[station_code].get(
                    date, None
                )
                assert metrics["average"]["water_level_new"] == expected_average_water_level_new
                assert metrics["average"]["discharge_new"] == expected_average_discharge_new

    @pytest.mark.django_db(transaction=True)
    def test_multi_telegram_multi_station_check_old_metrics(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        """
        Test saving telegrams and seeing them as old values in the data processing overview afterwards.
        """

        station_code1 = manual_hydro_station_kyrgyz.station_code
        station_code2 = manual_second_meteo_station_kyrgyz.station_code
        stations = [manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz]

        discharge_model = {}
        discharge_model[station_code1] = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model[station_code1].save()

        discharge_model[station_code2] = DischargeModel(
            name="Test discharge curve",
            param_a=20,
            param_b=2,
            param_c=0.002,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_second_hydro_station_kyrgyz,
        )
        discharge_model[station_code2].save()

        telegrams = [
            {"raw": f"{station_code1} 01082 10251 20022 30249="},
            {"raw": f"{station_code1} 02082 10261 20010 30259="},
            {"raw": f"{station_code1} 03082 10271 20010 30269="},
            {"raw": f"{station_code1} 04082 10281 20010 30279="},
            {"raw": f"{station_code2} 01082 10151 20010 30149="},
            {"raw": f"{station_code2} 02082 10161 20010 30159="},
            {"raw": f"{station_code2} 10082 10171 20010 30169="},
            {"raw": f"{station_code2} 13082 10181 20010 30179="},
        ]

        # first save telegrams
        regular_user_kyrgyz_api_client.post(
            f"/api/v1/telegrams/{organization_kyrgyz.uuid}/save-input-telegrams",
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        refresh_continuous_aggregate()

        response = regular_user_kyrgyz_api_client.post(
            f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview",
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        dp_overview = res["data_processing_overview"]

        for station in stations:
            station_code = station.station_code
            for date, metrics in dp_overview[station_code]:
                smart_dt = SmartDatetime(date, station, tz_included=False)

                expected_morning_water_level_old = getattr(
                    HydrologicalMetric.objects.filter(
                        station=station,
                        timestamp_local=smart_dt.morning_local,
                        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                        value_type=HydrologicalMeasurementType.MANUAL,
                    ).first(),
                    "avg_value",
                    None,
                )

                expected_evening_water_level_old = getattr(
                    HydrologicalMetric.objects.filter(
                        station=station,
                        timestamp_local=smart_dt.evening_local,
                        metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
                        value_type=HydrologicalMeasurementType.MANUAL,
                    ).first(),
                    "avg_value",
                    None,
                )

                expected_average_water_level_old = getattr(
                    EstimationsWaterLevelDailyAverage.objects.filter(
                        station=station,
                        timestamp_local=smart_dt.midday_local,
                    ).first(),
                    "avg_value",
                    None,
                )

                expected_morning_discharge_old = getattr(
                    EstimationsWaterDischargeDaily.objects.filter(
                        station=station,
                        timestamp_local=smart_dt.morning_local,
                    ).first(),
                    "avg_value",
                    None,
                )

                expected_evening_discharge_old = getattr(
                    EstimationsWaterDischargeDaily.objects.filter(
                        station=station,
                        timestamp_local=smart_dt.evening_local,
                    ).first(),
                    "avg_value",
                    None,
                )

                expected_average_discharge_old = getattr(
                    EstimationsWaterDischargeDailyAverage.objects.filter(
                        station=station,
                        timestamp_local=smart_dt.midday_local,
                    ).first(),
                    "avg_value",
                    None,
                )

                assert metrics["morning"]["water_level_old"] == expected_morning_water_level_old
                assert metrics["morning"]["discharge_old"] == custom_round(expected_morning_discharge_old, 1)
                assert metrics["evening"]["water_level_old"] == expected_evening_water_level_old
                assert metrics["evening"]["discharge_old"] == custom_round(expected_evening_discharge_old, 1)
                assert metrics["average"]["water_level_old"] == expected_average_water_level_old
                assert metrics["average"]["discharge_old"] == custom_round(expected_average_discharge_old, 1)
