import logging
import os

from django.core.management.base import BaseCommand

from sapphire_backend.ingestion.utils.filemanager import FTPClient, ImomoStagingFTPClient
from sapphire_backend.ingestion.utils.ingester import ImomoIngester
from sapphire_backend.ingestion.utils.parser import XMLParser


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Add argument to include processed items
        parser.add_argument("--include-processed", action="store_true", help="Include processed items")
        parser.add_argument("--no-renaming", action="store_true", help="Don't flag items as processed")

    def handle(self, *args, **options):
        include_processed = options["include_processed"]
        no_renaming = options["no_renaming"]
        ingestion_ftp_client_class = os.environ.get("INGESTION_FTP_CLIENT_CLASS", "")
        ingester_class = os.environ.get("INGESTION_CLASS", "")

        if ingestion_ftp_client_class == "filemanager.ImomoStagingFTPClient":
            ftp_client = ImomoStagingFTPClient(
                ssh_host=os.environ["INGESTION_SSH_HOST"],
                ssh_user=os.environ["INGESTION_SSH_USER"],
                ssh_password=os.environ["INGESTION_SSH_PASSWORD"],
                ssh_port=int(os.environ["INGESTION_SSH_PORT"]),
                ssh_remote_dest_dir=os.environ["INGESTION_SSH_REMOTE_DEST_DIR"],
                ftp_host=os.environ["INGESTION_FTP_HOST"],
                ftp_port=int(os.environ["INGESTION_FTP_PORT"]),
                ftp_user=os.environ["INGESTION_FTP_USER"],
                ftp_password=os.environ["INGESTION_FTP_PASSWORD"],
                ftp_chunk_size=10,
            )
        elif ingestion_ftp_client_class == "filemanager.FTPClient":
            ftp_client = FTPClient(
                ftp_host=os.environ["INGESTION_FTP_HOST"],
                ftp_port=int(os.environ["INGESTION_FTP_PORT"]),
                ftp_user=os.environ["INGESTION_FTP_USER"],
                ftp_password=os.environ["INGESTION_FTP_PASSWORD"],
                ftp_chunk_size=10,
            )
        else:
            logging.error(
                "env INGESTION_FTP_CLIENT_CLASS not set or not supported. Supported values: filemanager.ImomoStagingFTPClient, filemanager.FTPClient"
            )
            return
        if ingester_class == "ingester.ImomoIngester":
            ingester = ImomoIngester(
                client=ftp_client,
                source_dir="/stream1",
                parser=XMLParser,
                include_processed=include_processed,
                no_renaming=no_renaming,
                # chunk_size=10
            )
        else:
            logging.error("env INGESTION_CLASS not set or not supported. Supported values: ingester.ImomoIngester")
            return
        ingester.run()
