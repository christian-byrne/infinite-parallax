import os
from PIL import Image
from moviepy.editor import VideoClip, ImageClip
from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
from utils.update_path_parts import update_path_parts
from utils.check_make_dir import check_make_dir
from termcolor import colored

from constants import (
    DEV,
    FEATHERING_MARGIN,
)


class BaseLayer(LayerInterface):
    def __init__(
        self, project: ProjectInterface, layer_config, name_prefix, layer_index
    ):
        self.project = project
        self.layer_config = layer_config
        self.name_prefix = name_prefix
        self.index = layer_index
        self.slide_distance = 0
        # NOTE: total steps start at -1 for now because the first image is skipped (saving the first layer slices before any inpainting in the current workflow)
        self.total_steps = -1
        self.set_original_layer()
        self.set_step_images()

        self.duration = int(
            self.total_steps * self.project.config_file()["seconds_per_step"]
        )
        self.output_vid_width = self.original_layer["image"].width

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

    def set_original_layer(self):
        if DEV:
            print(colored(f"Setting original layer for {self.name_prefix}", "yellow"))
            print(f"Original layers dir: {self.project.original_layers_dir()}")

        for original_layer in os.listdir(self.project.original_layers_dir()):
            # E.g., if the layer is layer_1, the original layer should be 1_original_layer.png
            if original_layer.startswith(str(self.index)):
                fullpath = os.path.join(
                    self.project.original_layers_dir(), original_layer
                )
                self.original_layer = {
                    "image": Image.open(fullpath),
                }
                update_path_parts(self.original_layer, fullpath)
                break

    def set_step_images(self):
        self.step_images = []
        all_step_images = os.listdir(self.project.layer_outputs_dir())

        temp = []
        for step_image in all_step_images:
            if step_image.startswith(self.name_prefix):
                temp.append(step_image)
                self.total_steps += 1
        temp.sort()

        for step_image in temp:
            # Append full path
            step_image_dict = {}
            update_path_parts(
                step_image_dict,
                os.path.join(self.project.layer_outputs_dir(), step_image),
            )
            self.step_images.append(step_image_dict)

    def create_cropped_steps(self):
        self.cropped_step_images = []

        for step_image in self.step_images:
            # Skip first image (the unaltered region of the original input layer)
            # NOTE: Ignore the first image
            # TODO: this is a temporary fix for the problem of the comfyUI workflow saving the layers of the original input image as well
            if step_image == self.step_images[0]:
                continue

            cropped_step_image = {}
            image = Image.open(step_image["fullpath"])
            # TODO: full vector range implementation
            width = abs(self.get_x_velocity())
            if self.get_x_velocity() < 0:
                x = image.width - width
            else:
                x = 0
            # TODO: y-axis velocity implementation
            y = 0
            height = image.height

            cropped_image = image.crop((x, y, x + width, y + height))
            cropped_step_image["image"] = cropped_image
            # save with cropped prefix
            filename = f"cropped-{step_image['filename']}"
            output_dir = os.path.join(
                self.project.cropped_steps_dir(), f"{self.name_prefix}_cropped_steps"
            )
            # If the directory doesn't exist, create it
            check_make_dir(output_dir)
            fullpath = os.path.join(output_dir, filename)
            cropped_image.save(fullpath)
            update_path_parts(cropped_step_image, fullpath)
            self.cropped_step_images.append(cropped_step_image)

    def stitch_cropped_steps(self):
        # Determine the width and height of the final stitched image
        width = self.get_final_layer_width()
        height = self.get_final_layer_height()

        # Create a new image with the calculated width and height
        # to serve as the canvas for the stitched image
        stitched_image = Image.new("RGB", (width, height))

        # Paste the cropped images onto the stitched image
        x_offset = 0
        stitched_image.paste(self.original_layer["image"], (x_offset, 0))
        x_offset += self.original_layer["image"].width
        x_offset -= FEATHERING_MARGIN

        for image_dict in self.cropped_step_images:
            image = image_dict["image"]

            stitched_image.paste(image, (x_offset, 0))
            x_offset += image.width
            x_offset -= FEATHERING_MARGIN
            self.slide_distance += image.width - FEATHERING_MARGIN

        # Save the stitched image
        output_filename = f"{self.name_prefix}_stitched_inpainted_regions.png"
        output_fullpath = os.path.join(
            self.project.stitched_inpainted_dir(), output_filename
        )
        stitched_image.save(output_fullpath)

        self.stitched_inpainted_regions = {
            "image": stitched_image,
        }
        update_path_parts(self.stitched_inpainted_regions, output_fullpath)

    def create_layer_videoclip(self):
        image_clip = ImageClip(self.stitched_inpainted_regions["fullpath"])

        def make_frame(t):
            # Print progress and x-coordinate of the layer every 10 seconds if devmode
            if DEV and t % 10 == 0 and t != 0:
                print(
                    colored(f"Layer_{self.name_prefix} at {t}seconds", "light_green"),
                    colored("progress (t / duration): ", "green"),
                    f"{t / self.duration}",
                )
                print(
                    colored(
                        f"Layer_{self.name_prefix} current x-coordinate (self.slide_distance * (t / duration): ",
                        "light_blue",
                    ),
                    f"{int(self.slide_distance * (t / self.duration))}",
                )

            x = int(self.slide_distance * (t / self.duration))
            return image_clip.get_frame(t)[:, x : x + self.output_vid_width]

        return VideoClip(make_frame, duration=self.duration)
