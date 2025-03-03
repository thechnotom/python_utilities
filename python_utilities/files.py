import os
import shutil
from . import logger


def create_file(filename, string):
    with open(filename, "w") as f:
        f.write(string)


def clear_file(filename):
    create_file(filename, "")


def target_exists(target):
    return False if target is None else os.path.exists(target)


def delete_file(filename, logger=None):
    try:
        os.remove(filename)
        return True
    except Exception as e:
        logger.Logger.log(f"Failed to delete file \"{filename}\"", logger, "operation")
        logger.Logger.log(f"Exception: {str(e)}", logger, "error")
    return False


def get_file_size(filename):
    return os.path.getsize(filename)


def is_file_from_filename(target):
    return target.rfind(".") >= 0


def find_last_slash(string):
    return max(string.rfind("\\"), string.rfind("/"))


def path_to_leaf(string):
    return string[find_last_slash(string) + 1:]


def path_to_directory(string):
    return string[:find_last_slash(string)]


def get_directory_size(target):
    size = 0
    for dirpath, dirnames, filenames in os.walk(target):
        size += sum(get_file_size(os.path.join(dirpath, filename)) for filename in filenames)
    return size


def copy(source, destination, max_use_of_free_space=1, logger=None):
    if not target_exists(source):
        logger.Logger.log(f"Source \"{source}\" does not exist", logger, "error")
        return False

    disk_check_dest = destination
    if not target_exists(destination):
        disk_check_dest = path_to_directory(disk_check_dest)

    space_allowance = shutil.disk_usage(disk_check_dest).free * max_use_of_free_space

    if os.path.isfile(source):
        logger.Logger.log(f"Copying source file \"{source}\" to \"{destination}\"", logger, "operation")
        if get_file_size(source) > space_allowance:
            logger.Logger.log(f"Source file \"{source}\" is too large to copy to \"{destination}\"")
            return False
        return copy_file(source, destination, logger)
    else:
        logger.Logger.log(f"Copying source directory \"{source}\" to \"{destination}\"", logger, "operation")
        if get_directory_size(source) > space_allowance:
            logger.Logger.log(f"Source directory \"{source}\" is too large to copy to \"{destination}\"")
            return False
        return copy_dir(source, destination, logger)


def copy_file(source, destination, logger=None):
    try:
        shutil.copy2(source, destination)
        return True
    except IOError as e:
        logger.Logger.log(f"Error copying \"{source}\" to \"{destination}\"", logger, "operation")
        logger.Logger.log(f"IOError: {str(e)}", logger, "error")
    except shutil.SameFileError as e:
        logger.Logger.log(f"Same file error", logger, "operation")
    except Exception as e:
        logger.Logger.log(f"Unknown error copying \"{source}\" to \"{destination}\"", logger, "operation")
        logger.Logger.log(f"Exception: {str(e)}", logger, "error")
    return False


def copy_dir(source, destination, logger=None):
    try:
        shutil.copytree(source, destination)
        return True
    except FileExistsError as e:
        logger.Logger.log(f"File in directory already exists while copying \"{source}\" to \"{destination}\"", logger, "error")
        logger.Logger.log(f"FileExistsError: {str(e)}", logger, "error")
    except Exception as e:
        logger.Logger.log(f"Error copying \"{source}\" to \"{destination}\"", logger, "error")
        logger.Logger.log(f"Exception: {str(e)}", logger, "error")
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
        logger.Logger.log(f"Failed to delete file \"{filename}\"", logger, "operation")
        logger.Logger.log(f"Exception: {str(e)}", logger, "error")
        return False


def delete_dir(directory, logger=None):
    try:
        shutil.rmtree(directory)
        return True
    except Exception as e:
        logger.Logger.log(f"Failed to delete directory \"{directory}\"", logger, "operation")
        logger.Logger.log(f"Exception: {str(e)}", logger, "error")
    return False


def get_timestamp(target, logger=None):
    try:
        return os.path.getmtime(target)
    except OSError as e:
        return None