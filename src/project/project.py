import os
import json
from constants import (
    DEV,
    PROJECT_DATA_REL_PATH,
    CONFIG_FILENAME,
    ORIGINAL_LAYERS_DIR,
    OUTPUTS_USER_REL_PATH,
    LAYER_OUTPUT_DIR,
    SALIENT_OBJECTS_DIR,
    WORKFLOW_DIR,
    CROPPED_STEPS_DIR,
    STITCHED_INPAINT_DIR,
)
from .create_config import create_config
from utils.check_make_dir import check_make_dir
from interfaces.project_interface import ProjectInterface
from parallax_video.video import ParallaxVideo
from PIL import Image


class ParallaxProject(ProjectInterface):
    """
    Represents a parallax project.

    This class handles the creation of a parallax project, including initializing the project with the given name,
    setting up the project directory, loading the project configuration, creating and saving original layer slices,
    creating layer video clips, and generating the final parallax video.

    Attributes:
        name (str): The name of the project.
        version (str): The version of the project.
        author (str): The author of the project.
        repo_root (str): The root directory of the project repository.
        project_dir_path (str): The path to the project directory.
        config_path (str): The path to the project configuration file.
        input_image (PIL.Image.Image): The input image for the project.
        layers (list): A list of Layer instances representing the layers in the project.
        layer_clips (list): A list of VideoClip instances representing the layer video clips.
    """

    def __init__(self, project_name, author=None, version="0.1.0"):
        self.name = project_name
        self.version = version
        if not author:
            try:
                self.author = os.getenv("USER")
            except Exception as e:
                print(f"Couldn't get author name: {e}")
                self.author = "Unknown"
        else:
            self.author = author

        self.init_project_structure()
        self.copy_input_image_to_project_dir()
        self.input_image = Image.open(self.config_file()["input_image_path"])
        self.create_original_layer_slices()

        ParallaxVideo(self)

    def init_project_structure(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Repo root: {self.repo_root}")

        self.project_dir_path = os.path.join(
            self.repo_root, PROJECT_DATA_REL_PATH, self.name
        )
        print(f"Project dir path: {self.project_dir_path}")

        if not check_make_dir(self.project_dir_path):
            print(f"Project directory created at {self.project_dir_path}")
            self.NEW_PROJECT = True
        else:
            self.NEW_PROJECT = False
        print(f"This is a new project: {self.NEW_PROJECT}")

        self.config_file()

        # Create folders for standard project structure
        self.layer_outputs_dir()
        self.salient_objects_dir()
        self.workflow_dir()  # TODO - copy copy of template workflow named to match project name

    def update_config(self, key, value):
        config = self.config_file()
        config[key] = value
        with open(self.config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

    def config_file(self):
        path = os.path.join(self.project_dir_path, CONFIG_FILENAME)
        self.config_path = path
        if not os.path.exists(path):
            self.set_config()

        with open(path, "r") as config_file:
            return json.load(config_file)

    def workflow_dir(self):
        path = os.path.join(self.project_dir_path, WORKFLOW_DIR)
        check_make_dir(path)
        # Add workflow logic
        return path

    def layer_outputs_dir(self):
        path = os.path.join(self.project_dir_path, LAYER_OUTPUT_DIR)
        check_make_dir(path)
        # Add layer outputs logic
        return path

    def salient_objects_dir(self):
        path = os.path.join(self.project_dir_path, SALIENT_OBJECTS_DIR)
        check_make_dir(path)
        # Add salient objects logic
        return path

    def original_layers_dir(self):
        path = os.path.join(self.project_dir_path, ORIGINAL_LAYERS_DIR)
        check_make_dir(path)
        # Add original layers logic
        return path

    def cropped_steps_dir(self):
        path = os.path.join(self.project_dir_path, CROPPED_STEPS_DIR)
        check_make_dir(path)
        # Add cropped steps logic
        return path

    def stitched_inpainted_dir(self):
        path = os.path.join(self.project_dir_path, STITCHED_INPAINT_DIR)
        check_make_dir(path)
        # Add stitched inpainted logic
        return path

    def output_video_dir(self):
        path = os.path.join(self.project_dir_path, OUTPUTS_USER_REL_PATH)
        check_make_dir(path)
        # Add output video logic
        return path

    def create_original_layer_slices(self):
        """
        Creates and saves individual slices of the original layers from the input image.

        This method iterates over the layers specified in the project configuration and crops
        the input image to create individual slices for each layer. The slices are then saved
        as separate image files in the original layers directory.

        Returns:
            None
        """
        x = 0
        y = 0
        # TODO: Full vector range logic
        width = self.input_image.width
        for index, layer in enumerate(self.config_file()["layers"]):
            height = layer["height"]
            input_layer_image = self.input_image.crop((x, y, x + width, y + height))
            input_layer_image.save(
                os.path.join(
                    self.original_layers_dir(), f"original_layer_{index+1}.png"
                )
            )
            y += height

    def set_config(self):
        config = create_config()
        config["project_dir_path"] = self.project_dir_path
        config["config_path"] = self.config_path
        config["project_name"] = self.name

        with open(self.config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

    def copy_input_image_to_project_dir(self):
        config = self.config_file()
        input_image_path = config["original_input_image_path"]
        input_image_filename = os.path.basename(input_image_path)
        input_image_dest_path = os.path.join(
            self.project_dir_path, input_image_filename
        )
        os.system(f"cp {input_image_path} {input_image_dest_path}")
        self.update_config("input_image_path", input_image_dest_path)

    def print_info(self):
        print(f"\n\n{self.name} v{self.version} by {self.author}\n")
