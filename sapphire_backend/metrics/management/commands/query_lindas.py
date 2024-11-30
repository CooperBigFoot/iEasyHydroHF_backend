import logging
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from sapphire_backend.metrics.utils.lindas import LindasSparqlHydroScraper


class Command(BaseCommand):
    """Django management command to scrape hydrological data from LINDAS."""

    help = "Scrapes hydrological data from LINDAS SPARQL endpoint"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--site-codes",
            nargs="+",
            type=str,
            help="List of site codes to scrape (e.g., 2044 2112)",
        )
        parser.add_argument(
            "--parameters",
            nargs="+",
            type=str,
            help="List of parameters to query (e.g., waterLevel waterTemperature)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        try:
            # Initialize scraper with provided arguments or defaults
            scraper = LindasSparqlHydroScraper(
                site_codes=options.get("site_codes"),
                parameters=options.get("parameters"),
            )

            self.stdout.write("Starting LINDAS data scraping...")
            scraper.run()
            self.stdout.write(self.style.SUCCESS("Successfully completed LINDAS data scraping"))

        except ValueError as e:
            raise CommandError(f"Configuration error: {str(e)}")
        except Exception as e:
            logging.exception("Error during LINDAS scraping")
            raise CommandError(f"Scraping failed: {str(e)}")
