import datetime as dt

from zoneinfo import ZoneInfo

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.utils.aggregations import custom_average
from sapphire_backend.utils.datetime_helper import SmartDatetime
from sapphire_backend.utils.rounding import custom_ceil, custom_round

INPUT_TELEGRAM = (
    "{station_code} 01082 10251 20022 30249 45820 51209 00100 "
    "96603 10150 23050 32521 40162 50313 "
    "96604 10250 22830 32436 52920 "
    "98805 111// 20013 30200="
)


class TestGetTelegramOverviewSaveDataOverviewMetaAPI:
    def test_get_telegram_overview_save_data_overview_meta(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["save_data_overview"]) == 1
        assert res["save_data_overview"][0]["station_code"] == manual_hydro_station_kyrgyz.station_code
        assert res["save_data_overview"][0]["station_name"] == manual_hydro_station_kyrgyz.name
        assert res["save_data_overview"][0]["telegram_day_date"] == "2020-04-01"
        assert res["save_data_overview"][0]["type"] == "discharge / meteo"

    def test_get_multi_telegram_overview_save_data_overview_meta(
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

        # telegrams need to be ordered by station code and by telegram date in order to simplify the test logic
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
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100="},
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["save_data_overview"]) == len(telegrams)

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(
                decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=True
            )
            telegram_date = telegram_day_smart.local.date().isoformat()

            assert entry["station_code"] == decoded_data["section_zero"]["station_code"]
            assert entry["station_name"] == parser.hydro_station.name
            assert entry["telegram_day_date"] == telegram_date
            assert entry["type"] == "discharge / meteo" if decoded_data.get("section_eight", False) else "discharge"


