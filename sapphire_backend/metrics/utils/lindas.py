import csv
import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
from SPARQLWrapper import JSON, SPARQLWrapper


class LindasSparqlQueryBuilder:
    """Builder class for SPARQL queries for hydrological data."""

    BASE_URL = "https://environment.ld.admin.ch/foen/hydro"
    DIMENSION_URL = urljoin(BASE_URL, "dimension")

    # Dictionary mapping shorter parameter names to full URIs
    PARAMETER_MAPPING = {
        "station": urljoin(DIMENSION_URL, "station"),
        "discharge": urljoin(DIMENSION_URL, "discharge"),
        "measurementTime": urljoin(DIMENSION_URL, "measurementTime"),
        "waterLevel": urljoin(DIMENSION_URL, "waterLevel"),
        "dangerLevel": urljoin(DIMENSION_URL, "dangerLevel"),
        "waterTemperature": urljoin(DIMENSION_URL, "waterTemperature"),
        "airTemperature": urljoin(DIMENSION_URL, "airTemperature"),
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
  BIND(<{self.BASE_URL}/river/observation/{self._site_code}> AS ?subject)
  ?subject ?predicate ?object .
  FILTER (?predicate IN (
    {params_filter}
  ))
}}
"""


class LindasSparqlHydroScraper:
    """A scraper for collecting hydrological data from LINDAS SPARQL endpoint."""

    DEFAULT_SITE_CODES = ["2044", "2112", "2491", "2355"]
    DEFAULT_PARAMETERS = [
        "station",
        "discharge",
        "measurementTime",
        "waterLevel",
        "dangerLevel",
        "waterTemperature",
        "isLiter",
    ]
    CSV_HEADERS = [
        "timestamp",
        "station_id",
        "discharge",
        "water_level",
        "danger_level",
        "water_temperature",
        "is_liter",
    ]
    NUMERIC_FIELDS = ["discharge", "water_level", "water_temperature", "danger_level"]
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 2

    def __init__(self):
        self.logger = self._setup_logging()
        self.endpoint_url = os.getenv("SPARQL_ENDPOINT", "https://example.com/sparql")
        self.data_dir = self._setup_data_dir()
        self.output_file = self.data_dir / "lindas_hydro_data.csv"
        self.query_builder = LindasSparqlQueryBuilder()
        self.site_codes = self._get_site_codes()
        self.parameters = self._get_parameters()
        self.sparql = self._setup_sparql_client()
        self.processed_records = self._initialize_storage()

    def _setup_logging(self) -> logging.Logger:
        """Configure and return a logger instance."""
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        return logging.getLogger(__name__)

    def _setup_data_dir(self) -> Path:
        """Set up and return the data directory path."""
        data_dir = Path(os.getenv("HYDRO_DATA_DIR", ""))
        if not data_dir:
            data_dir = Path("/app/data") if os.path.exists("/.dockerenv") else Path.cwd() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def _get_site_codes(self) -> list:
        """Get site codes from environment or defaults."""
        env_codes = os.getenv("SITE_CODES")
        return env_codes.split(",") if env_codes else self.DEFAULT_SITE_CODES

    def _get_parameters(self) -> list:
        """Get parameters from environment or defaults."""
        env_params = os.getenv("PARAMETERS")
        return env_params.split(",") if env_params else self.DEFAULT_PARAMETERS

    def _setup_sparql_client(self) -> SPARQLWrapper:
        """Initialize and configure SPARQL client."""
        sparql = SPARQLWrapper(self.endpoint_url)
        sparql.setReturnFormat(JSON)
        return sparql

    def _initialize_storage(self) -> set[str]:
        """Initialize storage and return set of processed records."""
        if not self.output_file.exists():
            self._create_csv_file()
        return self._load_processed_records()

    def _create_csv_file(self):
        """Create new CSV file with headers."""
        with open(self.output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.CSV_HEADERS)
        self.logger.info(f"Created new CSV file at {self.output_file}")

    def _load_processed_records(self) -> set[str]:
        """Load and return set of previously processed records."""
        if not self.output_file.exists():
            return set()
        try:
            df = pd.read_csv(self.output_file)
            return set(df["timestamp"].astype(str) + "_" + df["station_id"].astype(str))
        except Exception as e:
            self.logger.error(f"Error loading processed records: {e}")
            return set()

    def _convert_value(self, value: str | None, type_hint: str) -> float | None:
        """Convert string values to appropriate numeric types."""
        if value is None:
            return None
        try:
            return float(value) if type_hint in self.NUMERIC_FIELDS else value
        except (ValueError, TypeError):
            self.logger.warning(f"Could not convert {value} for {type_hint}")
            return None

    def process_data(self, results: dict, site_code: str) -> list:
        """Process SPARQL results into structured records."""
        if not results or not results.get("results", {}).get("bindings"):
            self.logger.warning(f"No valid results for site {site_code}")
            return []

        record = {
            "station_id": site_code,
            "timestamp": None,
            "discharge": None,
            "water_level": None,
            "water_temperature": None,
            "danger_level": None,
            "isLiter": None,
        }

        try:
            for result in results["results"]["bindings"]:
                predicate = self._clean_predicate(result["predicate"]["value"])
                obj = result["object"]["value"]
                self._update_record(record, predicate, obj)

            if self._is_valid_record(record):
                return [record]

            self.logger.warning(f"No valid measurements for site {site_code}")
            return []

        except Exception as e:
            self.logger.error(f"Error processing site {site_code}: {str(e)}")
            return []

    def _clean_predicate(self, predicate: str) -> str:
        """Clean predicate URL to get base name."""
        return predicate.replace("https://environment.ld.admin.ch/foen/hydro/dimension/", "").replace(
            "http://example.com/", ""
        )

    def _update_record(self, record: dict, predicate: str, value: str):
        """Update record with predicate-value pair."""
        if predicate == "measurementTime":
            record["timestamp"] = value
        elif predicate in ["discharge", "waterLevel", "waterTemperature", "dangerLevel"]:
            field = predicate.replace("water", "water_").lower()
            record[field] = self._convert_value(value, field)

    def _is_valid_record(self, record: dict) -> bool:
        """Check if record has timestamp and at least one measurement."""
        return bool(
            record["timestamp"]
            and any(record[key] is not None for key in ["discharge", "water_level", "water_temperature"])
        )

    def run(self):
        """Execute the main scraping process."""
        self.logger.info("Starting data collection...")
        all_records = []

        for site_code in self.site_codes:
            try:
                records = self._process_site(site_code)
                all_records.extend(self._filter_new_records(records))
            except Exception as e:
                self.logger.error(f"Error processing site {site_code}: {str(e)}")
                continue

        if all_records:
            self.save_data(all_records)
            self.logger.info(f"Successfully processed {len(all_records)} records")
        else:
            self.logger.warning("No new records collected")

    def _process_site(self, site_code: str) -> list:
        """Process a single site and return records."""
        self.logger.info(f"Processing site {site_code}")
        query = self.query_builder.add_site(site_code).add_parameters(self.parameters).build_query()
        self.sparql.setQuery(query)
        results = self.fetch_data()
        return self.process_data(results, site_code) if results else []

    def _filter_new_records(self, records: list) -> list:
        """Filter out previously processed records."""
        new_records = []
        for record in records:
            record_key = f"{record['timestamp']}_{record['station_id']}"
            if record_key not in self.processed_records:
                self.processed_records.add(record_key)
                new_records.append(record)
        return new_records

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

    def save_data(self, records: list):
        """Save valid records to CSV file."""
        if not records:
            self.logger.warning("No records to save")
            return

        try:
            with open(self.output_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
                valid_records = [r for r in records if r["timestamp"]]
                writer.writerows(valid_records)
                self.logger.info(f"Saved {len(valid_records)} records")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")

    def clean_csv_duplicates(self):
        """Remove duplicate entries from CSV file."""
        if not self.output_file.exists():
            self.logger.warning("No CSV file to clean")
            return

        try:
            df = pd.read_csv(self.output_file)
            initial_count = len(df)
            df_cleaned = df.drop_duplicates(keep="first")

            if len(df_cleaned) < initial_count:
                df_cleaned.to_csv(self.output_file, index=False)
                self.processed_records = set(
                    df_cleaned["timestamp"].astype(str) + "_" + df_cleaned["station_id"].astype(str)
                )
                self.logger.info(f"Removed {initial_count - len(df_cleaned)} duplicates")
            else:
                self.logger.info("No duplicates found")

        except Exception as e:
            self.logger.error(f"Error cleaning duplicates: {str(e)}")
