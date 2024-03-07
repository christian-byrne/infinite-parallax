from moviepy.editor import VideoClip, ImageClip
from moviepy.video.fx import mask_color
from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
from interfaces.logger_interface import LoggerInterface
import os
import numpy as np
import cv2
from PIL import Image
from comfy_api.client import ComfyClient
from comfy_api.server import ComfyServer
from workflow_wrapper.workflow import ComfyAPIWorkflow
from utils.update_path_parts import update_path_parts
from termcolor import colored
from constants import (
    SALIENT_OBJECTS_WORKFLOW_PATH,
    FEATHERING_MARGIN,
    SALIENT_OBJECT_ALPHA_LAYER_PREFIX,
    BASE_LAYER_WITHOUT_OBJECTS_PREFIX,
    DEV,
)


class SalientObjectLayer(LayerInterface):
    def __init__(
        self,
        project: ProjectInterface,
        logger: LoggerInterface,
        prompt_tags: list[str],
        object_index: int,
    ):
        self.project = project
        self.logger = logger
        self.index = object_index
        self.name_prefix = f"salient_object_{self.index + 1}"
        self.prompt_tags = " . ".join(prompt_tags).strip()

        self.workflow = ComfyAPIWorkflow(
            self.project,
            self.logger,
            os.path.join(self.project.repo_root, SALIENT_OBJECTS_WORKFLOW_PATH),
        )
        self.__update_workflow()

        self.alpha_layer_fullpath, self.base_layer_fullpath = self.__get_comfy_outputs()

        # Only generate salient objects layers and new base layer if they don't already exist
        if (
            not self.alpha_layer_fullpath
            or input("\n\nUse existing salient object layers? (y/n):\n> ").lower()
            != "y"
        ):
            # Construct comfy client with the custom workflow
            try:
                server = ComfyServer(
                    self.project,
                    self.logger,
                    output_directory=self.project.project_dir_path,
                    input_directory=self.project.project_dir_path,
                )
                server.start()

                client = ComfyClient(self.project, self.workflow, self.logger)
                client.queue_workflow()
            except Exception as e:
                self.logger.log(f"Error starting comfy server/client: {e}")
                raise e
            finally:
                try:
                    server.kill()
                    client.disconnect()
                except Exception as e:
                    self.logger.log(f"Error stopping comfy server/client: {e}")

            self.alpha_layer_fullpath, self.base_layer_fullpath = (
                self.__get_comfy_outputs()
            )

        self.logger.log(
            f"Salient Object Alpha Layer: {self.alpha_layer_fullpath}",
            pad_with_rules=False,
        )
        self.logger.log(
            f"Base Layer Without Objects: {self.base_layer_fullpath}",
            pad_with_rules=False,
        )
        # Set the inpainted base image (with objects removed) as the new input image
        self.project.update_config(
            "input_image_original_path", self.project.config_file()["input_image_path"]
        )
        self.project.update_config("input_image_path", self.base_layer_fullpath)

        self.__set_original_layer()
        self.__set_layer_breakpoints()
        self.__set_parent_layer()
        self.layer_config = self.project.config_file()["layers"][
            self.parent_layer_index
        ]
        self.logger.log(
            f"Parent layer for salient object {self.index} determined as: layer_{self.parent_layer_index+1}"
        )
        self.logger.log(
            f"Parent layer config: {self.layer_config}", pad_with_rules=False
        )

    def create_cropped_steps(self) -> None:
        sample_layer_dir = os.listdir(self.project.cropped_steps_dir())[0]
        # TODO: determine num_steps at a more global scope in a non error-prone way
        self.total_steps = (
            len(
                os.listdir(
                    os.path.join(self.project.cropped_steps_dir(), sample_layer_dir)
                )
            )
            - 1  # NOTE: -1 because the first image is skipped for now
        )
        self.slide_distance = abs(self.get_x_velocity() * self.total_steps)
        self.duration = int(
            self.total_steps * self.project.config_file()["seconds_per_step"]
        )
        self.output_vid_width = self.original_layer["image"].width

        # Create an empty alpha image with height the same as the base image and width = original + slide distance
        width = (self.total_steps * abs(self.get_x_velocity())) - (
            (self.total_steps + 1) * FEATHERING_MARGIN
        )
        alpha_image = Image.new(
            "RGBA",
            (width, self.original_layer["image"].height),
            (0, 0, 0, 0),
        )
        self.cropped_step_images = [
            {
                "image": alpha_image,
            }
        ]

    def stitch_cropped_steps(self) -> None:
        width = self.get_final_layer_width()
        height = self.get_final_layer_height()

        stitched_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        x_offset = 0
        stitched_image.paste(self.original_layer["image"], (x_offset, 0))
        x_offset += self.original_layer["image"].width - FEATHERING_MARGIN
        stitched_image.paste(self.cropped_step_images[0]["image"], (x_offset, 0))

        output_filename = f"{self.name_prefix}_stitched_alpha_layer.png"
        output_fullpath = os.path.join(
            self.project.stitched_objects_dir(), output_filename
        )
        stitched_image.save(output_fullpath)

        self.stitched = {
            "image": stitched_image,
        }
        update_path_parts(self.stitched, output_fullpath)

        self.logger.log(
            f"Stitched alpha layer saved to: {output_fullpath}",
            pad_with_rules=False,
        )

    def create_layer_videoclip(self) -> VideoClip:
        image_clip = ImageClip(self.stitched["fullpath"])

        # Convert alpha channel to binary mask
        cv2_image = cv2.imread(self.stitched["fullpath"], cv2.IMREAD_UNCHANGED)
        height, width, _ = cv2_image.shape
        alpha_channel = cv2_image[:, :, 3]
        mask = np.zeros((height, width), dtype=np.uint8)
        for i in range(height):
            for j in range(width):
                if alpha_channel[i, j] > 0:
                    mask[i, j] = 1

        def make_mask_frame(t):
            # Calculate the position based on time
            x = int(self.slide_distance * (t / self.duration))
            # Take a cropping of the mask from x to x + self.output_vid_width
            return mask[:, x : x + self.output_vid_width]

        def make_frame(t):
            if DEV and t % 10 == 0 and t != 0:
                print(
                    colored(f"{self.name_prefix} at {t}seconds", "light_green"),
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

        mask_video = VideoClip(make_mask_frame, duration=self.duration, ismask=True)

        ret = VideoClip(make_frame, duration=self.duration)
        ret = ret.set_mask(mask_video)
        return ret

    def get_x_velocity(self):
        # Add logic to clean, adjust, or change type of velocity
        # NOTE: for now, make velocity of salient objects slightly slower to make them stand out
        # return int(self.layer_config["velocity"][0] * 0.6)
        return int(self.layer_config["velocity"][0])

    def get_y_velocity(self):
        # Add logic to clean, adjust, or change type of velocity
        return int(self.layer_config["velocity"][1])

    def get_final_layer_height(self):
        # Add cleaning, adjusting, or type changing logic
        return int(self.original_layer["image"].height)

    def get_final_layer_width(self):
        return self.slide_distance + self.original_layer["image"].width

    def __set_original_layer(self):
        self.original_layer = {
            "image": Image.open(self.alpha_layer_fullpath),
        }
        update_path_parts(self.original_layer, self.alpha_layer_fullpath)

    def __set_layer_breakpoints(self):
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

    def __find_lowest_non_alpha_pixel(self):
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

        return lowest_pixel

    def __set_parent_layer(self):
        """Determine the parent layer for this salient object.
        First, determine the lowest point in the salient object original image which has a non-alpha pixel (i.e., the lowest non-alpha pixel).
        Then, determine which layer contains that point.
        """
        lowest_non_alpha_pixel = self.__find_lowest_non_alpha_pixel()
        self.logger.log(
            f"Lowest non-alpha pixel: {lowest_non_alpha_pixel}", pad_with_rules=False
        )

        # Default is the last layer (lowest) because if the loop doesn't break, then the salient object's lowest non-alpha pixel isnt below any of the layer breakpoints
        self.parent_layer_index = len(self.layer_height_breakpoints) - 1
        for index, breakpoint in enumerate(self.layer_height_breakpoints):
            self.logger.log(
                f"Testing layer {index+1} breakpoint: {breakpoint}",
                pad_with_rules=False,
            )
            if lowest_non_alpha_pixel[1] < breakpoint:
                self.parent_layer_index = index
                self.logger.log(f"Salient object's lowest point is in layer {index+1}")
                break

    def __update_workflow(self):
        # Set the input image for the salient object workflow as the project's input image
        self.workflow.update(
            "LoadImage",
            "image",
            os.path.basename(self.project.config_file()["input_image_path"]),
        )

        self.workflow.update(
            "Save Inpainted Base Layer",
            "filename_prefix",
            BASE_LAYER_WITHOUT_OBJECTS_PREFIX,
        )

        self.workflow.update(
            "Save Alpha Layer",
            "filename_prefix",
            SALIENT_OBJECT_ALPHA_LAYER_PREFIX,
        )

        # Add the salient object tags to the negative prompt for the inpainting (so that when inpainted, the same types of objects are not just recreated in the place they were extracted from)
        self.workflow.update(
            "CLIP Text Encode (Negative Prompt)",
            "text",
            self.prompt_tags.replace(" . ", ", "),
            append=True,
        )
        self.workflow.update(
            "Negative Prompt - Fill Object Region with BG Content Only",
            "text",
            self.prompt_tags.replace(" . ", ", "),
            append=True,
        )

        # Also add to the auto-prompt exclude list so the tagger that generates the prompt doesn't include the salient object tags
        self.workflow.update(
            "Auto Prompt Exclude List",
            "prompt",
            self.prompt_tags.replace(" . ", ", "),
            append=True,
        )

        # Set the salient object tags (descriptors) from the project's config file
        self.workflow.update(
            "Generalized Salient Object Tags (Descriptors)",
            "prompt",
            self.prompt_tags,
        )

        self.workflow.save()

    def __get_comfy_outputs(self):
        try:
            alpha_layer = [
                f
                for f in os.listdir(self.project.project_dir_path)
                if SALIENT_OBJECT_ALPHA_LAYER_PREFIX in f
            ][-1]
            base_layer = [
                f
                for f in os.listdir(self.project.project_dir_path)
                if BASE_LAYER_WITHOUT_OBJECTS_PREFIX in f
            ][-1]
            return (
                os.path.join(self.project.project_dir_path, alpha_layer),
                os.path.join(self.project.project_dir_path, base_layer),
            )
        except IndexError:
            self.logger.log(
                "Salient Object Alpha Layers: Not found",
            )
            return (False, False)
