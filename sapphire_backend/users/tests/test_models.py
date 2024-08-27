import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import UserAssignedStation


class TestUserModelController:
    def test_display_name_for_user_with_first_and_last_name(self, inactive_user):
        assert inactive_user.display_name == "Inactive User"

    def test_display_name_for_user_without_first_or_last_name(self, user_without_first_last_name):
        assert user_without_first_last_name.display_name == "my_display_name"

    def test_display_name_for_user_with_only_first_name(self, user_with_only_first_name):
        assert user_with_only_first_name.display_name == "my_display_name"

    def test_display_name_for_user_with_only_last_name(self, user_with_only_last_name):
        assert user_with_only_last_name.display_name == "my_display_name"

    def test_is_admin_for_regular_user(self, regular_user):
        assert regular_user.is_admin is False

    def test_is_admin_for_organization_admin(self, organization_admin):
        assert organization_admin.is_admin

    def test_is_admin_for_super_admin(self, superadmin):
        assert superadmin.is_admin

    def test_is_organization_admin_for_regular_user(self, regular_user):
        assert regular_user.is_organization_admin is False

    def test_is_organization_admin_for_organization_admin(self, organization_admin):
        assert organization_admin.is_organization_admin

    def test_is_organization_admin_for_super_admin(self, superadmin):
        assert superadmin.is_organization_admin is False

    def test_is_super_admin_for_regular_user(self, regular_user):
        assert regular_user.is_superadmin is False

    def test_is_super_admin_for_organization_admin(self, organization_admin):
        assert organization_admin.is_superadmin is False

    def test_is_super_admin_for_super_admin(self, superadmin):
        assert superadmin.is_superadmin

    def test_user_soft_delete(self, deleted_user):
        deleted_user.soft_delete()

        assert deleted_user.username == f"User {deleted_user.uuid}"
        assert deleted_user.email == "deleted@user.com"
        assert deleted_user.organization is None
        assert deleted_user.is_active is False
        assert deleted_user.is_deleted


class TestUserAssignedStationModelController:
    def test_model_fields(self, regular_user, manual_hydro_station, regular_user_assigned_hydro_station):
        assert regular_user_assigned_hydro_station.user == regular_user
        assert regular_user_assigned_hydro_station.hydro_station == manual_hydro_station
        assert regular_user_assigned_hydro_station.meteo_station is None
        assert regular_user_assigned_hydro_station.virtual_station is None
        assert regular_user_assigned_hydro_station.assigned_by is None

    def test_station_property_for_hydro(self, manual_hydro_station, regular_user_assigned_hydro_station):
        assert regular_user_assigned_hydro_station.station == manual_hydro_station

    def test_station_property_for_meteo(self, manual_meteo_station, regular_user_assigned_meteo_station):
        assert regular_user_assigned_meteo_station.station == manual_meteo_station

    def test_station_property_for_virtual(self, virtual_station_kyrgyz, regular_user_assigned_virtual_station):
        assert regular_user_assigned_virtual_station.station == virtual_station_kyrgyz

    def test_save_with_no_assigned_station(self, regular_user):
        with pytest.raises(ValidationError, match="You must assign a station"):
            UserAssignedStation.objects.create(
                user=regular_user, hydro_station=None, meteo_station=None, virtual_station=None, assigned_by=None
            )

    def test_save_with_station_from_different_organization(
        self, regular_user, manual_hydro_station_other_organization
    ):
        with pytest.raises(ValidationError, match="The assigned station and user must be in the same organization"):
            UserAssignedStation.objects.create(
                user=regular_user,
                hydro_station=manual_hydro_station_other_organization,
                meteo_station=None,
                virtual_station=None,
                assigned_by=None,
            )

    def test_save_with_multiple_stations_assigned(self, regular_user, manual_hydro_station, manual_meteo_station):
        with pytest.raises(IntegrityError):
            UserAssignedStation.objects.create(
                user=regular_user,
                hydro_station=manual_hydro_station,
                meteo_station=manual_meteo_station,
                virtual_station=None,
                assigned_by=None,
            )
