import os
from constants import PROJECT_DATA_REL_PATH, CONFIG_FILENAME, LAYER_OUTPUT_DIR

class Layer:
    def __init__(self, project_config, name_prefix):
        self.project_config = project_config
        self.name_prefix = name_prefix
        self.set_step_image_paths()
        print(self.step_image_paths)

    def set_step_image_paths(self):
        self.step_image_paths = []
        all_step_images = os.listdir(os.path.join(self.project_config["project_dir_path"], LAYER_OUTPUT_DIR))
        for step_image in all_step_images:
            if step_image.startswith(self.name_prefix):
                self.step_image_paths.append(step_image)

    def forward(self, input):
        raise NotImplementedError

    def backward(self, output_grad):
        raise NotImplementedError