from sapphire_backend.telegrams.parser import KN15TelegramParser
from sapphire_backend.utils.datetime_helper import SmartDatetime

INPUT_TELEGRAM = (
    "{station_code} 01082 10251 20022 30249 45820 51209 00100 "
    "96603 10150 23050 32521 40162 50313 "
    "96604 10250 22830 32436 52920 "
    "98805 111// 20013 30200="
)


class TestGetTelegramOverviewGeneralAPI:
    def test_get_telegram_overview_status_code(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_get_multiple_telegram_overview_status_code(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        telegrams = [
            {
                "raw": f"{manual_hydro_station_kyrgyz.station_code} 01082 10251 20022 30249 45820 51209 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{manual_hydro_station_kyrgyz.station_code} 02082 10261 20010 30256 46822 51209 00100="},
            {"raw": f"{manual_second_hydro_station_kyrgyz.station_code} 01082 10151 20010 30149 45820 51209 00100="},
            {"raw": f"{manual_second_hydro_station_kyrgyz.station_code} 02082 10161 20010 30156 46822 51209 00100="},
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_get_telegram_overview_response_keys(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        EXPECTED_KEYS = {
            "daily_overview",
            "data_processing_overview",
            "save_data_overview",
            "reported_discharge_points",
            "discharge_codes",
            "meteo_codes",
            "errors",
        }
        actual_keys = set(res.keys())

        assert actual_keys == EXPECTED_KEYS, f"Expected keys {EXPECTED_KEYS}, but got {actual_keys}"

    def test_get_telegram_overview_no_errors(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()
        assert len(res["errors"]) == 0

    def test_get_multi_telegram_overview_no_errors(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        telegrams = [
            {
                "raw": f"{manual_hydro_station_kyrgyz.station_code} 01082 10251 20022 30249 45820 51209 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{manual_hydro_station_kyrgyz.station_code} 02082 10261 20010 30256 46822 51209 00100="},
            {"raw": f"{manual_second_hydro_station_kyrgyz.station_code} 01082 10151 20010 30149 45820 51209 00100="},
            {"raw": f"{manual_second_hydro_station_kyrgyz.station_code} 02082 10161 20010 30156 46822 51209 00100="},
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        assert len(res["errors"]) == 0

    def test_get_telegram_overview_with_error(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, authenticated_regular_user_kyrgyz_api_client
    ):
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        )

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["errors"]) == 1
        assert res["errors"][0]["error"] == "Expected token starting with '3', got: 96603"

    def test_get_multi_telegram_overview_with_errors(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, authenticated_regular_user_kyrgyz_api_client
    ):
        telegrams = [
            {
                "raw": f"{manual_hydro_station_kyrgyz.station_code} 01082 10251 20022 30249 45820 51209 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{manual_hydro_station_kyrgyz.station_code} 02082 10261 20010 30256 46822 51209 00100="},
            {"raw": "98765 01082 10151 20010 30149 45820 51209 00100="},
            {"raw": "98765 02082 10161 20010 30156 46822 51209 00100="},
        ]
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["errors"]) == 3
        assert res["errors"][0] == {
            "index": 0,
            "telegram": "12345 01082 10251 20022 30249 45820 51209 00100 96603 10150 23050 32521 40162 50313 96604 10250 22830 32436 52920 98805 111// 20013 30200=",
            "error": "No meteo station with code 12345, but found token: 98805",
        }
        assert res["errors"][1] == {
            "index": 2,
            "telegram": "98765 01082 10151 20010 30149 45820 51209 00100=",
            "error": "No manual hydro or meteo station with the following code: 98765",
        }
        assert res["errors"][2] == {
            "index": 3,
            "telegram": "98765 02082 10161 20010 30156 46822 51209 00100=",
            "error": "No manual hydro or meteo station with the following code: 98765",
        }


class TestGetTelegramOverviewDailyOverviewMetaAPI:
    def test_get_telegram_overview_daily_overview_meta(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["daily_overview"]) == 1
        assert res["daily_overview"][0]["station_code"] == manual_hydro_station_kyrgyz.station_code
        assert res["daily_overview"][0]["station_name"] == manual_hydro_station_kyrgyz.name
        assert res["daily_overview"][0]["telegram_day_date"] == "2020-04-01"
        assert res["daily_overview"][0]["previous_day_date"] == "2020-03-31"

    def test_get_multi_telegram_overview_daily_overview_meta(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station1_code = manual_hydro_station_kyrgyz.station_code
        station2_code = manual_second_hydro_station_kyrgyz.station_code

        telegrams = [
            {
                "raw": f"{station1_code} 01082 10251 20022 30249 45820 51209 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{station1_code} 02082 10261 20010 30256 46822 51209 00100="},
            {"raw": f"{station2_code} 01082 10151 20010 30149 45820 51209 00100="},
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 51209 00100="},
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["daily_overview"]) == len(telegrams)
        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            telegram_day_smart = SmartDatetime(
                decoded_data["section_zero"]["date"], parser.hydro_station, tz_included=True
            )
            assert entry["station_code"] == decoded_data["section_zero"]["station_code"]
            assert entry["station_name"] == decoded_data["section_zero"]["station_name"]
            assert entry["telegram_day_date"] == telegram_day_smart.local.date().isoformat()
            assert entry["previous_day_date"] == telegram_day_smart.previous_local.date().isoformat()

    def test_get_telegram_overview_daily_overview_override_date(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram, "override_date": "2019-06-01"}]},
            content_type="application/json",
        )

        res = response.json()
        assert res["daily_overview"][0]["telegram_day_date"] == "2019-06-01"
        assert res["daily_overview"][0]["previous_day_date"] == "2019-05-31"

    def test_get_multi_telegram_overview_daily_overview_override_date(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        station1_code = manual_hydro_station_kyrgyz.station_code
        station2_code = manual_second_hydro_station_kyrgyz.station_code

        telegrams = [
            {
                "raw": f"{station1_code} 01082 10251 20022 30249 45820 51209 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200=",
                "override_date": "2019-06-01",
            },
            {"raw": f"{station1_code} 02082 10261 20010 30256 46822 51209 00100=", "override_date": "2019-06-02"},
            {"raw": f"{station2_code} 01082 10151 20010 30149 45820 51209 00100=", "override_date": "2019-05-12"},
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 51209 00100=", "override_date": "2019-05-13"},
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            parser.parse()  # necessary to load the hydro_station attribute in parser
            telegram_day_smart = SmartDatetime(telegrams[idx]["override_date"], parser.hydro_station, tz_included=True)
            assert entry["telegram_day_date"] == telegram_day_smart.local.date().isoformat()
            assert entry["previous_day_date"] == telegram_day_smart.previous_local.date().isoformat()


class TestGetTelegramOverviewDailyOverviewSectionOneAPI:
    def test_get_telegram_overview_daily_overview_section_one(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

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
        assert (
            res["daily_overview"][0]["section_one"]["daily_precipitation"]["precipitation"]
            == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
        )
        assert (
            res["daily_overview"][0]["section_one"]["daily_precipitation"]["duration_code"]
            == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
        )

    def test_get_multi_telegram_overview_daily_overview_section_one(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station1_code = manual_hydro_station_kyrgyz.station_code
        station2_code = manual_second_hydro_station_kyrgyz.station_code

        telegrams = [
            {
                "raw": f"{station1_code} 01082 10251 20022 30249 45820 52020 00100 "
                "96603 10150 23050 32521 40162 50313 "
                "96604 10250 22830 32436 52920 "
                "98805 111// 20013 30200="
            },
            {"raw": f"{station1_code} 02082 10261 20010 30256 46822 51210 00100="},
            {"raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100="},
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100="},
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_one"]["morning_water_level"] == decoded_data["section_one"]["morning_water_level"]
            assert (
                entry["section_one"]["water_level_20h_period"] == decoded_data["section_one"]["water_level_20h_period"]
            )
            assert entry["section_one"]["water_temperature"] == decoded_data["section_one"]["water_temperature"]
            assert entry["section_one"]["air_temperature"] == decoded_data["section_one"]["air_temperature"]
            assert (
                entry["section_one"]["daily_precipitation"]["precipitation"]
                == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
            )
            assert (
                entry["section_one"]["daily_precipitation"]["duration_code"]
                == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
            )


class TestGetTelegramOverviewDailyOverviewSectionOneIcePhenomenaAPI:
    def test_get_telegram_overview_daily_overview_section_one_ice_phenomena(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 52020 51210 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        )

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        for idx_ice, ice_ph_entry in enumerate(
            res["daily_overview"][0]["section_one"]["ice_phenomena"]
        ):  # in case of multiple ice phenomenas
            assert ice_ph_entry["code"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["code"]
            assert ice_ph_entry["intensity"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["intensity"]

    def test_get_multi_telegram_overview_daily_overview_section_one_ice_phenomena(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            # in case of multiple ice phenomenas
            for idx_ice, ice_ph_entry in enumerate(entry["section_one"]["ice_phenomena"]):
                assert ice_ph_entry["code"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["code"]
                assert ice_ph_entry["intensity"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["intensity"]


class TestGetTelegramOverviewDailyOverviewSectionSixAPI:
    def test_get_telegram_overview_daily_overview_section_six(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        assert res["daily_overview"][0]["section_six"] == decoded_data["section_six"]

    def test_get_telegram_overview_daily_overview_section_six_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 98805 111// 20013 30200="

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert res["daily_overview"][0]["section_six"] == []

    def test_get_multi_telegram_overview_daily_overview_section_six(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_six"] == decoded_data.get("section_six", [])


class TestGetTelegramOverviewDailyOverviewSectionEightAPI:
    def test_get_telegram_overview_daily_overview_section_eight_empty(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, authenticated_regular_user_kyrgyz_api_client
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
        )

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert res["daily_overview"][0]["section_eight"] is None

    def test_get_telegram_overview_daily_overview_section_eight(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()

        res = response.json()

        assert res["daily_overview"][0]["section_eight"] == decoded_data["section_eight"]

    def test_get_multi_telegram_overview_daily_overview_section_eight(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_eight"] == decoded_data.get("section_eight", None)


class TestGetTelegramOverviewDataProcessingOverviewAPI:  # TODO DEVELOP MORE
    def test_get_telegram_overview_data_processing_overview(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert set(res["data_processing_overview"].keys()) == {station1_code, station2_code}


class TestGetTelegramOverviewSaveDataOverviewMetaAPI:
    def test_get_telegram_overview_save_data_overview_meta(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["save_data_overview"]) == 1
        assert res["save_data_overview"][0]["station_code"] == manual_hydro_station_kyrgyz.station_code
        assert res["save_data_overview"][0]["station_name"] == manual_hydro_station_kyrgyz.name
        assert res["save_data_overview"][0]["telegram_day_date"] == "2020-04-01"
        assert res["save_data_overview"][0]["previous_day_date"] == "2020-03-31"
        assert res["save_data_overview"][0]["type"] == "discharge / meteo"

    def test_get_multi_telegram_overview_save_data_overview_meta(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
            telegram_previous_date = telegram_day_smart.previous_local.date().isoformat()

            assert entry["station_code"] == decoded_data["section_zero"]["station_code"]
            assert entry["station_name"] == parser.hydro_station.name
            assert entry["telegram_day_date"] == telegram_date
            assert entry["previous_day_date"] == telegram_previous_date
            assert entry["type"] == "discharge / meteo" if decoded_data.get("section_eight", False) else "discharge"


class TestGetTelegramOverviewSaveDataOverviewSectionOneAPI:
    def test_get_multi_telegram_overview_save_data_overview_section_one(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

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

        assert (
            res["save_data_overview"][0]["section_one"]["daily_precipitation"]["precipitation"]
            == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
        )
        assert (
            res["save_data_overview"][0]["section_one"]["daily_precipitation"]["duration_code"]
            == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
        )

    def test_get_telegram_overview_save_data_overview_section_one(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_one"]["morning_water_level"] == decoded_data["section_one"]["morning_water_level"]
            assert (
                entry["section_one"]["water_level_20h_period"] == decoded_data["section_one"]["water_level_20h_period"]
            )
            assert entry["section_one"]["water_temperature"] == decoded_data["section_one"]["water_temperature"]
            assert entry["section_one"]["air_temperature"] == decoded_data["section_one"]["air_temperature"]
            assert (
                entry["section_one"]["daily_precipitation"]["precipitation"]
                == decoded_data["section_one"]["daily_precipitation"]["precipitation"]
            )
            assert (
                entry["section_one"]["daily_precipitation"]["duration_code"]
                == decoded_data["section_one"]["daily_precipitation"]["duration_code"]
            )


class TestGetTelegramOverviewSaveDataOverviewSectionOneIcePhenomenaAPI:
    def test_get_telegram_overview_save_data_overview_section_one_ice_phenomena(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

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

    def test_get_multi_telegram_overview_save_data_overview_section_one_ice_phenomena(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            # in case of multiple ice phenomenas
            for idx_ice, ice_ph_entry in enumerate(entry["section_one"]["ice_phenomena"]):
                assert ice_ph_entry["code"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["code"]
                assert ice_ph_entry["intensity"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["intensity"]


class TestGetTelegramOverviewSaveDataOverviewSectionSixAPI:
    def test_get_telegram_overview_save_data_overview_section_six_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100"

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
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
        authenticated_regular_user_kyrgyz_api_client,
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

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["save_data_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_eight"] == decoded_data.get("section_eight", None)


class TestGetTelegramOverviewReportedDischargePointsAPI:
    def test_get_telegram_overview_reported_discharge_points_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 " "98805 111// 20013 30200="

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert list(res["reported_discharge_points"].keys()) == [station_code]
        assert len(res["reported_discharge_points"][station_code]) == 0

    def test_get_telegram_overview_reported_discharge_points(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()

        assert list(res["reported_discharge_points"].keys()) == [station_code]
        for idx, section_six_entry in enumerate(decoded_data["section_six"]):
            assert res["reported_discharge_points"][station_code][idx]["date"] == section_six_entry["date"]
            assert res["reported_discharge_points"][station_code][idx]["h"] == float(section_six_entry["water_level"])
            assert res["reported_discharge_points"][station_code][idx]["q"] == float(section_six_entry["discharge"])

    def test_get_multi_telegram_overview_reported_discharge_points(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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
            {
                "raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100 "
                f"96607 10150 23050 32521 40162 50308="
            },
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        parser = KN15TelegramParser(telegrams[0]["raw"], organization_kyrgyz.uuid)
        decoded_data = parser.parse()

        parser2 = KN15TelegramParser(telegrams[1]["raw"], organization_kyrgyz.uuid)
        decoded_data2 = parser2.parse()

        assert set(res["reported_discharge_points"].keys()) == {station1_code, station2_code}
        assert len(res["reported_discharge_points"][station1_code]) == len(decoded_data["section_six"])
        assert res["reported_discharge_points"][station1_code][0]["date"] == decoded_data["section_six"][0]["date"]
        assert res["reported_discharge_points"][station1_code][0]["h"] == decoded_data["section_six"][0]["water_level"]
        assert res["reported_discharge_points"][station1_code][0]["q"] == decoded_data["section_six"][0]["discharge"]

        assert res["reported_discharge_points"][station1_code][1]["date"] == decoded_data["section_six"][1]["date"]
        assert res["reported_discharge_points"][station1_code][1]["h"] == decoded_data["section_six"][1]["water_level"]
        assert res["reported_discharge_points"][station1_code][1]["q"] == decoded_data["section_six"][1]["discharge"]

        assert len(res["reported_discharge_points"][station2_code]) == len(decoded_data2["section_six"])
        assert res["reported_discharge_points"][station2_code][0]["date"] == decoded_data2["section_six"][0]["date"]
        assert (
            res["reported_discharge_points"][station2_code][0]["h"] == decoded_data2["section_six"][0]["water_level"]
        )
        assert res["reported_discharge_points"][station2_code][0]["q"] == decoded_data2["section_six"][0]["discharge"]


class TestGetTelegramOverviewReportedDischargeCodesAPI:
    def test_get_telegram_overview_discharge_codes(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["discharge_codes"]) == 1
        assert res["discharge_codes"][0] == [
            manual_hydro_station_kyrgyz.station_code,
            str(manual_hydro_station_kyrgyz.uuid),
        ]

    def test_get_multi_telegram_overview_discharge_codes(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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
            {
                "raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100 "
                f"96607 10150 23050 32521 40162 50308="
            },
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["discharge_codes"]) == 2
        for idx, telegram in enumerate(telegrams):
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert res["discharge_codes"][idx][0] == decoded_data["section_zero"]["station_code"]
            assert res["discharge_codes"][idx][1] == str(parser.hydro_station.uuid)


class TestGetTelegramOverviewReportedMeteoCodesAPI:
    def test_get_telegram_overview_meteo_codes_empty(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, authenticated_regular_user_kyrgyz_api_client
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "
        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["meteo_codes"]) == 0

    def test_get_telegram_overview_meteo_codes(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["meteo_codes"]) == 1
        assert res["meteo_codes"][0] == [
            manual_meteo_station_kyrgyz.station_code,
            str(manual_meteo_station_kyrgyz.uuid),
        ]

    def test_get_multi_telegram_overview_meteo_codes(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        authenticated_regular_user_kyrgyz_api_client,
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
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100 " f"98805 111// 20013 30300="},
        ]

        response = authenticated_regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["meteo_codes"]) == 2
        for idx, telegram in enumerate(telegrams):
            parser = KN15TelegramParser(telegram["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert res["meteo_codes"][idx][0] == decoded_data["section_zero"]["station_code"]
            assert res["meteo_codes"][idx][1] == str(parser.meteo_station.uuid)
