from . import files
import os
from enum import Enum
from .logger import Logger, LoggerInvalidUsageExceptions


class Command:

    def __init__(self, code, operation, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        self.__operation = operation
        self.__code = code
        self.__result = None

    def do(self, logger=None):
        # Try passing a logger to the operation (try again without if it doesn't accept it)
        try:
            self.__result = self.__operation(*self.__args, **self.__kwargs, logger=logger)
        except TypeError as e:
            self.__result = self.__operation(*self.__args, **self.__kwargs)
        return self.__result

    def get_result(self):
        return self.__result

    def get_operation_name(self):
        return self.__operation.__name__

    def get_args_copy(self):
        return self.__args.copy()

    def get_kwargs_copy(self):
        return self.__kwargs.copy()

    def get_code(self):
        return self.__code

    def __str__(self):
        return f"{str(self.__result)}, {self.__code}, {self.get_operation_name()}: {str(self.__args)}, {str(self.__kwargs)}"


class CommandCode(Enum):
    NEW_FROM_D1 = 1
    NEW_FROM_D2 = 2
    NEWEST = 3
    MAKE_DIR = 4
    FILE_DIR_MATCH_CONFLICT = 5


class FileItem:

    def __init__(self, base, tail):
        self.__base = base
        self.__tail = tail

    def get_path(self):
        return FileItem.attach_paths(self.__base, self.__tail)

    def get_base(self):
        return self.__base

    def get_tail(self):
        return self.__tail
    
    def with_new_base(self, base):
        return FileItem(base, self.__tail)
    
    def is_file(self):
        return os.path.isfile(self.get_path())

    @staticmethod
    def attach_paths(p1, p2):
        delimiter = ("" if (len(p1) == 0 or len(p2) == 0 or p1[len(p1) - 1] == "/" or p2[0] == "/") else "/")
        return f"{p1}{delimiter}{p2}"

    # __hash__ and __eq__ don't do a good job at their usual purposes, here (especially __eq__).
    # They don't really measure uniqueness or quality properly -- just in the limited way
    # needed for the purpose of the class.

    def __hash__(self):
        return hash(self.__tail)

    def __eq__(self, fc):
        return self.__tail == fc.get_tail() and self.is_file() == self.is_file()

    def __str__(self):
        return self.get_path()


def __newer_file(f1, f2):
    if files.get_timestamp(f1.get_path()) > files.get_timestamp(f2.get_path()):
        return f1
    return f2


def create_logger(show_general, show_copy, show_conflict):
    return Logger(
        types={"general": show_general, "copy": show_copy, "conflict": show_conflict},
        printer=print,
        do_timestamp=True,
        do_type=True
    )


def __copy(source, destination, logger=None):
    logger_function = None if logger is None else logger.copy
    return files.copy(source, destination, 1, logger=logger_function)


def __mk_dir(directory):
    return files.create_directory(directory)


def __warn(path1, path2, logger=None):
    Logger.log(f"File and directory share a name (both have been skipped): {path1}, {path2}", logger, "conflict")


def merge(directory1, directory2, destination, logger=None):
    required_types = ["general", "copy", "conflict"]
    if logger is not None:
        logger.has_all_types(required_types, do_exception=True)
    commands = __get_merge_commands_recursive(FileItem(directory1, ""), FileItem(directory2, ""), destination, [])
    for command in commands:
        command.do(logger=logger)
    return commands


def __get_merge_commands_recursive(item1, item2, destination, commands):
    if item1.is_file() and item2.is_file():
        newer = __newer_file(item1, item2)
        commands.append(Command(CommandCode.NEWEST, __copy, newer.get_path(), FileItem(destination, newer.get_tail()).get_path()))
        return commands

    # Handle special case where there's a file in one item and a folder in the other sharing the same name
    if item1.get_tail() == item2.get_tail() and item1.is_file() != item2.is_file():
        commands.append(Command(CommandCode.FILE_DIR_MATCH_CONFLICT, __warn, item1.get_path(), item2.get_path()))
        return commands

    items1 = {FileItem(item1.get_base(), FileItem.attach_paths(item1.get_tail(), x)) for x in set(files.get_all_items(item1.get_path()))}
    items2 = {FileItem(item2.get_base(), FileItem.attach_paths(item2.get_tail(), x)) for x in set(files.get_all_items(item2.get_path()))}

    union = items1.union(items2)
    items1_extras = union - items2
    items2_extras = union - items1
    same = items1.intersection(items2)

    # Create the current directory
    commands.append(Command(CommandCode.MAKE_DIR, __mk_dir, FileItem.attach_paths(destination, item1.get_tail())))

    if len(items1) == 0 and len(items2) == 0:
        return commands

    # Check same items (at this point, we know they're either both files or both directories)
    for i in same:
        __get_merge_commands_recursive(
            i.with_new_base(item1.get_base()),
            i.with_new_base(item2.get_base()),
            destination,
            commands
        )

    # Determine what to do with differences
    for i in items1_extras:
        new_item1 = i.with_new_base(item1.get_base())
        commands.append(Command(CommandCode.NEW_FROM_D1, __copy, new_item1.get_path(), FileItem(destination, new_item1.get_tail()).get_path()))
    for i in items2_extras:
        new_item2 = i.with_new_base(item2.get_base())
        commands.append(Command(CommandCode.NEW_FROM_D2, __copy, new_item2.get_path(), FileItem(destination, new_item2.get_tail()).get_path()))
    return commands