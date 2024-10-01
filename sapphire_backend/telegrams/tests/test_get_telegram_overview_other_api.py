from sapphire_backend.telegrams.parser import KN15TelegramParser

INPUT_TELEGRAM = (
    "{station_code} 01082 10251 20022 30249 45820 51209 00100 "
    "96603 10150 23050 32521 40162 50313 "
    "96604 10250 22830 32436 52920 "
    "98805 111// 20013 30200="
)


class TestGetTelegramOverviewReportedDischargePointsAPI:
    def test_get_telegram_overview_reported_discharge_points_empty(
        self,
        organization_kyrgyz,
        manual_hydro_station_kyrgyz,
        manual_meteo_station_kyrgyz,
        regular_user_kyrgyz_api_client,
    ):
        endpoint = f"/api/v1/telegrams/{organization_kyrgyz.uuid}/get-telegram-overview"
        station_code = manual_hydro_station_kyrgyz.station_code

        telegram = f"{station_code} 01082 10251 20022 30249 45820 51209 00100 " "98805 111// 20013 30200="

        response = regular_user_kyrgyz_api_client.post(
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
            {
                "raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100 "
                f"96607 10150 23050 32521 40162 50308="
            },
        ]

        response = regular_user_kyrgyz_api_client.post(
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
            {
                "raw": f"{station2_code} 01082 10151 20010 30149 45820 55008 00100 "
                f"96607 10150 23050 32521 40162 50308="
            },
        ]

        response = regular_user_kyrgyz_api_client.post(
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
        self, organization_kyrgyz, manual_hydro_station_kyrgyz, regular_user_kyrgyz_api_client
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

        assert len(res["meteo_codes"]) == 0

    def test_get_telegram_overview_meteo_codes(
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
            {"raw": f"{station2_code} 02082 10161 20010 30156 46822 52121 00100 " f"98805 111// 20013 30300="},
        ]

        response = regular_user_kyrgyz_api_client.post(
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
