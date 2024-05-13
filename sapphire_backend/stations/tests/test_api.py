from ..models import VirtualStation, VirtualStationAssociation


class TestVirtualStationsAPI:
    endpoint = "/api/v1/stations/{}/virtual"
    endpoint_detail = "/api/v1/stations/{}/virtual/{}"
    new_station_payload = {
        "name": "New Virtual Station",
        "description": "",
        "station_code": "55555",
        "latitude": 45.35227,
        "longitude": 19.00459,
        "timezone": "Europe/Zagreb",
        "country": "Croatia",
    }

    def test_get_all_virtual_stations_for_unauthorized_user(self, api_client, organization):
        response = api_client.get(self.endpoint.format(organization.uuid))
        assert response.status_code == 401

    def test_get_all_virtual_stations_for_other_organization_user(
        self, authenticated_regular_user_other_organization_api_client, organization
    ):
        response = authenticated_regular_user_other_organization_api_client.get(
            self.endpoint.format(organization.uuid)
        )
        assert response.status_code == 403

    def test_get_all_virtual_stations_for_super_admin(self, authenticated_superadmin_user_api_client, organization):
        response = authenticated_superadmin_user_api_client.get(self.endpoint.format(organization.uuid))
        assert response.status_code == 200

    def test_get_all_virtual_stations_for_regular_user(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(self.endpoint.format(organization.uuid))
        assert response.status_code == 200

    def test_get_all_virtual_stations_return_only_active_stations_for_own_organization(
        self,
        authenticated_regular_user_api_client,
        organization,
        virtual_station,
        virtual_station_no_associations,
        virtual_station_backup_organization,
        virtual_station_deleted,
    ):
        assert VirtualStation.objects.count() == 4

        response = authenticated_regular_user_api_client.get(self.endpoint.format(organization.uuid))

        assert len(response.json()) == 2

    def test_get_all_virtual_stations_expected_response(
        self,
        authenticated_regular_user_api_client,
        organization,
        virtual_station,
        virtual_station_no_associations,
        virtual_station_backup_organization,
        virtual_station_deleted,
    ):
        response = authenticated_regular_user_api_client.get(self.endpoint.format(organization.uuid))

        EXPECTED_RESPONSE = [
            {
                "basin": {
                    "name": virtual_station.basin.name,
                    "id": virtual_station.basin.id,
                    "uuid": str(virtual_station.basin.uuid),
                },
                "region": {
                    "name": virtual_station.region.name,
                    "id": virtual_station.region.id,
                    "uuid": str(virtual_station.region.uuid),
                },
                "uuid": str(virtual_station.uuid),
                "id": virtual_station.id,
                "name": virtual_station.name,
                "station_code": virtual_station.station_code,
                "latitude": float(virtual_station.latitude) if virtual_station.latitude else None,
                "longitude": float(virtual_station.longitude) if virtual_station.longitude else None,
                "timezone": str(virtual_station.timezone),
                "country": virtual_station.country,
                "description": virtual_station.description,
                "elevation": virtual_station.elevation,
                "station_type": "V",
            },
            {
                "basin": {
                    "name": virtual_station_no_associations.basin.name,
                    "id": virtual_station_no_associations.basin.id,
                    "uuid": str(virtual_station_no_associations.basin.uuid),
                },
                "region": {
                    "name": virtual_station_no_associations.region.name,
                    "id": virtual_station_no_associations.region.id,
                    "uuid": str(virtual_station_no_associations.region.uuid),
                },
                "uuid": str(virtual_station_no_associations.uuid),
                "id": virtual_station_no_associations.id,
                "name": virtual_station_no_associations.name,
                "station_code": virtual_station_no_associations.station_code,
                "latitude": float(virtual_station_no_associations.latitude)
                if virtual_station_no_associations.latitude
                else None,
                "longitude": float(virtual_station_no_associations.longitude)
                if virtual_station_no_associations.latitude
                else None,
                "timezone": str(virtual_station_no_associations.timezone),
                "country": virtual_station_no_associations.country,
                "description": virtual_station_no_associations.description,
                "elevation": virtual_station_no_associations.elevation,
                "station_type": "V",
            },
        ]

        assert response.json() == EXPECTED_RESPONSE

    def test_get_single_station_for_unauthorized_user(self, api_client, organization, virtual_station):
        response = api_client.get(self.endpoint_detail.format(organization.uuid, virtual_station.uuid))
        assert response.status_code == 401

    def test_get_single_station_from_different_organization(
        self, authenticated_regular_user_api_client, backup_organization, virtual_station_backup_organization
    ):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(backup_organization.uuid, virtual_station_backup_organization.uuid)
        )
        assert response.status_code == 403

    def test_get_single_station_for_super_admin(
        self, authenticated_superadmin_user_api_client, backup_organization, virtual_station_backup_organization
    ):
        response = authenticated_superadmin_user_api_client.get(
            self.endpoint_detail.format(backup_organization.uuid, virtual_station_backup_organization.uuid)
        )
        assert response.status_code == 200

    def test_get_single_station_that_does_not_exist(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(organization.uuid, "11111111-aaaa-bbbb-cccc-222222222222")
        )

        assert response.status_code == 404

    def test_get_single_station(self, authenticated_regular_user_api_client, organization, virtual_station):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(organization.uuid, virtual_station.uuid)
        )

        assert response.status_code == 200

    def test_get_single_station_no_associations_response(
        self, authenticated_regular_user_api_client, organization, virtual_station_no_associations
    ):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(organization.uuid, virtual_station_no_associations.uuid)
        )

        EXPECTED_RESPONSE = {
            "uuid": str(virtual_station_no_associations.uuid),
            "basin": {
                "name": virtual_station_no_associations.basin.name,
                "id": virtual_station_no_associations.basin.id,
                "uuid": str(virtual_station_no_associations.basin.uuid),
            },
            "region": {
                "name": virtual_station_no_associations.region.name,
                "id": virtual_station_no_associations.region.id,
                "uuid": str(virtual_station_no_associations.region.uuid),
            },
            "country": virtual_station_no_associations.country,
            "latitude": float(virtual_station_no_associations.latitude),
            "longitude": float(virtual_station_no_associations.longitude),
            "timezone": str(virtual_station_no_associations.timezone),
            "elevation": virtual_station_no_associations.elevation,
            "name": virtual_station_no_associations.name,
            "description": virtual_station_no_associations.description,
            "station_code": virtual_station_no_associations.station_code,
            "id": virtual_station_no_associations.id,
            "station_type": "V",
            "associations": [],
        }

        assert response.json() == EXPECTED_RESPONSE

    def test_get_single_station_with_associations(
        self,
        authenticated_regular_user_api_client,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        manual_hydro_station,
        automatic_hydro_station,
    ):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(organization.uuid, virtual_station.uuid)
        )

        EXPECTED_ASSOCIATIONS = [
            {
                "name": automatic_hydro_station.name,
                "id": automatic_hydro_station.id,
                "uuid": str(automatic_hydro_station.uuid),
                "weight": virtual_station_association_one.weight,
                "station_code": automatic_hydro_station.station_code,
            },
            {
                "name": manual_hydro_station.name,
                "id": manual_hydro_station.id,
                "uuid": str(manual_hydro_station.uuid),
                "weight": virtual_station_association_two.weight,
                "station_code": manual_hydro_station.station_code,
            },
        ]

        assert response.json()["associations"] == EXPECTED_ASSOCIATIONS

    def test_create_new_virtual_station_for_unauthorized_user(self, api_client, organization):
        response = api_client.post(
            self.endpoint.format(organization.uuid), data=self.new_station_payload, content_type="application/json"
        )

        assert response.status_code == 401

    def test_create_new_virtual_station_for_other_organization(
        self, authenticated_regular_user_other_organization_api_client, organization, region, basin
    ):
        payload = self.new_station_payload.copy()
        payload["basin_id"] = str(basin.uuid)
        payload["region_id"] = str(region.uuid)
        response = authenticated_regular_user_other_organization_api_client.post(
            self.endpoint.format(organization.uuid), data=payload, content_type="application/json"
        )

        assert response.status_code == 403

    def test_create_new_virtual_station_with_missing_payload_data(
        self, authenticated_regular_user_api_client, organization
    ):
        response = authenticated_regular_user_api_client.post(
            self.endpoint.format(organization.uuid), data=self.new_station_payload, content_type="application/json"
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "Some data is invalid or missing", "code": "schema_error"}

    def test_create_new_virtual_station_with_duplicate_station_code(
        self, authenticated_regular_user_api_client, organization, basin, region, virtual_station
    ):
        payload = self.new_station_payload.copy()
        payload["basin_id"] = str(basin.uuid)
        payload["region_id"] = str(region.uuid)
        payload["station_code"] = virtual_station.station_code

        response = authenticated_regular_user_api_client.post(
            self.endpoint.format(organization.uuid), data=payload, content_type="application/json"
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Object could not be saved", "code": "integrity_error"}

    def test_create_new_virtual_station_with_valid_payload_data(
        self, authenticated_regular_user_api_client, organization, basin, region
    ):
        payload = self.new_station_payload.copy()
        payload["basin_id"] = str(basin.uuid)
        payload["region_id"] = str(region.uuid)

        response = authenticated_regular_user_api_client.post(
            self.endpoint.format(organization.uuid), data=payload, content_type="application/json"
        )

        assert response.status_code == 201
        assert VirtualStation.objects.count() == 1

        station = VirtualStation.objects.last()

        EXPECTED_RESPONSE = {
            "basin": {
                "name": basin.name,
                "id": basin.id,
                "uuid": str(basin.uuid),
            },
            "region": {
                "name": region.name,
                "id": region.id,
                "uuid": str(region.uuid),
            },
            "elevation": None,
            "name": "New Virtual Station",
            "description": "",
            "station_code": "55555",
            "latitude": 45.35227,
            "longitude": 19.00459,
            "timezone": "Europe/Zagreb",
            "country": "Croatia",
            "id": station.id,
            "uuid": str(station.uuid),
            "station_type": "V",
            "associations": [],
        }

        assert response.json() == EXPECTED_RESPONSE

    def test_update_virtual_station_that_does_not_exist(self, authenticated_regular_user_api_client, organization):
        payload = {"name": "New Name"}

        response = authenticated_regular_user_api_client.put(
            self.endpoint_detail.format(organization.uuid, "11111111-aaaa-bbbb-cccc-222222222222"),
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_update_virtual_station(self, authenticated_regular_user_api_client, organization, virtual_station):
        payload = {"name": "New Name"}

        response = authenticated_regular_user_api_client.put(
            self.endpoint_detail.format(organization.uuid, virtual_station.uuid),
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == 200

        vs_from_db = VirtualStation.objects.get(id=virtual_station.id)

        assert vs_from_db.name == "New Name"

    def test_delete_virtual_station_that_does_not_exist(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.delete(
            self.endpoint_detail.format(organization.uuid, "11111111-aaaa-bbbb-cccc-222222222222")
        )

        assert response.status_code == 404

    def test_delete_virtual_station(self, authenticated_regular_user_api_client, organization, virtual_station):
        _ = authenticated_regular_user_api_client.delete(
            self.endpoint_detail.format(organization.uuid, virtual_station.uuid)
        )

        vs = VirtualStation.objects.get(id=virtual_station.id)

        assert vs.is_deleted is True

    def test_create_associations_with_empty_list_removes_existing_associations(
        self,
        authenticated_regular_user_api_client,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
    ):
        vs = VirtualStation.objects.get(id=virtual_station.id)
        assert vs.virtualstationassociation_set.count() == 2

        payload = []

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint_detail.format(organization.uuid, virtual_station.uuid)}/associations",
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == 201

        assert response.json()["associations"] == []

        vs.refresh_from_db()

        assert vs.virtualstationassociation_set.count() == 0

    def test_create_associations_overwrites_existing_associations(
        self,
        authenticated_regular_user_api_client,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        automatic_hydro_station_backup,
    ):
        payload = [{"uuid": str(automatic_hydro_station_backup.uuid), "weight": 100}]

        vs = VirtualStation.objects.get(id=virtual_station.id)
        assert vs.virtualstationassociation_set.count() == 2

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint_detail.format(organization.uuid, virtual_station.uuid)}/associations",
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == 201

        assert response.json()["associations"] == [
            {
                "uuid": str(automatic_hydro_station_backup.uuid),
                "id": automatic_hydro_station_backup.id,
                "weight": 100,
                "name": automatic_hydro_station_backup.name,
                "station_code": automatic_hydro_station_backup.station_code,
            }
        ]

        vs.refresh_from_db()

        assert vs.virtualstationassociation_set.count() == 1
        assert VirtualStationAssociation.objects.count() == 1


class TestForecastStatusAPI:
    endpoint = "/api/v1/stations/{}/forecast-status"
    endpoint_detail = "/api/v1/stations/{}/forecast-status/{}"

    def test_get_status_for_unauthenticated_user(self, api_client, organization):
        response = api_client.get(self.endpoint.format(organization.uuid))

        assert response.status_code == 401

    def test_get_status_for_unauthorized_user(self, authenticated_regular_user_api_client, backup_organization):
        response = authenticated_regular_user_api_client.get(self.endpoint.format(backup_organization.uuid))

        assert response.status_code == 403

    def test_get_status_for_no_stations(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(self.endpoint.format(organization.uuid))

        assert response.status_code == 200
        assert response.json() == []

    def test_get_status_for_all_stations(
        self, authenticated_regular_user_api_client, organization, manual_hydro_station, automatic_hydro_station
    ):
        response = authenticated_regular_user_api_client.get(self.endpoint.format(organization.uuid))

        assert response.json() == [
            {
                "daily_forecast": False,
                "pentad_forecast": False,
                "decadal_forecast": False,
                "monthly_forecast": False,
                "seasonal_forecast": False,
                "uuid": str(manual_hydro_station.uuid),
                "station_code": manual_hydro_station.station_code,
                "id": manual_hydro_station.id,
                "name": manual_hydro_station.name,
                "station_type": "M",
            },
            {
                "daily_forecast": False,
                "pentad_forecast": False,
                "decadal_forecast": False,
                "monthly_forecast": False,
                "seasonal_forecast": False,
                "uuid": str(automatic_hydro_station.uuid),
                "station_code": automatic_hydro_station.station_code,
                "id": automatic_hydro_station.id,
                "name": automatic_hydro_station.name,
                "station_type": "A",
            },
        ]

    def test_for_single_non_existing_station(self, authenticated_regular_user_api_client, organization):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(organization.uuid, "11111111-aaaa-bbbb-cccc-222222222222")
        )

        assert response.status_code == 404

    def test_for_single_station_from_different_organization(
        self, authenticated_regular_user_other_organization_api_client, organization, manual_hydro_station
    ):
        response = authenticated_regular_user_other_organization_api_client.get(
            self.endpoint_detail.format(organization.uuid, manual_hydro_station.uuid)
        )

        assert response.status_code == 403

    def test_for_single_station(self, authenticated_regular_user_api_client, organization, manual_hydro_station):
        response = authenticated_regular_user_api_client.get(
            self.endpoint_detail.format(organization.uuid, manual_hydro_station.uuid)
        )

        assert response.status_code == 200
        assert response.json() == {
            "daily_forecast": False,
            "pentad_forecast": False,
            "decadal_forecast": False,
            "monthly_forecast": False,
            "seasonal_forecast": False,
            "uuid": str(manual_hydro_station.uuid),
            "station_code": manual_hydro_station.station_code,
            "id": manual_hydro_station.id,
            "name": manual_hydro_station.name,
            "station_type": "M",
        }

    def test_set_status_for_non_existing_station(self, authenticated_regular_user_api_client, organization):
        data = {
            "daily_forecast": True,
            "pentad_forecast": True,
            "decadal_forecast": False,
            "monthly_forecast": False,
            "seasonal_forecast": False,
        }

        response = authenticated_regular_user_api_client.post(
            self.endpoint_detail.format(organization.uuid, "11111111-aaaa-bbbb-cccc-222222222222"),
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_for_incomplete_payload(self, authenticated_regular_user_api_client, organization, manual_hydro_station):
        data = {"daily_forecast": True, "pentad_forecast": True, "seasonal_forecast": False}

        response = authenticated_regular_user_api_client.post(
            self.endpoint_detail.format(organization, manual_hydro_station.uuid),
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 422

    def test_set_forecast_status(self, authenticated_regular_user_api_client, organization, manual_hydro_station):
        data = {
            "daily_forecast": True,
            "pentad_forecast": True,
            "decadal_forecast": False,
            "monthly_forecast": False,
            "seasonal_forecast": False,
        }

        response = authenticated_regular_user_api_client.post(
            self.endpoint_detail.format(organization.uuid, manual_hydro_station.uuid),
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json() == {
            "daily_forecast": True,
            "pentad_forecast": True,
            "decadal_forecast": False,
            "monthly_forecast": False,
            "seasonal_forecast": False,
            "uuid": str(manual_hydro_station.uuid),
            "station_code": manual_hydro_station.station_code,
            "id": manual_hydro_station.id,
            "name": manual_hydro_station.name,
            "station_type": "M",
        }

    def test_bulk_toggle_for_non_existing_stations(self, authenticated_regular_user_api_client, organization):
        data = ["11111111-aaaa-bbbb-cccc-222222222222"]
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint.format(organization.uuid)}/bulk-toggle?action=on",
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json() == []

    def test_bulk_toggle_for_single_station(
        self, authenticated_regular_user_api_client, organization, manual_hydro_station
    ):
        data = [str(manual_hydro_station.uuid)]
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint.format(organization.uuid)}/bulk-toggle?action=on",
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json() == [
            {
                "daily_forecast": True,
                "pentad_forecast": True,
                "decadal_forecast": True,
                "monthly_forecast": True,
                "seasonal_forecast": True,
                "uuid": str(manual_hydro_station.uuid),
                "station_code": manual_hydro_station.station_code,
                "id": manual_hydro_station.id,
                "name": manual_hydro_station.name,
                "station_type": "M",
            }
        ]

        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint.format(organization.uuid)}/bulk-toggle?action=off",
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json() == [
            {
                "daily_forecast": False,
                "pentad_forecast": False,
                "decadal_forecast": False,
                "monthly_forecast": False,
                "seasonal_forecast": False,
                "uuid": str(manual_hydro_station.uuid),
                "station_code": manual_hydro_station.station_code,
                "id": manual_hydro_station.id,
                "name": manual_hydro_station.name,
                "station_type": "M",
            }
        ]

    def test_bulk_toggle_for_multiple_stations(
        self, authenticated_regular_user_api_client, organization, manual_hydro_station, automatic_hydro_station
    ):
        data = [
            str(manual_hydro_station.uuid),
            str(automatic_hydro_station.uuid),
            "11111111-aaaa-bbbb-cccc-222222222222",
        ]
        response = authenticated_regular_user_api_client.post(
            f"{self.endpoint.format(organization.uuid)}/bulk-toggle?action=on",
            data=data,
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json() == [
            {
                "daily_forecast": True,
                "pentad_forecast": True,
                "decadal_forecast": True,
                "monthly_forecast": True,
                "seasonal_forecast": True,
                "uuid": str(manual_hydro_station.uuid),
                "station_code": manual_hydro_station.station_code,
                "id": manual_hydro_station.id,
                "name": manual_hydro_station.name,
                "station_type": "M",
            },
            {
                "daily_forecast": True,
                "pentad_forecast": True,
                "decadal_forecast": True,
                "monthly_forecast": True,
                "seasonal_forecast": True,
                "uuid": str(automatic_hydro_station.uuid),
                "station_code": automatic_hydro_station.station_code,
                "id": automatic_hydro_station.id,
                "name": automatic_hydro_station.name,
                "station_type": "A",
            },
        ]
