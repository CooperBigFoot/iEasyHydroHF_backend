from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from sapphire_backend.telegrams.parser import KN15TelegramParser


class Command(BaseCommand):
    help = "Parse the given telegram"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--telegrams", type=str, nargs="+", help="List of telegrams to parse")
        parser.add_argument(
            "--store_in_db", default=False, action="store_true", help="Store the decoded telegram in the database"
        )

    def handle(self, *args: Any, **options: Any) -> str | None:
        telegrams = options["telegrams"]
        store_in_db = options["store_in_db"]
        KN15TelegramParser.parse_bulk(telegrams, store_in_db, False)

        return None
