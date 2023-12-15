import pytest

from ..models import Basin, Region


class TestOrganizationsAPIController:
    endpoint = "/api/v1/organizations"

    @pytest.mark.django_db
    def test_get_single_organization_for_anonymous_user(self, organization, api_client):
        response = api_client.get(f"{self.endpoint}/{organization.uuid}")

        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    @pytest.mark.django_db
    def test_get_organizations_for_anonymous_user(self, api_client):
        response = api_client.get(self.endpoint)

        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"

    def test_get_organization_for_other_organization_admin(
        self, authenticated_regular_user_api_client, backup_organization
    ):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{backup_organization.uuid}")

        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to perform this action."


class TestBasinsAPIController:
    endpoint = "/api/v1/basins"
    basin_data = {"name": "Test basin"}

    @pytest.mark.django_db
    def test_create_basin_success(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}", self.basin_data, content_type="application/json"
        )
        assert response.status_code == 201
        assert "id" in response.json()
        assert Basin.objects.get(pk=response.json()["id"]).organization == organization

    @pytest.mark.django_db
    def test_create_basin_unauthorized(self, api_client, organization):
        response = api_client.post(f"/api/v1/basins/{organization.uuid}", self.basin_data)
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_create_basin_invalid_data(self, authenticated_regular_user_api_client, organization):
        invalid_basin_data = {"name": ""}  # Incomplete or invalid data
        response = authenticated_regular_user_api_client.post(
            f"/api/v1/basins/{organization.uuid}", invalid_basin_data
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_create_basin_missing_data(self, authenticated_regular_user_api_client, organization):
        invalid_basin_data = {}  # Incomplete or invalid data
        response = authenticated_regular_user_api_client.post(
            f"/api/v1/basins/{organization.uuid}", invalid_basin_data
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_get_basin_success(self, authenticated_regular_user_api_client, basin):
        response = authenticated_regular_user_api_client.get(f"/api/v1/basins/{basin.organization.uuid}/{basin.uuid}")
        assert response.status_code == 200
        assert response.json()["uuid"] == str(basin.uuid)

    @pytest.mark.django_db
    def test_get_basin_not_found(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(
            f"/api/v1/basins/{organization.uuid}/11111111-aaaa-bbbb-cccc-222222222222"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Basin not found."

    @pytest.mark.django_db
    def test_get_basin_unauthorized(self, api_client, basin):
        response = api_client.get(f"/api/v1/basins/{basin.organization.uuid}/{basin.uuid}")
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_get_basin_from_other_organization(self, authenticated_regular_user_other_organization_api_client, basin):
        response = authenticated_regular_user_other_organization_api_client.get(
            f"/api/v1/basins/{basin.organization.uuid}/{basin.uuid}"
        )
        assert response.status_code == 403
        assert "detail" in response.json()


class TestRegionsAPIController:
    endpoint = "/api/v1/regions"
    region_data = {
        "name": "Test region",
        # Add other required fields
    }

    @pytest.mark.django_db
    def test_create_region_success(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}", self.region_data, content_type="application/json"
        )
        assert response.status_code == 201
        assert "id" in response.json()
        assert Region.objects.get(pk=response.json()["id"]).organization == organization

    @pytest.mark.django_db
    def test_create_region_unauthorized(self, api_client, organization):
        response = api_client.post(f"{self.endpoint}/{organization.uuid}", self.region_data)
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_create_region_invalid_data(self, authenticated_regular_user_api_client, organization):
        invalid_region_data = {"name": ""}  # Incomplete or invalid data
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}", invalid_region_data
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_get_region_success(self, authenticated_regular_user_api_client, region):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{region.organization.uuid}/{region.uuid}"
        )
        assert response.status_code == 200
        assert response.json()["uuid"] == str(region.uuid)

    @pytest.mark.django_db
    def test_get_region_not_found(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(
            f"{self.endpoint}/{organization.uuid}/11111111-aaaa-bbbb-cccc-222222222222"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Region not found."

    @pytest.mark.django_db
    def test_get_region_unauthorized(self, api_client, region):
        response = api_client.get(f"{self.endpoint}/{region.organization.uuid}/{region.uuid}")
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.django_db
    def test_get_region_from_other_organization(
        self, authenticated_regular_user_other_organization_api_client, region
    ):
        response = authenticated_regular_user_other_organization_api_client.get(
            f"{self.endpoint}/{region.organization.uuid}/{region.uuid}"
        )
        assert response.status_code == 403
        assert "detail" in response.json()
