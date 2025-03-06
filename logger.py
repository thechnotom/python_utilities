import time
import inspect
from . import files


class Logger:

    __prohibited_names = ["logger", "generic", "in_prompt", "in_received"]
    default_print = print


    def __new__(cls, *args, **kargs):
        # Return a Proxy instead of a Logger
        logger = object.__new__(cls)
        logger.__init__(*args, **kargs)
        return Logger.Proxy(logger)


    def __init__(self, types=None, printer=None, do_timestamp=False, do_type=False, do_location=False, do_short_location=False, do_type_missing_indicator=True):
        self.__types = {} if types is None else types
        self.__printer = printer
        self.__do_timestamp = do_timestamp
        self.__do_type = do_type
        self.__do_location = do_location
        self.__do_short_location = do_short_location
        self.__do_type_missing_indicator = do_type_missing_indicator
        self.input = self.__input_instance
        self.__prepare_logger()


    def get_prohibited_names(self):
        return self.__prohibited_names.copy()


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
            Logger.__ilog(f"WARNING: an invalid logger name was given: {name}")
            return
        # Ignore attempts to override existing properties
        if check_override and hasattr(self, name):
            Logger.__ilog(f"WARNING: a logger name cannot override an existing attribute: {name}")
            return
        # Add the logger to the Logger instance
        setattr(self, name, self.__make_printer(name, active))


    # Prepare the Logger based on the provided configuration
    def __prepare_logger(self):
        # For each of the types...
        for key, value in self.__types.items():
            self.__add_type(key, value)


    # Create a log preamble
    @staticmethod
    def __create_preamble(name=None, do_type=False, do_timestamp=False, do_location=False, do_short_location=False):
        # Add the type of log
        result = f"({name}) " if (do_type and name is not None) else ""
        # Add the timestamp
        result += Logger.__get_timestamp() if do_timestamp else ""
        # If a timestamp and location are included, add a space
        if do_timestamp and do_location:
            result += " "
        # Add the location
        if do_location:
            result += f"[{Logger.__get_caller_location(do_short_location)}]"
        # If a timestamp or location is included, add a colon
        if do_timestamp or do_location:
            result += ": "
        return result


    def __create_preamble_from_self(self, name):
        return Logger.__create_preamble(
            name=name,
            do_type=self.__do_type,
            do_timestamp=self.__do_timestamp,
            do_location=self.__do_location,
            do_short_location=self.__do_short_location
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


    # Allow for log functions to be retrieved from the logger
    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            return None


    # Allows for logger usage where a logger instance may not be available
    @staticmethod
    def __log(message, logger=None, log_type=None, do_type_missing_indicator=True, *args, **kwargs):
        if logger is None or log_type is None:
            preamble = Logger.__create_preamble(name=log_type, do_type=True, do_timestamp=True, do_location=True)
            Logger.default_print(preamble + message)
            return
        logger_func = logger[log_type]
        if logger_func is None:
            preamble = logger.__create_preamble_from_self(log_type)
            type_missing_indicator = ("*" if (logger.__do_type_missing_indicator and do_type_missing_indicator) else "")
            logger.__printer(type_missing_indicator + preamble + message, *args, **kwargs)
            return
        logger_func(message, *args, **kwargs)


    # Blocks off prohibited loggers
    @staticmethod
    def log(message, logger=None, log_type=None):
        if log_type in Logger.__prohibited_names:
            Logger.__ilog(f"Cannot use prohibited logger name \"{log_type}\"")
            Logger.__ilog(f"Message: {message}")
            return
        Logger.__log(message, logger=logger, log_type=log_type)


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
    def __input(prompt, logger=None):
        Logger.__log(prompt, logger=logger, log_type="in_prompt", do_type_missing_indicator=False)
        result = input("> ")
        Logger.__log(f"> {result}", logger=logger, log_type="in_received", do_type_missing_indicator=False)
        return result


    @staticmethod
    def make_generic_logger():
        logger = Logger({}, Logger.default_print, True, False, True, True)
        logger.__add_type("generic", True, False, True)  # bypass prohibited name checking
        return logger


    @staticmethod
    def silence_static_logging():
        Logger.default_print = (lambda string: None)


    @staticmethod
    def from_settings_dict(settings):
        printer = Printers.select_printer(
            settings["do_logging"],
            settings["console"]["enable"],
            settings["file"]["enable"],
            settings["file"]["clear"],
            settings["file"]["output_filename"],
            settings["file"]["max_file_size"]
        )

        return Logger(
            settings["types"],
            printer=printer,
            do_timestamp=settings["do_timestamp"],
            do_type=settings["do_type"],
            do_location=settings["do_location"],
            do_short_location=settings["do_short_location"]
        )


    # Proxy to intercept calls made to the Logger object
    # Proxy is returned when attempting to instantiate Logger and passes calls onto the "proxied" instance
    class Proxy:

        def __init__(self, proxied):
            self.__proxied = proxied


        def __getattr__(self, name):
            # If the proxied class does not have the attribute, return a default attribute
            if not hasattr(self.__proxied, name):
                if name not in self.__proxied.get_prohibited_names():
                    def printer(string):
                        Logger.log(string, self, name)

                    return printer
                return lambda string: Logger.default_print(f"Prohibited logger name ({name}) for message: {string}")
            # If the proxied class does have the attribute, return it
            return getattr(self.__proxied, name)


        # Pass subscripting to the proxied instance
        def __getitem__(self, key):
            return self.__proxied[key]


        def __call__(self, message):
            if hasattr(self.__proxied, "generic"):
                self.__proxied.generic(message)


class Printers:

    @staticmethod
    def make_console_printer():
        def printer(string, do_newline=True):
            print(string, end=("\n" if do_newline else ""))
        return printer


    @staticmethod
    def make_file_printer(filename, clear, max_size=None, backup_suffix=".backup"):
        backup_filename = filename + backup_suffix

        if not files.target_exists(filename):
            files.create_file(filename, "")

        if clear:
            files.clear_file(filename)
            if files.target_exists(filename + backup_suffix):
                files.delete_file(backup_filename)

        def printer(string, do_newline=True):
            if max_size is not None and files.get_file_size(filename) >= max_size:
                files.copy_file(filename, backup_filename)
                files.clear_file(filename)

            with open(filename, "a") as f:
                try:
                    f.write(string + ("\n" if do_newline else ""))
                except UnicodeEncodeError as e:
                    f.write("PRINTER ERROR: Cannot write string\n")
        return printer


    @staticmethod
    def make_combined_printer(filename, clear, max_file_size):
        console_printer = Printers.make_console_printer()
        file_printer = Printers.make_file_printer(filename, clear, max_file_size)

        def printer(string, do_newline=True):
            console_printer(string, do_newline)
            file_printer(string, do_newline)
        return printer


    @staticmethod
    def select_printer(do_logging, do_console_logging, do_file_logging, clear_log_file, output_filename, max_file_size):
        if not do_logging:
            return None
        elif do_console_logging and do_file_logging:
            return make_combined_printer(output_filename, clear_log_file, max_file_size)
        elif do_console_logging:
            return Printers.make_console_printer()
        elif do_file_logging:
            return Printers.make_file_printer(output_filename, clear_log_file, max_file_size)
        return None