import logging
import os

from django.core.management.base import BaseCommand

from sapphire_backend.ingestion.utils.filemanager import FTPClient, ImomoStagingFTPClient
from sapphire_backend.ingestion.utils.ingester import ImomoAutoXMLIngester
from sapphire_backend.ingestion.utils.parser import XMLParser


class Command(BaseCommand):
    def handle(self, *args, **options):
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
            ftp_chunk_size=100,
        )
        processed_files = ftp_client.list_dir("/stream1", file_extension=".xml.part.processed")
        old_new_pairs = []
        for old_file in processed_files:
            dir, old_filename = os.path.split(old_file)
            new_filename = old_filename.rsplit('.processed')[0]
            old_new_pairs.append((old_filename, new_filename))
        ftp_client.rename_files("/stream1", old_new_pairs)
        logging.info("Flagged files as processed")
