import pytest


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

    def test_get_user_by_id(self, api_client, regular_user):
        response = api_client.get(f"{self.endpoint}/{regular_user.id}")

        assert response.status_code == 200
        assert response.json()["id"] == regular_user.id

    @pytest.mark.django_db
    def test_get_non_existing_user_by_id(self, api_client):
        response = api_client.get(f"{self.endpoint}/999999999999")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "User not found.",
            "code": "user_not_found"
        }

    def test_get_inactive_user_by_id(self, api_client, inactive_user):
        response = api_client.get(f"{self.endpoint}/{inactive_user.id}")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "User not found.",
            "code": "user_not_found"
        }
