import pytest

from sapphire_backend.estimations.query import EstimationsViewQueryManager


class TestEstimationsQueryManager:
    def test_invalid_model(self):
        with pytest.raises(
            ValueError,
            match="EstimationsViewQueryManager can only be instantiated with an existing view.",
        ):
            _ = EstimationsViewQueryManager("estimations_view_that_does_not_exist", "123")

    @pytest.mark.django_db
    def test_invalid_organization_uuid(self):
        with pytest.raises(ValueError, match="Organization with the given UUID does not exist."):
            _ = EstimationsViewQueryManager(
                "estimations_water_level_daily_average", "aaaa1111-bb22-cc33-dd44-eee555fff666"
            )

    def test_with_empty_filter_dict(self, organization):
        with pytest.raises(ValueError, match="EstimationsViewQueryManager requires filtering by station ID"):
            _ = EstimationsViewQueryManager("estimations_water_level_daily_average", organization.uuid, {})

    def test_available_filter_fields(self, organization, manual_hydro_station):
        query_manager = EstimationsViewQueryManager(
            "estimations_water_level_daily_average", organization.uuid, {"station_id": manual_hydro_station.id}
        )

        assert query_manager.filter_fields.sort() == ["station_id", "avg_value", "timestamp"].sort()

    def test_unsupported_filter_in_filter_fields(self, organization, manual_hydro_station):
        with pytest.raises(
            ValueError, match="something field does not exist on the estimations_water_level_daily_average view."
        ):
            _ = EstimationsViewQueryManager(
                "estimations_water_level_daily_average",
                organization.uuid,
                {"station_id": manual_hydro_station.id, "something": 123},
            )
