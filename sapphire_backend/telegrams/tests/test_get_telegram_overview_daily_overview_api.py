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
        assert response.status_code == 200

    def test_get_multiple_telegram_overview_status_code(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
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

        response = regular_user_kyrgyz_api_client.post(
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
        assert len(res["errors"]) == 0

    def test_get_multi_telegram_overview_no_errors(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_second_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        manual_second_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
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

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()
        assert len(res["errors"]) == 0

    def test_get_telegram_overview_with_error(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, regular_user_kyrgyz_api_client
    ):
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
            "98805 111// 20013 30200="
        )

        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        res = response.json()

        assert len(res["errors"]) == 1
        assert res["errors"][0]["error"] == "Expected token starting with '3', got: 96603"

    def test_get_multi_telegram_overview_with_errors(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, regular_user_kyrgyz_api_client
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

        response = regular_user_kyrgyz_api_client.post(
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
        regular_user_kyrgyz_api_client,
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

        response = regular_user_kyrgyz_api_client.post(
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
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = INPUT_TELEGRAM.format(station_code=station_code)

        response = regular_user_kyrgyz_api_client.post(
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
        regular_user_kyrgyz_api_client,
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

        response = regular_user_kyrgyz_api_client.post(
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
        regular_user_kyrgyz_api_client,
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

        response = regular_user_kyrgyz_api_client.post(
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
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 52020 51210 00100 "
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

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            # in case of multiple ice phenomenas
            for idx_ice, ice_ph_entry in enumerate(entry["section_one"]["ice_phenomena"]):
                assert ice_ph_entry["code"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["code"]
                assert ice_ph_entry["intensity"] == decoded_data["section_one"]["ice_phenomena"][idx_ice]["intensity"]


class TestGetTelegramOverviewDailyOverviewSectionTwoAPI:
    def test_get_single_telegram_overview_daily_overview_section_two(
        self,
        datetime_kyrgyz_mock,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 11082 10215 20100 30210 92210 10205 20100 30200 45820 92209 10195 20100 30190 92208 10185 20100 30180 46830="

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": [{"raw": telegram}]},
            content_type="application/json",
        )

        decoded_data = KN15TelegramParser(telegram, organization_kyrgyz.uuid).parse()
        res = response.json()
        assert len(res["daily_overview"]) == 1
        assert res["daily_overview"][0]["station_code"] == decoded_data["section_zero"]["station_code"]
        assert res["daily_overview"][0]["section_two"] == sorted(decoded_data["section_two"], key=lambda x: x["date"])

    def test_get_multi_telegram_overview_daily_overview_section_two(
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
                "raw": f"{station1_code} 11082 10215 20100 30210 92210 10205 20100 30200 45820 52020 92209 10195 20100 30190 92208 10185 20100 30180 46830="
            },
            {
                "raw": f"{station2_code} 11082 10172 20000 30175 45820 00003 92210 10172 20022 30176 92209 10174 20011 30178 51409 92205 10174 20011 30178 46830="
            },
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            decoded_section_two_sorted = sorted(decoded_data["section_two"], key=lambda x: x["date"])
            for entry_section_two, expected_section_two in zip(entry["section_two"], decoded_section_two_sorted):
                assert entry_section_two["morning_water_level"] == expected_section_two["morning_water_level"]
                assert entry_section_two["water_level_20h_period"] == expected_section_two["water_level_20h_period"]
                assert entry_section_two["water_temperature"] == expected_section_two["water_temperature"]
                assert entry_section_two["air_temperature"] == expected_section_two["air_temperature"]

    def test_get_multi_telegram_overview_daily_overview_section_two_ice_phenomena(
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
                "raw": f"{station1_code} 11082 10215 20100 30210 92210 10205 20100 30200 45820 51209 52020 00003 92209 10195 20100 30190 92208 10185 20100 30180 46830="
            },
            {
                "raw": f"{station2_code} 11082 10172 20000 30175 45820 51209 52020 00003 92210 10172 20022 30176 51308 00011 92209 10174 20011 30178 51409 92205 10174 20011 30178 46830="
            },
        ]

        response = regular_user_kyrgyz_api_client.post(
            endpoint,
            data={"telegrams": telegrams},
            content_type="application/json",
        )

        res = response.json()

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            decoded_section_two_sorted = sorted(decoded_data["section_two"], key=lambda x: x["date"])
            for idx_sec_two, sec_two in enumerate(entry["section_two"]):
                # in case of multiple ice phenomenas
                for idx_ice, ice_ph_entry in enumerate(sec_two["ice_phenomena"]):
                    assert (
                        ice_ph_entry["code"]
                        == decoded_section_two_sorted[idx_sec_two]["ice_phenomena"][idx_ice]["code"]
                    )
                    assert (
                        ice_ph_entry["intensity"]
                        == decoded_section_two_sorted[idx_sec_two]["ice_phenomena"][idx_ice]["intensity"]
                    )


class TestGetTelegramOverviewDailyOverviewSectionSixAPI:
    def test_get_telegram_overview_daily_overview_section_six(
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

        assert res["daily_overview"][0]["section_six"] == decoded_data["section_six"]

    def test_get_telegram_overview_daily_overview_section_six_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 98805 111// 20013 30200="

        response = regular_user_kyrgyz_api_client.post(
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

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_six"] == decoded_data.get("section_six", [])


class TestGetTelegramOverviewDailyOverviewSectionEightAPI:
    def test_get_telegram_overview_daily_overview_section_eight_empty(
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, regular_user_kyrgyz_api_client
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code
        telegram = (
            f"{station_code} 01082 10251 20022 30249 45820 51209 00100 "
            "96603 10150 23050 32521 40162 50313 "
            "96604 10250 22830 32436 52920 "
        )

        response = regular_user_kyrgyz_api_client.post(
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

        assert res["daily_overview"][0]["section_eight"] == decoded_data["section_eight"]

    def test_get_multi_telegram_overview_daily_overview_section_eight(
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

        for idx, entry in enumerate(res["daily_overview"]):
            parser = KN15TelegramParser(telegrams[idx]["raw"], organization_kyrgyz.uuid)
            decoded_data = parser.parse()
            assert entry["section_eight"] == decoded_data.get("section_eight", None)
