from constants import DEV, LOGS_DIR
from termcolor import colored
import os
import time
from utils.check_make_dir import check_make_dir


class Logger:
    def __init__(
        self, project_name: str, author="", version="0.1.0", write_to_log=True
    ):
        self.project_name = project_name.replace(" ", "_")
        if author == "":
            self.set_author()
        else:
            self.author = author.replace(" ", "_")
        self.version = version.replace(" ", "_")
        self.write_to_log = write_to_log

        self.set_log_file_fullpath()

        self.terminal_length = os.get_terminal_size().columns
        self.horizontal_break = "\n" + "—" * (self.terminal_length - 4) + "\n"
        self.horizontal_break_colored = (
            "\n" + colored("—" * (self.terminal_length - 4), "light_red") + "\n"
        )
        self.prefix_string = "[DEVMODE] "
        self.prefix_colored = colored(self.prefix_string, "red")
        self.prefix_whitespace = " " * (len(self.prefix_string) - 1)
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
        logs_dir = os.path.join(repo_root, LOGS_DIR)
        check_make_dir(logs_dir)
        log_filename = (
            f"logs-{self.project_name}-{self.author}-{time.strftime('%m_%d_%Y-%I_%M')}.log"
        )
        self.log_file_fullpath = os.path.join(logs_dir, log_filename)

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

        horizontal_break = (
            self.horizontal_break_colored if color_text else self.horizontal_break
        )
        prefix = self.prefix_colored if color_text else self.prefix_string
        colored_title = colored(title, "light_cyan") if color_text else title
        horizontal_break_end = (
            self.horizontal_break_colored if color_text else self.horizontal_break
        )

        return (
            horizontal_break
            + prefix
            + colored_title
            + text_formatted
            + horizontal_break_end
        )

    def log(self, *args):
        """
        Prints the formatted message to the console if DEV is True,
        and logs the formatted message.

        Args:
            *args: Variable number of arguments to be formatted and logged.
        """
        if DEV:
            print(self.format_log_message(*args, color_text=True))

        if self.write_to_log:
            with open(
                self.log_file_fullpath, "a" if self.session_log_exists() else "w"
            ) as log_file:
                log_file.write(self.format_log_message(*args, color_text=False))
