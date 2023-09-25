from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from sapphire_backend.telegrams.parser import KN15TelegramParser


class Command(BaseCommand):
    help = "Parse the given telegram"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--telegrams", type=str, nargs="+", help="List of telegrams to parse")

    def handle(self, *args: Any, **options: Any) -> str | None:
        telegrams = options["telegrams"]

        parsed_telegrams = KN15TelegramParser.parse_bulk(telegrams)

        print(parsed_telegrams)

        return None
