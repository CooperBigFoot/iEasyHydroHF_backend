import pytest
from unittest.mock import patch
from sapphire_backend.organizations.models import Organization, Basin, Region
from sapphire_backend.stations.models import HydrologicalStation, Site
from sapphire_backend.estimations.models import DischargeModel

@pytest.mark.django_db
@patch('sapphire_backend.imomo.migrate_old_db.create_engine')
class TestMigration:
    def verify_empty_state(self):
        """Verify that all relevant database tables are empty"""
        assert Organization.objects.count() == 0
        assert Basin.objects.count() == 0
        assert Region.objects.count() == 0
        assert Site.objects.count() == 0
        assert HydrologicalStation.objects.count() == 0
        assert DischargeModel.objects.count() == 0

    def test_initial_state(self, mock_create_engine, clean_django_db):
        """Test that database starts empty"""
        self.verify_empty_state()

    def test_migrate_single_station(self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
                                  old_kyrgyz_discharge_model_first, clean_django_db):
        """Test migration of a single station with its discharge model"""
        from sapphire_backend.imomo.migrate_old_db import migrate

        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        migrate(skip_cleanup=False, skip_structure=False, target_station="1234", limiter=100)

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

    def test_migrate_multiple_stations(self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
                                     old_kyrgyz_station_second, old_kyrgyz_discharge_model_first,
                                     old_kyrgyz_discharge_model_second, clean_django_db):
        """Test migration of multiple stations"""
        from sapphire_backend.imomo.migrate_old_db import migrate

        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        migrate(skip_cleanup=False, skip_structure=False, target_station="", limiter=100)

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

    def test_migrate_different_organizations(self, mock_create_engine, old_db_session, old_kyrgyz_station_first,
                                          old_uzbek_station_first, old_kyrgyz_discharge_model_first,
                                          old_uzbek_discharge_model_first, clean_django_db):
        """Test migration of stations from different organizations"""
        from sapphire_backend.imomo.migrate_old_db import migrate

        self.verify_empty_state()
        mock_create_engine.return_value = old_db_session.bind

        migrate(skip_cleanup=False, skip_structure=False, target_station="", limiter=100)

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
