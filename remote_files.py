import subprocess
from . import logger as lg
from collections import namedtuple


ProcessResults = namedtuple("ProcessResults", ["stdout", "stderr", "success"])


# Utilities focusing on using an external SSH process
# These operations have been tested on Windows with Raspberry Pi OS on the remote machine
class ProcessSSH:

    failureMessages = {
        "LINUX_NO_EXIST": "No such file or directory",
        "WINDOWS_NO_EXIST": "Cannot find path"
    }


    def __init__(self, user, host, logger=None):
        self.user = user
        self.host = host
        self.logger = logger

        # Set instance methods
        self.copy_to_remote = self.__inst_copy_to_remote
        self.copy_from_remote = self.__inst_copy_from_remote
        self.delete = self.__inst_delete
        self.ls = self.__inst_ls
        self.exists = self.__inst_exists
        self.is_file = self.__inst_is_file
        self.is_dir = self.__inst_is_dir
        self.last_modified = self.__inst_last_modified
        self.last_accessed = self.__inst_last_accessed


    @staticmethod
    def __is_failure(string):
        for system, message in ProcessSSH.failureMessages.items():
            if message in string:
                return True
        return False


    @staticmethod
    def __run_process(command, logger=None):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output = process.communicate()
        out = output[0].decode("utf-8")
        err = output[1].decode("utf-8")

        if ProcessSSH.__is_failure(err):
            lg.Logger.log(err.strip("\n"), logger)
            return ProcessResults(out, err, False)
        return ProcessResults(out, err, True)


    @staticmethod
    def copy_to_remote(user, host, src, dest, logger=None):
        return ProcessSSH.__run_process(
            f"scp -r {src} {user}@{host}:{dest}",
            logger
        ).success


    @staticmethod
    def copy_from_remote(user, host, src, dest, logger=None):
        return ProcessSSH.__run_process(
            f"scp -r {user}@{host}:{src} {dest}",
            logger
        ).success


    @staticmethod
    def delete(user, host, filename, logger=None):
        return ProcessSSH.__run_process(
            f"ssh {user}@{host} \"rm -r {filename}\"",
            logger
        ).success


    @staticmethod
    def ls(user, host, filename, logger=None):
        return ProcessSSH.__run_process(
            f"ssh {user}@{host} \"ls {filename}\"",
            logger
        ).stdout.strip("\n").split("\n")


    @staticmethod
    def __file_test(user, host, option, filename, logger=None):
        return ProcessSSH.__run_process(
            f"ssh {user}@{host} \"[[ -{option} '{filename}' ]] && echo True\"",
            logger
        ).stdout.strip("\n") == "True"


    @staticmethod
    def exists(user, host, filename, logger=None):
        return ProcessSSH.__file_test(user, host, "e", filename, logger)


    @staticmethod
    def is_file(user, host, filename, logger=None):
        return ProcessSSH.__file_test(user, host, "f", filename, logger)


    @staticmethod
    def is_dir(user, host, filename, logger=None):
        return ProcessSSH.__file_test(user, host, "d", filename, logger)


    @staticmethod
    def __stat(user, host, option, filename, logger=None):
        result = ProcessSSH.__run_process(
            f"ssh {user}@{host} \"find \"{filename}\" -type f -exec stat \\" + "{}" + f" -c=\"%{option}\" \\; | sort -n -r | head -n 1\"",
            logger
        ).stdout.strip("\n").strip("=")
        try:
            return int(result)
        except ValueError as e:
            lg.Logger.log(f"Cannot convert \"{result}\" to int", logger)
            return -1


    @staticmethod
    def last_modified(user, host, filename, logger=None):
        return ProcessSSH.__stat(user, host, "Y", filename, logger)


    @staticmethod
    def last_accessed(user, host, filename, logger=None):
        return ProcessSSH.__stat(user, host, "X", filename, logger)


    def __inst_copy_to_remote(self, src, dest):
        return ProcessSSH.copy_to_remote(self.user, self.host, src, dest, self.logger)


    def __inst_copy_from_remote(self, src, dest):
        return ProcessSSH.copy_from_remote(self.user, self.host, src, dest, self.logger)


    def __inst_delete(self, filename):
        return ProcessSSH.delete(self.user, self.host, filename, self.logger)


    def __inst_ls(self, filename):
        return ProcessSSH.ls(self.user, self.host, filename, self.logger)


    def __inst_exists(self, filename):
        return ProcessSSH.exists(self.user, self.host, filename, self.logger)


    def __inst_is_file(self, filename):
        return ProcessSSH.is_file(self.user, self.host, filename, self.logger)


    def __inst_is_dir(self, filename):
        return ProcessSSH.is_dir(self.user, self.host, filename, self.logger)


    def __inst_last_modified(self, filename):
        return ProcessSSH.last_modified(self.user, self.host, filename, self.logger)


    def __inst_last_accessed(self, filename):
        return ProcessSSH.last_accessed(self.user, self.host, filename, self.logger)