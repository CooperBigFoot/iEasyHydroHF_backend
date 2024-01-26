import logging
import os
import tempfile
from abc import ABC, abstractmethod

from sapphire_backend.ingestion.utils.filemanager import BaseFileManager
from sapphire_backend.ingestion.utils.parser import BaseParser


class BaseIngester(ABC):
    def __init__(self, client: BaseFileManager, source_dir: str, parser: BaseParser):
        self.client = client
        self._source_dir = source_dir
        self._files_discovered = []
        self._files_downloaded = []
        self.parser = parser

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
    def __init__(self, client: BaseFileManager, source_dir: str, parser: BaseParser):
        super(ImomoIngester, self).__init__(client, source_dir, parser)
        self._temp_dir = tempfile.TemporaryDirectory()

    def _post_cleanup(self):
        self._temp_dir.cleanup()
        logging.info(f"Temporary directory cleaned up")

    def _discover_files(self):
        """
        Filter files which are eliglible for ingestion from the _source_dir
        """
        files = self.client.list_dir(self._source_dir)
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
        for old_file in self.files_discovered:
            dir, old_filename = os.path.split(old_file)
            new_filename = f"{old_filename}.processed"
            old_new_pairs.append((old_filename, new_filename))
        self.client.rename_files(self._source_dir, old_new_pairs)
        logging.info("Flagged files as processed")

    def run(self):
        try:
            logging.info(f"Ingestion started for folder {self._source_dir}")
            self._discover_files()
            self.files_downloaded = self.client.get_files(self.files_discovered,
                                                          self._temp_dir.name)
            self._run_parser()
            self._flag_processed_files()
            logging.info("Ingestion finished")
        finally:
            self.client.close()
            self._post_cleanup()
