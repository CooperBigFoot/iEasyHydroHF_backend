import logging
import os

from django.core.management.base import BaseCommand

from sapphire_backend.ingestion.utils.filemanager import FTPClient, ImomoStagingFTPClient
from sapphire_backend.ingestion.utils.ingester import ImomoAutoXMLIngester, ImomoTelegramIngester
from sapphire_backend.ingestion.utils.parser import XMLParser, ZKSParser
from sapphire_backend.organizations.models import Organization


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--skip-telegrams", action="store_true", default=False, help="Ingest telegrams")
        parser.add_argument("--skip-xml", action="store_true", default=False, help="Ingest auto stations XMLs")

    def handle(self, *args, **options):
        skip_telegrams = options["skip_telegrams"]
        skip_xml = options["skip_xml"]
        logging.info(
            f"Running ingestion {'--skip-telegrams' if skip_telegrams else ''} {'--skip-xml' if skip_xml else ''}"
        )

        ingestion_ftp_client_class = os.environ.get("INGESTION_FTP_CLIENT_CLASS", "")
        ingester_auto_class = os.environ.get("INGESTION_AUTO_XML_CLASS", "")
        ingester_telegram_class = os.environ.get("INGESTION_TELEGRAM_CLASS", "")

        if ingestion_ftp_client_class == "filemanager.ImomoStagingFTPClient":
            ftp_client = ImomoStagingFTPClient(
                ssh_host=os.environ["INGESTION_SSH_HOST"],
                ssh_user=os.environ["INGESTION_SSH_USER"],
                ssh_password=os.environ["INGESTION_SSH_PASSWORD"],
                ssh_port=int(os.environ["INGESTION_SSH_PORT"]),
                ssh_remote_dest_dir=os.environ["INGESTION_FTP_CLIENT_SSH_REMOTE_DEST_DIR"],
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

        if ingester_auto_class == "ingester.ImomoAutoXMLIngester" and not skip_xml:
            ingester_auto = ImomoAutoXMLIngester(
                ingester_name="imomo_auto",
                client=ftp_client,
                source_dir="/stream1",
                parser=XMLParser,
                offline_storage_dir=os.environ.get("INGESTION_AUTO_XML_LOCAL_STORAGE_DIR", None),
                chunk_size=100,
                organization=Organization.objects.get(name="КыргызГидроМет"),
            )
            ingester_auto.run()

        elif ingester_auto_class != "ingester.ImomoAutoXMLIngester" and not skip_xml:
            logging.warning(
                "env INGESTION_AUTO_XML_CLASS not set or not supported. Supported values: ingester.ImomoAutoXMLIngester"
            )

        if ingester_telegram_class == "ingester.ImomoTelegramIngester" and not skip_telegrams:
            ingester_manual = ImomoTelegramIngester(
                ingester_name="imomo_zks",
                client=ftp_client,
                source_dir="/manual",
                parser=ZKSParser,
                offline_storage_dir=os.environ.get("INGESTION_TELEGRAM_LOCAL_STORAGE_DIR", None),
                chunk_size=100,
                organization=Organization.objects.get(name="КыргызГидроМет"),
            )
            ingester_manual.run()
        elif ingester_telegram_class != "ingester.ImomoTelegramIngester" and not skip_telegrams:
            logging.warning(
                "env INGESTION_TELEGRAM_CLASS not set or not supported. Supported values: ingester.ImomoTelegramIngester"
            )
