from typing import Protocol
from constants import DEV


class LoggerInterface(Protocol):
    HRULE_COLOR: str  # The color of the horizontal rule. A termcolor color.
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

    def get_prompt(self) -> str:
        """Returns the prompt string for the logger.
        
        Example:
            print("Enter your name" + logger.get_prompt())
            >>> Enter your name:
            >>> >  
        """
        ...

    def session_log_exists(self) -> bool:
        """Returns True if the session log file exists, False otherwise."""
        ...

    def get_isolated_child_logfile(self, suffix: str) -> str:
        """Returns the full path to a log file for a child process to write to.
        This new child logfile will be isolated from the main log file, but will
        be associated with the same session by naming convention."""
        ...

    def progress_bar(self, cur: str, total: str, header: str, caller_prefix: str):
        """
        Displays a progress bar with the current progress, total progress, and a header.

        Args:
            cur (str): The current progress value.
            total (str): The total progress value.
            header (str): The header to be displayed.
            caller_prefix (str): The prefix to be added before the header.

        Returns:
            None
        """
        ...