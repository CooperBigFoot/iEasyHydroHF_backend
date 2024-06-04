import logging
import os
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from zoneinfo import ZoneInfo

from sapphire_backend.ingestion.models import FileState
from sapphire_backend.ingestion.utils.filemanager import BaseFileManager
from sapphire_backend.ingestion.utils.parser import BaseParser


class BaseIngester(ABC):
    def __init__(self, client: BaseFileManager, source_dir: str, parser: BaseParser, chunk_size=200):
        self.client = client
        self._source_dir = source_dir
        self._files_discovered = []
        self._files_downloaded = []
        self.parser = parser
        self._ingestion_chunk_size = chunk_size

    @property
    def files_to_download(self):
        return FileState.objects.filter(state__in=[FileState.States.DISCOVERED])

    @property
    def files_to_process(self):
        return FileState.objects.filter(state__in=[FileState.States.DOWNLOADED])

    @property
    def files_unprocessed(self):
        return FileState.objects.exclude(state=FileState.States.PROCESSED)

    @property
    def files_downloaded(self):
        return FileState.objects.filter(state=FileState.States.DOWNLOADED)

    @property
    def files_failed(self):
        return FileState.objects.filter(state=FileState.States.FAILED)

    def _run_parser(self):
        for filestate in self.files_to_process:
            try:
                filestate.change_state(FileState.States.PROCESSING)
                filestate.save()
                parser = self.parser(file_path=filestate.local_path)
                parser.run()
                filestate.change_state(FileState.States.PROCESSED)
                filestate.save()
            except Exception as e:
                logging.exception(e)
                filestate.change_state(FileState.States.FAILED)
                filestate.save()

    @abstractmethod
    def run(self):
        pass


class ImomoIngester(BaseIngester):
    def __init__(
        self,
        client: BaseFileManager,
        source_dir: str,
        parser: BaseParser,
        include_processed=False,
        chunk_size=200,
        offline_storage_dir=None
    ):
        super().__init__(client, source_dir, parser, chunk_size)
        self._temp_dir = tempfile.TemporaryDirectory()
        self._include_processed = include_processed
        self._offline_storage_dir = offline_storage_dir

    @property
    def flag_save_offline(self) -> bool:
        return self._offline_storage_dir is not None

    @property
    def local_dest_dir(self):
        if self._offline_storage_dir is not None:
            return self._offline_storage_dir
        else:
            return self._temp_dir.name

    def _post_cleanup(self):
        if not self.flag_save_offline:
            # if files are not stored permanently
            file_states_with_local_path = FileState.objects.filter(local_path__contains=self.local_dest_dir)
            file_states_with_local_path.update(local_path=None)

            # everything that's not PROCESSED should be FAILED
            self.files_unprocessed.update(state=FileState.States.FAILED, state_timestamp=datetime.now(tz=ZoneInfo("UTC")))
            self._temp_dir.cleanup()
            logging.info("Temporary directory cleaned up")
        else:
            # if files are stored permanently
            # only PROCESSING are marked as FAILED
            filtered_file_states = FileState.objects.filter(state=FileState.States.PROCESSING)
            filtered_file_states.update(state=FileState.States.FAILED)

        if self.files_failed.exists():
            logging.warning(f"Flagged {self.files_failed.count()} as failed.")

    def _discover_new_files(self):
        """
        Filter files which are eliglible for ingestion from the _source_dir and save the FileState objects
        """
        logging.info("Discovering new files")
        FileState.objects.filter(
            state=FileState.States.FAILED).delete()  # delete failed file states in order to try again

        source_files_all = self.client.list_dir(self._source_dir)
        if self._include_processed:
            files_processed = self.client.list_dir(self._source_dir, file_extension=".xml.part.processed")
            source_files_all = source_files_all + files_processed

        already_discovered_files = FileState.objects.values_list('remote_path', flat=True)

        new_files = [file for file in source_files_all if file not in already_discovered_files]

        new_filestate_objs = []
        for fullpath in new_files:
            dir, filename = os.path.split(fullpath)
            if filename.startswith("DATA"):
                new_filestate_objs.append(FileState(remote_path=fullpath,
                                                    state_timestamp=datetime.now(tz=ZoneInfo("UTC")),
                                                    state=FileState.States.DISCOVERED
                                                    ))

        FileState.objects.bulk_create(new_filestate_objs)
        logging.info(f"Discovered {FileState.objects.filter(state=FileState.States.DISCOVERED).count()} new xml files")


    def _download_discovered_files(self):
        logging.info(f"Downloading discovered files...")
        for i in range(0, len(self.files_to_download), self._ingestion_chunk_size):
            logging.info(f"Downloading {i + 1}/{len(self.files_to_download)}")

            remote_files_chunk = self.files_to_download[i: i + self._ingestion_chunk_size].values_list('remote_path',
                                                                                                      flat=True)
            files_downloaded_chunk = self.client.get_files(remote_files_chunk, self.local_dest_dir)

            for remote_path, local_path in zip(remote_files_chunk, files_downloaded_chunk):
                filestate_obj = FileState.objects.get(remote_path=remote_path,
                                                      state=FileState.States.DISCOVERED)
                filestate_obj.state = FileState.States.DOWNLOADED
                filestate_obj.local_path = local_path
                filestate_obj.state_timestamp = datetime.now(tz=ZoneInfo("UTC"))
                filestate_obj.save()

        logging.info(f"Downloaded {self.files_downloaded.count()} files.")

    def run(self):
        try:
            logging.info(
                f"Ingestion started for folder {self._source_dir}, (include_processed = {self._include_processed})"
            )
            self._sync_local_storage_with_db()
            self._discover_new_files()
            self._download_discovered_files()
            self._run_parser()
            logging.info("Ingestion finished")
        finally:
            self.client.close()
            self._post_cleanup()

