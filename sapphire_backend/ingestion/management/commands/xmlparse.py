from django.core.management.base import BaseCommand

from sapphire_backend.ingestion.utils.parser import XMLParser


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str)

    def handle(self, *args, **options):
        parser = XMLParser(file_path=options["filepath"])
        parser.run()

    # for all files in a dir
    # def handle(self, *args, **options):
    #     for file in os.listdir(options["filepath"]):
    #         parser = XMLParser(file_path=os.path.join(options["filepath"], file))
    #         parser.run()
