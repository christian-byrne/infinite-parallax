import os
from PIL import Image
from constants import PROJECT_DATA_REL_PATH, CONFIG_FILENAME, LAYER_OUTPUT_DIR, FEATHERING_MARGIN

class Layer:
    def __init__(self, project_config, layer_config, name_prefix):
        self.project_config = project_config
        self.layer_config = layer_config
        self.name_prefix = name_prefix
        self.set_step_images()
        self.pixel_velocity = layer_config["velocity"]
        self.create_cropped_steps()
        self.stitch_cropped_steps()

    def set_step_images(self):
        self.step_images = []
        all_step_images = os.listdir(os.path.join(self.project_config["project_dir_path"], LAYER_OUTPUT_DIR))

        temp = []
        for step_image in all_step_images:
            if step_image.startswith(self.name_prefix):
                temp.append(step_image)
        temp.sort()
        for step_image in temp:
                # Append full path
                step_image = {
                    # no prefix
                    "filename": step_image,
                    "basename": ".".join(step_image.split(".")[:-1]),
                    "ext": step_image.split(".")[-1],
                    "path" : os.path.join(self.project_config["project_dir_path"], LAYER_OUTPUT_DIR),
                    "fullpath" : os.path.join(self.project_config["project_dir_path"], LAYER_OUTPUT_DIR, step_image)
                }
                self.step_images.append(step_image)

    def create_cropped_steps(self):
        """For each step image, crop the image to only include the inpainted region. 
        If the layer velocity is -13, we should extract the 13xheight picture starting from the right.
        If the layer velocity is 240, we shoudl extract the 240xheight starting from the left"""

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
            fullpath = os.path.join(step_image["path"], filename)
            cropped_image.save(fullpath)

            cropped_step_image["filename"] = filename
            cropped_step_image["basename"] = ".".join(filename.split(".")[:-1])
            cropped_step_image["ext"] = filename.split(".")[-1]
            cropped_step_image["path"] = step_image["path"]
            cropped_step_image["fullpath"] = fullpath

            self.cropped_step_images.append(cropped_step_image)

    def stitch_cropped_steps(self):
        """Stitch the cropped step images together to create the final layer output. 
        The order of the images should be from the first step to the last step. 
        The output image should be saved in the project directory with the name {layer_prefix}_stitched_inpainted_regions.png"""
        print(self.cropped_step_images)
        # Create a list to store the cropped images
        cropped_images = []
        
        # Load the cropped step images
        for cropped_step_image in self.cropped_step_images:
            image = Image.open(cropped_step_image["fullpath"])
            cropped_images.append(image)
        
        # print(cropped_images)
        # Determine the width and height of the final stitched image
        width = sum([image.width for image in cropped_images]) - (len(cropped_images) - 1) * FEATHERING_MARGIN
        height = int(self.layer_config["height"])
        
        # Create a new image with the calculated width and height
        stitched_image = Image.new("RGB", (width, height))
        
        # Paste the cropped images onto the stitched image
        x_offset = 0
        for image in cropped_images:
            stitched_image.paste(image, (x_offset, 0))
            x_offset += image.width
            x_offset -= FEATHERING_MARGIN
        
        # Save the stitched image
        output_filename = f"{self.name_prefix}_stitched_inpainted_regions.png"
        output_path = os.path.join(self.project_config["project_dir_path"], output_filename)
        stitched_image.save(output_path)

        self.stitched_inpainted_regions = {
            "filename": output_filename,
            "basename": ".".join(output_filename.split(".")[:-1]),
            "ext": output_filename.split(".")[-1],
            "path": self.project_config["project_dir_path"],
            "fullpath": output_path
        }


    