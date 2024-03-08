from PIL import Image
import os
from interfaces.project_interface import ProjectInterface
from interfaces.logger_interface import LoggerInterface


class LayerShifter:
    def __init__(
        self,
        project: ProjectInterface,
        logger: LoggerInterface,
        caller_prefix="PREPROCESS > SHIFT",
    ):
        self.project = project
        self.logger = logger
        self.start_image_fullpath = project.config_file()["input_image_path"]
        self.start_image_pil = Image.open(self.start_image_fullpath)
        self.caller_prefix = caller_prefix
        self.step_count = 1

    def log(self, *args, **kwargs):
        self.logger.log(caller_prefix=self.caller_prefix, *args, **kwargs)

    def save_img(self, img: Image.Image) -> str:
        path = os.path.join(
            self.project.layer_outputs_dir(),
            f"start_step_{self.step_count:05d}_.png",
        )
        img.save(path)
        return path

    def x_velocity(self, layer_config):
        return round(layer_config["velocity"][0])

    def y_velocity(self, layer_config):
        return round(layer_config["velocity"][1])

    def create_shifted_image(self, input_image_pil: Image.Image) -> str:
        self.slice_and_shift_layers(input_image_pil)
        canvas = Image.new("RGBA", input_image_pil.size, (0, 0, 0, 0))

        y = 0
        for layer, layer_config in zip(
            self.cropped_shifted_layers, self.project.config_file()["layers"]
        ):
            # Moving right
            if self.x_velocity(layer_config) >= 0:
                # Moving down
                if self.y_velocity(layer_config) >= 0:
                    canvas.paste(
                        layer,
                        (
                            self.x_velocity(layer_config),
                            y + self.y_velocity(layer_config),
                        ),
                    )
                # Moving up
                else:
                    canvas.paste(layer, (self.x_velocity(layer_config), y))
            # Moving left
            else:
                # Moving down
                if self.y_velocity(layer_config) >= 0:
                    canvas.paste(layer, (0, y + self.y_velocity(layer_config)))
                # Moving up
                else:
                    canvas.paste(layer, (0, y))

            y += layer.height

        save_path = self.save_img(canvas)
        self.step_count += 1

        return save_path

    def slice_and_shift_layers(self, input_image_pil: Image.Image):
        """
        Cuts the input image into slices defined by each layers' dimensions.
        """
        self.log("Separating layers")
        self.cropped_shifted_layers = []
        top = 0
        bottom = 0
        layer_n = 0
        for layer_config in self.project.config_file()["layers"]:
            x_velocity = self.x_velocity(layer_config)
            y_velocity = self.y_velocity(layer_config)
            bottom += layer_config["height"]
            if x_velocity < 0:
                left = abs(x_velocity)
                right = input_image_pil.width
            else:
                left = 0
                right = input_image_pil.width - x_velocity

            # If bottom layer, and y_velocity is negative, then crop
            if (
                y_velocity < 0
                and layer_n == len(self.project.config_file()["layers"]) - 1
            ):
                bottom -= abs(y_velocity)
            # If top layer, and y_velocity is positive, then crop
            elif y_velocity > 0 and layer_n == 0:
                top += y_velocity

            layer_pil = input_image_pil.crop((left, top, right, bottom))

            # Save unshifted layers for base Layer to use in stitching
            layer_pil_unshifted = input_image_pil.crop((0, top, input_image_pil.width, bottom))
            layer_pil_unshifted.save(
                os.path.join(
                    self.project.layer_outputs_dir(),
                    f"layer_{layer_n+1}_{self.step_count:05d}_.png",
                )
            )

            # Readjust y position so rest of layers arent also cropped horizontally (only layer bordering on the horizontal edge towards the direction of movement)
            # If bottom layer, and y_velocity is negative
            if (
                y_velocity < 0
                and layer_n == len(self.project.config_file()["layers"]) - 1
            ):
                bottom += abs(y_velocity)
            # If top layer, and y_velocity is positive
            if y_velocity > 0 and layer_n == 0:
                top -= y_velocity

            self.cropped_shifted_layers.append(layer_pil)
            top += layer_config["height"]
            layer_n += 1
