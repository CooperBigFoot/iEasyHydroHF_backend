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

    # TODO fix and rename the test. This test doesn't do what the name says and it doesn't work.
    #  Currently it checks if a regular user which is a member of an organization can
    #  get the details of his organization and should assert 200.
    #  To get 403 a new test needs to be made.
    # def test_get_organization_for_other_organization_admin(self, authenticated_regular_user_api_client,
    # organization):
    #     response = authenticated_regular_user_api_client.get(f"{self.endpoint}/{organization.uuid}")

    #     assert response.status_code == 403
    #     assert response.json()["detail"] == "You do not have permission to perform this action."
