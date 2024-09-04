import uuid

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


class TestUserAPIController:
    endpoint = "/api/v1/users"

    def test_get_current_user_for_logged_user(self, authenticated_regular_user_api_client, regular_user):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/me")
        assert response.status_code == 200
        assert response.json()["id"] == regular_user.id

    @pytest.mark.django_db
    def test_get_current_user_for_unauthorized_user(self, api_client):
        response = api_client.get(f"{self.endpoint}/me")
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_get_user_by_uuid(self, authenticated_regular_user_api_client, regular_user):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{regular_user.uuid}")

        assert response.status_code == 200
        assert response.json()["id"] == regular_user.id

    def test_get_deleted_user(self, authenticated_superadmin_user_api_client, deleted_user):
        response = authenticated_superadmin_user_api_client.get(f"{self.endpoint}/{deleted_user.uuid}")

        assert response.status_code == 404

    def test_get_user_by_uuid_for_unauthorized_user(self, api_client, regular_user):
        response = api_client.get(f"{self.endpoint}/{regular_user.uuid}")

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_non_existing_user_by_uuid(self, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Object does not exist", "code": "not_found"}

    def test_get_inactive_user_by_uuid(self, authenticated_regular_user_api_client, inactive_user):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{inactive_user.uuid}")

        assert response.status_code == 200

    def test_update_user(self, authenticated_regular_user_api_client, regular_user):
        update_data = {"first_name": "Update first name", "last_name": "Updated last name"}

        original_username = regular_user.username
        original_email = regular_user.email

        response = authenticated_regular_user_api_client.put(
            f"{self.endpoint}/{regular_user.uuid}", update_data, content_type="application/json"
        )
        assert response.status_code == 200
        regular_user.refresh_from_db()

        assert regular_user.first_name == update_data["first_name"]
        assert regular_user.last_name == update_data["last_name"]

        # test that other attributes are unchanged
        assert regular_user.username == original_username
        assert regular_user.email == original_email

    def test_update_non_existing_user(self, authenticated_superadmin_user_api_client, superadmin):
        update_data = {
            "email": "new@email.com",
        }
        response = authenticated_superadmin_user_api_client.put(
            f"{self.endpoint}/{uuid.uuid4()}", update_data, content_type="application/json"
        )

        assert response.status_code == 404

    def test_update_other_user_data_for_regular_user(
        self, authenticated_regular_user_api_client, regular_user, organization_admin
    ):
        update_data = {
            "email": "new@email.com",
        }
        response = authenticated_regular_user_api_client.put(
            f"{self.endpoint}/{organization_admin.uuid}", update_data, content_type="application/json"
        )

        assert response.status_code == 403

    def test_update_other_user_data_for_superadmin(
        self, authenticated_superadmin_user_api_client, superadmin, organization_admin
    ):
        update_data = {
            "email": "new@email.com",
        }
        response = authenticated_superadmin_user_api_client.put(
            f"{self.endpoint}/{organization_admin.uuid}", update_data, content_type="application/json"
        )

        assert response.status_code == 200

        organization_admin.refresh_from_db()
        assert organization_admin.email == "new@email.com"

    def test_regular_user_update_own_role(self, authenticated_regular_user_api_client, regular_user):
        update_data = {"user_role": User.UserRoles.SUPER_ADMIN}

        response = authenticated_regular_user_api_client.put(
            f"{self.endpoint}/{regular_user.uuid}", update_data, content_type="application/json"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Role cannot be changed, please contact your administrator."

    def test_superadmin_update_other_user_role(
        self, authenticated_superadmin_user_api_client, superadmin, regular_user
    ):
        update_data = {"user_role": User.UserRoles.ORGANIZATION_ADMIN}

        assert regular_user.user_role == User.UserRoles.REGULAR_USER

        response = authenticated_superadmin_user_api_client.put(
            f"{self.endpoint}/{regular_user.uuid}", update_data, content_type="application/json"
        )

        assert response.status_code == 200
        regular_user.refresh_from_db()

        assert regular_user.user_role == User.UserRoles.ORGANIZATION_ADMIN


class TestUserAssignedStationsAPIController:
    endpoint = "/api/v1/users"

    def test_get_assigned_stations_for_empty_list(self, regular_user, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{regular_user.uuid}/assigned-stations")

        assert response.json() == []

    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("organization_admin_kyrgyz_api_client", 403),
            ("authenticated_regular_user_other_organization_api_client", 403),
            ("authenticated_regular_user_api_client", 200),
            ("authenticated_regular_user_2_api_client", 200),
            ("authenticated_organization_user_api_client", 200),
            ("superadmin_kyrgyz_api_client", 200),
            ("superadmin_uzbek_api_client", 200),
        ],
    )
    def test_get_assigned_stations_for_different_users(self, client, expected_status_code, regular_user, request):
        client = request.getfixturevalue(client)
        response = client.get(f"{self.endpoint}/{regular_user.uuid}/assigned-stations")

        assert response.status_code == expected_status_code

    def test_get_assigned_stations(
        self,
        authenticated_regular_user_api_client,
        regular_user,
        regular_user_assigned_hydro_station,
        regular_user_assigned_meteo_station,
        regular_user_assigned_virtual_station,
    ):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{regular_user.uuid}/assigned-stations")

        assert len(response.json()) == 3

    def test_get_assigned_station_api_response(
        self,
        datetime_mock_auto_now_add,
        authenticated_regular_user_api_client,
        regular_user,
        regular_user_assigned_hydro_station,
        manual_hydro_station,
        regular_user_assigned_meteo_station,
        manual_meteo_station,
    ):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{regular_user.uuid}/assigned-stations")

        EXPECTED_RESPONSE = [
            {
                "id": manual_hydro_station.id,
                "name": manual_hydro_station.name,
                "station_code": manual_hydro_station.station_code,
                "uuid": str(manual_hydro_station.uuid),
                "station_type": manual_hydro_station.station_type.value,
                "created_date": "2024-08-25T12:00:00Z",
            },
            {
                "id": manual_meteo_station.id,
                "name": manual_meteo_station.name,
                "station_code": manual_meteo_station.station_code,
                "uuid": str(manual_meteo_station.uuid),
                "station_type": None,
                "created_date": "2024-08-25T12:00:00Z",
            },
        ]

        assert response.json() == EXPECTED_RESPONSE

    def test_bulk_assign(
        self, regular_user, authenticated_regular_user_api_client, manual_hydro_station, manual_meteo_station
    ):
        assert regular_user.assigned_stations.count() == 0

        payload = [
            {"hydro_station_id": str(manual_hydro_station.uuid)},
            {"meteo_station_id": str(manual_meteo_station.uuid)},
        ]
        _ = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-bulk-create",
            data=payload,
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 2

    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("organization_admin_kyrgyz_api_client", 403),
            ("authenticated_regular_user_other_organization_api_client", 403),
            ("authenticated_regular_user_2_api_client", 403),
            ("authenticated_regular_user_api_client", 201),
            ("authenticated_organization_user_api_client", 201),
            ("superadmin_kyrgyz_api_client", 201),
            ("superadmin_uzbek_api_client", 201),
        ],
    )
    def test_bulk_assign_to_other_users(
        self, client, expected_status_code, regular_user, manual_hydro_station, request
    ):
        client = request.getfixturevalue(client)

        payload = [{"hydro_station_id": str(manual_hydro_station.uuid)}]

        response = client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-bulk-create",
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == expected_status_code

    def test_bulk_assign_empty_payload_deletes_assigned_stations(
        self,
        authenticated_regular_user_api_client,
        regular_user,
        regular_user_assigned_hydro_station,
        regular_user_assigned_meteo_station,
    ):
        assert regular_user.assigned_stations.count() == 2

        _ = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-bulk-create",
            data=[],
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 0

    def test_bulk_assign_replaces_existing_with_payload(
        self,
        authenticated_regular_user_api_client,
        regular_user,
        regular_user_assigned_hydro_station,
        manual_hydro_station,
        manual_meteo_station,
    ):
        assert regular_user.assigned_stations.count() == 1
        assert regular_user.assigned_stations.first().hydro_station == manual_hydro_station
        assert regular_user.assigned_stations.first().meteo_station is None

        payload = [{"meteo_station_id": str(manual_meteo_station.uuid)}]

        _ = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-bulk-create",
            data=payload,
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 1
        assert regular_user.assigned_stations.first().hydro_station is None
        assert regular_user.assigned_stations.first().meteo_station == manual_meteo_station

    def test_toggle_assigned_station_removes_station_if_assigned(
        self,
        authenticated_regular_user_api_client,
        regular_user,
        regular_user_assigned_hydro_station,
        manual_hydro_station,
    ):
        assert regular_user.assigned_stations.count() == 1

        payload = {"hydro_station_id": str(manual_hydro_station.uuid)}

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-single-toggle",
            data=payload,
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 0
        assert response.status_code == 200

    def test_toggle_assigned_station_assigns_station_if_not_assigned(
        self, authenticated_regular_user_api_client, regular_user, manual_hydro_station
    ):
        assert regular_user.assigned_stations.count() == 0

        payload = {"hydro_station_id": str(manual_hydro_station.uuid)}

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-single-toggle",
            data=payload,
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 1
        assert response.status_code == 201

    def test_toggle_assigned_station_only_adds_selected_station(
        self,
        authenticated_regular_user_api_client,
        regular_user,
        manual_hydro_station,
        regular_user_assigned_meteo_station,
    ):
        assert regular_user.assigned_stations.count() == 1

        payload = {"hydro_station_id": str(manual_hydro_station.uuid)}

        _ = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-single-toggle",
            data=payload,
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 2

    def test_toggle_assigned_station_only_removes_selected_station(
        self,
        authenticated_regular_user_api_client,
        regular_user,
        manual_hydro_station,
        regular_user_assigned_meteo_station,
        regular_user_assigned_hydro_station,
    ):
        assert regular_user.assigned_stations.count() == 2

        payload = {"hydro_station_id": str(manual_hydro_station.uuid)}

        _ = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-single-toggle",
            data=payload,
            content_type="application/json",
        )

        regular_user.refresh_from_db()
        assert regular_user.assigned_stations.count() == 1

    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("organization_admin_kyrgyz_api_client", 403),
            ("authenticated_regular_user_other_organization_api_client", 403),
            ("authenticated_regular_user_2_api_client", 403),
            ("authenticated_regular_user_api_client", 201),
            ("authenticated_organization_user_api_client", 201),
            ("superadmin_kyrgyz_api_client", 201),
            ("superadmin_uzbek_api_client", 201),
        ],
    )
    def test_toggle_assigned_station_for_other_users(
        self, client, expected_status_code, regular_user, manual_hydro_station, request
    ):
        client = request.getfixturevalue(client)

        payload = {"hydro_station_id": str(manual_hydro_station.uuid)}

        response = client.post(
            f"{self.endpoint}/{regular_user.uuid}/assigned-stations-single-toggle",
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == expected_status_code
