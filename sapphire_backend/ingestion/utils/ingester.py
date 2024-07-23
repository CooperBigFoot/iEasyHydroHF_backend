import logging
import os
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime

from zoneinfo import ZoneInfo

from sapphire_backend.ingestion.models import FileState
from sapphire_backend.ingestion.utils.filemanager import BaseFileManager
from sapphire_backend.ingestion.utils.parser import BaseParser
from sapphire_backend.organizations.models import Organization


class BaseIngester(ABC):
    def __init__(
        self,
        client: BaseFileManager,
        source_dir: str,
        parser: BaseParser,
        ingester_name: str,
        organization: Organization,
        chunk_size=200,
        offline_storage_dir=None,
    ):
        self.client = client
        self._source_dir = source_dir
        self._files_discovered = []
        self._files_downloaded = []
        self.parser = parser
        self._ingestion_chunk_size = chunk_size
        self._temp_dir = tempfile.TemporaryDirectory()
        self._offline_storage_dir = offline_storage_dir
        self._ingester_name = ingester_name
        self._organization = organization

    @property
    def ingester_name(self):
        return self._ingester_name

    @property
    def files_to_download(self):
        return FileState.objects.filter(
            state=FileState.States.DISCOVERED,
            ingester_name=self.ingester_name,
        )

    @property
    def files_to_process(self):
        return FileState.objects.filter(
            state=FileState.States.DOWNLOADED,
            ingester_name=self.ingester_name,
        )

    @property
    def files_unprocessed(self):
        return FileState.objects.filter(ingester_name=self.ingester_name).exclude(state=FileState.States.PROCESSED)

    @property
    def files_downloaded(self):
        return FileState.objects.filter(
            state=FileState.States.DOWNLOADED,
            ingester_name=self.ingester_name,
        )

    @property
    def files_failed(self):
        return FileState.objects.filter(
            state=FileState.States.FAILED,
            ingester_name=self.ingester_name,
        )

    def _run_parser(self):
        for idx, filestate in enumerate(self.files_to_process):
            try:
                if (idx + 1) % 10 == 0:
                    logging.info(f"Parsing file {idx + 1}/{len(self.files_to_process)}")
                filestate.state = FileState.States.PROCESSING
                filestate.save()
                parser = self.parser(
                    file_path=filestate.local_path, filestate=filestate, organization=self._organization
                )
                parser.run()
                filestate.state = FileState.States.PROCESSED
                filestate.save()
            except Exception as e:
                logging.exception(e)
                filestate.state = FileState.States.FAILED
                filestate.save()

    @property
    def flag_save_offline(self) -> bool:
        """
        Flag whether the files are permanently saved offline or temporarily
        """
        return self._offline_storage_dir is not None

    @property
    def local_dest_dir(self):
        """
        Path to permanent offline storage dir or temporary storage dir
        :return:
        """
        if self._offline_storage_dir is not None:
            return self._offline_storage_dir
        else:
            return self._temp_dir.name

    @staticmethod
    def remove_gz_extension(filename: str) -> str:
        """
        Remove .gz extension from a file list
        """
        return filename[:-3] if filename.endswith(".gz") else filename

    @property
    def list_offline_filenames(self) -> list[str]:
        """
        List files already available offline
        """
        # List all files in the directory
        filenames = [
            f for f in os.listdir(self.local_dest_dir) if os.path.isfile(os.path.join(self.local_dest_dir, f))
        ]
        return filenames

    @property
    def list_offline_filenames_no_gz(self) -> list[str]:
        """
        List files already available offline but remove .gz extension
        """
        filenames_without_gz = [self.remove_gz_extension(filename) for filename in self.list_offline_filenames]
        return filenames_without_gz

    def _include_offline_files(self):
        """
        Find which discovered files are already available offline (in case the DB was dropped but the files are there).
        No need to download again, just update their state to DOWNLOADED
        """
        logging.info("Syncing offline files...")
        filenames_to_download = set(self.files_to_download.values_list("filename", flat=True))
        filenames_already_downloaded = set(self.list_offline_filenames_no_gz)
        filenames_to_mark_as_downloaded = filenames_to_download & filenames_already_downloaded

        for filestate_obj in FileState.objects.filter(
            filename__in=filenames_to_mark_as_downloaded,
            state=FileState.States.DISCOVERED,
            ingester_name=self.ingester_name,
        ):
            filestate_obj.state = FileState.States.DOWNLOADED
            filestate_obj.local_path = os.path.join(self.local_dest_dir, f"{filestate_obj.filename}.gz")
            filestate_obj.save()

        logging.info(f"Synced {len(filenames_to_mark_as_downloaded)} offline files.")

    def _download_discovered_files(self):
        """
        Download all the files with state DISCOVERED
        """
        logging.info("Downloading discovered files...")
        remote_files_to_download = self.files_to_download.values_list("remote_path", flat=True)
        for i in range(0, len(remote_files_to_download), self._ingestion_chunk_size):
            logging.info(f"Downloading {i + 1}/{len(remote_files_to_download)}")

            remote_files_chunk = remote_files_to_download[i : i + self._ingestion_chunk_size]
            files_downloaded_chunk = self.client.get_files(remote_files_chunk, self.local_dest_dir)

            for remote_path, local_path in zip(remote_files_chunk, files_downloaded_chunk):
                filestate_obj = FileState.objects.get(
                    remote_path=remote_path,
                    state=FileState.States.DISCOVERED,
                    ingester_name=self.ingester_name,
                )
                filestate_obj.state = FileState.States.DOWNLOADED
                filestate_obj.local_path = local_path
                filestate_obj.save()

        logging.info(f"Downloaded {self.files_downloaded.count()} files.")

    def _post_cleanup(self):
        logging.info("Post cleanup...")
        if not self.flag_save_offline:
            # if files are not stored permanently, remove their local_path from the table
            file_states_with_local_path = FileState.objects.filter(
                local_path__contains=self.local_dest_dir,
                ingester_name=self.ingester_name,
            )
            # here we don't need to run post save signals since the state is not changed, we can use .update()
            file_states_with_local_path.update(local_path="")

            # in this case everything that's not PROCESSED should be FAILED
            self.files_unprocessed.update(
                state=FileState.States.FAILED, state_timestamp=datetime.now(tz=ZoneInfo("UTC"))
            )

            self._temp_dir.cleanup()
            logging.info("Temporary directory cleaned up")
        else:
            # if files are stored permanently, only states PROCESSING are marked as FAILED
            filtered_file_states = FileState.objects.filter(
                state=FileState.States.PROCESSING,
                ingester_name=self.ingester_name,
            )
            filtered_file_states.update(
                state=FileState.States.FAILED, state_timestamp=datetime.now(tz=ZoneInfo("UTC"))
            )

        if self.files_failed.exists():
            logging.warning(f"Flagged {self.files_failed.count()} as failed.")
        logging.info("Post cleanup done.")

    @abstractmethod
    def _discover_new_files(self):
        pass

    @abstractmethod
    def run(self):
        pass


