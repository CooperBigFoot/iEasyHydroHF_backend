import pytest


class TestAuthController:
    endpoint = "/api/v1/auth"

    def test_token_obtain_for_valid_credentials(self, api_client, regular_user):
        user_data = {"username": regular_user.username, "password": "password123"}
        response = api_client.post(f"{self.endpoint}/token-obtain", data=user_data, content_type="application/json")

        assert response.status_code == 200

        response_data = response.json()

        assert all(key in response_data for key in ["refresh", "access", "user"])
        assert all(
            key in response_data["user"]
            for key in [
                "id",
                "uuid",
                "username",
                "email",
                "first_name",
                "avatar",
                "last_name",
                "contact_phone",
                "user_role",
                "display_name",
                "organization",
            ]
        )

    def test_token_obtain_for_invalid_credentials(self, api_client, regular_user):
        user_data = {"username": regular_user.username, "password": "wrong-password"}
        response = api_client.post(f"{self.endpoint}/token-obtain", data=user_data, content_type="application/json")

        assert response.status_code == 401
        assert response.json() == {"detail": "No active account found with the given credentials", "code": ""}

    def test_token_obtain_for_inactive_user(self, api_client, inactive_user):
        user_data = {"username": inactive_user.username, "password": "password123"}

        response = api_client.post(f"{self.endpoint}/token-obtain", data=user_data, content_type="application/json")

        assert response.status_code == 401
        assert response.json() == {"detail": "No active account found with the given credentials", "code": ""}

    @pytest.mark.django_db
    def test_token_obtain_for_non_existing_user(self, api_client):
        user_data = {"username": "non-existing", "password": "password123"}

        response = api_client.post(f"{self.endpoint}/token-obtain", data=user_data, content_type="application/json")

        assert response.status_code == 401
        assert response.json() == {"detail": "No active account found with the given credentials", "code": ""}

    @pytest.mark.django_db
    def test_token_obtain_for_missing_username(self, api_client):
        user_data = {"password": "password123"}

        response = api_client.post(f"{self.endpoint}/token-obtain", data=user_data, content_type="application/json")

        assert response.status_code == 400

    def test_token_refresh_for_valid_token(self, regular_user, api_client):
        user_data = {"username": regular_user.username, "password": "password123"}
        login_response = api_client.post(
            f"{self.endpoint}/token-obtain", data=user_data, content_type="application/json"
        )

        token_refresh_data = {"refresh": login_response.json()["refresh"]}
        refresh_response = api_client.post(
            f"{self.endpoint}/token-refresh", data=token_refresh_data, content_type="application/json"
        )

        assert refresh_response.status_code == 200

    @pytest.mark.django_db
    def test_token_refresh_for_invalid_token(self, api_client):
        token_refresh_data = {"refresh": "1234abcd5678efgh"}

        refresh_response = api_client.post(
            f"{self.endpoint}/token-refresh", data=token_refresh_data, content_type="application/json"
        )

        assert refresh_response.status_code == 401
        assert refresh_response.json() == {"detail": "Token is invalid or expired", "code": "token_not_valid"}
