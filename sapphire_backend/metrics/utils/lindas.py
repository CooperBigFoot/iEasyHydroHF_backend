import logging
import os
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

from django.db.models import QuerySet
from SPARQLWrapper import JSON, SPARQLWrapper
from zoneinfo import ZoneInfo

from sapphire_backend.metrics.choices import HydrologicalMeasurementType, HydrologicalMetricName, MetricUnit
from sapphire_backend.metrics.models import HydrologicalMetric
from sapphire_backend.organizations.models import Organization
from sapphire_backend.stations.models import HydrologicalStation


class LindasSparqlQueryBuilder:
    """Builder class for SPARQL queries for hydrological data."""

    BASE_URL = "https://environment.ld.admin.ch/foen/hydro/"
    DIMENSION_URL = urljoin(BASE_URL, "dimension/")

    # Dictionary mapping shorter parameter names to full URIs
    PARAMETER_MAPPING = {
        "station": urljoin(DIMENSION_URL, "station"),
        "measurementTime": urljoin(DIMENSION_URL, "measurementTime"),
        "waterLevel": urljoin(DIMENSION_URL, "waterLevel"),
        "waterTemperature": urljoin(DIMENSION_URL, "waterTemperature"),
    }

    def __init__(self) -> None:
        self._site_code: str | None = None
        self._parameters: list[str] = []

    def add_site(self, site_code: str) -> "LindasSparqlQueryBuilder":
        """
        Add a single site code to the query.

        Args:
            site_code: A string containing a site code number

        Returns:
            Self for method chaining

        Raises:
            ValueError: If site code is not a valid integer between 1-9999
        """
        try:
            code_int = int(site_code)
            if not 1 <= code_int <= 9999:
                raise ValueError(f"Site code {site_code} must be between 1 and 9999")
            self._site_code = str(code_int)
        except ValueError:
            raise ValueError(f"Site code {site_code} must be an integer")
        return self

    def add_parameters(self, parameters: list[str]) -> "LindasSparqlQueryBuilder":
        """
        Add parameters to the query.

        Args:
            parameters: List of parameter names to query

        Returns:
            Self for method chaining

        Raises:
            ValueError: If any parameters are not in PARAMETER_MAPPING
        """
        invalid_params = [p for p in parameters if p not in self.PARAMETER_MAPPING]
        if invalid_params:
            raise ValueError(f"Invalid parameters: {invalid_params}")

        self._parameters.extend(parameters)
        return self

    def reset(self) -> "LindasSparqlQueryBuilder":
        """Reset the query builder to its initial state."""
        self._site_code = None
        self._parameters = []
        return self

    def build_query(self) -> str:
        """
        Build the complete SPARQL query for a single site.

        Returns:
            A SPARQL query string

        Raises:
            ValueError: If site code or parameters are not set
        """
        if not self._site_code:
            raise ValueError("No site code specified")
        if not self._parameters:
            raise ValueError("No parameters specified")

        params_filter = ",\n    ".join(f"<{self.PARAMETER_MAPPING[param]}>" for param in self._parameters)

        return f"""
PREFIX schema: <http://schema.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?predicate ?object
FROM <https://lindas.admin.ch/foen/hydro>
WHERE {{
  BIND(<{self.BASE_URL}river/observation/{self._site_code}> AS ?subject)
  ?subject ?predicate ?object .
  FILTER (?predicate IN (
    {params_filter}
  ))
}}
"""


