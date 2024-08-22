import pytest

from sapphire_backend.estimations.models import DischargeModel


class TestDischargeModelsDeleteAPI:
    endpoint = "/api/v1/estimations/discharge-models/{discharge_model_uuid}/delete"

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
    def test_delete_kyrgyz_permissions_status_codes(
        self, client, expected_status_code, discharge_model_manual_hydro_station_kyrgyz, request
    ):
        client = request.getfixturevalue(client)
        response = client.delete(
            self.endpoint.format(discharge_model_uuid=discharge_model_manual_hydro_station_kyrgyz.uuid)
        )

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
    def test_delete_kyrgyz_existing_model(self, client, discharge_model_manual_hydro_station_kyrgyz, request):
        client = request.getfixturevalue(client)
        client.delete(self.endpoint.format(discharge_model_uuid=discharge_model_manual_hydro_station_kyrgyz.uuid))

        dm_queryset = DischargeModel.objects.filter(uuid=discharge_model_manual_hydro_station_kyrgyz.uuid)

        assert dm_queryset.exists() is False

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_delete_kyrgyz_nonexisting_model(self, client, request):
        client = request.getfixturevalue(client)
        response = client.delete(self.endpoint.format(discharge_model_uuid="11111111-2222-3333-4444-555555555555"))
        # Returns 403 because it actually fails on the permission side since regular_permissions
        # can't extract organization from non-existing discharge model uuid
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_delete_kyrgyz_existing_model_returns_name(
        self, client, discharge_model_manual_hydro_station_kyrgyz, request
    ):
        client = request.getfixturevalue(client)
        response = client.delete(
            self.endpoint.format(discharge_model_uuid=discharge_model_manual_hydro_station_kyrgyz.uuid)
        )
        res = response.json()

        assert res == {"name": discharge_model_manual_hydro_station_kyrgyz.name}
