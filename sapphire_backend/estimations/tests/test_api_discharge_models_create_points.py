from datetime import datetime

import pytest

from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.estimations.schema import DischargeModelPointsPair
from sapphire_backend.estimations.utils import least_squares_fit
from sapphire_backend.utils.rounding import custom_round


class TestDischargeModelsCreatePointsAPI:
    endpoint = "/api/v1/estimations/discharge-models/{station_uuid}/create-points"

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
    def test_create_points_kyrgyz_permissions_status_codes(
        self, client, manual_hydro_station_kyrgyz, expected_status_code, request
    ):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testmodel",
            "points": [{"q": 10, "h": 100}, {"q": 20, "h": 150}, {"q": 32, "h": 200}],
            "valid_from_local": "2024-01-19T11:52:20.076Z",
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
    def test_create_from_points(self, client, manual_hydro_station_kyrgyz, request):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testmodel",
            "points": [{"q": 10, "h": 100}, {"q": 20, "h": 150}, {"q": 32, "h": 200}],
            "valid_from_local": "2024-01-19T11:52:20.076Z",
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
    def test_create_from_points_returns_db_object(self, client, manual_hydro_station_kyrgyz, request):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testmodel",
            "points": [{"q": 10, "h": 100}, {"q": 20, "h": 150}, {"q": 32, "h": 200}],
            "valid_from_local": "2024-01-19T11:52:20.076Z",
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
    def test_create_from_points_coefficients_from_least_squares_fit(
        self, client, manual_hydro_station_kyrgyz, request
    ):
        client = request.getfixturevalue(client)
        payload = {
            "name": "testmodel",
            "points": [{"q": 10, "h": 100}, {"q": 20, "h": 150}, {"q": 32, "h": 200}],
            "valid_from_local": "2024-01-19T11:52:20.076Z",
        }

        response = client.post(
            self.endpoint.format(station_uuid=manual_hydro_station_kyrgyz.uuid),
            data=payload,
            content_type="application/json",
        )
        res = response.json()
        input_points = [DischargeModelPointsPair(**kwargs) for kwargs in payload["points"]]
        expected = least_squares_fit(input_points)

        assert custom_round(res["param_a"], 10) == custom_round(expected["param_a"], 10)
        assert custom_round(res["param_b"], 10) == custom_round(expected["param_b"], 10)
        assert custom_round(res["param_c"], 10) == custom_round(expected["param_c"], 10)
