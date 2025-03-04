# Utilities for counting files

from . import files
from collections import namedtuple


DELIMITER = "_"


class Components:
    pre_count = ""
    count_str = ""
    count = None
    post_count = ""

    def __init__(self, pre_count="", count_str="", post_count=""):
        self.pre_count = pre_count
        self.count_str = count_str
        self.post_count = post_count

    @staticmethod
    def from_src_and_count(source_name, count):
        result = Components()
        if files.is_file_from_filename(source_name):
            result.pre_count = files.remove_extension(files.path_to_leaf(source_name))
        else:
            result.pre_count = files.path_to_leaf(source_name)
        result.pre_count = f"{result.pre_count}{DELIMITER}"
        result.count_str = str(count)
        if files.is_file_from_filename(source_name):
            result.post_count = f".{files.get_extension(source_name)}"
        return result

    def compose(self):
        return f"{self.pre_count}{self.count_str}{self.post_count}"

    def __change_count(self, function):
        self.count = function(self.count)
        self.count_str = f"{self.count}"

    def increment(self):
        self.__change_count(lambda x: x + 1)

    def decrement(self):
        self.__change_count(lambda x: x - 1)

    def __str__(self):
        return f"pre_count: {self.pre_count}\ncount: {self.count_str}\npost_count: {self.post_count}"


def decompose(string):
    result = Components()
    i = string.find(DELIMITER)
    if DELIMITER == "":
        i = 0
    if DELIMITER is not None:
        result.pre_count = string[:i + len(DELIMITER)]

    count_str = ""
    for char in string[i + len(DELIMITER):]:
        try:
            int(char)
            count_str += char
        except ValueError:
            break

    result.count_str = count_str
    try:
        result.count = int(count_str)
    except ValueError:
        return None

    result.post_count = string[i + len(DELIMITER) + len(count_str):]

    return result


def compose(components):
    return components.compose()


def get_string_components(strings, compare):
    if len(strings) == 0:
        return None
    result = decompose(strings[0])
    for string in strings:
        curr = decompose(string)
        if compare(curr.count, result.count):
            result = curr
    return result


def get_string(strings, compare):
    return compose(get_string_components(strings, compare))


def get_first(strings):
    return get_string(strings, lambda x, y: x < y)


def get_last(strings):
    return get_string(strings, lambda x, y: x > y)


def get_next(strings):
    temp = get_string_components(strings, lambda x, y: x > y)
    temp.increment()
    return compose(temp)


def get_backup_names(source_name, backup_directory):
    items = files.get_all_items(backup_directory)
    if items is None:
        return None
    return [x for x in items if is_backup(source_name, x)]


def is_backup(source_name, backup_name):
    body = backup_name
    if files.is_file_from_filename(source_name):
        body = files.remove_extension(backup_name)
    delimiter_index = body.rfind(DELIMITER)
    if delimiter_index < 0:
        return False
    body = body[:delimiter_index]
    if files.is_file_from_filename(source_name):
        return files.path_to_leaf(source_name) == f"{body}.{files.get_extension(backup_name)}"
    return files.path_to_leaf(source_name) == f"{body}"


def get_relevant_backup_names(src, backup_names, backup_dir):
    RelevantBackupNames = namedtuple("RelevantBackupNames", ["first", "last", "next"])

    if len(backup_names) < 1:
        return RelevantBackupNames(
            None,
            None,
            f"{backup_dir}/{Components.from_src_and_count(src, 0).compose()}"
        )

    return RelevantBackupNames(
        f"{backup_dir}/{get_first(backup_names)}",
        f"{backup_dir}/{get_last(backup_names)}",
        f"{backup_dir}/{get_next(backup_names)}"
    )