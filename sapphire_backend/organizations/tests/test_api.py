import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


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
    basin_data = {"name": "Test basin", "secondary_name": "", "bulletin_order": 0}

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 201),
            ("organization_admin_kyrgyz_api_client", 201),
            ("superadmin_kyrgyz_api_client", 201),
            ("superadmin_uzbek_api_client", 201),
        ],
    )
    def test_create_basin_success(self, client, organization_kyrgyz, expected_status_code, request):
        client = request.getfixturevalue(client)
        response = client.post(
            f"{self.endpoint}/{organization_kyrgyz.uuid}", self.basin_data, content_type="application/json"
        )
        assert response.status_code == expected_status_code

    @pytest.mark.django_db
    def test_create_basin_invalid_data(self, authenticated_regular_user_api_client, organization):
        invalid_basin_data = {"name": "Doesn't have other fields"}  # Incomplete or invalid data
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
        assert response.json()["detail"] == "Object does not exist"

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
    region_data = {"name": "Test region", "secondary_name": "", "bulletin_order": 0}

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "client, expected_status_code",
        [
            ("unauthenticated_api_client", 401),
            ("regular_user_uzbek_api_client", 403),
            ("organization_admin_uzbek_api_client", 403),
            ("regular_user_kyrgyz_api_client", 201),
            ("organization_admin_kyrgyz_api_client", 201),
            ("superadmin_kyrgyz_api_client", 201),
            ("superadmin_uzbek_api_client", 201),
        ],
    )
    def test_create_region_success(self, client, organization_kyrgyz, expected_status_code, request):
        client = request.getfixturevalue(client)
        response = client.post(
            f"{self.endpoint}/{organization_kyrgyz.uuid}", self.region_data, content_type="application/json"
        )
        assert response.status_code == expected_status_code

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
        assert response.json()["detail"] == "Object does not exist"

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


class TestOrganizationMembersAPIController:
    endpoint = "/api/v1/organizations"
    new_user_data = {
        "username": "user123",
        "email": "user123@user.com",
        "user_role": User.UserRoles.REGULAR_USER,
        "language": User.Language.ENGLISH,
    }

    @pytest.mark.django_db
    def test_get_organization_members(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{organization.uuid}/members")
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.django_db
    def test_add_organization_member_as_regular_user(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}/members/add",
            data=self.new_user_data,
            content_type="application/json",
        )
        assert response.status_code == 403  # forbidden

    @pytest.mark.django_db
    def test_add_organization_member_as_organization_admin(
        self, authenticated_organization_user_api_client, organization
    ):
        response = authenticated_organization_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}/members/add",
            data=self.new_user_data,
            content_type="application/json",
        )
        assert response.status_code == 201
        assert "id" in response.json()
        assert User.objects.filter(username="user123").exists()

    @pytest.mark.django_db
    def test_add_organization_member_as_superadmin(self, authenticated_superadmin_user_api_client, organization):
        response = authenticated_superadmin_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}/members/add",
            data=self.new_user_data,
            content_type="application/json",
        )
        assert response.status_code == 201
        assert "id" in response.json()
        assert User.objects.filter(username="user123").exists()

    @pytest.mark.django_db
    def test_add_organization_member_missing_data(self, authenticated_organization_user_api_client, organization):
        invalid_user_data = {"username": "", "email": "", "user_role": "", "language": ""}
        response = authenticated_organization_user_api_client.post(
            f"{self.endpoint}/{organization.uuid}/members/add", data=invalid_user_data, content_type="application/json"
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "Some data is invalid or missing", "code": "schema_error"}
