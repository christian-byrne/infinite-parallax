from interfaces.project_interface import ProjectInterface
from interfaces.logger_interface import LoggerInterface
import json
import os


class ComfyAPIWorkflow:
    def __init__(
        self,
        project: ProjectInterface,
        logger: LoggerInterface,
        workflow_template_path: str,
    ):
        self.project = project
        self.logger = logger
        self.workflow_template_path = workflow_template_path
        self.set_workflow()

    def save(self):
        filename = f"{os.path.basename(self.workflow_template_path).replace('.json', '')}-{self.project.name}.json"
        save_path = os.path.join(self.project.workflow_dir(), filename)
        with open(save_path, "w") as workflow_file:
            json.dump(self.workflow_dict, workflow_file, indent=4)

    def update(self, node_name, key, value):
        for node in self.workflow_dict:
            if (
                self.workflow_dict[node]["_meta"]["title"] == node_name
                or self.workflow_dict[node]["class_type"] == node_name
            ):
                self.workflow_dict[node][key] = value
                break

    def get_workflow_dict(self):
        return self.workflow_dict

    def set_workflow(self):
        try:
            with open(self.workflow_template_path, "r") as workflow_file:
                self.workflow_dict = json.load(workflow_file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The passed workflow template json file could not be found at the given path: {self.workflow_template_path}"
            )

    def parse_node_name(self, data):
        """Accepts the data dict from a response from the comfy server and returns the name of the node that the data is about. Allows errors, in which case returns "Unknown" """
        node_index = str(data["node"])
        try:
            node_name = self.workflow_dict[node_index]["_meta"]["title"]
        except KeyError:
            try:
                node_name = self.workflow_dict[node_index]["class_type"]
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