class LindasSparqlHydroScraper:
    """Initialize the LINDAS SPARQL scraper.

    Args:
        organization_name: Name of the organization to scrape stations for
        site_codes: Optional list of specific site codes to scrape
        parameters: Optional list of parameters to query

    Raises:
        ValueError: If SPARQL_ENDPOINT environment variable is not set
    """

    DEFAULT_PARAMETERS = [
        "station",
        "measurementTime",
        "waterLevel",
        "waterTemperature",
    ]
    NUMERIC_FIELDS = ["waterLevel", "waterTemperature"]
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 2
    MANUAL_STATION_HOURS = {8, 20}

    def __init__(
        self,
        organization_name: str = "Hydrosolutions GmbH",
        site_codes: list[str] | None = None,
        parameters: list[str] | None = None,
    ):
        self.logger = self._setup_logging()
        self.endpoint_url = os.getenv("SPARQL_ENDPOINT")
        if not self.endpoint_url:
            self.logger.error("SPARQL_ENDPOINT environment variable is not set")
            raise ValueError("SPARQL_ENDPOINT environment variable is not set")

        self.organization_name = organization_name
        self.site_codes = site_codes
        self.parameters = parameters or self.DEFAULT_PARAMETERS

        self.query_builder = LindasSparqlQueryBuilder()
        self.sparql = self._setup_sparql_client()

    def _setup_logging(self) -> logging.Logger:
        """Configure and return a logger instance."""
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        return logging.getLogger(__name__)

    def _setup_sparql_client(self) -> SPARQLWrapper:
        """Initialize and configure SPARQL client."""
        sparql = SPARQLWrapper(self.endpoint_url)
        sparql.setReturnFormat(JSON)
        return sparql

    def _convert_value(self, value: str | None, type_hint: str) -> float | None:
        """Convert string values to appropriate numeric types."""
        if value is None:
            return None
        try:
            return float(value) if type_hint in self.NUMERIC_FIELDS else value
        except (ValueError, TypeError):
            self.logger.warning(f"Could not convert {value} for {type_hint}")
            return None

    def process_data(self, results: dict, site_code: str) -> dict | None:
        """Process SPARQL results into structured records."""
        if not results or not results.get("results", {}).get("bindings"):
            self.logger.warning(f"No valid results for site {site_code}")
            return []

        record = {
            "station": None,
            "timestamp": None,
            "water_level": None,
            "water_temperature": None,
        }

        try:
            for result in results["results"]["bindings"]:
                predicate = self._clean_predicate(result["predicate"]["value"])
                obj = result["object"]["value"]

                if predicate == "measurementTime":
                    record["timestamp"] = obj
                elif predicate == "station":
                    record["station"] = obj.split("/")[-1]
                elif predicate in ["waterLevel", "waterTemperature"]:
                    record[predicate.replace("water", "water_").lower()] = self._convert_value(obj, predicate)

            if self._is_valid_record(record):
                return record

            self.logger.warning(f"No valid measurements for site {site_code}")
            return None

        except Exception as e:
            self.logger.error(f"Error processing site {site_code}: {str(e)}")
            return None

    def _clean_predicate(self, predicate: str) -> str:
        """Clean predicate URL to get base name."""
        return predicate.split("/")[-1]

    def _is_valid_record(self, record: dict) -> bool:
        """Check if record has timestamp and at least one measurement."""
        return bool(
            record["timestamp"] and any(record[key] is not None for key in ["water_level", "water_temperature"])
        )

    def _process_site(self, site_code: str) -> list:
        """Process a single site and return records."""
        self.logger.info(f"Processing site {site_code}")
        query = self.query_builder.reset().add_site(site_code).add_parameters(self.parameters).build_query()
        self.sparql.setQuery(query)
        results = self.fetch_data()
        return self.process_data(results, site_code) if results else None

    def _get_organization_timezone(self, organization_name: str) -> str:
        """Get the timezone for the organization."""
        try:
            organization = Organization.objects.get(name=organization_name)
            return str(organization.timezone)
        except Organization.DoesNotExist:
            self.logger.warning(f"Organization {organization_name} not found")
            return "UTC"

    def _get_stations_to_process(self) -> QuerySet[HydrologicalStation]:
        """Get queryset of stations to process."""
        if self.site_codes:
            return HydrologicalStation.objects.filter(
                station_code__in=[f"0{code}" for code in self.site_codes], is_deleted=False
            )

        # Return all non-deleted stations for the organization
        return HydrologicalStation.objects.filter(site__organization__name=self.organization_name, is_deleted=False)

    def _convert_timestamp(self, timestamp_str: str) -> datetime:
        """Convert LINDAS timestamp to UTC-based local time."""
        # Parse the ISO timestamp
        dt = datetime.fromisoformat(timestamp_str)
        # Convert to naive UTC time (keeping the same hour/minute values)
        utc_dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return utc_dt

    def _save_metrics(self, station: HydrologicalStation, site_data: dict) -> None:
        """Save metrics for a station."""
        timestamp_local = self._convert_timestamp(site_data["timestamp"])

        # For manual stations, only save measurements if they fall within our target hours
        if station.station_type == HydrologicalStation.StationType.MANUAL:
            hour = timestamp_local.hour
            if hour not in self.MANUAL_STATION_HOURS:
                self.logger.info(
                    f"Skipping manual measurement for station {station.name} at {timestamp_local} - outside target hours"
                )
                return

        metric_mappings = {
            "water_level": {
                "metric_name": HydrologicalMetricName.WATER_LEVEL_DAILY,
                "unit": MetricUnit.WATER_LEVEL,
            },
            "water_temperature": {
                "metric_name": HydrologicalMetricName.WATER_TEMPERATURE,
                "unit": MetricUnit.TEMPERATURE,
            },
        }

        # Determine measurement type based on station type
        value_type = (
            HydrologicalMeasurementType.MANUAL
            if station.station_type == HydrologicalStation.StationType.MANUAL
            else HydrologicalMeasurementType.AUTOMATIC
        )

        for data_key, mapping in metric_mappings.items():
            value = site_data.get(data_key)
            if value is not None:
                try:
                    metric = HydrologicalMetric(
                        timestamp_local=timestamp_local,
                        station=station,
                        metric_name=mapping["metric_name"],
                        value_type=value_type,
                        unit=mapping["unit"],
                        avg_value=value,
                        source_type=HydrologicalMetric.SourceType.UNKNOWN,
                        source_id=0,
                    )
                    metric.save()
                    self.logger.info(f"Saved {mapping['metric_name']} = {value} for station {station.name}")
                except Exception as e:
                    self.logger.error(f"Failed to save {mapping['metric_name']} for station {station.name}: {str(e)}")

    def fetch_data(self) -> dict | None:
        """Fetch data with retry logic."""
        retry_delay = self.INITIAL_RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                results = self.sparql.query().convert()
                if results.get("results", {}).get("bindings"):
                    self.logger.info(f"Fetched {len(results['results']['bindings'])} results")
                    return results
                return None
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.logger.error(f"Failed to fetch data: {str(e)}")
                    return None

    def run(self):
        """Execute the main scraping process."""
        self.logger.info("Starting data collection...")

        stations = self._get_stations_to_process()
        if not stations:
            self.logger.warning("No stations found to process")
            return

        self.logger.info(f"Processing {len(stations)} stations")

        for station in stations:
            try:
                # Remove leading '0' from station code for LINDAS
                site_code = station.station_code.lstrip("0")

                site_data = self._process_site(site_code)
                if not site_data:
                    continue

                self._save_metrics(station, site_data)
                self.logger.info(f"Processed data for station {station.name}")

            except Exception as e:
                self.logger.error(f"Error processing site {site_code}: {str(e)}")
                continue
