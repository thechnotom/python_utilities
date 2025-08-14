import time
import inspect
import threading
from . import files
from . import file_counting as fc


class Logger:

    __universal_logger_name = "_"
    __prohibited_functions = ["get_functions", "generic_logger"]
    __prohibited_names = __prohibited_functions + ["logger", "generic", "in_prompt", "in_received", __universal_logger_name]
    default_print = print


    def __new__(cls, *args, **kargs):
        # Return a Proxy instead of a Logger
        logger = object.__new__(cls)
        logger.__init__(*args, **kargs)
        return Logger.Proxy(logger)


    # types: list of logger names
    # printer: function used to print (must take at least a string as an argument)
    # do_timestamp: whether to display the timestamp in the logged line
    # do_type: whether to display the logger type in the logged line
    # do_location: whether to display the log message's origin in the logged line
    # do_short_location: whether to shorten the log message's origin in the logged line
    # do_thread_name: whether to show the thread's name in the logged line
    # do_type_missing_indicator: whether to indicate that a message is from a missing log type in the logged line
    # do_strict_types: whether to show messages that come from missing types
    # do_unknown_type_exception: whether to raise an exception when missing log types are used
    # do_override_type_exception: whether to raise an exception when an attempt to override and existing attribute is made
    # do_prohibited_type_exception: whether to raise an exception when prohibited log types are used
    def __init__(
        self,
        types=None,
        printer=None,
        identifier=None,
        do_timestamp=False,
        do_type=False,
        do_location=False,
        do_short_location=False,
        do_thread_name=False,
        do_type_missing_indicator=True,
        do_strict_types=False,
        do_unknown_type_exception=False,
        do_override_type_exception=True,
        do_prohibited_type_exception=True,
        do_invalid_generic_exception=True
    ):
        self.__types = {} if types is None else types
        self.__printer = printer
        self.__identifier = identifier
        self.__do_timestamp = do_timestamp
        self.__do_type = do_type
        self.__do_location = do_location
        self.__do_short_location = do_short_location
        self.__do_thread_name = do_thread_name
        self.__do_type_missing_indicator = do_type_missing_indicator
        self.__do_strict_types = do_strict_types
        self.__do_unknown_type_exception = do_unknown_type_exception
        self.__do_override_type_exception = do_override_type_exception
        self.__do_prohibited_type_exception = do_prohibited_type_exception
        self.__do_invalid_generic_exception = do_invalid_generic_exception
        self.__functions = {}
        self.input = self.__input_instance
        self.__prepare_logger()
        self.__add_type(Logger.__universal_logger_name, True, False, True)  # universal logger


    @staticmethod
    def get_prohibited_names():
        return Logger.__prohibited_names.copy()

    @staticmethod
    def get_prohibited_functions():
        return Logger.__prohibited_functions.copy()


    # Used by the Proxy object (which prohibits its use elsewhere)
    def get_functions(self):
        return self.__functions


    def get_type_names(self):
        return list(self.__functions.keys())


    def get_do_prohibited_type_exception(self):
        return self.__do_prohibited_type_exception


    def get_do_invalid_generic_exception(self):
        return self.__do_invalid_generic_exception


    # Make the printer that will be added to the Logger instance
    def __make_printer(self, name, use):
        def logger(string, *args, **kwargs):
            if use and self.__printer is not None:
                preamble = self.__create_preamble_from_self(name)
                # Use the provided printer to log the result
                self.__printer(preamble + string, *args, **kwargs)
        return logger


    def __add_type(self, name, active, check_prohibited=True, check_override=True):
        # Ignore attempts to use a prohibited name
        if check_prohibited and name in Logger.__prohibited_names:
            if self.__do_prohibited_type_exception:
                raise LoggerExceptions.ProhibitedLoggerTypeException(f"Prohibited logger name was given: {name}", name)
            return False
        # Ignore attempts to override existing properties
        if check_override and (hasattr(self, name) or name in self.__functions):
            if self.__do_override_type_exception:
                raise LoggerExceptions.OverrideLoggerTypeException(f"Cannot override an existing attribute: {name}", name)
            return False
        # Add logger type to __types if it isn't already there
        if name not in self.__types:
            self.__types[name] = active
        # Add the logger to the Logger instance
        self.__functions[name] = self.__make_printer(name, active)
        return True


    def add_type(self, name, active):
        return self.__add_type(name, active, True, True)


    def add_all_types(self, types, hide_exceptions=True):
        for logger_type in types:
            try:
                self.add_type(logger_type, True)
            except (LoggerExceptions.ProhibitedLoggerTypeException, LoggerExceptions.OverrideLoggerTypeException) as e:
                if not hide_exceptions:
                    raise e


    def has_type(self, name):
        return name in self.__functions


    def has_all_types(self, types):
        for logger_type in types:
            if not self.has_type(logger_type):
                return False
        return True


    def is_type_active(self, name):
        if name in self.__types:
            return self.__types[name]
        return False


    @staticmethod
    def __get_function(logger, name):
        try:
            return logger.__functions[name]
        except KeyError as e:
            return None


    def __get_function_from_self(self, name):
        return Logger.__get_function(self, name)


    # Prepare the Logger based on the provided configuration
    def __prepare_logger(self):
        # For each of the types...
        for key, value in self.__types.items():
            self.__add_type(key, value)


    # Create a log preamble
    @staticmethod
    def __create_preamble(name=None, identifier=None, do_type=False, do_timestamp=False, do_location=False, do_short_location=False, do_thread_name=False):
        # Add logger indentifier
        result = f"{identifier}: " if (identifier is not None) else ""
        # Add the type of log
        result += f"({name}) " if (do_type and name is not None) else ""
        # Add the timestamp
        result += Logger.__get_timestamp() if do_timestamp else ""
        # If a timestamp and location are included, add a space
        if do_timestamp and do_location:
            result += " "
        # Add the location
        if do_location or do_thread_name:
            result += "["
        if do_location:
            result += f"{Logger.__get_caller_location(do_short_location)}"
        if do_location and do_thread_name:
            result += " | "
        if do_thread_name:
            result += f"{Logger.__get_thread_name()}"
        if do_location or do_thread_name:
            result += "]"
        # If a timestamp or location is included, add a colon
        if do_timestamp or do_location:
            result += ": "
        return result


    def __create_preamble_from_self(self, name):
        return Logger.__create_preamble(
            name=name,
            identifier=self.__identifier,
            do_type=self.__do_type,
            do_timestamp=self.__do_timestamp,
            do_location=self.__do_location,
            do_short_location=self.__do_short_location,
            do_thread_name=self.__do_thread_name
        )


    # Get a named tuple containing the stack's info
    @staticmethod
    def __get_caller_frame_info(filename=None, function=None):
        stack = inspect.stack()
        curr_file = Logger.__path_to_filename(__file__)
        # Traverse through the stack until we find a frame that isn't from the logger's file
        for frame_info in stack:
            if curr_file not in frame_info.filename:
                return frame_info
        return None


    # Convert a FrameInfo named tuple into a string
    @staticmethod
    def __frame_info_to_string(frame, do_short_location):
        if frame is None:
            return None
        location = frame.filename.replace("\\", "/")
        if do_short_location:
            location = Logger.__path_to_filename(location)
        result = location
        result += ":"
        result += frame.function
        result += ":"
        result += str(frame.lineno)
        return result


    # Get a string containing details of the caller's location
    @staticmethod
    def __get_caller_location(do_short_location):
        return Logger.__frame_info_to_string(Logger.__get_caller_frame_info(), do_short_location)


    # Convert a string representing a path into just the filename
    @staticmethod
    def __path_to_filename(string):
        return string[max(string.rfind("\\"), string.rfind("/")) + 1:]


    # Get a formatted timestamp
    @staticmethod
    def __get_timestamp():
        return time.strftime("%Y-%m-%d %H:%M:%S")


    @staticmethod
    def __get_thread_name():
        return threading.current_thread().name


    # Allow for log functions to be retrieved from the logger
    def __getitem__(self, key):
        try:
            if (func := self.__get_function_from_self(key) is not None):
                return func
            return getattr(self, key)
        except AttributeError:
            return None


    # Allows for logger usage where a logger instance may not be available
    @staticmethod
    def __log(message, logger=None, log_type=None, do_type_missing_indicator=True, *args, **kwargs):
        if logger is None or log_type is None:
            preamble = Logger.__create_preamble(name=log_type, identifier=None, do_type=True, do_timestamp=True, do_location=True, do_thread_name=True)
            Logger.default_print(preamble + message, *args, **kwargs)
            return
        logger_func = Logger.__get_function(logger, log_type)
        if logger_func is None:
            if logger.__do_unknown_type_exception:
                raise LoggerExceptions.UnknownLoggerTypeException(f"Unknown logger type: {log_type}", log_type)
            if logger.__do_strict_types:
                return
            preamble = logger.__create_preamble_from_self(log_type)
            type_missing_indicator = ("*" if (logger.__do_type_missing_indicator and do_type_missing_indicator) else "")
            logger.__printer(type_missing_indicator + preamble + message, *args, **kwargs)
            return
        logger_func(message, *args, **kwargs)


    # Blocks off prohibited loggers
    @staticmethod
    def log(message, logger=None, log_type=None, *args, **kwargs):
        if logger is None:
            return
        if callable(logger) and not isinstance(logger, Logger.Proxy):
            logger(message)
            return
        if log_type in Logger.__prohibited_names:
            raise LoggerExceptions.ProhibitedLoggerTypeException(f"Prohibited logger name was given: {log_type}", log_type)
        if log_type is None:
            log_type = Logger.__universal_logger_name
        Logger.__log(message, logger=logger, log_type=log_type, *args, **kwargs)


    @staticmethod
    def make_log_function(logger=None, log_type=None):
        return lambda string, *args, **kwargs: Logger.log(string, logger, log_type, *args, **kwargs)


    # Internal logger
    @staticmethod
    def __ilog(message):
        Logger.__log(message, logger=None, log_type="logger")


    # Logged input
    @staticmethod
    def input(prompt, logger=None):
        return Logger.__input(prompt, logger)


    # Instance replacement for static equivalent
    def __input_instance(self, prompt):
        return Logger.__input(prompt, self)


    # Logged input
    @staticmethod
    def __input(prompt, logger=None, *args, **kwargs):
        Logger.__log(prompt, logger=logger, log_type="in_prompt", do_type_missing_indicator=False, *args, **kwargs)
        result = input("> ")
        Logger.__log(f"> {result}", logger=logger, log_type="in_received", do_type_missing_indicator=False, *args, **kwargs)
        return result


    @staticmethod
    def make_generic_logger():
        logger = Logger({}, Logger.default_print, None, True, False, True, True)
        logger.__add_type("generic", True, False, True)  # bypass prohibited name checking
        return logger


    @staticmethod
    def make_silent_logger():
        logger = Logger({}, lambda *args: None)
        return logger


    # Used by Proxy class (which blocks it from being used elsewhere)
    def generic_logger(self, message, *args, **kwargs):
        Logger.__log(message, self, "generic", *args, **kwargs)


    @staticmethod
    def from_settings_dict(settings):
        printer = Printers.select_printer(
            settings["do_logging"],
            settings["console"]["enable"],
            settings["file"]["enable"],
            settings["file"]["clear"],
            settings["file"]["output_filename"],
            settings["file"]["max_file_size"],
            settings["file"]["max_backups"]
        )

        return Logger(
            settings["types"],
            printer=printer,
            identifier=settings["identifier"],
            do_timestamp=settings["do_timestamp"],
            do_type=settings["do_type"],
            do_location=settings["do_location"],
            do_short_location=settings["do_short_location"],
            do_thread_name=settings["do_thread_name"],
            do_type_missing_indicator=settings["do_type_missing_indicator"],
            do_strict_types=settings["do_strict_types"],
            do_unknown_type_exception=settings["type_error_handling"]["do_unknown_type_exception"],
            do_override_type_exception=settings["type_error_handling"]["do_override_type_exception"],
            do_prohibited_type_exception=settings["type_error_handling"]["do_prohibited_type_exception"]
        )


    # Proxy to intercept calls made to the Logger object
    # Proxy is returned when attempting to instantiate Logger and passes calls onto the "proxied" instance
    class Proxy:

        def __init__(self, proxied):
            self.__proxied = proxied


        def __getattr__(self, name):
            # Check if the function is meant only for the Proxy
            if name in Logger.get_prohibited_functions():
                raise LoggerExceptions.ProhibitedLoggerMethodException(f"Prohibited logger function: {name}", name)

            # Check if the logger name is prohibited
            if name in Logger.get_prohibited_names():
                if self.__proxied.get_do_prohibited_type_exception():
                    raise LoggerExceptions.ProhibitedLoggerTypeException(f"Prohibited logger type: {name}", name)
                else:
                    return lambda string, *args, **kwargs: None

            # If the proxied class does not have the attribute, return a default attribute
            if name not in self.__proxied.get_type_names() and not hasattr(self.__proxied, name):

                def printer(string, *args, **kwargs):
                    Logger.log(string, self, name, *args, **kwargs)

                return printer

            # If the proxied class does have the attribute, return it
            if hasattr(self.__proxied, name):
                return getattr(self.__proxied, name)
            return self.__proxied.get_functions()[name]


        # Pass subscripting to the proxied instance
        def __getitem__(self, key):
            return self.__proxied[key]


        def __call__(self, message, *args, **kwargs):
            if "generic" in self.__proxied.get_type_names():
                self.__proxied.generic_logger(message, *args, **kwargs)
            else:
                if self.__proxied.get_do_invalid_generic_exception():
                    raise LoggerInvalidUsageExceptions.InvalidGenericException(message)


