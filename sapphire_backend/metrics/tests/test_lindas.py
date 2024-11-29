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
        assert scraper.site_codes == (site_codes or scraper.DEFAULT_SITE_CODES)
        assert scraper.parameters == (parameters or scraper.DEFAULT_PARAMETERS)

    @pytest.mark.django_db
    def test_get_station(self, manual_hydro_station_kyrgyz):
        scraper = LindasSparqlHydroScraper()
        # Test with station that exists (note: station codes in DB are prefixed with '0')
        station = scraper._get_station("2099")
        assert station is None  # Should be None as we don't have this station in test DB

        # Test with non-existent station
        station = scraper._get_station("9999")
        assert station is None

    def test_convert_timestamp(self):
        scraper = LindasSparqlHydroScraper()
        timestamp = "2024-03-19T10:00:00+01:00"
        result = scraper._convert_timestamp(timestamp)

        # Should convert to UTC while preserving the hour
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
    def test_save_metrics(self, mock_fetch, mock_sparql_response, manual_hydro_station_kyrgyz):
        mock_fetch.return_value = mock_sparql_response
        scraper = LindasSparqlHydroScraper()

        site_data = {
            "station": manual_hydro_station_kyrgyz.station_code,
            "timestamp": "2024-03-19T10:00:00+01:00",
            "water_level": 123.45,
            "water_temperature": 15.6,
        }

        # Save metrics
        scraper._save_metrics(manual_hydro_station_kyrgyz, site_data)

        # Verify water level metric
        water_level = HydrologicalMetric.objects.filter(
            station=manual_hydro_station_kyrgyz,
            metric_name=HydrologicalMetricName.WATER_LEVEL_DAILY,
        ).first()
        assert water_level is not None
        assert water_level.avg_value == Decimal("123.45")
        assert water_level.value_type == HydrologicalMeasurementType.AUTOMATIC

        # Verify water temperature metric
        water_temp = HydrologicalMetric.objects.filter(
            station=manual_hydro_station_kyrgyz,
            metric_name=HydrologicalMetricName.WATER_TEMPERATURE,
        ).first()
        assert water_temp is not None
        assert water_temp.avg_value == Decimal("15.6")
        assert water_temp.value_type == HydrologicalMeasurementType.AUTOMATIC

    @pytest.mark.django_db
    @patch.object(LindasSparqlHydroScraper, "fetch_data")
    def test_run_integration(self, mock_fetch, mock_sparql_response, manual_hydro_station_kyrgyz):
        mock_fetch.return_value = mock_sparql_response

        # Modify station code to match LINDAS data
        manual_hydro_station_kyrgyz.station_code = "02099"
        manual_hydro_station_kyrgyz.save()

        scraper = LindasSparqlHydroScraper(site_codes=["2099"])
        scraper.run()

        # Verify metrics were saved
        metrics = HydrologicalMetric.objects.filter(station=manual_hydro_station_kyrgyz)
        assert metrics.count() == 2  # Should have water level and temperature
