from termcolor import colored
from moviepy.editor import CompositeVideoClip, VideoClip
from PIL import Image
from layers.layer import Layer
import os
from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
from constants import (
    DEV,
    VIDEO_CODEC,
)


class ParallaxVideo:
    def __init__(self, project: ProjectInterface):
        self.project = project
        if not self.user_confirm():
            return

        self.layers = self.create_layers()
        for layer in self.layers:
            layer.create_cropped_steps()
            layer.stitch_cropped_steps()

        self.layer_videoclips = self.create_layer_videoclips()
        self.composite_layer_videoclips()

    def user_confirm(self):
        prompt = (
            colored("\n[CONFIRM PROCEED]", "red")
            + f"\nHave you finished inpainting the layers and putting the outputs in {self.project.layer_outputs_dir()}? (y/n):\n> "
        )
        decline_message = colored(
            "Please do so and then run the script again.\n\n", "red"
        )

        if input(prompt).lower() != "y":
            print(decline_message)
            return False

        return True

    def get_video_size(self):
        input_image = Image.open(self.project.config_file()["input_image_path"])
        return input_image.size

    def create_layers(self) -> list[LayerInterface]:
        layers = []
        for index, layer_config in enumerate(self.project.config_file()["layers"]):
            name_prefix = f"layer_{index+1}"
            layers.append(Layer(self.project, layer_config, name_prefix, index + 1))

        return layers

    def create_layer_videoclips(self) -> list[VideoClip]:

        layer_clips = []
        x = 0
        y = 0
        for layer, layer_config in zip(
            self.layers, self.project.config_file()["layers"]
        ):
            layer_videoclip = layer.create_layer_videoclip()
            layer_videoclip = layer_videoclip.set_position((x, y))
            layer_clips.append(layer_videoclip)
            y += layer_config["height"]

        return layer_clips

    def composite_layer_videoclips(self):
        """
        Create a final video from the frames.

        self.layer_clips is a list of lists of VideoClip instances.
        Each list of VideoClip instances represents a layer.
        The layers should be stacked according to the vector of motion.

        This function creates a final video by compositing the layer clips and saving it to the specified output path.
        """

        video_composite = CompositeVideoClip(
            self.layer_videoclips, size=self.get_video_size()
        )

        output_path = os.path.join(
            self.project.output_video_dir(),
            f"{self.project.name}-final_parallax_video.mp4",
        )

        video_composite.write_videofile(
            output_path,
            codec=VIDEO_CODEC,
            fps=self.project.config_file()["fps"],
        )

        print(f"\n\nFinal video saved to {output_path}\n")
