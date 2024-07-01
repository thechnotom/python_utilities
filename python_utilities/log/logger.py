import time
import inspect


class Logger:

    __prohibited_names = ["logger", "generic"]
    default_print = print

    def __new__(cls, *args, **kargs):
        # Return a Proxy instead of a Logger
        logger = object.__new__(cls)
        logger.__init__(*args, **kargs)
        return Logger.Proxy(logger)

    def __init__(self, types, printer=None, do_timestamp=False, do_type=False, do_location=False, do_short_location=False):
        self.__types = [] if types is None else types
        self.__printer = printer
        self.__do_timestamp = do_timestamp
        self.__do_type = do_type
        self.__do_location = do_location
        self.__do_short_location = do_short_location
        self.__prepare_logger()

    def get_prohibited_names(self):
        return self.__prohibited_names.copy()

    # Make the printer that will be added to the Logger instance
    def __make_printer(self, name, use):
        def logger(string):
            if use and self.__printer is not None:
                preamble = self.__create_preamble_from_self(name)
                # Use the provided printer to log the result
                self.__printer(preamble + string)
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
            return "frame unavaliable"
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
    def __log(message, logger=None, log_type=None):
        if logger is None or log_type is None:
            preamble = Logger.__create_preamble(name=log_type, do_type=True, do_timestamp=True, do_location=True)
            Logger.default_print(preamble + message)
            return
        logger_func = logger[log_type]
        if logger_func is None:
            preamble = logger.__create_preamble_from_self(log_type)
            logger.__printer("*" + preamble + message)
            return
        logger_func(message)

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

    @staticmethod
    def make_generic_logger():
        logger = Logger({}, Logger.default_print, True, False, True, True)
        logger.__add_type("generic", True, False, True)  # bypass prohibited name checking
        return logger

    @staticmethod
    def silence_static_logging():
        Logger.default_print = (lambda string: None)


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