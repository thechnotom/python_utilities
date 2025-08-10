import subprocess
from . import logger as lg
from collections import namedtuple


ProcessResults = namedtuple("ProcessResults", ["stdout", "stderr", "success"])


# Utilities focusing on using an external SSH process
# These operations have been tested on Windows with Raspberry Pi OS on the remote machine
class ProcessSSH:

    TIMEOUT = 10

    failureMessages = {
        "LINUX_NO_EXIST": "No such file or directory",
        "WINDOWS_NO_EXIST": "Cannot find path"
    }


    def __init__(self, user, host, timeout=TIMEOUT, logger=None):
        self.user = user
        self.host = host
        self.timeout = timeout
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


    def set_logger(logger):
        self.logger = logger


    @staticmethod
    def __is_failure(string):
        for name, message in ProcessSSH.failureMessages.items():
            if message in string:
                return True
        return False


    @staticmethod
    def run_process(command, timeout=TIMEOUT, logger=None):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output = None
        try:
            output = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            lg.Logger.log(f"Failed to communicate with process (timeout: {timeout}): {command}", logger)
            process.kill()
            return ProcessResults("", "", False)
        out = output[0].decode("utf-8")
        err = output[1].decode("utf-8")

        if ProcessSSH.__is_failure(err):
            lg.Logger.log(err.strip("\n"), logger)
            return ProcessResults(out, err, False)
        return ProcessResults(out, err, True)


    @staticmethod
    def copy_to_remote(user, host, src, dest, timeout=TIMEOUT, logger=None):
        return ProcessSSH.run_process(
            f"scp -r {src} {user}@{host}:{dest}",
            timeout,
            logger
        ).success


    @staticmethod
    def copy_from_remote(user, host, src, dest, timeout=TIMEOUT, logger=None):
        return ProcessSSH.run_process(
            f"scp -r {user}@{host}:{src} {dest}",
            timeout,
            logger
        ).success


    @staticmethod
    def delete(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.run_process(
            f"ssh {user}@{host} \"rm -r {filename}\"",
            timeout,
            logger
        ).success


    @staticmethod
    def ls(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.run_process(
            f"ssh {user}@{host} \"ls {filename}\"",
            timeout,
            logger
        ).stdout.strip("\n").split("\n")


    @staticmethod
    def __file_test(user, host, option, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.run_process(
            f"ssh {user}@{host} \"[[ -{option} '{filename}' ]] && echo True\"",
            timeout,
            logger
        ).stdout.strip("\n") == "True"


    @staticmethod
    def exists(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__file_test(user, host, "e", filename, timeout, logger)


    @staticmethod
    def is_file(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__file_test(user, host, "f", filename, timeout, logger)


    @staticmethod
    def is_dir(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__file_test(user, host, "d", filename, timeout, logger)


    @staticmethod
    def __stat(user, host, option, filename, timeout=TIMEOUT, logger=None):
        result = ProcessSSH.run_process(
            f"ssh {user}@{host} \"find \"{filename}\" -type f -exec stat \\" + "{}" + f" -c=\"%{option}\" \\; | sort -n -r | head -n 1\"",
            timeout,
            logger
        ).stdout.strip("\n").strip("=")
        try:
            return int(result)
        except ValueError as e:
            lg.Logger.log(f"Cannot convert \"{result}\" to int", logger)
            return -1


    @staticmethod
    def last_modified(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__stat(user, host, "Y", filename, timeout, logger)


    @staticmethod
    def last_accessed(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__stat(user, host, "X", filename, timeout, logger)


    def __get_timeout(self, timeout):
        return self.timeout if timeout is None else timeout


    def __inst_copy_to_remote(self, src, dest, timeout=None):
        return ProcessSSH.copy_to_remote(self.user, self.host, src, dest, self.__get_timeout(timeout), self.logger)


    def __inst_copy_from_remote(self, src, dest, timeout=None):
        return ProcessSSH.copy_from_remote(self.user, self.host, src, dest, self.__get_timeout(timeout), self.logger)


    def __inst_delete(self, filename, timeout=None):
        return ProcessSSH.delete(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_ls(self, filename, timeout=None):
        return ProcessSSH.ls(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_exists(self, filename, timeout=None):
        return ProcessSSH.exists(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_is_file(self, filename, timeout=None):
        return ProcessSSH.is_file(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_is_dir(self, filename, timeout=None):
        return ProcessSSH.is_dir(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_last_modified(self, filename, timeout=None):
        return ProcessSSH.last_modified(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_last_accessed(self, filename, timeout=None):
        return ProcessSSH.last_accessed(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)