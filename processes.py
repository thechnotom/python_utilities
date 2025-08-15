from . import logger as lg
import subprocess
from collections import namedtuple


ProcessResults = namedtuple("ProcessResults", ["stdout", "stderr", "success"])


def run_process(command, timeout=float("inf"), encoding="utf-8", logger=None):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output = None
    try:
        output = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as e:
        lg.Logger.log(f"Failed to communicate with process (timeout: {timeout}): {command}", logger)
        process.kill()
        return ProcessResults("", "", False)
    out = output[0].decode(encoding)
    err = output[1].decode(encoding)

    return ProcessResults(out, err, True)