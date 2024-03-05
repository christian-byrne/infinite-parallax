import os
from PIL import Image
from moviepy.editor import VideoClip, ImageClip
from termcolor import colored

from constants import (
    DEV,
    LAYER_OUTPUT_DIR,
    FEATHERING_MARGIN,
    STITCHED_INPAINT_DIR,
    CROPPED_STEPS_DIR,
    ORIGINAL_LAYERS_DIR,
)


class Layer:
    def __init__(self, project_config, layer_config, name_prefix):
        self.project_config = project_config
        self.layer_config = layer_config
        self.name_prefix = name_prefix
        self.slide_distance = 0
        # NOTE: total steps start at -1 for now because the first image is skipped (saving the first layer slices before any inpainting in the current workflow)
        self.total_steps = -1
        self.set_step_images()
        self.pixel_velocity = layer_config["velocity"]
        self.set_original_layer()

    def set_step_images(self):
        """
        Sets the step images for the layer.

        This method retrieves all step images from the layer's project directory
        and populates the `step_images` list with relevant information about each image.

        Returns:
            None
        """
        self.step_images = []
        all_step_images = os.listdir(
            os.path.join(self.project_config["project_dir_path"], LAYER_OUTPUT_DIR)
        )

        temp = []
        for step_image in all_step_images:
            if step_image.startswith(self.name_prefix):
                temp.append(step_image)
                self.total_steps += 1
        temp.sort()
        for step_image in temp:
            # Append full path
            step_image = {
                # no prefix
                "filename": step_image,
                "basename": ".".join(step_image.split(".")[:-1]),
                "ext": step_image.split(".")[-1],
                "path": os.path.join(
                    self.project_config["project_dir_path"], LAYER_OUTPUT_DIR
                ),
                "fullpath": os.path.join(
                    self.project_config["project_dir_path"],
                    LAYER_OUTPUT_DIR,
                    step_image,
                ),
            }
            self.step_images.append(step_image)

    def create_cropped_steps(self):
        """
        For each step image, crop the image to only include the inpainted region.
        If the layer velocity is -13, we should extract the 13xheight picture starting from the right.
        If the layer velocity is 240, we should extract the 240xheight starting from the left.
        """

        self.cropped_step_images = []

        for step_image in self.step_images:
            cropped_step_image = {}
            image = Image.open(step_image["fullpath"])
            width = abs(self.pixel_velocity[0])
            if self.pixel_velocity[0] < 0:
                x = image.width - width
            else:
                x = 0
            # TODO: y-axis velocity implementation
            y = 0
            height = image.height

            cropped_image = image.crop((x, y, x + width, y + height))
            # save with cropped prefix
            filename = f"cropped-{step_image['filename']}"
            output_dir = os.path.join(
                self.project_config["project_dir_path"], CROPPED_STEPS_DIR
            )
            # If the directory doesn't exist, create it
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            fullpath = os.path.join(output_dir, filename)
            cropped_image.save(fullpath)

            cropped_step_image["filename"] = filename
            cropped_step_image["basename"] = ".".join(filename.split(".")[:-1])
            cropped_step_image["ext"] = filename.split(".")[-1]
            cropped_step_image["path"] = output_dir
            cropped_step_image["fullpath"] = fullpath

            self.cropped_step_images.append(cropped_step_image)

    def stitch_cropped_steps(self):
        """Stitch the cropped step images together to create the final layer output.
        
        The order of the images should be from the first step to the last step.
        The output image should be saved in the project directory with the name {layer_prefix}_stitched_inpainted_regions.png.
        
        Args:
            None
        
        Returns:
            None
        """
        # Create a list to store the cropped images
        cropped_images = []

        # Load the cropped step images
        for cropped_step_image in self.cropped_step_images:
            # NOTE: Ignore the first image
            # TODO: this is a temporary fix for the problem of the comfyUI workflow saving the layers of the original input image as well
            if cropped_step_image == self.cropped_step_images[0]:
                continue
            image = Image.open(cropped_step_image["fullpath"])
            cropped_images.append(image)

        # Determine the width and height of the final stitched image
        width = (
            sum([image.width for image in cropped_images])
            - ((len(cropped_images) - 1) * FEATHERING_MARGIN)
            + self.original_layer["image"].width
            - FEATHERING_MARGIN
        )
        height = int(self.layer_config["height"])

        # Create a new image with the calculated width and height
        stitched_image = Image.new("RGB", (width, height))

        # Paste the cropped images onto the stitched image
        x_offset = 0
        stitched_image.paste(self.original_layer["image"], (x_offset, 0))
        x_offset += self.original_layer["image"].width
        x_offset -= FEATHERING_MARGIN
        for image in cropped_images:
            stitched_image.paste(image, (x_offset, 0))
            x_offset += image.width
            x_offset -= FEATHERING_MARGIN
            self.slide_distance += image.width - FEATHERING_MARGIN

        # Save the stitched image
        output_filename = f"{self.name_prefix}_stitched_inpainted_regions.png"
        output_dir_path = os.path.join(
            self.project_config["project_dir_path"], STITCHED_INPAINT_DIR
        )

        # If the directory doesn't exist, create it
        if not os.path.exists(output_dir_path):
            os.makedirs(output_dir_path)
        output_path = os.path.join(
            output_dir_path,
            output_filename,
        )

        stitched_image.save(output_path)

        self.stitched_inpainted_regions = {
            "image": stitched_image,
            "filename": output_filename,
            "basename": ".".join(output_filename.split(".")[:-1]),
            "ext": output_filename.split(".")[-1],
            "path": os.path.join(
                self.project_config["project_dir_path"], STITCHED_INPAINT_DIR
            ),
            "fullpath": output_path,
        }

    def set_original_layer(self):
        """
        Sets the original layer for the current layer.

        This method searches for the original layer file in the specified directory
        and assigns the necessary information to the `original_layer` attribute.

        Args:
            None

        Returns:
            None
        """
        original_layers_dir = os.path.join(
            self.project_config["project_dir_path"], ORIGINAL_LAYERS_DIR
        )
        for original_layer in os.listdir(original_layers_dir):
            if original_layer.startswith(self.name_prefix):
                self.original_layer = {
                    "image": Image.open(
                        os.path.join(original_layers_dir, original_layer)
                    ),
                    "filename": original_layer,
                    "basename": ".".join(original_layer.split(".")[:-1]),
                    "ext": original_layer.split(".")[-1],
                    "path": original_layers_dir,
                    "fullpath": os.path.join(original_layers_dir, original_layer),
                }

                break

    def create_layer_videoclip(self):
        """
        Creates a video clip from the stitched image, panning from left to right.

        The duration is uniform for all layers and is calculated as the total number of steps
        multiplied by the number of seconds per step.

        Returns:
            VideoClip: The created video clip.
        """
        duration = int(self.total_steps * self.project_config["seconds_per_step"])
        output_vid_width = self.original_layer["image"].width
        # total_width = self.stitched_inpainted_regions["image"].width

        image_clip = ImageClip(self.stitched_inpainted_regions["fullpath"])

        def make_frame(t):
            if DEV and t % 5 == 0 and t != 0:
                print(colored(f"t: {t}seconds", "light_green"))
                print(
                    colored(f"progress (t / duration): {t / duration}", "light_green")
                )
                print(
                    colored(
                        f"current x-coordinate (self.slide_distance * (t / duration): {int(self.slide_distance * (t / duration))}",
                        "light_blue",
                    )
                )
                
            x = int(self.slide_distance * (t / duration))
            return image_clip.get_frame(t)[:, x : x + output_vid_width]

        return VideoClip(make_frame, duration=duration)
