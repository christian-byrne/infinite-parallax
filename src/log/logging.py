from constants import DEV, LOGS_DIR
from termcolor import colored
import os
import time
from utils.check_make_dir import check_make_dir
from interfaces.logger_interface import LoggerInterface

class Logger(LoggerInterface):
    def __init__(self, project_name: str, author="", version="0.1.0"):
        self.project_name = project_name.replace(" ", "_")
        if author == "":
            self.set_author()
        else:
            self.author = author.replace(" ", "_")
        self.version = version.replace(" ", "_")

        self.set_log_file_fullpath()

        self.RULE_COLOR = "light_red"
        self.PREFIX_COLOR = "red"

        self.terminal_length = os.get_terminal_size().columns
        self.horizontal_rule = "\n" + "—" * (self.terminal_length - 4) + "\n"
        self.horizontal_rule_colored = (
            "\n" + colored("—" * (self.terminal_length - 4), self.RULE_COLOR) + "\n"
        )
        self.prefix_string = "[DEVMODE] "
        self.prefix_colored = colored(self.prefix_string, self.PREFIX_COLOR)
        self.prefix_whitespace = " " * len(self.prefix_string)
        self.max_text_line_length = self.terminal_length - (len(self.prefix_string) + 1)

    def session_log_exists(self):
        return os.path.exists(self.log_file_fullpath)

    def set_author(self):
        try:
            username = os.getenv("USER")
        except KeyError:
            self.dev_print("USER environment variable not set")
            username = "windows_user"
        except (TypeError, PermissionError):
            self.dev_print("USER environment variable not a string")
            username = "secure_user"
        except ValueError:
            self.dev_print("USER environment variable not valid")
            username = "nonASCII_user"
        except Exception as e:
            self.dev_print(e)
            username = "unknown_user"

        self.author = username.replace(" ", "_")

    def set_log_file_fullpath(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        repo_root = os.path.dirname(repo_root)
        self.logs_dir = os.path.join(repo_root, LOGS_DIR)
        check_make_dir(self.logs_dir)
        log_filename = f"logs-{self.project_name}-{self.author}-{time.strftime('%m_%d_%Y-%I_%M')}.log"
        self.log_file_fullpath = os.path.join(self.logs_dir, log_filename)

    def get_top_horizontal_rule(self, color_text: bool) -> str:
        # Top horizontal rule should have hours:minutes in the 3/4th of the terminal width, still surrounded by emdashes
        cur_time = time.strftime("%H:%M%p")
        one_fourth = (self.terminal_length - len(cur_time) + 2) // 4
        three_fourths = 3 * one_fourth
        rule = f"\n{'—' * one_fourth}{cur_time}{'—' * three_fourths}"
        return colored(rule, self.RULE_COLOR) if color_text else rule

    def format_log_message(self, *args, color_text: bool) -> str:
        in_string = " ".join(map(str, args))
        message_parts = in_string.split(":")
        if len(message_parts) == 1:
            message_parts = in_string.split("\n")
        if len(message_parts) == 1:
            message_parts = [in_string.strip().split(" ")[0], in_string]

        title = message_parts[0]
        text = " ".join(message_parts[1:])

        # Split the text into lines which are less than (teminal width - length of the prefix)
        char_index = 0
        text_formatted = ""
        for char in text:
            if char_index % self.max_text_line_length == 0:
                text_formatted += "\n" + self.prefix_whitespace
            text_formatted += char
            char_index += 1

        top_horizontal_rule = self.get_top_horizontal_rule(color_text)
        prefix = self.prefix_colored if color_text else self.prefix_string

        colored_title = colored(title, "light_cyan") if color_text else title
        bot_horizontal_rule = (
            self.horizontal_rule_colored if color_text else self.horizontal_rule
        )

        return (
            top_horizontal_rule
            + prefix
            + colored_title
            + text_formatted
            + bot_horizontal_rule
        )

    def log(self, *args, print_to_console: bool = DEV, write_to_log: bool = True):
        """
        Prints the formatted message to the console if DEV is True,
        and logs the formatted message.

        Args:
            *args: Variable number of arguments to be formatted and logged.
        """
        if print_to_console:
            print(self.format_log_message(*args, color_text=True))

        if write_to_log:
            with open(
                self.log_file_fullpath, "a" if self.session_log_exists() else "w"
            ) as log_file:
                log_file.write(self.format_log_message(*args, color_text=False))
