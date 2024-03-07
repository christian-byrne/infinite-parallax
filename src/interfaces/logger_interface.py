from typing import Protocol
from constants import DEV


class LoggerInterface(Protocol):
    RULE_COLOR: str  # The color of the horizontal rule. A termcolor color.
    PREFIX_COLOR: str  # The color of the log prefix. A termcolor color.
    log_file_fullpath: str  # The full path to the log file for this logging instance's session.

    def log(self, *args, print_to_console: bool = DEV, write_to_log: bool = True, pad_with_rules: bool = True):
        """
        Automatically parses and formats the message, regardless of type or number of
        arguments and prints it and/or writes it to the log file.

        Args:
            *args: Variable number of arguments to be formatted and logged.
            print_to_console: Whether to print the message to the console. Default is DEV.
            write_to_log: Whether to write the message to the log file. Default is True.
            pad_with_rules: Whether to pad the message with horizontal rules. Default is True.
        """
        ...
