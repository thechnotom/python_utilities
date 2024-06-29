import os
import shutil


__print = print


def clear_file(filename):
    with open(filename, "w") as f:
        f.write("")


def target_exists(target):
    return False if target is None else os.path.exists(target)


def delete_file(filename, logger=None):
    try:
        os.remove(filename)
        return True
    except Exception as e:
        __print(f"Failed to delete file \"{filename}\"", logger, "operation")
        __print(f"Exception: {str(e)}", logger, "error")
    return False


def get_file_size(filename):
    return os.path.getsize(filename)


def copy_file(source, destination, logger=None):
    try:
        shutil.copy2(source, destination)
        return True
    except IOError as e:
        __print(f"Error copying \"{source}\" to \"{destination}\"")
        __print(f"IOError: {str(e)}")
    except shutil.SameFileError as e:
        __print(f"Same file error")
    except Exception as e:
        __print(f"Unknown error copying \"{source}\" to \"{destination}\"")
        __print(f"Exception: {str(e)}")
    return False