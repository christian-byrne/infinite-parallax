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
        caller_prefix: str = "WORKFLOW MANAGER",
    ):
        self.project = project
        self.logger = logger
        self.workflow_template_path = workflow_template_path
        self.caller_prefix = caller_prefix

        self.filename = (
            os.path.basename(self.workflow_template_path).replace(".json", "")
            + f"-{self.project.name}.json"
        )
        self.path = os.path.join(self.project.workflow_dir(), self.filename)

        self.__set_workflow()
        self.__set_node_mappings()
        self.save()
        self.log(
            "Created Copy in Project Dir of Workflow Template:",
            self.workflow_template_path,
        )
    
    def log(self, *args, **kwargs):
        self.logger.log(caller_prefix=self.caller_prefix, *args, **kwargs)

    def save(self):
        with open(self.path, "w") as workflow_file:
            json.dump(self.workflow_dict, workflow_file, indent=4)

    def update(
        self, node_name: str, key: str, value: any, save_after=False, append=False
    ) -> None:
        """Update one of the inputs of a node in the workflow dict

        Args:
            node_name (str): The name of the node to update (either its title or class_type)
            key (str): The name of the input field to update
            value (any): The new value to put in the input field
            save_after (bool, optional): Whether to save the workflow to the disk after updating.
                Defaults to False.
            append (bool, optional): Whether to append the new value to the existing value.
        """
        if node_name in self.__node_titles:
            index = self.__node_titles[node_name]
        elif node_name in self.__node_class_types:
            index = self.__node_class_types[node_name]
        else:
            raise ValueError(
                "Project Workflow Error:",
                f"The node {node_name} does not exist in the provided template workflow",
            )

        if "image" in key.lower():
            print(
                "\nKeep in mind that the image inputs are just filenames, not full paths.\nThe path is assumed to be the comfy input image directory\n(which should be manually set to whatever folder you need before passing this workflow to a comfy client)\n"
            )
        if key not in self.workflow_dict[index]["inputs"].keys():
            raise KeyError(
                "Project Workflow Error:",
                f"The key {key} does not exist in the workflow node {node_name}",
            )

        if self.workflow_dict[index]["inputs"][key] == value:
            self.log(
                f"{node_name}'s {key} value is already set to: {value}",
                pad_with_rules=False,
            )
            return

        if append:
            self.log(
                f"{node_name}'s {key} Value Appended with:",
                value,
                pad_with_rules=False,
            )
            # Try to add a space between the old and new value
            try:
                self.workflow_dict[index]["inputs"][key] += " " + value
            except TypeError:
                self.workflow_dict[index]["inputs"][key] += value
        else:
            self.log(
                f"Updating {node_name}'s {key} value:",
                f"from {self.workflow_dict[index]['inputs'][key]} to {value}",
                pad_with_rules=False,
            )
            self.workflow_dict[index]["inputs"][key] = value
        if save_after:
            self.save()

    def get_workflow_dict(self):
        return self.workflow_dict

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

    def __set_workflow(self):
        try:
            with open(self.workflow_template_path, "r") as workflow_file:
                self.workflow_dict = json.load(workflow_file)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The passed workflow template json file could not be found at the given path: {self.workflow_template_path}"
            )

    def __set_node_mappings(self):
        """If speed is more important than memory"""
        self.__node_titles = {}
        self.__node_class_types = {}

        for node_index, node in self.workflow_dict.items():
            if "_meta" in node.keys() and "title" in node["_meta"].keys():
                self.__node_titles[node["_meta"]["title"]] = node_index
            if "class_type" in node.keys():
                self.__node_class_types[node["class_type"]] = node_index
