import logging
import os
import tempfile
from abc import ABC, abstractmethod

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
    def files_discovered(self):
        return self._files_discovered

    @files_discovered.setter
    def files_discovered(self, files: list[str]):
        self._files_discovered = files

    @property
    def files_downloaded(self):
        return self._files_downloaded

    @files_downloaded.setter
    def files_downloaded(self, files: list[str]):
        self._files_downloaded = files

    def _run_parser(self):
        for file_path in self.files_downloaded:
            parser = self.parser(file_path=file_path)
            parser.run()

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
        no_renaming=False,
        chunk_size=200,
    ):
        super().__init__(client, source_dir, parser, chunk_size)
        self._temp_dir = tempfile.TemporaryDirectory()
        self._include_processed = include_processed
        self._no_renaming = no_renaming

    def _post_cleanup(self):
        self._temp_dir.cleanup()
        logging.info("Temporary directory cleaned up")

    def _discover_files(self):
        """
        Filter files which are eliglible for ingestion from the _source_dir
        """
        files = self.client.list_dir(self._source_dir)
        if self._include_processed:
            files_processed = self.client.list_dir(self._source_dir, file_extension=".xml.part.processed")
            files = files + files_processed

        for fullpath in files:
            dir, filename = os.path.split(fullpath)
            if filename.startswith("DATA"):
                self.files_discovered.append(fullpath)
        logging.info(f"Discovered {len(self.files_discovered)} xml files")

    def _flag_processed_files(self):
        """
        Rename processed files on the ftp server - add .processed suffix
        """
        old_new_pairs = []
        for old_file in self.files_downloaded:
            dir, old_filename = os.path.split(old_file)
            if old_filename.endswith(".processed"):  # this could be true in case --include-processed is set
                continue
            new_filename = f"{old_filename}.processed"
            old_new_pairs.append((old_filename, new_filename))
        self.client.rename_files(self._source_dir, old_new_pairs)
        logging.info("Flagged files as processed")

    def run(self):
        try:
            logging.info(
                f"Ingestion started for folder {self._source_dir}, (include_processed = {self._include_processed}, no_renaming = {self._no_renaming})"
            )
            self._discover_files()
            for i in range(0, len(self.files_discovered), self._ingestion_chunk_size):
                logging.info(f"Ingesting {i + 1}/{len(self.files_discovered)}")
                files_chunk = self.files_discovered[i : i + self._ingestion_chunk_size]
                self.files_downloaded = self.client.get_files(files_chunk, self._temp_dir.name)
                self._run_parser()
                if not self._no_renaming:
                    self._flag_processed_files()
            logging.info("Ingestion finished")
        finally:
            self.client.close()
            self._post_cleanup()