# class ImomoIngesterV1(BaseIngester):
#     def __init__(
#         self,
#         client: BaseFileManager,
#         source_dir: str,
#         parser: BaseParser,
#         include_processed=False,
#         no_renaming=False,
#         chunk_size=200,
#     ):
#         super().__init__(client, source_dir, parser, chunk_size)
#         self._temp_dir = tempfile.TemporaryDirectory()
#         self._include_processed = include_processed
#         self._no_renaming = no_renaming
#
#     def _post_cleanup(self):
#         self._temp_dir.cleanup()
#         logging.info("Temporary directory cleaned up")
#
#     def _discover_files(self):
#         """
#         Filter files which are eliglible for ingestion from the _source_dir
#         """
#         files = self.client.list_dir(self._source_dir)
#         if self._include_processed:
#             files_processed = self.client.list_dir(self._source_dir, file_extension=".xml.part.processed")
#             files = files + files_processed
#
#         for fullpath in files:
#             dir, filename = os.path.split(fullpath)
#             if filename.startswith("DATA"):
#                 self.files_discovered.append(fullpath)
#         logging.info(f"Discovered {len(self.files_discovered)} xml files")
#
#     def _flag_processed_files(self):
#         """
#         Rename processed files on the ftp server - add .processed suffix
#         """
#         old_new_pairs = []
#         for old_file in self.files_downloaded:
#             dir, old_filename = os.path.split(old_file)
#             if old_filename.endswith(".processed"):  # this could be true in case --include-processed is set
#                 continue
#             new_filename = f"{old_filename}.processed"
#             old_new_pairs.append((old_filename, new_filename))
#         self.client.rename_files(self._source_dir, old_new_pairs)
#         logging.info("Flagged files as processed")
#
#     def run(self):
#         try:
#             logging.info(
#                 f"Ingestion started for folder {self._source_dir}, (include_processed = {self._include_processed}, no_renaming = {self._no_renaming})"
#             )
#             self._discover_files()
#             for i in range(0, len(self.files_discovered), self._ingestion_chunk_size):
#                 logging.info(f"Ingesting {i + 1}/{len(self.files_discovered)}")
#                 files_chunk = self.files_discovered[i: i + self._ingestion_chunk_size]
#                 self.files_downloaded = self.client.get_files(files_chunk, self._temp_dir.name)
#                 self._run_parser()
#                 if not self._no_renaming:
#                     self._flag_processed_files()
#             logging.info("Ingestion finished")
#         finally:
#             self.client.close()
#             self._post_cleanup()
