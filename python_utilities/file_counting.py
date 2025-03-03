# Utilities for counting files

from files import is_file_from_filename, get_extension, remove_extension, path_to_leaf, get_all_items
from collections import namedtuple


DELIMITER = "_"


class Components:
    pre_count = ""
    count_str = ""
    count = None
    post_count = ""

    def compose(self):
        return f"{self.pre_count}{self.count_str}{self.post_count}"

    def __change_count(self, function):
        lead_chars = ""
        for char in self.count_str:
            if char == "0":
                lead_chars += char
        self.count = function(self.count)
        self.count_str = f"{lead_chars}{self.count}"

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
    items = get_all_items(backup_directory)
    if items is None:
        return None
    return [x for x in items if is_backup(source_name, x)]


def is_backup(source_name, backup_name):
    body = backup_name
    if is_file_from_filename(source_name):
        body = remove_extension(backup_name)
    delimiter_index = body.rfind(DELIMITER)
    if delimiter_index < 0:
        return False
    body = body[:delimiter_index]
    if is_file_from_filename(source_name):
        return path_to_leaf(source_name) == f"{body}.{get_extension(backup_name)}"
    return path_to_leaf(source_name) == f"{body}"


def get_relevant_backup_names(backup_names):
    RelevantBackupNames = namedtuple("RelevantBackupNames", ["first", "last", "next"])
    return RelevantBackupNames(
        get_first(backup_names),
        get_last(backup_names),
        get_next(backup_names)
    )