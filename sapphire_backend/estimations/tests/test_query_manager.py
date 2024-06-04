import pytest

from sapphire_backend.estimations.query import EstimationsViewQueryManager


class TestEstimationsQueryManager:
    def test_invalid_model(self):
        with pytest.raises(
            ValueError,
            match="EstimationsViewQueryManager can only be instantiated with an existing view.",
        ):
            _ = EstimationsViewQueryManager("estimations_view_that_does_not_exist")

    def test_with_empty_filter_dict(self, organization):
        with pytest.raises(ValueError, match="EstimationsViewQueryManager requires filtering by station ID"):
            _ = EstimationsViewQueryManager("estimations_water_level_daily_average", {})

    def test_available_filter_fields(self, organization, manual_hydro_station):
        query_manager = EstimationsViewQueryManager(
            "estimations_water_level_daily_average", {"station_id": manual_hydro_station.id}
        )

        assert query_manager.filter_fields.sort() == ["station_id", "avg_value", "timestamp"].sort()

    def test_unsupported_filter_in_filter_fields(self, organization, manual_hydro_station):
        with pytest.raises(
            ValueError, match="something field does not exist on the estimations_water_level_daily_average view."
        ):
            _ = EstimationsViewQueryManager(
                "estimations_water_level_daily_average",
                {"station_id": manual_hydro_station.id, "something": 123},
            )
