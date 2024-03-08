from constants import DEV, GLOABL_LOGS_DIR
from termcolor import colored
import os
import time
import re
from utils.check_make_dir import check_make_dir
from interfaces.logger_interface import LoggerInterface
from interfaces.project_interface import ProjectInterface


class Logger(LoggerInterface):
    def __init__(self, project: ProjectInterface):
        self.project = project
        self.style_dict = {
            "hrule": {"color": "light_red", "attr": [], "char": "—"},
            "prefix": {
                "color": "red",
                "attr": ["dark"],
                "lpad": "[",
                "rpad": "] ",
            },
            "header": {"color": "light_cyan", "attr": ["bold"]},
            "time": {"color": "light_grey", "attr": [], "format": "%I:%M%p"},
            "prompt": {"color": "light_blue", "attr": ["blink", "bold"], "char": ">>"},
        }
        self.PROGRESS_CHARSET = "squares"
        # How many seconds must have passed since last log message to embed text in rule, set to 0 to always embed
        self.last_logged_second = None
        self.TIME_INVERVAL_UPDATE = 40
        self.most_recent_caller = None

        self.__set_log_file_fullpath()

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
        progress_bar_charsets = {
            "stars_and_moon": {
                "filled": [" ✨", " 🌟", " 💫", " ⭐️"],
                "empty": " 🌑",
            },
            "slices": {
                "filled": [" ◴", " ◷", " ◶", " ◵"],
                "empty": " ◎",
            },
            "hemispheres": {
                "filled": [" ◐", " ◓", " ◑", " ◒"],
                "empty": " ◯",
            },
            "arcs": {
                "filled": [" ◜", " ◝", " ◞", " ◟"],
                "empty": " ○",
            },
            "squares": {"filled": [" ◰", " ◳", " ◲", " ◱"], "empty": " ◻"},
            "keycap_digits": {
                "filled": [" 1️⃣", " 2️⃣", " 3️⃣", " 4️⃣", " 5️⃣", " 6️⃣", " 7️⃣", " 8️⃣", " 9️⃣", " 🔟"],
                "empty": " ⏸️",
            },
            "day_cycle": {"filled": ["🌄", "🌅", "🌇", "🌆", "🌃"], "empty": "⬜️"},
        }
        prefix = self.__get_prefix(caller_prefix)
        prefix_len = self.__len_without_ansi(prefix)
        header = colored(
            header.title(),
            self.style_dict["header"]["color"],
            attrs=self.style_dict["header"]["attr"],
        )
        cur = int(cur)
        total = int(total)
        original_cur = int(cur)
        original_total = int(total)
        filled = progress_bar_charsets[self.PROGRESS_CHARSET]["filled"]
        # Divide Max and Value if necessary to fit within (terminal width - (prefix length + header length))
        allowed_len = self.__terminal_length() - (prefix_len + len(header) + 9)
        if len(total * filled[0]) > allowed_len:
            ratio = len(total * filled[0]) / allowed_len
            total = int(total / ratio)
            cur = int(cur / ratio)

        filled_str = filled[cur % len(filled)]
        empty_str = progress_bar_charsets[self.PROGRESS_CHARSET]["empty"]

        bar = filled_str * cur + empty_str * (total - cur)

        print(
            f"{prefix}{header} {bar} {original_cur: >2}/{original_total: <2} {original_cur/original_total*100:.2f}%".replace(
                "\n", ""
            ),
            end="\r",
        )

    def get_isolated_child_logfile(self, suffix):
        filename = "-".join(
            [
                f"logs-{self.project.name}",
                suffix.replace(" ", "_"),
                self.project.author.replace(" ", "_"),
                time.strftime("%b_%d-%I_%M"),
                ".log",
            ]
        )
        return os.path.join(self.logs_dir, filename)

    def get_prompt(self):
        return "\n" + colored(
            self.style_dict["prompt"]["char"].strip() + " ",
            self.style_dict["prompt"]["color"],
            attrs=self.style_dict["prompt"]["attr"],
        )

    def __terminal_length(self):
        return os.get_terminal_size().columns - 2

    def session_log_exists(self):
        return os.path.exists(self.log_file_fullpath)

    def __set_log_file_fullpath(self):
        self.logs_dir = os.path.join(self.project.repo_root, GLOABL_LOGS_DIR)
        check_make_dir(self.logs_dir)
        self.log_filename = "-".join(
            [
                f"logs-{self.project.name}",
                self.project.author.replace(" ", "_"),
                time.strftime("%b_%d-%I_%M"),
                ".log",
            ]
        )
        self.log_file_fullpath = os.path.join(self.logs_dir, self.log_filename)

    def __time_has_changed(self):
        cur_second = int(time.time())
        if (
            not self.last_logged_second
            or cur_second - self.last_logged_second >= self.TIME_INVERVAL_UPDATE
        ):
            self.last_logged_second = cur_second
            return True
        return False

    def __get_prefix(self, text):
        return colored(
            self.style_dict["prefix"]["lpad"]
            + text
            + self.style_dict["prefix"]["rpad"],
            self.style_dict["prefix"]["color"],
            attrs=self.style_dict["prefix"]["attr"],
        )

    def get_embedded_hrule(self, embed_text) -> str:
        if not self.__time_has_changed():
            return self.get_hrule()

        non_embedded_len = self.__len_without_ansi(self.get_hrule())
        # Text is embedded in rule at 3/4th of the terminal width
        if len(embed_text) > self.__terminal_length() - 4:
            print("Embedded text is too long to fit in terminal width")
            return self.get_hrule()
        one_fourth = (self.__terminal_length() - len(embed_text)) // 4
        three_fourths = 3 * one_fourth

        cur_length = three_fourths + len(embed_text) + one_fourth
        # Decrement one_fourth if necessary to match non-embedded hrule length
        if cur_length < non_embedded_len:
            one_fourth += non_embedded_len - cur_length
        # Increment one_fourth if necessary to match non-embedded hrule length
        elif cur_length > non_embedded_len:
            one_fourth -= cur_length - non_embedded_len

        return (
            colored(
                "—" * three_fourths,
                self.style_dict["hrule"]["color"],
                attrs=self.style_dict["hrule"]["attr"],
            )
            + colored(
                embed_text,
                self.style_dict["time"]["color"],
                attrs=self.style_dict["time"]["attr"],
            )
            + colored(
                "—" * one_fourth,
                self.style_dict["hrule"]["color"],
                attrs=self.style_dict["hrule"]["attr"],
            )
        )

    def __len_without_ansi(self, text: str) -> int:
        return len(self.decolor(text))

    def get_hrule(self) -> str:
        return colored(
            self.style_dict["hrule"]["char"] * self.__terminal_length(),
            self.style_dict["hrule"]["color"],
            attrs=self.style_dict["hrule"]["attr"],
        )

    def extract_header(self, msg: str) -> list[str]:
        separator_candidates = [
            ":",
            "—",
            r"\)",  # Escaped parenthesis
            r"\]",  # Escaped square bracket
            r"\}",  # Escaped curly bracket
            r"\|",
            "-",
            ";",
            "=",
            ">",
            "\t",
            "\n",
            r"\?",  # Escaped question mark
            r"\*",  # Escaped asterisk
            r"\+",  # Escaped plus sign
            ",",
            "~",
            "/",
            r"\\",  # Escaped backslash
            "&",
            "_",
            " ",
            "",
        ]
        split_by_sep = lambda sep: re.split(sep, msg, 1)
        i = 0
        # Proceed through possible separators until one actually separates the message
        while len(split_by_sep(separator_candidates[i])) <= 1:
            i += 1
        separator = separator_candidates[i]
        msg_parts = split_by_sep(separator)
        return [msg_parts[0] + separator, msg_parts[1].strip()]

    def text_to_lines(self, text: str, caller_prefix) -> str:
        # Split the text into lines which are less than (teminal width - length of the prefix)
        prefix_len = self.__len_without_ansi(self.__get_prefix(caller_prefix))
        max_text_line_len = self.__terminal_length() - prefix_len
        return "".join(
            [
                "\n" + " " * prefix_len + text.strip()[i : i + max_text_line_len]
                for i in range(0, len(text), max_text_line_len)
            ]
        )

    def decolor(self, text: str) -> str:
        # Define a regular expression pattern to match any ANSI escape sequence
        ansi_escape = re.compile(r"\x1B\[([\d]{1,2}(;[\d]{1,2})*)?[m|K]")

        # Use the regular expression to remove ANSI escape sequences from the text
        return ansi_escape.sub("", text)

    def pad_with_rules(self, text: str, embed_text) -> str:
        return "\n".join([self.get_embedded_hrule(embed_text), text, self.get_hrule()])

    def format_log_message(
        self,
        *args,
        caller_prefix: str,
        color_text: bool,
        pad_with_rules: bool,
        embed=None,
    ) -> str:
        if not embed:
            embed = f" {time.strftime('%I:%M%p')} "

        in_string = " ".join(map(str, args))
        header, text = self.extract_header(in_string)
        lines_string = self.text_to_lines(text, caller_prefix)

        ret = (
            self.__get_prefix(caller_prefix)
            + colored(
                header.title(),
                self.style_dict["header"]["color"],
                attrs=self.style_dict["header"]["attr"],
            )
            + lines_string
        )
        if pad_with_rules or caller_prefix != self.most_recent_caller:
            ret = self.pad_with_rules(ret, embed)
        if not color_text:
            ret = self.decolor(ret)

        self.most_recent_caller = caller_prefix
        return "\n" + ret

    def log(
        self,
        *args,
        caller_prefix: str,
        print_to_console: bool = DEV,
        write_to_log: bool = True,
        pad_with_rules: bool = False,
    ):
        """
        Prints the formatted message to the console if DEV is True,
        and logs the formatted message.

        Args:
            *args: Variable number of arguments to be formatted and logged.
            print_to_console (bool, optional): Whether to print the message to the console. Defaults to DEV.
            write_to_log (bool, optional): Whether to write the message to the log file. Defaults to True.
            pad_with_rules (bool, optional): Whether to pad the message with horizontal rules. Defaults to False.
        """
        if print_to_console:
            print(
                self.format_log_message(
                    *args,
                    caller_prefix=caller_prefix,
                    color_text=True,
                    pad_with_rules=pad_with_rules,
                )
            )

        if write_to_log:
            with open(
                self.log_file_fullpath, "a" if self.session_log_exists() else "w"
            ) as log_file:
                log_file.write(
                    self.format_log_message(
                        *args,
                        caller_prefix=caller_prefix,
                        color_text=False,
                        pad_with_rules=pad_with_rules,
                    )
                )
