# Python Utilities
A module containing a variety of utilities for Python development.

# Important Notes
Be sure to include the directory containing this module in your PYTHONPATH.
Modules in the package refer to other modules in the package, so it relies
on this to be able to access the necessary functionality.

# Versions and Requirements
Development was conducted with recent versions of Python 3. The package is
guarenteed to work as expected with a Python 3.12 installation. Development
was done on a Windows 11 machine, but realistically it'll work on any OS.
This is Python, not C.

There are no external libraries used in this module. Any imports (with the
of self-use) come packaged with a standard Python 3 installation.

# Documentation
See each module to see what is included in each module. I'm far to lazy
and forgetful to both write it all here *and* remember to keep this updated.

---

## <code>*python_utilities.*__file__</code>
Contains utilities related to file management and manipulation.

### <code>*python_utilities.file.*__file_counting__</code>
Count the files in a directory. Useful for creating backups.
Using the names of the files in the specified directory, utilities in the
module can determine the next file name.

### <code>*python_utilities.file.*__utilities__</code>
General file utilities.

---

## <code>*python_utilities.*__log__</code>
Contains utilities related to logging.

### <code>*python_utilities.log.*__logger__</code>
The primary logger. Instantiate a generic (and limitted) logger with
`Logger.make_generic_logger`. The resulting instance can be treated like
a method which takes a single string as an argument.

More complex loggers require further set up. Create an instance of the
`Logger` object and pass the desired details into the constructor. The
`types` argument must be a dictionary of strings (the name of that type)
and a boolean (whether or not that type is active). The `printer` argument
must be a function that takes a single string (the message being logged)
as an argument and does the desired action with that string.

### <code>*python_utilities.log.*__printers__</code>
A small repository of printer-generating functions. The returns of these
functions can be used as the `printer` argument of the `Logger` constructor.

---

# Extra Notes
Realistically, this entire package is over engineered to do things that
Python can do fairly easily already. The logger? The `print` function
works beautifully. The file utilities? Probably something easy for that, too.
But oh well. This was (mostly) fun.