class LoggerExceptions:

    class LoggerNameException(Exception):
        def __init__(self, message, name):
            super().__init__(message)
            self.name = name

    class ProhibitedLoggerTypeException(LoggerNameException):
        pass


    class UnknownLoggerTypeException(LoggerNameException):
        pass


    class OverrideLoggerTypeException(LoggerNameException):
        pass


    class ProhibitedLoggerMethodException(LoggerNameException):
        pass


class LoggerInvalidUsageExceptions:

    class LoggerInvalidUsageException(Exception):
        def __init__(self, message):
            super().__init__(message)

    class InvalidGenericException(LoggerInvalidUsageException):
        pass


class Printers:

    
    file_printer_lock = threading.Lock()


    @staticmethod
    def make_console_printer():
        def printer(string, *args, **kwargs):
            print(string, *args, **kwargs)
        return printer


    @staticmethod
    def make_file_printer(filename, clear, max_size=None, max_backups=1):
        log_dir = files.path_to_directory(filename)

        if not files.target_exists(filename):
            files.create_file(filename, "")

        if clear:
            files.clear_file(filename)
            for backup_filename in fc.get_backup_names(filename, log_dir):
                backup_filename = f"{log_dir}/{backup_filename}"
                if files.target_exists(backup_filename):
                    files.delete_file(backup_filename)

        def printer(string, do_newline=True):
            with Printers.file_printer_lock:
                if max_size is not None and files.get_file_size(filename) >= max_size:
                    backup_log_filenames = fc.get_backup_names(filename, log_dir)
                    next_log_filename = fc.get_relevant_backup_names(filename, backup_log_filenames, log_dir).next
                    files.copy_file(filename, next_log_filename)
                    files.clear_file(filename)

                    while True:
                        backup_log_filenames = fc.get_backup_names(filename, log_dir)
                        if len(backup_log_filenames) <= max_backups or len(backup_log_filenames) == 0:
                            break
                        files.delete_file(fc.get_relevant_backup_names(filename, backup_log_filenames, log_dir).first)

                with open(filename, "a") as f:
                    try:
                        f.write(string + ("\n" if do_newline else ""))
                    except UnicodeEncodeError as e:
                        f.write("PRINTER ERROR: Cannot write string\n")
        return printer


    @staticmethod
    def make_combined_printer(filename, clear, max_file_size, max_backups):
        console_printer = Printers.make_console_printer()
        file_printer = Printers.make_file_printer(filename, clear, max_file_size, max_backups)

        def printer(string, do_file_newline=True, *args, **kwargs):
            console_printer(string, *args, **kwargs)
            file_printer(string, do_file_newline)
        return printer


    @staticmethod
    def select_printer(do_logging, do_console_logging, do_file_logging, clear_log_file, output_filename, max_file_size, max_backups):
        if not do_logging:
            return None
        elif do_console_logging and do_file_logging:
            return Printers.make_combined_printer(output_filename, clear_log_file, max_file_size, max_backups)
        elif do_console_logging:
            return Printers.make_console_printer()
        elif do_file_logging:
            return Printers.make_file_printer(output_filename, clear_log_file, max_file_size, max_backups)
        return None