class ImomoAutoXMLIngester(BaseIngester):
    def _discover_new_files(self):
        """
        Filter files which are eliglible for ingestion from the _source_dir and save the FileState objects
        """
        logging.info("Discovering new files")
        # delete failed file states in order to try again
        FileState.objects.filter(state=FileState.States.FAILED, ingester_name=self.ingester_name).delete()

        remote_files_all = self.client.list_dir(self._source_dir, file_extension=".xml.part")

        already_known_files = FileState.objects.values_list("remote_path", flat=True)
        new_files = [file for file in remote_files_all if file not in already_known_files]

        new_filestate_objs = []
        for fullpath in new_files:
            dir, filename = os.path.split(fullpath)
            if filename.startswith("DATA"):
                new_filestate_objs.append(
                    FileState(
                        remote_path=fullpath,
                        state=FileState.States.DISCOVERED,
                        ingester_name=self.ingester_name,
                    )
                )
        new_discovered = FileState.objects.bulk_create(new_filestate_objs)
        logging.info(f"Discovered {len(new_discovered)} new xml files")

    def run(self):
        try:
            logging.info(
                f"Ingestion started for folder {self._source_dir}, (storage location = {self.local_dest_dir})"
            )
            self._discover_new_files()
            if self.flag_save_offline:
                self._include_offline_files()
            self._download_discovered_files()
            self._run_parser()
            logging.info("Ingestion finished")
        finally:
            self.client.close()
            self._post_cleanup()


class ImomoTelegramIngester(BaseIngester):
    def _discover_new_files(self):
        """
        Filter files which are eliglible for ingestion from the _source_dir and save the FileState objects
        """
        logging.info("Discovering new files")
        # delete failed file states in order to try again
        FileState.objects.filter(
            state=FileState.States.FAILED,
            ingester_name=self.ingester_name,
        ).delete()

        remote_files_all = self.client.list_dir(self._source_dir, file_extension="")

        already_known_files = FileState.objects.filter(ingester_name=self.ingester_name).values_list(
            "remote_path", flat=True
        )
        new_files = [file for file in remote_files_all if file not in already_known_files]

        new_filestate_objs = []
        for fullpath in new_files:
            dir, filename = os.path.split(fullpath)
            if filename.startswith("imomo"):
                new_filestate_objs.append(
                    FileState(
                        remote_path=fullpath,
                        state=FileState.States.DISCOVERED,
                        ingester_name=self.ingester_name,
                    )
                )
        new_discovered = FileState.objects.bulk_create(new_filestate_objs)
        logging.info(f"Discovered {len(new_discovered)} new telegram files")

    def run(self):
        try:
            logging.info(
                f"ZKS telegram ingestion started for folder {self._source_dir}, (storage location = {self.local_dest_dir})"
            )
            self._discover_new_files()
            if self.flag_save_offline:
                self._include_offline_files()
            self._download_discovered_files()
            self._run_parser()
            logging.info("Ingestion finished")
        finally:
            self.client.close()
            self._post_cleanup()
