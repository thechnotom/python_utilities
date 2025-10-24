import subprocess
from . import logger as lg
from . import processes as pr


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
        self.mkdir = self.__inst_mkdir
        self.exists = self.__inst_exists
        self.is_file = self.__inst_is_file
        self.is_dir = self.__inst_is_dir
        self.last_modified = self.__inst_last_modified
        self.last_accessed = self.__inst_last_accessed


    def set_logger(self, logger):
        self.logger = logger


    @staticmethod
    def __is_failure(string):
        for name, message in ProcessSSH.failureMessages.items():
            if message in string:
                return True
        return False


    @staticmethod
    def __prep_filename(filename):
        return filename.replace("\\", "/").replace(" ", r"\ ")


    @staticmethod
    def __run_process(command, timeout=TIMEOUT, logger=None):
        result = pr.run_process(command, timeout, "utf-8", logger)
        if ProcessSSH.__is_failure(result.stderr):
            lg.Logger.log(f"Command failed: {command}", logger)
            lg.Logger.log(result.stderr.strip("\n"), logger)
            result = pr.ProcessResults(result.stdout, result.stderr, False)
        return result


    @staticmethod
    def copy_to_remote(user, host, src, dest, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__run_process(
            f"scp -r \"{src}\" {user}@{host}:\"{dest}\"",
            timeout,
            logger
        ).success


    @staticmethod
    def copy_from_remote(user, host, src, dest, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__run_process(
            f"scp -r {user}@{host}:\"{src}\" \"{dest}\"",
            timeout,
            logger
        ).success


    @staticmethod
    def delete(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__run_process(
            f"ssh {user}@{host} \"rm -r {ProcessSSH.__prep_filename(filename)}\"",
            timeout,
            logger
        ).success


    @staticmethod
    def ls(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__run_process(
            f"ssh {user}@{host} \"ls {ProcessSSH.__prep_filename(filename)}\"",
            timeout,
            logger
        ).stdout.strip("\n").split("\n")


    @staticmethod
    def mkdir(user, host, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__run_process(
            f"ssh {user}@{host} \"mkdir {ProcessSSH.__prep_filename(filename)}\"",
            timeout,
            logger
        ).success


    @staticmethod
    def __file_test(user, host, option, filename, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__run_process(
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
    def __stat(user, host, option, filename, exclusions=None, timeout=TIMEOUT, logger=None):
        condition = ""
        if exclusions is not None and len(exclusions) > 0:
            condition += " \\("
            for i, exclusion in enumerate(exclusions):
                condition += f" -not -wholename \"*{exclusion}*\" "
                if i != len(exclusions) - 1:
                    condition += "-and"
            condition += "\\)"

        result = ProcessSSH.__run_process(
            f"ssh {user}@{host} \"find \"{filename}\" -type f{condition} -exec stat \\" + "{}" + f" -c=\"%{option}\" \\; | sort -n -r | head -n 1\"",
            timeout,
            logger
        ).stdout.strip("\n").strip("=")
        try:
            return int(result)
        except ValueError as e:
            lg.Logger.log(f"Cannot convert \"{result}\" to int", logger)
            return float("-inf")


    @staticmethod
    def last_modified(user, host, filename, exclusions=None, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__stat(user, host, "Y", filename, exclusions, timeout, logger)


    @staticmethod
    def last_accessed(user, host, filename, exclusions=None, timeout=TIMEOUT, logger=None):
        return ProcessSSH.__stat(user, host, "X", filename, exclusions, timeout, logger)


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


    def __inst_mkdir(self, filename, timeout=None):
        return ProcessSSH.mkdir(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_exists(self, filename, timeout=None):
        return ProcessSSH.exists(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_is_file(self, filename, timeout=None):
        return ProcessSSH.is_file(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_is_dir(self, filename, timeout=None):
        return ProcessSSH.is_dir(self.user, self.host, filename, self.__get_timeout(timeout), self.logger)


    def __inst_last_modified(self, filename, exclusions=None, timeout=None):
        return ProcessSSH.last_modified(self.user, self.host, filename, exclusions, self.__get_timeout(timeout), self.logger)


    def __inst_last_accessed(self, filename, exclusions=None, timeout=None):
        return ProcessSSH.last_accessed(self.user, self.host, filename, exclusions, self.__get_timeout(timeout), self.logger)