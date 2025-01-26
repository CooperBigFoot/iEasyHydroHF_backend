import pytest
from unittest.mock import patch
from sapphire_backend.organizations.models import Organization, Basin, Region
from sapphire_backend.stations.models import HydrologicalStation, Site, MeteorologicalStation
from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.imomo.migrate_old_db import (
    MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ,
    MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ,
)
from sapphire_backend.imomo.migrate_old_db import migrate
from sapphire_backend.imomo.data_structs.standard_data import Variables
from sapphire_backend.metrics.models import HydrologicalMetric, MeteorologicalMetric
from sapphire_backend.metrics.choices import HydrologicalMetricName, HydrologicalMeasurementType, MetricUnit
from datetime import datetime, timezone

from .factories import DataValueFactory


@pytest.mark.django_db(transaction=True)
@patch('sapphire_backend.imomo.migrate_old_db.create_engine')
class TestImomoMigration:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, clean_django_db):
        """Run before and after each test"""
        # Setup
        yield
        # Teardown
        MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ.clear()
        MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ.clear()

    def verify_empty_state(self):
        """Verify that all relevant database tables are empty"""
        assert Organization.objects.count() == 0
        assert Basin.objects.count() == 0
        assert Region.objects.count() == 0
        assert Site.objects.count() == 0
        assert HydrologicalStation.objects.count() == 0
        assert DischargeModel.objects.count() == 0

    def test_initial_state(self, mock_create_engine):
        """Test that database starts empty"""
        self.verify_empty_state()

    def test_migrate_single_station(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first, old_kyrgyz_discharge_model_first
        ):
        """Test migration of a single station with its discharge model"""
        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        migrate(skip_cleanup=False, skip_structure=False, target_station="1234", target_organization="", limiter=100)

        # Check organization was created
        org = Organization.objects.get(name="КыргызГидроМет")
        assert org.language == Organization.Language.RUSSIAN

        # Check basin and region were created
        basin = Basin.objects.get(name="Нарын")
        region = Region.objects.get(name="ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ")

        # Check site was created with correct relationships
        site = Site.objects.get(
            organization=org,
            basin=basin,
            region=region,
            country="Kyrgyzstan"
        )
        assert site.latitude == 42.8746
        assert site.longitude == 74.5698

        # Check station was created with correct relationship to site
        station = HydrologicalStation.objects.get(
            station_code="1234",
            site=site
        )
        assert station.name == "Kyrgyz Station First"

        # Check discharge model was created
        model = DischargeModel.objects.get(station=station)
        assert model.name == "Kyrgyz Model First"
        assert model.param_a == 1.0

    def test_migrate_multiple_stations(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            old_kyrgyz_station_second, old_kyrgyz_discharge_model_first,
            old_kyrgyz_discharge_model_second
        ):
        """Test migration of multiple stations"""

        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        migrate(skip_cleanup=False, skip_structure=False, target_station="", target_organization="", limiter=100)

        # Check all objects were created
        assert Organization.objects.count() == 1
        org = Organization.objects.get(name="КыргызГидроМет")

        assert Basin.objects.count() == 1
        assert Region.objects.count() == 1
        assert Site.objects.count() == 2

        # Verify both stations exist and are linked to sites
        sites = Site.objects.filter(organization=org)
        assert sites.count() == 2

        stations = HydrologicalStation.objects.all()
        assert stations.count() == 2
        for station in stations:
            assert station.site in sites

        assert DischargeModel.objects.count() == 2

    def test_migrate_different_organizations(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            old_uzbek_station_first, old_kyrgyz_discharge_model_first,
            old_uzbek_discharge_model_first
        ):
        """Test migration of stations from different organizations"""

        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        migrate(skip_cleanup=False, skip_structure=False, target_station="", target_organization="", limiter=100)

        # Check organizations were created
        assert Organization.objects.count() == 2
        kyrgyz_org = Organization.objects.get(name="КыргызГидроМет")
        uzbek_org = Organization.objects.get(name="УзГидроМет")

        # Check sites were created with correct relationships
        assert Site.objects.count() == 2
        kyrgyz_site = Site.objects.get(organization=kyrgyz_org)
        uzbek_site = Site.objects.get(organization=uzbek_org)

        # Check stations were created with correct relationships
        assert HydrologicalStation.objects.count() == 2
        kyrgyz_station = HydrologicalStation.objects.get(station_code="1234")
        assert kyrgyz_station.site == kyrgyz_site

        uzbek_station = HydrologicalStation.objects.get(station_code="9012")
        assert uzbek_station.site == uzbek_site

    def test_migrate_organization_structure(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_station_first, old_uzbek_station_first):
        """Test migration of structure for specific organization"""

        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        # Migrate only Kyrgyz organization structure
        migrate(
            skip_cleanup=False,
            skip_structure=False,
            target_station="",
            target_organization="КыргызГидроМет",
            limiter=0
        )

        # Verify only Kyrgyz organization structure was created
        assert Organization.objects.count() == 1
        org = Organization.objects.get(name="КыргызГидроМет")

        # Check only Kyrgyz sites were created
        assert Site.objects.count() == 1
        site = Site.objects.first()
        assert site.organization == org

        # Check only Kyrgyz stations were created
        assert HydrologicalStation.objects.count() == 1
        station = HydrologicalStation.objects.first()
        assert station.site == site
        assert station.station_code == "1234"


