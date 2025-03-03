ELLIPSIS = "..."


def pad_string(string, length, padding=" ", to_end=True):
    if len(string) >= length:
        return string

    while len(string) < length:
        if to_end:
            string += " "
        else:
            string = " " + string

    return string


def shorten_string(string, length, remove_end=True, do_ellipsis=False):
    if len(string) <= length:
        return string

    num_discard = len(string) - length + (len(ELLIPSIS) if do_ellipsis else 0)

    if num_discard > len(string):
        return ""

    if remove_end:
        return string[:-num_discard] + (ELLIPSIS if do_ellipsis else "")
    return (ELLIPSIS if do_ellipsis else "") + string[num_discard:]