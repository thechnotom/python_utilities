# Data type utilities

# Allow dictionaries to be accessed using dot notation
# https://stackoverflow.com/a/23689767/11731813
# This may have some issues as seen in comments here: https://stackoverflow.com/a/1123026/11731813
class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__