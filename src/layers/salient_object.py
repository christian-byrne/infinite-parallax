from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
import os
from PIL import Image
from utils.check_make_dir import check_make_dir
from utils.update_path_parts import update_path_parts
from log.logging import Logger
from termcolor import colored

from constants import DEV, FEATHERING_MARGIN


class SalientObjectLayer(LayerInterface):
    def __init__(
        self, project: ProjectInterface, alpha_layer_fullpath, object_index: int
    ):
        self.project = project
        self.index = object_index
        self.alpha_layer_fullpath = alpha_layer_fullpath
        self.logger = Logger(
            self.project.name, self.project.author, self.project.version
        )
        
        self.set_original_layer()

        self.set_layer_breakpoints()
        self.set_parent_layer()
        self.layer_config = self.project.config_file()["layers"][self.parent_layer_index]
        self.logger.log(f"Parent layer for salient object {self.index} determined as: layer_{self.parent_layer_index+1}")
        self.logger.log(f"Parent layer config: {self.layer_config}")
        self.name_prefix = f"salient_object_{self.index}"
        exit()

        self.slide_distance = 0
        # NOTE: total steps start at -1 for now because the first image is skipped (saving the first layer slices before any inpainting in the current workflow)
        self.total_steps = -1
        self.set_step_images()
        self.set_original_layer()

        self.duration = int(self.total_steps * self.project_config["seconds_per_step"])
        self.output_vid_width = self.original_layer["image"].width

    def set_original_layer(self):
        self.original_layer = {
            "image": Image.open(self.alpha_layer_fullpath),
        }
        update_path_parts(self.original_layer, self.alpha_layer_fullpath)

    def set_layer_breakpoints(self):
        self.layer_height_breakpoints = [0]
        layer_configs = self.project.config_file()["layers"]
        if len(layer_configs) == 1:
            self.logger.log(
                "Setting layer breakpoints:",
                "Only one layer in the project.",
                "Salient object is in the only layer.",
            )
            return

        for layer in layer_configs[:-1]:
            self.layer_height_breakpoints.append(self.layer_height_breakpoints[-1] + layer["height"])

    def find_lowest_non_alpha_pixel(self):
        width, height = self.original_layer["image"].size
        lowest_pixel = None

        last_layer_breakpoint = self.layer_height_breakpoints[-1]

        for y in range(height - 1, -1, -1):
            for x in range(width):
                pixel = self.original_layer["image"].getpixel((x, y))
                if pixel[3] != 0:
                    lowest_pixel = (x, y)
                    # If the any non-alpha pixel is in the lowest layer, then we can stop searching
                    if y >= last_layer_breakpoint:
                        return lowest_pixel
                    break
            if lowest_pixel:
                break

    def set_parent_layer(self):
        """Determine the parent layer for this salient object.
        First, determine the lowest point in the salient object original image which has a non-alpha pixel (i.e., the lowest non-alpha pixel).
        Then, determine which layer contains that point.
        """
        lowest_non_alpha_pixel = self.find_lowest_non_alpha_pixel()
        self.logger.log(f"Lowest non-alpha pixel: {lowest_non_alpha_pixel}")

        # Default is the last layer (lowest) because if the loop doesn't break, then the salient object's lowest non-alpha pixel isnt below any of the layer breakpoints
        self.parent_layer_index = len(self.layer_height_breakpoints) - 1
        for index, breakpoint in enumerate(self.layer_height_breakpoints):
            self.logger.log(f"Testing layer {index+1} breakpoint: {breakpoint}")
            if lowest_non_alpha_pixel[1] < breakpoint:
                self.parent_layer_index = index
                self.logger.log(f"Salient object's lowest point is in layer {index+1}")
                break

    def get_x_velocity(self):
        # Add logic to clean, adjust, or change type of velocity
        return int(self.layer_config["velocity"][0])

    def get_y_velocity(self):
        # Add logic to clean, adjust, or change type of velocity
        return int(self.layer_config["velocity"][1])

    def get_final_layer_height(self):
        # Add cleaning, adjusting, or type changing logic
        return int(self.layer_config["height"])

    def get_final_layer_width(self):
        width = 0
        # Add the width of all cropped inpainted regions minus the feathering margin
        for image in self.cropped_step_images:
            width += image["image"].width
            width -= FEATHERING_MARGIN

        # Add the length of the original layer onto which the inpainted regions are stitched
        width += self.original_layer["image"].width - FEATHERING_MARGIN

        # Subtract 1 feathering margin because the last image doesn't have a feathering margin
        width -= FEATHERING_MARGIN

        return width
