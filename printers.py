from . import files as ut


def make_console_printer():
    def printer(string, do_newline=True):
        print(string, end=("\n" if do_newline else ""))
    return printer


def make_file_printer(filename, clear, max_size=None, backup_suffix=".backup"):
    backup_filename = filename + backup_suffix

    if not ut.target_exists(filename):
        ut.create_file(filename, "")

    if clear:
        ut.clear_file(filename)
        if ut.target_exists(filename + backup_suffix):
            ut.delete_file(backup_filename)

    def printer(string, do_newline=True):
        if max_size is not None and ut.get_file_size(filename) >= max_size:
            ut.copy_file(filename, backup_filename)
            ut.clear_file(filename)

        with open(filename, "a") as f:
            try:
                f.write(string + ("\n" if do_newline else ""))
            except UnicodeEncodeError as e:
                f.write("PRINTER ERROR: Cannot write string\n")
    return printer


def make_combined_printer(filename, clear, max_file_size):
    console_printer = make_console_printer()
    file_printer = make_file_printer(filename, clear, max_file_size)

    def printer(string, do_newline=True):
        console_printer(string, do_newline)
        file_printer(string, do_newline)
    return printer


def select_printer(do_logging, do_console_logging, do_file_logging, clear_log_file, output_filename, max_file_size):
    if not do_logging:
        return None
    elif do_console_logging and do_file_logging:
        return make_combined_printer(output_filename, clear_log_file, max_file_size)
    elif do_console_logging:
        return make_console_printer()
    elif do_file_logging:
        return make_file_printer(output_filename, clear_log_file, max_file_size)
    return None