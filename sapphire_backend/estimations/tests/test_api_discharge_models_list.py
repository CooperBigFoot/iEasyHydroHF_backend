from datetime import date

import pytest

from sapphire_backend.estimations.models import DischargeModel


class TestDischargeModelsListAPI:
    endpoint = "/api/v1/estimations/discharge-models/{station_uuid}/list"

    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 200),
            ("organization_admin_kyrgyz_api_client", 200),
            ("superadmin_kyrgyz_api_client", 200),
            ("superadmin_uzbek_api_client", 200),
        ],
    )
    def test_list_permissions_status_codes(self, client, manual_hydro_station_kyrgyz, expected_status_code, request):
        client = request.getfixturevalue(client)

        # Create at least one model to avoid validation errors
        DischargeModel(
            name="Test Model",
            valid_from_local=date(2023, 1, 1),
            param_a=10,
            param_b=2,
            param_c=0.0005,
            station=manual_hydro_station_kyrgyz,
        ).save()

        response = client.get(self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid))
        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_list_empty_year(self, client, manual_hydro_station_kyrgyz, request):
        client = request.getfixturevalue(client)

        # Create a model for 2023 to be the latest
        latest_model = DischargeModel(
            name="Latest Model",
            valid_from_local=date(2023, 12, 31),
            param_a=10,
            param_b=2,
            param_c=0.0005,
            station=manual_hydro_station_kyrgyz,
        )
        latest_model.save()

        response = client.get(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            {"year": 2024},
        )
        res = response.json()
        assert len(res) == 1  # Should return only the latest model
        assert res[0]["uuid"] == str(latest_model.uuid)

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_list_year_2021_first_station(
        self, client, manual_hydro_station_kyrgyz, manual_second_hydro_station_kyrgyz, request
    ):
        valid_from_dates = (
            date(2020, 1, 1),
            date(2020, 3, 1),
            date(2020, 4, 15),
            date(2020, 8, 20),
            date(2021, 2, 1),
            date(2021, 4, 6),
            date(2021, 5, 1),
            date(2021, 7, 10),
            date(2021, 8, 10),
            date(2021, 9, 10),
            date(2021, 11, 1),
        )
        for idx, dt in enumerate(valid_from_dates):
            DischargeModel(
                name=f"Discharge model first station number {idx + 1}",
                valid_from_local=dt,
                param_a=10,
                param_b=2,
                param_c=0.0005,
                station=manual_hydro_station_kyrgyz,
            ).save()
            DischargeModel(
                name=f"Discharge model second station number {idx + 1}",
                valid_from_local=dt,
                param_a=20,
                param_b=2,
                param_c=0.0005,
                station=manual_second_hydro_station_kyrgyz,
            ).save()

        client = request.getfixturevalue(client)

        response = client.get(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            {"year": 2021},
        )
        res = response.json()
        expected_queryset = DischargeModel.objects.filter(
            station=manual_hydro_station_kyrgyz, valid_from_local__year=2021
        ).order_by("-valid_from_local")
        assert len(res) == len(expected_queryset)
        for returned, expected in zip(res, expected_queryset):
            assert returned["uuid"] == str(expected.uuid)

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_list_future_year_returns_latest_model(self, client, manual_hydro_station_kyrgyz, request):
        # Create models for 2021
        DischargeModel(
            name="Discharge model 2021",
            valid_from_local=date(2021, 1, 1),
            param_a=10,
            param_b=2,
            param_c=0.0005,
            station=manual_hydro_station_kyrgyz,
        ).save()

        latest_model = DischargeModel(
            name="Latest model 2022",
            valid_from_local=date(2022, 12, 31),
            param_a=20,
            param_b=2,
            param_c=0.0005,
            station=manual_hydro_station_kyrgyz,
        )
        latest_model.save()

        client = request.getfixturevalue(client)

        # Request models for 2023 (which doesn't exist)
        response = client.get(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            {"year": 2023},
        )

        res = response.json()
        assert len(res) == 1
        assert res[0]["uuid"] == str(latest_model.uuid)

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_list_without_year_returns_all_models(self, client, manual_hydro_station_kyrgyz, request):
        # Create models for three consecutive years
        models = []
        for year in [2020, 2021, 2022]:
            model = DischargeModel(
                name=f"Discharge model {year}",
                valid_from_local=date(year, 12, 1),
                param_a=10,
                param_b=2,
                param_c=0.0005,
                station=manual_hydro_station_kyrgyz,
            )
            model.save()
            models.append(model)

        client = request.getfixturevalue(client)
        response = client.get(self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid))

        res = response.json()
        assert len(res) == 3  # All models should be returned

        # Verify models are returned in descending order by year
        years = [int(item["valid_from_local"][:4]) for item in res]  # Extract year directly from ISO date string
        assert years == [2022, 2021, 2020]  # Check years are in descending order
