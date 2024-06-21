from datetime import datetime

import pytest

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.utils.rounding import custom_round


class TestDischargeModelsCreatePointsAPI:
    endpoint = "/api/v1/estimations/discharge-models/{station_uuid}/create-delta"

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
    def test_create_delta_kyrgyz_permissions_status_codes(
        self,
        client,
        manual_hydro_station_kyrgyz,
        expected_status_code,
        discharge_model_manual_hydro_station_kyrgyz,
        request,
    ):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testdeltamodel",
            "valid_from_local": "2024-03-01T11:52:20.076Z",
            "param_delta": 25,
            "from_model_uuid": discharge_model_manual_hydro_station_kyrgyz.uuid,
        }

        response = client.post(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            data=payload,
            content_type="application/json",
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
    def test_create_from_delta(
        self, client, manual_hydro_station_kyrgyz, discharge_model_manual_hydro_station_kyrgyz, request
    ):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testdeltamodel",
            "valid_from_local": "2024-03-01T11:52:20.076Z",
            "param_delta": 25,
            "from_model_uuid": discharge_model_manual_hydro_station_kyrgyz.uuid,
        }

        client.post(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            data=payload,
            content_type="application/json",
        )
        dm_queryset = DischargeModel.objects.filter(
            name=payload["name"],
            valid_from_local__date=datetime.fromisoformat(payload["valid_from_local"]).date(),
            station=manual_hydro_station_kyrgyz,
        )

        assert dm_queryset.exists() is True

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_create_from_delta_returns_db_object(
        self, client, manual_hydro_station_kyrgyz, discharge_model_manual_hydro_station_kyrgyz, request
    ):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testdeltamodel",
            "valid_from_local": "2024-03-01T11:52:20.076Z",
            "param_delta": 25,
            "from_model_uuid": discharge_model_manual_hydro_station_kyrgyz.uuid,
        }

        response = client.post(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            data=payload,
            content_type="application/json",
        )
        res = response.json()
        dm_obj = DischargeModel.objects.filter(
            name=res["name"],
            valid_from_local__date=datetime.fromisoformat(res["valid_from_local"]).date(),
            station_id=res["station_id"],
            uuid=res["uuid"],
        ).first()

        assert dm_obj is not None
        assert custom_round(dm_obj.param_a, 10) == custom_round(res["param_a"], 10)
        assert custom_round(dm_obj.param_b, 10) == custom_round(res["param_b"], 10)
        assert custom_round(dm_obj.param_c, 10) == custom_round(res["param_c"], 10)

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_create_from_delta_coefficients_correct(
        self, client, manual_hydro_station_kyrgyz, discharge_model_manual_hydro_station_kyrgyz, request
    ):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testdeltamodel",
            "valid_from_local": "2024-03-01T11:52:20.076Z",
            "param_delta": 25,
            "from_model_uuid": discharge_model_manual_hydro_station_kyrgyz.uuid,
        }

        response = client.post(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            data=payload,
            content_type="application/json",
        )
        res = response.json()
        expected_param_a = discharge_model_manual_hydro_station_kyrgyz.param_a + payload["param_delta"]
        expected_param_b = 2
        expected_param_c = discharge_model_manual_hydro_station_kyrgyz.param_c

        assert custom_round(res["param_a"], 10) == custom_round(expected_param_a, 10)
        assert custom_round(res["param_b"], 10) == custom_round(expected_param_b, 10)
        assert custom_round(res["param_c"], 10) == custom_round(expected_param_c, 10)

    @pytest.mark.parametrize(
        "client",
        [
            "regular_user_kyrgyz_api_client",
            "organization_admin_kyrgyz_api_client",
            "superadmin_kyrgyz_api_client",
            "superadmin_uzbek_api_client",
        ],
    )
    def test_create_from_delta_nonexisting_reference_model(self, client, manual_hydro_station_kyrgyz, request):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testdeltamodel",
            "valid_from_local": "2024-03-01T11:52:20.076Z",
            "param_delta": 25,
            "from_model_uuid": "11111111-2222-3333-4444-555555555555",
        }

        response = client.post(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            data=payload,
            content_type="application/json",
        )
        res = response.json()
        assert response.status_code == 404
        assert res == {"code": "not_found", "detail": "Object does not exist"}
