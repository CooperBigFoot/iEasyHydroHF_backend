from decimal import Decimal
from unittest.mock import patch

import pytest
from zoneinfo import ZoneInfo

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.metrics.utils.lindas import LindasSparqlHydroScraper, LindasSparqlQueryBuilder


class TestLindasSparqlQueryBuilder:
    def test_build_query_without_site_raises_error(self):
        builder = LindasSparqlQueryBuilder()
        with pytest.raises(ValueError, match="No site code specified"):
            builder.build_query()

    def test_build_query_without_parameters_raises_error(self):
        builder = LindasSparqlQueryBuilder()
        builder.add_site("2099")
        with pytest.raises(ValueError, match="No parameters specified"):
            builder.build_query()

    def test_build_query_success(self):
        builder = LindasSparqlQueryBuilder()
        query = builder.add_site("2099").add_parameters(["waterLevel"]).build_query()

        expected_query = """
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?predicate ?object
FROM <https://lindas.admin.ch/foen/hydro>
WHERE {
  BIND(<https://environment.ld.admin.ch/foen/hydro/river/observation/2099> AS ?subject)
  ?subject ?predicate ?object .
  FILTER (?predicate IN (
    <https://environment.ld.admin.ch/foen/hydro/dimension/waterLevel>
  ))
}
"""
        assert query.strip() == expected_query.strip()

    def test_reset_method(self):
        builder = LindasSparqlQueryBuilder()
        builder.add_site("2099").add_parameters(["waterLevel"])
        builder.reset()

        with pytest.raises(ValueError, match="No site code specified"):
            builder.build_query()