class TestGetTelegramOverviewSaveDataOverviewSectionOneAPI:
    def test_get_single_telegram_overview_save_data_overview_section_one(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        assert res["save_data_overview"][0]["section_one_two"][0]["date"] == decoded_data["section_one"]["date"]
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["morning_water_level"]
            == decoded_data["section_one"]["morning_water_level"]
        )
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["water_level_20h_period"]
            == decoded_data["section_one"]["water_level_20h_period"]
        )
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["water_temperature"]
            == decoded_data["section_one"]["water_temperature"]
        )
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["air_temperature"]
            == decoded_data["section_one"]["air_temperature"]
        )

        assert (
            res["save_data_overview"][0]["section_one_two"][0]["daily_precipitation"]["precipitation"]
            == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
        )
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["daily_precipitation"]["duration_code"]
            == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
        )

    def test_get_multi_telegram_overview_save_data_overview_section_one(
        self,
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

        # telegrams need to be ordered by station code and by telegram date in order to simplify the test logic
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
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100="},
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert (
                entry["section_one_two"][0]["morning_water_level"]
                == decoded_data["section_one"]["morning_water_level"]
            )
            assert (
                entry["section_one_two"][0]["water_level_20h_period"]
                == decoded_data["section_one"]["water_level_20h_period"]
            )
            assert entry["section_one_two"][0]["water_temperature"] == decoded_data["section_one"]["water_temperature"]
            assert entry["section_one_two"][0]["air_temperature"] == decoded_data["section_one"]["air_temperature"]
            assert (
                entry["section_one_two"][0]["daily_precipitation"]["precipitation"]
                == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
            )
            assert (
                entry["section_one_two"][0]["daily_precipitation"]["duration_code"]
                == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
            )
            assert entry["section_one_two"][0]["date"] == decoded_data["section_one"]["date"]


class TestGetTelegramOverviewSaveDataOverviewSectionOneIcePhenomenaAPI:
    def test_get_telegram_overview_save_data_overview_section_one_ice_phenomena(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        assert len(res["save_data_overview"][0]["section_one_two"][0]["ice_phenomena"]) == len(
            decoded_data["section_one"]["ice_phenomena"]
        )
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["ice_phenomena"][0]["code"]
            == decoded_data["section_one"]["ice_phenomena"][0]["code"]
        )
        assert (
            res["save_data_overview"][0]["section_one_two"][0]["ice_phenomena"][0]["intensity"]
            == decoded_data["section_one"]["ice_phenomena"][0]["intensity"]
        )

    def test_get_multi_telegram_overview_save_data_overview_section_one_ice_phenomena(
        self,
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

        telegrams = [
            {
                "raw": f"{station1_code} 01082 10251 20022 30249 45820 52020 51210 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{station1_code} 02082 10261 20010 30256 46822 51210 00100="},
            {"raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100="},
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100="},
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            # in case of multiple ice phenomenas
            for idx_ice, ice_ph_entry in enumerate(entry["section_one_two"][0]["ice_phenomena"]):
                assert ice_ph_entry["code"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["code"]
                assert ice_ph_entry["intensity"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["intensity"]


class TestGetTelegramOverviewSaveDataOverviewSectionOneTwoAPI:
    def test_get_single_telegram_overview_save_data_overview_section_one_two(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station1_code = manual_hydro_station_kyrgyz.station_code

        # telegrams need to be ordered by station code and by telegram date in order to simplify the test logic
        telegrams = [
            {
                "raw": f"{station1_code} 11082 10172 20000 30175 45820 51209 52020 00003 92210 10172 20022 30176 51308 00011 92209 10174 20011 30178 51409 92205 10174 20011 30178 46830="
            },
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        sd_overview = res["save_data_overview"][0]
        parser = KN15TelegramParser(telegrams[0]["raw"], organization_kyrgyz.uuid)
        decoded_data = parser.parse()
        decoded_section_one_two = sorted(
            [decoded_data["section_one"]] + decoded_data["section_two"], key=lambda x: x["date"]
        )
        for entry, expected in zip(sd_overview["section_one_two"], decoded_section_one_two):
            assert entry["morning_water_level"] == expected["morning_water_level"]
            assert entry["water_level_20h_period"] == expected["water_level_20h_period"]
            assert entry["water_temperature"] == expected["water_temperature"]
            assert entry["air_temperature"] == expected["air_temperature"]
            assert entry["date"] == expected["date"]

            if expected["daily_precipitation"] is not None:
                assert (
                    entry["daily_precipitation"]["precipitation"] == expected["daily_precipitation"]["precipitation"]
                )
                assert (
                    entry["daily_precipitation"]["duration_code"] == expected["daily_precipitation"]["duration_code"]
                )

            assert len(entry["ice_phenomena"]) == len(expected["ice_phenomena"])
            for ice_entry, expected_ice in zip(entry["ice_phenomena"], expected["ice_phenomena"]):
                assert ice_entry["code"] == expected_ice["code"]
                assert ice_entry["intensity"] == expected_ice["intensity"]


class TestGetTelegramOveriewSaveDataOverviewWlQTripletsAPI:
    def test_get_single_telegram_overview_save_data_overview_wl_q_triplets_section_two(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        discharge_model = DischargeModel(
            name="Test discharge curve",
            param_a=10,
            param_b=2,
            param_c=0.001,
            valid_from_local=dt.datetime(2020, 3, 1, tzinfo=ZoneInfo("UTC")),
            station=manual_hydro_station_kyrgyz,
        )
        discharge_model.save()

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        # telegrams need to be ordered by station code and by telegram date in order to simplify the test logic
        telegrams = [
            {
                "raw": f"{station_code} 11082 10172 20000 30175 45820 51209 52020 00003 92210 10172 20022 30176 51308 00011 92209 10174 20011 30178 51409 92205 10174 20011 30178 46830="
            },
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        sd_overview = res["save_data_overview"][0]

        expected_evening_water_level_new = {}
        expected_evening_discharge_new = {}
        expected_morning_water_level_new = {}
        expected_morning_discharge_new = {}

        section_one_two = sd_overview["section_one_two"]

        for decoded_entry in section_one_two:
            day_smart = SmartDatetime(decoded_entry["date"], manual_hydro_station_kyrgyz, tz_included=False)
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

        for entry in sd_overview["wl_q_triplets"]:
            date = entry["date"]
            metrics = entry["metrics"]
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


class TestGetTelegramOverviewSaveDataOverviewSectionSixAPI:
    def test_get_telegram_overview_save_data_overview_section_six_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["save_data_overview"][0]["section_six"]) == 0

    def test_get_telegram_overview_save_data_overview_section_six(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        assert res["save_data_overview"][0]["section_six"] == decoded_data["section_six"]

    def test_get_multi_telegram_overview_save_data_overview_section_six(
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
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100="},
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_six"] == decoded_data.get("section_six", [])


class TestGetTelegramOverviewSaveDataOverviewSectionEightAPI:
    def test_get_telegram_overview_save_data_overview_section_eight_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert res["save_data_overview"][0]["section_eight"] is None

    def test_get_telegram_overview_save_data_overview_section_eight(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        assert res["save_data_overview"][0]["section_eight"] == decoded_data["section_eight"]

    def test_get_multi_telegram_overview_save_data_overview_section_eight(
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

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_eight"] == decoded_data.get("section_eight", None)
