from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
from interfaces.logger_interface import LoggerInterface
import os
import json
import shutil
from PIL import Image
from comfy_api.client import ComfyClient
from utils.check_make_dir import check_make_dir
from utils.update_path_parts import update_path_parts
from log.logging import Logger
from termcolor import colored

from constants import (
    SALIENT_OBJECTS_WORKFLOW_PATH,
    FEATHERING_MARGIN,
    COMFY_PATH,
    SALIENT_OBJECT_ALPHA_LAYER_PREFIX,
    BASE_LAYER_WITHOUT_OBJECTS_PREFIX,
)


class SalientObjectLayer(LayerInterface):
    def __init__(self, project: ProjectInterface, logger: LoggerInterface, object_index: int):
        self.project = project
        self.index = object_index
        self.logger = logger

        self.template_workflow_path = os.path.join(
            self.project.repo_root, SALIENT_OBJECTS_WORKFLOW_PATH
        )
        self.logger.log(f"Template Workflow path: {self.template_workflow_path}")

        # load json data from workflow
        with open(self.template_workflow_path, "r") as f:
            self.workflow = json.load(f)

        # Copy project's input image to comfy input folder if it's not already there
        comfy_input_folder = os.path.join(COMFY_PATH, "input")
        pic_name = os.path.basename(self.project.config_file()["input_image_path"])
        comfy_input_path = os.path.join(comfy_input_folder, pic_name)
        if not os.path.exists(comfy_input_path):
            self.logger.log(
                f"Copying project's input image to comfy input folder: {comfy_input_folder}"
            )
            shutil.copy(
                self.project.config_file()["input_image_path"], comfy_input_folder
            )
        else:
            self.logger.log(
                f"Project's input image already exists in comfy input folder: {comfy_input_folder}"
            )

        # Find {class_type : LoadImage} node in workflow and replace inputs.image with pic_name
        load_image_index = None
        for node_index, node in self.workflow.items():
            if node["class_type"] == "LoadImage":
                load_image_index = node_index
                break
        if load_image_index:
            self.workflow[load_image_index]["inputs"]["image"] = pic_name
        else:
            raise ValueError("LoadImage node not found in salient object workflow")

        # Change other aspects of the workflow here

        # Save the modified workflow to this project's individual workflow dir (same name but prefixed with the project name)
        path = os.path.join(
            self.project.workflow_dir(),
            f"{self.project.name}_salient_object_workflow.json",
        )
        with open(path, "w") as f:
            json.dump(self.workflow, f, indent=4)
        self.workflow_path = path
        self.logger.log(
            f"Custom Salient object workflow path for this project: {self.workflow_path}"
        )

        # Construct comfy client with the custom workflow
        self.comfy = ComfyClient(self.project, self.workflow_path)
        self.comfy.queue_workflow()

        # Identify the most recent file in the comfy output folder that has the alpha layer prefix in its basename
        comfy_output_folder = os.path.join(COMFY_PATH, "output")
        alpha_layer_files = [
            file
            for file in os.listdir(comfy_output_folder)
            if SALIENT_OBJECT_ALPHA_LAYER_PREFIX in file
        ]
        alpha_layer_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(comfy_output_folder, x))
        )
        self.alpha_layer_fullpath = os.path.join(
            comfy_output_folder, alpha_layer_files[-1]
        )
        self.logger.log(
            f"Most recent alpha layer file in comfy output folder: {self.alpha_layer_fullpath}"
        )
        shutil.copy(self.alpha_layer_fullpath, self.project.salient_objects_dir())

        # TODO: the inpainted base layer (with the salient object removed) serves as the new base image for the slicing, inpainting, etc.

        # Identify the most recent file in the comfy output folder that has the base layer without objects prefix in its basename
        base_layer_files = [
            file
            for file in os.listdir(comfy_output_folder)
            if BASE_LAYER_WITHOUT_OBJECTS_PREFIX in file
        ]
        base_layer_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(comfy_output_folder, x))
        )
        self.base_layer_fullpath = os.path.join(
            comfy_output_folder, base_layer_files[-1]
        )
        self.logger.log(
            f"Most recent base layer file in comfy output folder: {self.base_layer_fullpath}"
        )

        # Copy the base layer to the project dir named "input-base_layer_no_objects"
        base_layer_dest_path = self.project.config_file()["project_dir_path"]
        base_layer_dest_path = os.path.join(
            base_layer_dest_path, "input-base_layer_no_objects.png"
        )
        shutil.copy(self.base_layer_fullpath, base_layer_dest_path)
        # Update the project's config file with the new base layer path
        # TODO: create new property specifying the path to the old input image prior to separation with salient object(s)
        self.project.update_config("input_image_path", base_layer_dest_path)

        self.set_original_layer()
        self.set_layer_breakpoints()
        self.set_parent_layer()
        self.layer_config = self.project.config_file()["layers"][
            self.parent_layer_index
        ]
        self.logger.log(
            f"Parent layer for salient object {self.index} determined as: layer_{self.parent_layer_index+1}"
        )
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
            self.layer_height_breakpoints.append(
                self.layer_height_breakpoints[-1] + layer["height"]
            )

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
