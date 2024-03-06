from interfaces.project_interface import ProjectInterface
from interfaces.layer_interface import LayerInterface
import os


class SalientObjectLayer(LayerInterface):
    def __init__(
        self, project: ProjectInterface, layer_config, name_prefix, layer_index
    ):
        self.project = project
        # The layer config should be a copy of the layer config for the LOWEST layer in which the salient object is in 
        # (because something's parallax motion/velocity is determined by where its base is, visually)
        self.layer_config = layer_config
        self.name_prefix = name_prefix
        self.index = layer_index
        self.slide_distance = 0
        # NOTE: total steps start at -1 for now because the first image is skipped (saving the first layer slices before any inpainting in the current workflow)
        self.total_steps = -1
        self.set_step_images()
        self.set_original_layer()

        self.duration = int(self.total_steps * self.project_config["seconds_per_step"])
        self.output_vid_width = self.original_layer["image"].width
