import os
import shutil
import json
from . import logger as lg


def import_json(filename):
    lines = None
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except FileNotFoundError as e:
        return None
    return json.loads("".join(lines))


def create_file(filename, string):
    with open(filename, "w") as f:
        f.write(string)


def clear_file(filename):
    create_file(filename, "")


def target_exists(target):
    return False if target is None else os.path.exists(target)


def get_file_size(filename):
    return os.path.getsize(filename)


def is_file_from_filename(target):
    return target.rfind(".") >= 0


def find_last_slash(string):
    return max(string.rfind("\\"), string.rfind("/"))


def path_to_leaf(string):
    return string[find_last_slash(string) + 1:]


def path_to_directory(string):
    slash_index = find_last_slash(string)
    if slash_index >= 0:
        return string[:find_last_slash(string)]
    else:
        return "."


def get_directory_size(target):
    size = 0
    for dirpath, dirnames, filenames in os.walk(target):
        size += sum(get_file_size(os.path.join(dirpath, filename)) for filename in filenames)
    return size


def copy(source, destination, max_use_of_free_space=1, logger=None):
    if not target_exists(source):
        lg.Logger.log(f"Source \"{source}\" does not exist", logger)
        return False

    disk_check_dest = destination
    if not target_exists(destination):
        disk_check_dest = path_to_directory(disk_check_dest)

    space_allowance = shutil.disk_usage(disk_check_dest).free * max_use_of_free_space

    if os.path.isfile(source):
        lg.Logger.log(f"Copying source file \"{source}\" to \"{destination}\"", logger)
        if get_file_size(source) > space_allowance:
            lg.Logger.log(f"Source file \"{source}\" is too large to copy to \"{destination}\"", logger)
            return False
        return copy_file(source, destination, logger)
    else:
        lg.Logger.log(f"Copying source directory \"{source}\" to \"{destination}\"", logger)
        if get_directory_size(source) > space_allowance:
            lg.Logger.log(f"Source directory \"{source}\" is too large to copy to \"{destination}\"", logger)
            return False
        return copy_dir(source, destination, logger)


def copy_file(source, destination, logger=None):
    try:
        shutil.copy2(source, destination)
        return True
    except IOError as e:
        lg.Logger.log(f"Error copying \"{source}\" to \"{destination}\"", logger)
        lg.Logger.log(f"IOError: {str(e)}", logger, "error")
    except shutil.SameFileError as e:
        lg.Logger.log(f"Same file error while \"{source}\" to \"{destination}\"", logger)
    except Exception as e:
        lg.Logger.log(f"Unknown error copying \"{source}\" to \"{destination}\"", logger)
        lg.Logger.log(f"Exception: {str(e)}", logger)
    return False


def copy_dir(source, destination, logger=None):
    try:
        shutil.copytree(source, destination)
        return True
    except FileExistsError as e:
        lg.Logger.log(f"File in directory already exists while copying \"{source}\" to \"{destination}\"", logger)
        lg.Logger.log(f"FileExistsError: {str(e)}", logger)
    except Exception as e:
        lg.Logger.log(f"Error copying \"{source}\" to \"{destination}\"", logger)
        lg.Logger.log(f"Exception: {str(e)}", logger)
    return False


def remove_extension(filename):
    return filename[:filename.find(".")]


def get_all_items(directory):
    try:
        return os.listdir(directory)
    except FileNotFoundError as e:
        return None


def get_extension(filename):
    return filename[filename.find(".") + 1:]


def delete(target, logger=None):
    if os.path.isfile(target):
        return delete_file(target, logger)
    else:
        return delete_dir(target, logger)


def delete_file(filename, logger=None):
    try:
        os.remove(filename)
        return True
    except Exception as e:
        lg.Logger.log(f"Failed to delete file \"{filename}\"", logger)
        lg.Logger.log(f"Exception: {str(e)}", logger)
        return False


def delete_dir(directory, logger=None):
    try:
        shutil.rmtree(directory)
        return True
    except Exception as e:
        lg.Logger.log(f"Failed to delete directory \"{directory}\"", logger)
        lg.Logger.log(f"Exception: {str(e)}", logger)
    return False


def get_timestamp(target, logger=None):
    try:
        return os.path.getmtime(target)
    except OSError as e:
        return None


def get_mod_time_dir(filename):
    latest = float("-inf")
    for root, dirs, files in os.walk(filename):
        root_m_time = get_timestamp(root)
        if root_m_time > latest:
            latest = root_m_time
        for file in files:
            file_m_time = get_timestamp(f"{root}/{file}")
            if file_m_time > latest:
                latest = file_m_time
    return latest


def get_mod_time(target):
    if not target_exists(target):
        return float("-inf")
    if os.path.isfile(target):
        return get_timestamp(target)
    else:
        return get_mod_time_dir(target)