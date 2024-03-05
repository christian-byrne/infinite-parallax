import os
import json
from constants import (
    DEV,
    PROJECT_DATA_REL_PATH,
    CONFIG_FILENAME,
    ORIGINAL_LAYERS_DIR,
    VIDEO_CODEC,
    OUTPUT_VIDEO_PATH,
)
from .create_config import create_config
from layers.layer import Layer
from PIL import Image
from moviepy.editor import CompositeVideoClip
from termcolor import colored


class ParallaxProject:
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
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_dir_path = os.path.join(
            self.repo_root, PROJECT_DATA_REL_PATH, self.name
        )
        if not self.project_dir_exists():
            os.makedirs(self.project_dir_path)
        self.config_path = os.path.join(self.project_dir_path, CONFIG_FILENAME)
        if not self.project_config_exists():
            self.set_config()

        self.copy_input_image_to_project_dir()
        self.input_image = Image.open(self.get_config()["input_image_path"])

        self.layers = []
        for index, layer in enumerate(self.get_config()["layers"]):
            name_prefix = f"layer_{index+1}"
            self.layers.append(Layer(self.get_config(), layer, name_prefix))

        self.create_original_layer_slices()

        for layer in self.layers:
            layer.create_cropped_steps()
            layer.stitch_cropped_steps()

        self.layer_clips = []
        x = 0
        y = 0
        for layer, layer_config in zip(self.layers, self.get_config()["layers"]):
            layer_videoclip = layer.create_layer_videoclip()
            layer_videoclip = layer_videoclip.set_position((x, y))
            self.layer_clips.append(layer_videoclip)
            y += layer_config["height"]

        self.video_from_layer_frames()

    def video_from_layer_frames(self):
        """
        Create a final video from the frames.

        self.frames is a list of lists of VideoClip instances. Each list of VideoClip instances represents a layer.
        The layers should be stacked vertically.

        This function creates a final video by compositing the layer clips and saving it to the specified output path.
        """

        video_composite = CompositeVideoClip(
            self.layer_clips, size=self.input_image.size
        )

        output_dir = os.path.join(self.project_dir_path, OUTPUT_VIDEO_PATH)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, f"{self.name}-final_parallax_video.mp4")

        video_composite.write_videofile(
            output_path,
            codec=VIDEO_CODEC,
            fps=self.get_config()["fps"],
        )

        print(f"\n\nFinal video saved to {output_path}\n")

    def create_original_layer_slices(self):
        """
        Creates and saves individual slices of the original layers from the input image.

        This method iterates over the layers specified in the project configuration and crops
        the input image to create individual slices for each layer. The slices are then saved
        as separate image files in the original layers directory.

        Returns:
            None
        """
        # Make dir if it doesn't exist
        if not os.path.exists(os.path.join(self.project_dir_path, ORIGINAL_LAYERS_DIR)):
            os.makedirs(os.path.join(self.project_dir_path, ORIGINAL_LAYERS_DIR))
        x = 0
        y = 0
        width = self.input_image.width
        for index, layer in enumerate(self.get_config()["layers"]):
            height = layer["height"]
            input_layer_image = self.input_image.crop((x, y, x + width, y + height))
            input_layer_image.save(
                os.path.join(
                    self.project_dir_path,
                    ORIGINAL_LAYERS_DIR,
                    f"layer_{index+1}-original_layer_slice.png",
                )
            )
            y += height

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
        print(f"\n\n{self.name} v{self.version} by {self.author}\n")