class TestLindasSparqlHydroScraper:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        """Setup test environment variables."""
        monkeypatch.setenv("SPARQL_ENDPOINT", "http://test.endpoint")

    def test_init_without_endpoint_raises_error(self, monkeypatch):
        monkeypatch.delenv("SPARQL_ENDPOINT", raising=False)
        with pytest.raises(ValueError, match="SPARQL_ENDPOINT environment variable is not set"):
            LindasSparqlHydroScraper()

    @pytest.mark.parametrize(
        "site_codes, parameters",
        [
            (None, None),  # Use defaults
            (["2099"], None),  # Custom sites, default parameters
            (None, ["waterLevel"]),  # Default sites, custom parameters
            (["2099"], ["waterLevel"]),  # Custom sites and parameters
        ],
    )
    def test_init_with_valid_parameters(self, site_codes, parameters):
        scraper = LindasSparqlHydroScraper(site_codes=site_codes, parameters=parameters)
        assert scraper.site_codes == site_codes
        assert scraper.parameters == (parameters or scraper.DEFAULT_PARAMETERS)

    @pytest.mark.django_db
    def test_get_organization_timezone(self, hydrosolutions_organization):
        scraper = LindasSparqlHydroScraper(organization_name=hydrosolutions_organization.name)
        timezone = scraper._get_organization_timezone(hydrosolutions_organization.name)
        assert timezone == str(ZoneInfo("Europe/Zurich"))

    @pytest.mark.django_db
    def test_get_organization_timezone_fallback(self):
        scraper = LindasSparqlHydroScraper(organization_name="NonexistentOrg")
        timezone = scraper._get_organization_timezone("NonexistentOrg")
        assert timezone == str(ZoneInfo("UTC"))

    @pytest.mark.django_db
    def test_get_stations_nonexistent_codes(self, hydrosolutions_organization):
        """Test that no stations are returned when providing nonexistent station codes."""
        scraper = LindasSparqlHydroScraper(
            organization_name=hydrosolutions_organization.name,
            site_codes=["9999", "8888"],  # Nonexistent codes
        )
        stations = scraper._get_stations_to_process()

        assert len(stations) == 0

    @pytest.mark.django_db
    def test_get_stations_nonexistent_organization(self):
        """Test that no stations are returned when providing a nonexistent organization."""
        scraper = LindasSparqlHydroScraper(organization_name="Nonexistent Organization")
        stations = scraper._get_stations_to_process()

        assert len(stations) == 0

    @pytest.mark.django_db
    def test_get_stations_specific_codes(
        self, hydrosolutions_organization, hydrosolutions_station_automatic, hydrosolutions_station_manual
    ):
        station_code = hydrosolutions_station_automatic.station_code.lstrip("0")
        scraper = LindasSparqlHydroScraper(
            organization_name=hydrosolutions_organization.name, site_codes=[station_code]
        )
        stations = scraper._get_stations_to_process()

        assert len(stations) == 1
        assert hydrosolutions_station_automatic in stations
        assert hydrosolutions_station_manual not in stations

    def test_convert_timestamp(self):
        scraper = LindasSparqlHydroScraper()
        timestamp = "2024-03-19T10:00:00+01:00"
        result = scraper._convert_timestamp(timestamp)

        assert result.tzinfo == ZoneInfo("UTC")
        assert result.hour == 10
        assert result.minute == 0

    @pytest.mark.django_db
    @patch.object(LindasSparqlHydroScraper, "fetch_data")
    def test_process_site(self, mock_fetch, mock_sparql_response):
        mock_fetch.return_value = mock_sparql_response
        scraper = LindasSparqlHydroScraper()

        result = scraper._process_site("2099")
        assert result["station"] == "2099"
        assert result["water_level"] == 123.45
        assert result["water_temperature"] == 15.6

    @pytest.mark.django_db
    @patch.object(LindasSparqlHydroScraper, "fetch_data")
    def test_save_metrics(self, mock_fetch, mock_sparql_response, hydrosolutions_station_automatic):
        mock_fetch.return_value = mock_sparql_response
        scraper = LindasSparqlHydroScraper()

        site_data = {
            "station": hydrosolutions_station_automatic.station_code.lstrip("0"),
            "timestamp": "2024-03-19T10:00:00+01:00",
            "water_level": 123.45,
            "water_temperature": 15.6,
        }

        scraper._save_metrics(hydrosolutions_station_automatic, site_data)

        metrics = HydrologicalMetric.objects.filter(station=hydrosolutions_station_automatic)
        assert metrics.count() == 2

        water_level = metrics.get(metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY)
        assert water_level.avg_value == Decimal("123.45")
        assert water_level.value_type == HydrologicalMeasurementType.AUTOMATIC

        water_temp = metrics.get(metric_name=HydrologicalMetricName.WATER_TEMPERATURE)
        assert water_temp.avg_value == Decimal("15.6")
        assert water_temp.value_type == HydrologicalMeasurementType.AUTOMATIC

    @pytest.mark.django_db
    @patch.object(LindasSparqlHydroScraper, "fetch_data")
    def test_save_duplicate_metrics(self, mock_fetch, mock_sparql_response, hydrosolutions_station_automatic):
        """Test saving metrics when they already exist in the database."""
        mock_fetch.return_value = mock_sparql_response
        scraper = LindasSparqlHydroScraper()
        timestamp = "2024-03-19T10:00:00+01:00"

        site_data = {
            "station": hydrosolutions_station_automatic.station_code.lstrip("0"),
            "timestamp": timestamp,
            "water_level": 123.45,
            "water_temperature": 15.6,
        }

        # Save metrics first time
        scraper._save_metrics(hydrosolutions_station_automatic, site_data)

        # Modify values and save again
        site_data_updated = {
            "station": hydrosolutions_station_automatic.station_code.lstrip("0"),
            "timestamp": timestamp,
            "water_level": 130.0,
            "water_temperature": 16.0,
        }

        scraper._save_metrics(hydrosolutions_station_automatic, site_data_updated)

        # Verify metrics were updated
        metrics = HydrologicalMetric.objects.filter(
            station=hydrosolutions_station_automatic, timestamp_local=scraper._convert_timestamp(timestamp)
        )
        assert metrics.count() == 2

        water_level = metrics.get(metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY)
        assert water_level.avg_value == Decimal("130.0")

        water_temp = metrics.get(metric_name=HydrologicalMetricName.WATER_TEMPERATURE)
        assert water_temp.avg_value == Decimal("16.0")

    @pytest.mark.django_db
    @patch.object(LindasSparqlHydroScraper, "fetch_data")
    def test_run_integration(
        self, mock_fetch, mock_sparql_response, hydrosolutions_organization, hydrosolutions_station_automatic
    ):
        mock_fetch.return_value = mock_sparql_response
        station_code = hydrosolutions_station_automatic.station_code.lstrip("0")

        scraper = LindasSparqlHydroScraper(
            organization_name=hydrosolutions_organization.name, site_codes=[station_code]
        )
        scraper.run()

        metrics = HydrologicalMetric.objects.filter(station=hydrosolutions_station_automatic)
        assert metrics.count() == 2

    @pytest.mark.django_db
    @patch.object(LindasSparqlHydroScraper, "fetch_data")
    def test_save_metrics_respects_station_type(
        self, mock_fetch, mock_sparql_response, hydrosolutions_station_automatic, hydrosolutions_station_manual
    ):
        mock_fetch.return_value = mock_sparql_response
        scraper = LindasSparqlHydroScraper()

        # Test data
        site_data = {
            "timestamp": "2024-12-03T10:00:00+01:00",
            "water_level": 123.45,
            "water_temperature": 15.6,
        }

        # Test automatic station
        scraper._save_metrics(hydrosolutions_station_automatic, site_data)
        auto_metrics = HydrologicalMetric.objects.filter(station=hydrosolutions_station_automatic)
        assert all(m.value_type == HydrologicalMeasurementType.AUTOMATIC for m in auto_metrics)

        # Test manual station
        scraper._save_metrics(hydrosolutions_station_manual, site_data)
        manual_metrics = HydrologicalMetric.objects.filter(station=hydrosolutions_station_manual)
        assert all(m.value_type == HydrologicalMeasurementType.MANUAL for m in manual_metrics)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "timestamp,should_save",
        [
            ("2024-12-03T08:30:00+01:00", True),  # Within 8-9 window
            ("2024-12-03T20:30:00+01:00", True),  # Within 20-21 window
            ("2024-12-03T07:30:00+01:00", False),  # Outside windows
            ("2024-12-03T15:30:00+01:00", False),  # Outside windows
        ],
    )
    def test_save_metrics_manual_station_time_windows(self, hydrosolutions_station_manual, timestamp, should_save):
        """Test that manual station measurements are only saved within specific time windows."""
        scraper = LindasSparqlHydroScraper()

        site_data = {
            "timestamp": timestamp,
            "water_level": 123.45,
            "water_temperature": 15.6,
        }

        scraper._save_metrics(hydrosolutions_station_manual, site_data)
        metrics = HydrologicalMetric.objects.filter(station=hydrosolutions_station_manual)

        if should_save:
            assert metrics.count() == 2
            for metric in metrics:
                assert metric.value_type == HydrologicalMeasurementType.MANUAL
        else:
            assert metrics.count() == 0

    @pytest.mark.django_db
    def test_get_stations_to_process_basic(
        self, hydrosolutions_organization, hydrosolutions_station_automatic, hydrosolutions_station_manual
    ):
        """Test that _get_stations_to_process returns all non-deleted stations."""
        scraper = LindasSparqlHydroScraper(organization_name=hydrosolutions_organization.name)
        stations = scraper._get_stations_to_process()

        assert hydrosolutions_station_automatic in stations
        assert hydrosolutions_station_manual in stations
        assert stations.count() == 2
