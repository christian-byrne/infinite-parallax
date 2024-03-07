import json
from urllib import request
import websocket
import uuid
import time
from workflow_wrapper.workflow import ComfyAPIWorkflow
from interfaces.project_interface import ProjectInterface
from interfaces.logger_interface import LoggerInterface
from constants import COMFY_PORT, COMFY_API_MAX_CONNECT_ATTEMPTS


class ComfyClient:
    """
    https://github.com/comfyanonymous/ComfyUI/blob/master/script_examples/websockets_api_example.py
    """

    def __init__(
        self,
        project: ProjectInterface,
        workflow: ComfyAPIWorkflow,
        logger: LoggerInterface,
    ):
        self.project = project
        self.workflow = workflow
        self.logger = logger
        self.server_url = f"http://localhost:{COMFY_PORT}"
        self.client_id = str(uuid.uuid4())
        self.__websocket = None
        self.logger.log(f"New Comfy Client Created with ID: {self.client_id}")

    def is_connected(self):
        """
        Check if the client is currently connected to the server.

        Returns:
            bool: True if the client is connected, False otherwise.
        """
        return self.__websocket is not None and self.__websocket.connected

    def connect(self):
        """
        Connects to the Comfy server using a WebSocket connection.
        Attempts to connect to the server every second COMFY_API_MAX_CONNECT_ATTEMPTS
        times.

        This is done because Comfy may take a long time to start up, but
        we don't want to wait any longer than necessary.

        Raises:
            ConnectionError: If the connection to the Comfy server fails.
        """
        self.__websocket = websocket.WebSocket()

        for attempt in range(COMFY_API_MAX_CONNECT_ATTEMPTS):
            try:
                self.__websocket.connect(
                    f"ws://localhost:{COMFY_PORT}/ws?clientId={self.client_id}"
                )
            except ConnectionRefusedError:
                self.logger.log(
                    f"Comfy server connection attempt {attempt + 1}/{COMFY_API_MAX_CONNECT_ATTEMPTS}: failed",
                    pad_with_rules=False,
                )
                time.sleep(1)
                continue
            self.logger.log(
                f"Comfy server connection attempt {attempt + 1}/{COMFY_API_MAX_CONNECT_ATTEMPTS}:",
                "sucecceeded - connection established",
                pad_with_rules=False,
            )

        if not self.__websocket.connected:
            raise ConnectionError("Failed to connect to Comfy server")

    def disconnect(self):
        """
        Disconnects from the Comfy server by closing the WebSocket connection.

        Returns:
            None
        """
        if self.is_connected():
            self.logger.log("Disconnecting Client from Comfy server")
            self.__websocket.close()
        else:
            self.logger.log("Disconnect Client Attempt: Client is already disconnected")

    def queue_workflow(self):
        """
        Queues a workflow by sending a request to the Comfy API server and waits for it to complete.

        If the client is not connected, it will establish a connection before queuing the workflow.

        Raises:
            Exception: If there is an error with the Comfy API Client process.

        Returns:
            None
        """
        if not self.is_connected():
            self.connect()

        try:
            start_time_epoch = time.time()
            self.logger.log(f"Queueing Workflow at: {time.strftime('%I:%M%p')}")

            self.__send_request()
            self.__listen_until_complete()

            time_diff_formatted = time.strftime(
                "%Mmin, %Ssec", time.gmtime(time.time() - start_time_epoch)
            )
            self.logger.log(
                f"Comfy server finished processing request at: {time.strftime('%I:%M%p')} (Time elapsed - {time_diff_formatted})"
            )

        except Exception as e:
            self.logger.log(f"Error with Comfy API Client process: {e}")
            raise e
        finally:
            self.__websocket.close()

    def __get_request_data(self):
        return json.dumps(
            {"prompt": self.workflow.get_workflow_dict(), "client_id": self.client_id}
        ).encode("utf-8")

    def __send_request(self):
        req = request.Request(
            self.server_url + "/prompt", data=self.__get_request_data()
        )
        resp = json.loads(request.urlopen(req).read())
        self.response_prompt_id = resp["prompt_id"]

    def __handle_response_message(self, message):
        if message["type"] == "status":
            self.logger.log(message["data"]["status"], pad_with_rules=False)
        if message["type"] == "progress":
            self.workflow.print_node_progress(message["data"])
        if message["type"] == "executing":
            cur_node_name = self.workflow.parse_node_name(message["data"])
            self.logger.log(f"Executing Node: {cur_node_name}", pad_with_rules=False)

            if (
                message["data"]["node"] is None
                and message["data"]["prompt_id"] == self.response_prompt_id
            ):
                return True  # Execution is done
        return False  # Previews are binary data

    def __listen_until_complete(self):
        while True:
            out = self.__websocket.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if self.__handle_response_message(message):
                    break
