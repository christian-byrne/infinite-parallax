from typing import Protocol
from constants import DEV


class LoggerInterface(Protocol):
    RULE_COLOR: str  # The color of the horizontal rule. A termcolor color.
    PREFIX_COLOR: str  # The color of the log prefix. A termcolor color.
    log_file_fullpath: str  # The full path to the log file for this logging instance's session.

    def log(self, *args, print_to_console: bool = DEV, write_to_log: bool = True):
        """
        Automatically parses and formats the message, regardless of type or number of
        arguments. Prints to console if print_to_console is True (default is based on 
        whether DEV is True), and writes to the log file if write_to_log is True.

        Args:
            *args: Variable number of arguments to be formatted and logged.
        """
        ...