@pytest.mark.django_db(transaction=True)
@patch('sapphire_backend.imomo.migrate_old_db.create_engine')
class TestImomoPartialMigration:
    """Test migration scenarios where structure already exists"""

    def test_migrate_discharge_model_with_existing_structure(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            old_kyrgyz_discharge_model_first, existing_kyrgyz_station):
        """Test migrating just a discharge model when station structure already exists"""

        assert DischargeModel.objects.filter(station=existing_kyrgyz_station).count() == 0
        mock_create_engine.return_value = old_db_session.bind
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="1234",
            target_organization="",
            limiter=100
        )

        # Verify discharge model was created
        model = DischargeModel.objects.get(station=existing_kyrgyz_station)
        assert model.name == "Kyrgyz Model First"
        assert model.param_a == 1.0

    def test_migrate_multiple_discharge_models_with_existing_structure(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_station_first, old_kyrgyz_station_second,
            old_kyrgyz_discharge_model_first, old_kyrgyz_discharge_model_second,
            existing_kyrgyz_station, existing_kyrgyz_station_second):
        """Test migrating multiple discharge models when stations already exist"""

        # Verify no discharge models exist initially
        assert DischargeModel.objects.count() == 0

        mock_create_engine.return_value = old_db_session.bind
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",  # Empty string to migrate all stations
            target_organization="",
            limiter=100
        )

        # Verify both discharge models were created
        assert DischargeModel.objects.count() == 2

        # Check first station's model
        model1 = DischargeModel.objects.get(station=existing_kyrgyz_station)
        assert model1.name == "Kyrgyz Model First"
        assert model1.param_a == 1.0

        # Check second station's model
        model2 = DischargeModel.objects.get(station=existing_kyrgyz_station_second)
        assert model2.name == "Kyrgyz Model Second"
        assert model2.param_a == 1.0

    def test_migrate_basic_water_level(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            existing_kyrgyz_station, old_water_level_value):
        """Test migrating a basic water level measurement"""

        assert HydrologicalMetric.objects.count() == 0
        mock_create_engine.return_value = old_db_session.bind

        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="1234",
            target_organization="",
            limiter=100
        )

        # Verify metric was created
        assert HydrologicalMetric.objects.count() == 1
        metric = HydrologicalMetric.objects.first()

        # Check metric fields
        assert metric.station == existing_kyrgyz_station
        assert metric.metric_name == HydrologicalMetricName.WATER_LEVEL_DAILY
        assert metric.value_type == HydrologicalMeasurementType.MANUAL
        assert float(metric.avg_value) == 123.45  # From fixture
        # Expect UTC timestamp in the metric
        expected_timestamp = old_water_level_value.local_date_time.replace(tzinfo=timezone.utc)
        assert metric.timestamp_local == expected_timestamp
        assert metric.unit == MetricUnit.WATER_LEVEL

    def test_migrate_nonexistent_organization(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            old_water_level_value):
        """Test migration with non-existing organization"""
        mock_create_engine.return_value = old_db_session.bind

        # Migrate with non-existent organization
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",
            target_organization="NonExistentOrg",
            limiter=100
        )

        # Verify no metrics were created
        assert HydrologicalMetric.objects.count() == 0

    def test_migrate_specific_organization_metrics(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_station_first, old_uzbek_station_first,
            old_water_level_value, old_uzbek_water_level_value,
            existing_kyrgyz_station, existing_uzbek_station):
        """Test migration of metrics for specific organization only"""
        mock_create_engine.return_value = old_db_session.bind

        # Migrate only Kyrgyz organization data
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",
            target_organization="КыргызГидроМет",
            limiter=100
        )

        # Verify only Kyrgyz metrics were created
        assert HydrologicalMetric.objects.count() == 1
        metric = HydrologicalMetric.objects.first()
        assert metric.station == existing_kyrgyz_station

    def test_migrate_invalid_organization_station_combination(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_station_first, old_water_level_value,
            existing_kyrgyz_station):
        """Test migration with mismatched organization and station"""
        mock_create_engine.return_value = old_db_session.bind

        # Try to migrate Kyrgyz station with Uzbek organization
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="1234",  # Kyrgyz station
            target_organization="УзГидроМет",  # Uzbek organization
            limiter=100
        )

        # Verify no metrics were created due to mismatch
        assert HydrologicalMetric.objects.count() == 0

    def test_migrate_organization_new_data(
        self, mock_create_engine, old_db_session,
        old_kyrgyz_station_first, old_water_level_value,
        existing_kyrgyz_station):
        """Test migration when organization has no existing data for timestamp"""
        mock_create_engine.return_value = old_db_session.bind

        # Create existing metric with different timestamp
        different_timestamp = old_water_level_value.local_date_time.replace(hour=10)  # 10:00 instead of 8:00
        existing_metric = HydrologicalMetric.objects.create(
            station=existing_kyrgyz_station,
            timestamp_local=different_timestamp.replace(tzinfo=timezone.utc),
            avg_value=999.99,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            unit=MetricUnit.WATER_LEVEL
        )

        initial_count = HydrologicalMetric.objects.count()

        # Migrate additional data
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",
            target_organization="КыргызГидроМет",
            limiter=100
        )

        # Verify new metric was added (no upsert, different timestamp)
        assert HydrologicalMetric.objects.count() == initial_count + 1
        assert HydrologicalMetric.objects.filter(avg_value=999.99).exists()
        assert HydrologicalMetric.objects.filter(avg_value=123.45).exists()

    def test_migrate_organization_upsert_data(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_station_first, old_water_level_value,
            existing_kyrgyz_station):
        """Test migration when organization has existing data for same timestamp (should upsert)"""
        mock_create_engine.return_value = old_db_session.bind

        # Create existing metric with same timestamp
        existing_metric = HydrologicalMetric.objects.create(
            station=existing_kyrgyz_station,
            timestamp_local=old_water_level_value.local_date_time.replace(tzinfo=timezone.utc),
            avg_value=999.99,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
            value_type=HydrologicalMeasurementType.MANUAL,
            unit=MetricUnit.WATER_LEVEL
        )

        initial_count = HydrologicalMetric.objects.count()

        # Migrate additional data
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",
            target_organization="КыргызГидроМет",
            limiter=100
        )

        # Verify upsert happened (count stayed same, value updated)
        assert HydrologicalMetric.objects.count() == initial_count  # No new records
        assert not HydrologicalMetric.objects.filter(avg_value=999.99).exists()  # Old value gone
        assert HydrologicalMetric.objects.filter(avg_value=123.45).exists()  # New value present

    def test_migrate_date_range_hydro_metrics(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_station_first, existing_kyrgyz_station):
        """Test migration of hydro metrics within date range"""
        mock_create_engine.return_value = old_db_session.bind

        # Create test data with different dates
        dates = [
            datetime(2023, 1, 1, 8, 0),  # Should be included
            datetime(2023, 2, 1, 8, 0),  # Should be included
            datetime(2023, 3, 1, 8, 0),  # Should be excluded
        ]

        for i, date in enumerate(dates):
            DataValueFactory.create(
                old_db_session,
                site=old_kyrgyz_station_first,
                local_date_time=date,
                data_value=100 + i,
                variable__variable_code=Variables.gauge_height_daily_measurement.value
            )

        # Migrate with date range
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="1234",
            target_organization="КыргызГидроМет",
            limiter=0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 28)
        )

        # Verify only metrics within date range were created
        assert HydrologicalMetric.objects.count() == 2
        assert HydrologicalMetric.objects.filter(avg_value=100).exists()  # Jan 1
        assert HydrologicalMetric.objects.filter(avg_value=101).exists()  # Feb 1
        assert not HydrologicalMetric.objects.filter(avg_value=102).exists()  # Mar 1 excluded

    def test_migrate_date_range_meteo_metrics(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_meteo_station, existing_kyrgyz_meteo_station):
        """Test migration of meteo metrics within date range"""
        mock_create_engine.return_value = old_db_session.bind

        # Create test data with different dates
        dates = [
            datetime(2023, 1, 1, 8, 0),  # Should be included
            datetime(2023, 2, 1, 8, 0),  # Should be included
            datetime(2023, 3, 1, 8, 0),  # Should be excluded
        ]

        for i, date in enumerate(dates):
            DataValueFactory.create(
                old_db_session,
                site=old_kyrgyz_meteo_station,
                local_date_time=date,
                data_value=100 + i,
                variable__variable_code=Variables.temperature_decade_average.value  # Use a meteo variable
            )

        # Migrate with date range
        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",
            target_organization="КыргызГидроМет",
            limiter=0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 28)
        )

        # Verify only metrics within date range were created
        assert MeteorologicalMetric.objects.count() == 2
        assert MeteorologicalMetric.objects.filter(value=100).exists()  # Jan 1
        assert MeteorologicalMetric.objects.filter(value=101).exists()  # Feb 1
        assert not MeteorologicalMetric.objects.filter(value=102).exists()  # Mar 1 excluded

    def test_migrate_invalid_values_meteo(
            self, mock_create_engine, old_db_session,
            old_kyrgyz_meteo_station, existing_kyrgyz_meteo_station
        ):
        """Test migration handles invalid meteo values (-9999)"""
        mock_create_engine.return_value = old_db_session.bind

        # Create test data with invalid values
        DataValueFactory.create(
            old_db_session,
            site=old_kyrgyz_meteo_station,
            local_date_time=datetime(2023, 1, 1, 8, 0),
            data_value=-9999,  # Should be skipped
            variable__variable_code=Variables.temperature_decade_average.value
        )
        DataValueFactory.create(
            old_db_session,
            site=old_kyrgyz_meteo_station,
            local_date_time=datetime(2023, 1, 3, 8, 0),
            data_value=100,  # Should be included
            variable__variable_code=Variables.temperature_decade_average.value
        )

        migrate(
            skip_cleanup=True,
            skip_structure=True,
            target_station="",
            target_organization="КыргызГидроМет",
            limiter=0
        )

        # Verify only valid metric was created
        assert MeteorologicalMetric.objects.count() == 1
        assert MeteorologicalMetric.objects.filter(value=100).exists()
