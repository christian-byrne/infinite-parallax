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
        logger: Logger,
        output_directory: str,
        input_directory: str,
        caller_prefix: str = "COMFY SERVER",
    ):
        self.project = project
        self.logger = logger
        # Create separate logger/logfile for parallel comfy server process's stdout/stderr
        self.detatched_logfile = self.logger.get_isolated_child_logfile(caller_prefix)
        # The directory to save the generated images for this server instance to, used as a command line argument when launching comfy
        self.output_directory = output_directory
        self.input_directory = input_directory
        self.caller_prefix = caller_prefix
        self.server_url = f"http://localhost:{COMFY_PORT}"
        self.comfy_compatible_python_ver = "3.10.6"
        self.comfy_launcher_target = os.path.join(COMFY_PATH, "main.py")

        self.__set_python_path()
        self.log(
            f"This is the command that will be used to start comfy: {self.__get_comfy_cli_args()}",
            pad_with_rules=False,
        )

    def log(self, *args, **kwargs):
        self.logger.log(caller_prefix=self.caller_prefix, *args, **kwargs)

    def start(self):
        """Wrapper for server so that it can be wrapped in try/except block that terminates the server on error"""
        try:
            self.__launch_process()
            self.log("Comfy server started")
        except Exception as e:
            self.log(f"Error starting comfy server: {e}")
            self.kill()

    def kill(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.log("Comfy Process: server stopped")
        else:
            self.log("Comfy Process Disconnect Attempt: No Comfy server to stop")

    def __get_comfy_cli_args(self):
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
            # Maybe need previews to be enabled for api client listener
            # "--preview-method",
            # "none",
            "--disable-auto-launch",
            "--disable-metadata",
            # --cuda-device [CUDA_DEVICE_INDEX],
            # --directml [DIRECTML_DEVICE],
            # --cpu
            # --dont-print-server
            # --windows-standalone-build
        ]

    # TODO: an actual solution for this (e.g., get python 3.8 in venv for starting comfy)
    def __set_python_path(self):
        self.log(
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
                self.log(
                    f"Python {self.comfy_compatible_python_ver}: not found, installing it with pyenv",
                    pad_with_rules=False,
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

        self.log(f"Using python path: {self.python_path}")

    def __launch_process(self):
        # Check if server already running
        try:
            with request.urlopen(self.server_url) as f:
                if f.status == 200:
                    self.log("Comfy server status: Already running. Connecting")
                    return
        except (error.URLError, error.HTTPError, KeyError):
            self.log(
                "Comfy server status: Not running. Starting new server in detached process"
            )

        # NOTE: Changing dirs necessary if using pyenv aliases per location, i think (not sure)
        original_dir = os.getcwd()
        os.chdir(COMFY_PATH)

        # Launch the server subprocess, don't wait for it to finish, and redirect its output to server log file
        server_logfile = open(self.detatched_logfile, "w")
        self.server_process = subprocess.Popen(
            self.__get_comfy_cli_args(),
            stdout=server_logfile,
            stderr=server_logfile,
            start_new_session=True,
        )
        os.chdir(original_dir)
