import os
import json
from constants import PROJECT_DATA_REL_PATH, CONFIG_FILENAME, LAYER_OUTPUT_DIR
from .create_config import create_config
from layers.layer import Layer


class ParallaxProject:
    def __init__(self, project_name):
        self.name = project_name
        self.version = "0.1.0"
        self.author = "Your Name"
        self.project_dir_path = os.path.join(PROJECT_DATA_REL_PATH, self.name)
        self.config_path = os.path.join(self.project_dir_path, CONFIG_FILENAME)
        if not self.project_dir_exists():
            os.makedirs(self.project_dir_path)
        if not self.project_config_exists():
            self.set_config()
        self.copy_input_image_to_project_dir()

        self.layers = []

        for index, layer in enumerate(self.get_config()["layers"]):
            name_prefix = f"layer_{index+1}"
            self.layers.append(Layer(self.get_config(), layer, name_prefix))

    def project_dir_exists(self):
        return os.path.exists(self.project_dir_path)

    def project_config_exists(self):
        return os.path.exists(self.config_path)

    def set_config(self):
        config = create_config()
        config["project_dir_path"] = self.project_dir_path
        config["config_path"] = self.config_path
        config["project_name"] = self.name

        with open(self.config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

    def get_config(self):
        with open(self.config_path, "r") as config_file:
            return json.load(config_file)

    def copy_input_image_to_project_dir(self):
        config = self.get_config()
        input_image_path = config["original_input_image_path"]
        input_image_filename = os.path.basename(input_image_path)
        input_image_dest_path = os.path.join(
            self.project_dir_path, input_image_filename
        )
        os.system(f"cp {input_image_path} {input_image_dest_path}")
        config["input_image_path"] = input_image_dest_path

    def print_info(self):
        print(f"{self.name} v{self.version} by {self.author}")
