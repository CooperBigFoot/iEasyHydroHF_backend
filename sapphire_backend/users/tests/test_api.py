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

    def test_get_user_by_uuid_for_unauthorized_user(self, api_client, regular_user):
        response = api_client.get(f"{self.endpoint}/{regular_user.uuid}")

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_non_existing_user_by_uuid(self, authenticated_regular_user_api_client):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json() == {"detail": "User not found.", "code": "user_not_found"}

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
        print(response.json())
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

    def test_organization_admin_update_member_role(
        self, authenticated_organization_user_api_client, organization_admin
    ):
        pass
