import os
from PIL import Image
from moviepy.editor import CompositeVideoClip, VideoClip
from layers.base import BaseLayer
from layers.salient_object import SalientObjectLayer
from inpaint.inpaint_loop import InpaintLooper
from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
from interfaces.logger_interface import LoggerInterface
from termcolor import colored
from constants import (
    VIDEO_CODEC,
    DEV,
)


class ParallaxVideo:
    def __init__(
        self,
        project: ProjectInterface,
        logger: LoggerInterface,
        caller_prefix="VIDEO EDITOR",
    ):
        self.project = project
        self.logger = logger
        self.caller_prefix = caller_prefix

        inpainter = InpaintLooper(project, logger)

        inpainter.iterative_inpaint(4)

        exit()


        self.object_layers = self.__create_object_layers()

        self.create_original_layer_slices()

        if not self.__user_confirm():
            return

        self.log("Creating: Base layers")
        self.base_layers = self.__create_base_layers()
        for layer in self.base_layers:
            self.log(f"Stitching: Layer {layer.index}")
            layer.create_cropped_steps()
            layer.stitch_cropped_steps()
        for obj_layer in self.object_layers:
            self.log(f"Extending: Oject layer {obj_layer.index+1}")
            obj_layer.create_cropped_steps()
            obj_layer.stitch_cropped_steps()

        self.log("Generating videoclips", pad_with_rules=True)
        self.log("Generating videoclips for each base layer")
        self.layer_videoclips = self.create_layer_videoclips()
        self.log("Generating videoclips and mask videoclips for each object layer")
        self.object_layer_videoclips = self.create_object_layer_videoclips()
        self.log("Compositing layer videoclips\n")
        self.composite_layer_videoclips()

    def log(self, *args, **kwargs):
        self.logger.log(caller_prefix=self.caller_prefix, *args, **kwargs)

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
        input_image = Image.open(self.project.config_file()["input_image_path"])
        width = input_image.width

        for index, layer in enumerate(self.project.config_file()["layers"]):
            height = layer["height"]
            input_layer_image = input_image.crop((x, y, x + width, y + height))
            input_layer_image.save(
                os.path.join(
                    self.project.original_layers_dir(), f"{index+1}_original_layer.png"
                )
            )
            y += height

    def create_layer_videoclips(self) -> list[VideoClip]:

        layer_clips = []
        x = 0
        y = 0
        for layer, layer_config in zip(
            self.base_layers, self.project.config_file()["layers"]
        ):
            layer_videoclip = layer.create_layer_videoclip()
            layer_videoclip = layer_videoclip.set_position((x, y))
            layer_clips.append(layer_videoclip)
            y += layer_config["height"]

        return layer_clips

    def create_object_layer_videoclips(self) -> list[VideoClip]:
        layer_clips = []
        for layer in self.object_layers:
            layer_videoclip = layer.create_layer_videoclip()
            layer_videoclip = layer_videoclip.set_position((0, 0))
            layer_clips.append(layer_videoclip)

        return layer_clips

    def composite_layer_videoclips(self):
        """
        Create a final video from the frames.

        self.layer_clips is a list of lists of VideoClip instances.
        Each list of VideoClip instances represents a layer.
        The layers should be stacked according to the vector of motion.

        The object layers are composited on top of the base layers, because
        they have an alpha channel and should be visible on top of the base layers.

        This function creates a final video by compositing the layer clips and saving it to the specified output path.
        """

        video_composite = CompositeVideoClip(
            self.layer_videoclips + self.object_layer_videoclips,
            size=self.__get_video_size(),
        )

        output_path = os.path.join(
            self.project.output_video_dir(),
            f"{self.project.name}-final_parallax_video.mp4",
        )

        video_composite.write_videofile(
            output_path,
            codec=VIDEO_CODEC,
            fps=self.project.config_file()["fps"],
            preset="slow" if DEV else "medium",
            ffmpeg_params=(
                [
                    "-crf",
                    "18",
                    "-b:v",
                    "2M",
                    "-pix_fmt",
                    "yuv420p",
                    "-profile:v",
                    "high",
                    "-vf",
                    "scale=1920:1080",
                ]
                if DEV
                else ["-crf", "18", "-b:v", "2M", "-pix_fmt", "yuv420p"]
            ),
            threads=12 if DEV else 4,
        )

        self.log(f"Final video saved to: {output_path}", pad_with_rules=True)

    def __create_base_layers(self) -> list[LayerInterface]:
        layers = []
        for index, layer_config in enumerate(self.project.config_file()["layers"]):
            name_prefix = f"layer_{index+1}"
            layers.append(
                BaseLayer(
                    self.project, self.logger, layer_config, name_prefix, index + 1
                )
            )

        return layers

    def __create_object_layers(self) -> list[LayerInterface]:
        layers = []
        for index, tags in enumerate(self.project.config_file()["salient_objects"]):
            # Sometimes layers will return False (because nothing was segmented/extracted)
            object_layer = SalientObjectLayer(self.project, self.logger, tags, index)
            if object_layer:
                layers.append(object_layer)

        return layers

    def __user_confirm(self):
        prompt = (
            f"\nHave you finished inpainting the layers and putting the outputs in {self.project.layer_outputs_dir()}? (y/n):"
            + self.logger.get_prompt()
        )
        decline_message = colored(
            "Please do so and then run the script again.\n\n", "red"
        )

        if input(prompt).lower() != "y":
            print(decline_message)
            return False

        return True

    def __get_video_size(self):
        input_image = Image.open(self.project.config_file()["input_image_path"])
        return input_image.size
