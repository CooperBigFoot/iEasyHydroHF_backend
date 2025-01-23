import pytest
from unittest.mock import patch
from sapphire_backend.organizations.models import Organization, Basin, Region
from sapphire_backend.stations.models import HydrologicalStation, Site
from sapphire_backend.estimations.models import DischargeModel
from sapphire_backend.imomo.migrate_old_db import MAP_OLD_SITE_CODE_TO_NEW_SITE_OBJ, MAP_OLD_SOURCE_ID_TO_NEW_ORGANIZATION_OBJ

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
        from sapphire_backend.imomo.migrate_old_db import migrate

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
        from sapphire_backend.imomo.migrate_old_db import migrate

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
        from sapphire_backend.imomo.migrate_old_db import migrate

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


@pytest.mark.django_db(transaction=True)
@patch('sapphire_backend.imomo.migrate_old_db.create_engine')
class TestImomoPartialMigration:
    """Test migration scenarios where structure already exists"""

    def test_migrate_discharge_model_with_existing_structure(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            old_kyrgyz_discharge_model_first, existing_kyrgyz_station):
        """Test migrating just a discharge model when station structure already exists"""
        from sapphire_backend.imomo.migrate_old_db import migrate

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
        from sapphire_backend.imomo.migrate_old_db import migrate

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


@pytest.mark.django_db(transaction=True)
@patch('sapphire_backend.imomo.migrate_old_db.create_engine')
class TestImomoMetricMigration:
    """Test migration of metrics from old DataValue to new HydrologicalMetric"""

    def test_migrate_basic_water_level(
            self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
            existing_kyrgyz_station, old_water_level_value):
        """Test migrating a basic water level measurement"""
        from sapphire_backend.imomo.migrate_old_db import migrate
        from sapphire_backend.metrics.models import HydrologicalMetric
        from sapphire_backend.metrics.choices import HydrologicalMetricName, HydrologicalMeasurementType, MetricUnit

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
        assert metric.timestamp_local == old_water_level_value.local_date_time
        assert metric.unit == MetricUnit.CENTIMETER
