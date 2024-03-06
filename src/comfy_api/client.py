import json
from urllib import request
import websocket
import uuid
import subprocess
import time
import os
from interfaces.project_interface import ProjectInterface
from interfaces.logger_interface import LoggerInterface
from constants import COMFY_PORT, COMFY_PATH, COMFY_API_MAX_CONNECT_ATTEMPTS


class ComfyClient:
    def __init__(
        self,
        project: ProjectInterface,
        workflow_json_path: str,
        logger: LoggerInterface,
    ):
        self.project = project
        self.workflow_json_path = workflow_json_path
        self.logger = logger
        self.server_url = f"http://localhost:{COMFY_PORT}"
        self.client_id = str(uuid.uuid4())

        self.set_workflow()
        self.logger.log(f"Starting Comfy server at {self.server_url}")

    def set_workflow(self):
        try:
            with open(self.workflow_json_path, "r") as workflow_file:
                self.workflow_json = json.load(workflow_file)
        except FileNotFoundError as e:
            raise e(
                f"The passed workflow template json file could not be found at the given path: {self.workflow_json_path}"
            )

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
        """
        https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py
        """
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
            self.logger.log(
                f"Comfy server finished processing request at: {end_time} (Time elapsed: {time_diff_formatted})"
            )

        except Exception as e:
            self.logger.log(f"Comfy API workflow failure: {e}")
            raise e
        finally:
            self.stop_comfy_server()
            ws.close()
