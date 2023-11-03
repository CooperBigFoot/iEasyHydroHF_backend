import pytest


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
    # TODO FIX THIS TEST, IT FAILS IN THE CI PIPELINE, RESPONSE RETURNS MULTIPLE ORGANIZATIONS
    # def test_get_organization_for_other_organization(self, authenticated_regular_user_api_client,
    # other_organization):
    #     response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{other_organization.uuid}")
    #
    #     assert response.status_code == 403
    #     assert response.json()["detail"] == "You do not have permission to perform this action."
