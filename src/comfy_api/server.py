from interfaces.project_interface import ProjectInterface
from log.logging import Logger
from constants import COMFY_PATH, COMFY_PORT
import subprocess
import os
from urllib import request, error


class ComfyServer:
    def __init__(
        self,
        project: ProjectInterface,
        main_thread_logger: Logger,
        output_directory: str,
        input_directory: str,
    ):
        self.project = project
        # Use main thread logger to still be able to print to console
        self.main_thread_logger = main_thread_logger
        # Create separate logger/logfile for parallel comfy server process's stdout/stderr
        self.detached_server_logger = Logger(
            f"{self.project.name}-comfy_server",
            author=self.project.author,
            version=self.project.version,
        )
        # The directory to save the generated images for this server instance to, used as a command line argument when launching comfy
        self.output_directory = output_directory
        self.input_directory = input_directory
        self.server_url = f"http://localhost:{COMFY_PORT}"
        self.comfy_compatible_python_ver = "3.10.6"
        self.comfy_launcher_target = os.path.join(COMFY_PATH, "main.py")

        self.set_python_path()
        self.main_thread_logger.log(
            f"This is the command that will be used to start comfy: {self.get_comfy_cli_args()}"
        )

    def get_comfy_cli_args(self):
        """https://github.com/comfyanonymous/ComfyUI/blob/master/comfy/cli_args.py"""
        # TODO: --extra-model-paths-config PATH [PATH . . . ] Load one or more extra_model_paths.yaml files. Load models specific to this project
        return [
            self.python_path,
            self.comfy_launcher_target,
            "--port",
            str(COMFY_PORT),
            "--output-directory",
            self.output_directory,
            "--input-directory",
            self.input_directory,
            "--preview-method",
            "none",
            "--disable-auto-launch",
            "--disable-metadata",
            # --cuda-device [CUDA_DEVICE_INDEX],
            # --directml [DIRECTML_DEVICE],
            # --cpu
            # --dont-print-server
            # --windows-standalone-build
        ]

    # TODO: an actual solution for this (e.g., get python 3.8 in venv for starting comfy)
    def set_python_path(self):
        self.main_thread_logger.log(
            f"Trying to find path to python version compatible with comfy server: version {self.comfy_compatible_python_ver}"
        )
        self.python_path = (
            subprocess.check_output(["which", "python3"]).decode().strip()
        )
        if "pyenv" in self.python_path:
            pyenv_root = subprocess.check_output(["pyenv", "root"]).decode().strip()
            self.python_path = os.path.join(
                pyenv_root,
                "versions",
                self.comfy_compatible_python_ver,
                "bin",
                "python",
            )
            if not os.path.exists(self.python_path):
                self.logger.log(
                    f"Python {self.comfy_compatible_python_ver}: not found, installing it with pyenv"
                )
                subprocess.run(["pyenv", "install", self.comfy_compatible_python_ver])
                self.python_path = os.path.join(
                    pyenv_root,
                    "versions",
                    self.comfy_compatible_python_ver,
                    "bin",
                    "python",
                )
        if not self.python_path or not os.path.exists(self.python_path):
            raise RuntimeError("Python path not found")

        self.main_thread_logger.log(f"Using python path: {self.python_path}")

    def start(self):
        # TODO: not sure if changing directories and then switching back is necessary
        original_dir = os.getcwd()

        # Check if server already running
        try:
            with request.urlopen(self.server_url) as f:
                if f.status == 200:
                    self.main_thread_logger.log(
                        "Comfy server status: already running, connecting to existing server"
                    )
                    return
        except (error.URLError, error.HTTPError, KeyError):
            self.main_thread_logger.log(
                "Comfy server status: not running. Starting new server in detached process"
            )

        os.chdir(COMFY_PATH)
        # Launch the server subprocess, don't wait for it to finish, and redirect its output to server log file
        server_log = open(self.detached_server_logger.log_file_fullpath, "w")
        self.server_process = subprocess.Popen(
            self.get_comfy_cli_args(),
            stdout=server_log,
            stderr=server_log,
            start_new_session=True,
        )
        os.chdir(original_dir)

    def terminate(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.main_thread_logger.log("Comfy server stopped")
        else:
            self.main_thread_logger.log("No Comfy server to stop")
