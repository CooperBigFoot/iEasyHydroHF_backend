import logging
import os
import subprocess
from abc import ABC, abstractmethod

import paramiko
from scp import SCPClient


class BaseFileManager(ABC):
    """
    Base class for file managers with basic file operations
    """

    @abstractmethod
    def __init__(self):
        pass

    def get_file(self, file_path):
        self.get_files([file_path])

    def move_file(self, file_path: str, destination_dir: str):
        self.move_files([file_path], destination_dir)

    def rename_file(self, source_dir: str, old_new_name: tuple):
        self.rename_files(source_dir=source_dir, old_new_names=[old_new_name])

    @abstractmethod
    def list_dir(self, path: str) -> list[str]:
        pass

    @abstractmethod
    def rename_files(self, source_dir: str, old_new_names: list[(str, str)]) -> str:
        pass

    @abstractmethod
    def mkdir(self, dir_path: str) -> str:
        pass

    @abstractmethod
    def get_files(self, file_path: list[str]) -> list[str]:
        """
        Fetch the files from file_path (could be remote locations)
        :return paths to the downloaded local files as a list
        """
        pass


class FTPClient(BaseFileManager):
    def __init__(self, ftp_host: str, ftp_port: int, ftp_user: str, ftp_password: str, ftp_chunk_size=10):
        super(BaseFileManager, self).__init__()
        self.ftp_host = ftp_host
        self.ftp_port = ftp_port
        self.ftp_user = ftp_user
        self.ftp_password = ftp_password
        self.ftp_cmd_wrapper = f"""
                echo 'open {self.ftp_host} {self.ftp_port}
                user {self.ftp_user} {self.ftp_password}
                passive
                binary
                {{partial_commands}}
                bye' | ftp -n
                """
        self.ftp_chunk_size = ftp_chunk_size  # how many files to process within one shell command

    def _exec_shell_command(self, command: str, silent=True) -> str:
        """
        Execute shell command on the local machine
        """
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)

            if not silent:
                logging.info(result.stdout)
            if result.stderr:
                logging.error(result.stderr)

        except subprocess.CalledProcessError as e:
            logging.error(f"Command {command} failed with exit code {e.returncode}: {e.stderr}")
        return result.stdout

    def _ftp_get_files(self, files_path: list, dest_folder_local: str):
        """
        Download files from the FTP server in chunks
        """
        downloaded_files_path = []
        for i in range(0, len(files_path), self.ftp_chunk_size):
            logging.info(f"FTP downloading {i+1}/{len(files_path)}")
            files_chunk = files_path[i : i + self.ftp_chunk_size]
            partial_commands = f"lcd {dest_folder_local}"
            for file in files_chunk:
                directory, filename = os.path.split(file)
                partial_commands = f"{partial_commands}\ncd {directory}\nget {filename}"
                downloaded_files_path.append(os.path.join(dest_folder_local, filename))
            ftp_commands = self.ftp_cmd_wrapper.format(partial_commands=partial_commands)
            self._exec_shell_command(ftp_commands)
        return downloaded_files_path

    def get_files(self, ftp_file_path: list[str], dest_folder_local: str):
        """
        Trigger FTP download
        :return paths to the downloaded files as a list
        """
        local_files = self._ftp_get_files(ftp_file_path)
        return local_files

    def list_dir(self, path):
        """
        List FTP directory
        """
        partial_commands = f"cd {path}\nls"
        ftp_commands = self.ftp_cmd_wrapper.format(partial_commands=partial_commands)
        response = self._exec_shell_command(ftp_commands)
        list_files = self._parse_list_dir(path, response)
        return list_files

    @staticmethod
    def _parse_list_dir(path: str, response: str):
        """
        Filter FTP ls response and only output .xml.part files
        """
        lines = response.split("\n")
        files = []
        for line in lines:
            if line.endswith(".xml.part"):
                f = os.path.join(path, line.split()[8])
                files.append(f)
        return files

    def mkdir(self, dir_path: str):
        """
        Create new dir
        """
        partial_commands = f"mkdir {dir_path}"
        ftp_commands = self.ftp_cmd_wrapper.format(partial_commands=partial_commands)
        response = self._exec_shell_command(ftp_commands)
        return response

    def rename_files(self, src_dir: str, old_new_names: list[(str, str)]):
        """
        Rename files within the same ftp dir in chunks
        """
        for i in range(0, len(old_new_names), self.ftp_chunk_size):
            old_new_names_chunk = old_new_names[i : i + self.ftp_chunk_size]
            partial_commands = f"cd {src_dir}"
            for old_name, new_name in old_new_names_chunk:
                partial_commands = f"{partial_commands}\nren {old_name} {new_name}"
            ftp_commands = self.ftp_cmd_wrapper.format(partial_commands=partial_commands)
            response = self._exec_shell_command(ftp_commands)
        return response


class ImomoStagingFTPClient(FTPClient):
    def __init__(
        self,
        ssh_host,
        ssh_user,
        ssh_password,
        ssh_port,
        ssh_remote_dest_dir,
        ftp_host,
        ftp_port,
        ftp_user,
        ftp_password,
        ftp_chunk_size=10,
    ):
        super().__init__(ftp_host, ftp_port, ftp_user, ftp_password, ftp_chunk_size)
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_port = ssh_port
        self.ssh_remote_dest_dir = ssh_remote_dest_dir
        self.ssh_client = None

    def _ssh_connect(self):
        """
        Establish SSH connection
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(self.ssh_host, username=self.ssh_user, password=self.ssh_password, port=self.ssh_port)
        self.ssh_client = ssh_client

    def close(self):
        if self.ssh_client is not None:
            self.ssh_client.close()

    def _exec_shell_command(self, command: str, silent=True) -> str:
        """
        Execute shell command via SSH
        """
        if self.ssh_client is None:
            self._ssh_connect()
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        stdin_decoded = stdout.read().decode()
        stderr_decoded = stderr.read().decode()
        if not silent:
            logging.info(stdin_decoded)
        if stderr_decoded:
            logging.error(stderr_decoded)
        return stdin_decoded

    def _scp_get_files(self, src_file_path: list[str], dest_folder: str):
        """
        Transfer files from remote machine to the local machine via SSH
        """
        scp = SCPClient(self.ssh_client.get_transport())
        local_downloaded_files = []
        logging.info(f"SCP downloading from the SSH machine to the local folder {dest_folder}...")
        for f in src_file_path:
            scp.get(f, dest_folder)
            ssh_directory, filename = os.path.split(f)
            local_downloaded_files.append(os.path.join(dest_folder, filename))
        scp.close()
        logging.info(f"Downloaded {len(local_downloaded_files)} files")
        return local_downloaded_files

    def _cleanup_ssh_files(self, ssh_file_path: list):
        """
        Remove downloaded temporary files from the SSH server
        """
        logging.info("Cleaning up downloaded files on the SSH server...")
        for f in ssh_file_path:
            bash_command = f"rm {f}"
            self._exec_shell_command(bash_command)
        logging.info("Done.")

    def get_files(self, ftp_file_path: str, dest_folder_local: str) -> list[str]:
        """
        Download FTP files to the SSH machine and then transfer to the local machine.
        Cleanup the temporary files on the SSH machine.
        :return paths to the downloaded files as a list
        """
        ssh_file_path = self._ftp_get_files(ftp_file_path, self.ssh_remote_dest_dir)
        local_files = self._scp_get_files(ssh_file_path, dest_folder_local)
        self._cleanup_ssh_files(ssh_file_path)
        return local_files
