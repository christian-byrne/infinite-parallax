"""
https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py
"""

import json
from urllib import request
import websocket
import uuid
import subprocess
import time
import os
from interfaces.project_interface import ProjectInterface
from constants import COMFY_PORT, COMFY_PATH, COMFY_API_MAX_CONNECT_ATTEMPTS
from log.logging import Logger


class ComfyClient:
    def __init__(self, project: ProjectInterface, workflow_json_path: str):
        self.project = project
        self.workflow_json_path = workflow_json_path
        self.server_url = f"http://localhost:{COMFY_PORT}"
        self.client_id = str(uuid.uuid4())

        self.logger = Logger(
            self.project.name, self.project.author, self.project.version
        )

        self.set_python_path()
        self.set_workflow()
        self.logger.log(f"Starting Comfy server at {self.server_url}")
        self.start_detached_comfy_server()

    def set_python_path(self):
        self.python_path = (
            subprocess.check_output(["which", "python3"]).decode().strip()
        )
        if "pyenv" in self.python_path:
            python_version = "3.10.6"
            pyenv_root = subprocess.check_output(["pyenv", "root"]).decode().strip()
            self.python_path = os.path.join(
                pyenv_root, "versions", python_version, "bin", "python"
            )
            if not os.path.exists(self.python_path):
                self.logger.log(
                    f"Python {python_version}: not found, installing it with pyenv"
                )
                subprocess.run(["pyenv", "install", python_version])
                self.python_path = os.path.join(
                    pyenv_root, "versions", python_version, "bin", "python"
                )
        if not self.python_path or not os.path.exists(self.python_path):
            raise RuntimeError("Python path not found")

    def start_detached_comfy_server(self):
        """cd /home/c_byrne/tools/sd/sd-interfaces/ComfyUI; python main.py"""

        comfy_main_path = os.path.join(COMFY_PATH, "main.py")
        original_dir = os.getcwd()

        server_log_filepath = os.path.join(self.logger.logs_dir, "comfy_server.log")
        # create the log file if it doesn't exist
        if not os.path.exists(server_log_filepath):
            with open(server_log_filepath, "w") as f:
                f.write("")

        # check if server already running
        try:
            with request.urlopen(self.server_url) as f:
                if f.status == 200:
                    self.logger.log("Comfy server already running")
                    return
        except Exception as e:
            self.logger.log("Comfy server not running. Starting")

        os.chdir(COMFY_PATH)
        # Launch the server subprocess, don't wait for it to finish, and redirect its output to a local log file
        server_log = open(server_log_filepath, "w")
        self.server_process = subprocess.Popen(
            [self.python_path, comfy_main_path],
            stdout=server_log,
            stderr=server_log,
            start_new_session=True,
        )
        os.chdir(original_dir)

    def stop_comfy_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.logger.log("Comfy server stopped")
        else:
            self.logger.log("No Comfy server to stop")

    def set_workflow(self):
        with open(self.workflow_json_path, "r") as workflow_file:
            self.workflow_json = json.load(workflow_file)

    def parse_node_name(self, data):
        node_index = str(data["node"])
        try:
            node_name = self.workflow_json[node_index]["_meta"]["title"]
        except KeyError:
            try:
                node_name = self.workflow_json[node_index]["class_type"]
            except KeyError:
                node_name = "Unknown"
        return node_name

    def print_node_progress(self, data):
        """print a progress bar
        progress dicts look like
        {'type': 'progress', 'data': {'value': 34, 'max': 35, 'prompt_id': '4c4d1544-da2e-4321-806c-49070a8b865a', 'node': '17'}}
        """
        cur_node_name = self.parse_node_name(data)
        try:
            print(
                f"{cur_node_name}: {'#' * data['value']}{'-' * (data['max'] - data['value'])} {data['value']}/{data['max']}",
                end="\r",
            )
        except KeyError:
            pass

    def queue_workflow(self):
        try:
            ws = websocket.WebSocket()
            # Try to connect every second for specified attempt #. Necessary because can take a long time for comfyui to start, but don't want to wait any longer than necessary
            for attempt in range(COMFY_API_MAX_CONNECT_ATTEMPTS):
                try:
                    ws.connect(
                        f"ws://localhost:{COMFY_PORT}/ws?clientId={self.client_id}"
                    )
                except ConnectionRefusedError:
                    self.logger.log(
                        f"Comfy server connection attempt {attempt + 1}/{COMFY_API_MAX_CONNECT_ATTEMPTS}: failed"
                    )
                    time.sleep(1)
                    continue

            data = json.dumps(
                {"prompt": self.workflow_json, "client_id": self.client_id}
            ).encode("utf-8")

            start_time_epoch = time.time()
            start_time = time.strftime("%I_%M")
            self.logger.log(f"Queueing workflow at: {start_time}")

            req = request.Request(self.server_url + "/prompt", data=data)
            resp = json.loads(request.urlopen(req).read())
            prompt_id = resp["prompt_id"]

            # Don't break until the server has finished processing the request
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message["type"] == "status":
                        print(message["data"]["status"])
                    if message["type"] == "progress":
                        self.print_node_progress(message["data"])
                    if message["type"] == "executing":
                        data = message["data"]
                        cur_node_name = self.parse_node_name(data)
                        print(f"Executing {cur_node_name}")

                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            break  # Execution is done
                else:
                    continue  # previews are binary data

            end_time_epoch = time.time()
            end_time = time.strftime("%I_%M")
            time_diff = end_time_epoch - start_time_epoch
            time_diff_formatted = time.strftime("%H:%M:%S", time.gmtime(time_diff))
            self.logger.log(f"Comfy server finished processing request at: {end_time} (Time elapsed: {time_diff_formatted})")

        except Exception as e:
            self.logger.log(f"Comfy API workflow failure: {e}")
            raise e
        finally:
            self.stop_comfy_server()
            ws.close()
