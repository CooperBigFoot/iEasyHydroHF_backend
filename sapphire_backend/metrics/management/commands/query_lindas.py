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
            help="List of specific site codes to scrape (e.g., 2044 2112). If not provided, scrapes all organization stations.",
        )
        parser.add_argument(
            "--parameters",
            nargs="+",
            type=str,
            help="List of parameters to query (e.g., waterLevel waterTemperature)",
        )
        parser.add_argument(
            "--organization",
            type=str,
            default="Hydrosolutions GmbH",
            help="Organization name to scrape stations for",
        )
        parser.add_argument(
            "--force-all",
            action="store_true",
            help="Force processing of all stations regardless of time",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        try:
            scraper = LindasSparqlHydroScraper(
                organization_name=options["organization"],
                force_all_stations=options["force_all"],
                site_codes=options.get("site_codes"),
                parameters=options.get("parameters"),
            )

            self.stdout.write("Starting LINDAS data scraping...")
            scraper.run()
            self.stdout.write(self.style.SUCCESS("Successfully completed LINDAS data scraping"))

        except ValueError as e:
            raise CommandError(f"Configuration error: {str(e)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Scraping failed: {str(e)}"))
            raise CommandError(f"Scraping failed: {str(e)}")
