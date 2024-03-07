from typing import Protocol, TypedDict
from moviepy.editor import VideoClip
from PIL.Image import Image as PILImage
from interfaces.project_interface import ProjectInterface


LayerConfigDict = TypedDict(
    "LayerConfigDict",
    {
        "height": int,  # The height of the layer in pixels.
        "distance": int,  # The arbitrary distance from viewer of the layer (relative to other layers, not in accordance with any unit system).
        "distance_ratio": float,  # The ratio of the distance-from-viewer of the layer relative to the total distance-from-viewer of all layers.
        "velocity": list[int],  # The velocity vector of the layer.
        "steps_x": int,  # The number of steps to move the layer in the x-direction.
        "steps_y": int,  # The number of steps to move the layer in the y-direction.
    },
)

ImageDict = TypedDict(
    "ImagesDict",
    {
        "image": PILImage,  # The PIL image object.
        "filename": str,  # The filename of the image.
        "basename": str,  # The basename of the image (filename without extension).
        "ext": str,  # The extension of the image (e.g., 'png').
        "path": str,  # The path to the image.
        "fullpath": str,  # The full path to the image (path + filename).
    },
)

PathPartsDict = TypedDict(
    "ImagesPathPartsDict",
    {
        "filename": str,  # The filename of the image.
        "basename": str,  # The basename of the image (filename without extension).
        "ext": str,  # The extension of the image (e.g., 'png').
        "path": str,  # The path to the image.
        "fullpath": str,  # The full path to the image (path + filename).
    },
)


class LayerInterface(Protocol):
    project: "ProjectInterface"  # The project to which the layer belongs.
    layer_config: LayerConfigDict  # The configuration for the layer.
    name_prefix: str  # The prefix for the name of the layer.
    index: int  # The index of the layer in the project configuration. From top to bottom, 1-indexed.
    slide_distance: int  # The total distance traveled by the layer in the video (in pixels). I.e., the total width of all inpainted regions stitched onto the original layer.
    total_steps: int  # The total number of inpainting steps for the layer (i.e., the number of stitched inpainted regions added to the layer).
    duration: int  # The duration of the layer video in seconds. Should be uniform for all layers.
    step_images: list[
        PathPartsDict
    ]  # A list of step images for the layer. Represented by dictionaries containing the filename, fullpath, and other path parts for the image.
    cropped_step_images: list[
        ImageDict
    ]  # A list of cropped step images for the layer. Represented by dictionaries containing the PIL image object, filename, and other path parts for the image.
    original_layer: ImageDict  # The original layer image. Represented by a dictionary containing the PIL image object, filename, and other path parts for the image.

    def get_x_velocity(self) -> int:
        """
        Returns the x-component of the layer's velocity vector.

        The x-component of the velocity vector is the first element in the velocity vector list.

        Returns:
            int: The x-component of the layer's velocity vector.
        """
        ...

    def get_y_velocity(self) -> int:
        """
        Returns the y-component of the layer's velocity vector.

        The y-component of the velocity vector is the second element in the velocity vector list.

        Returns:
            int: The y-component of the layer's velocity vector.
        """
        ...

    def create_cropped_steps(self) -> None:
        """
        Creates and saves individual cropped steps for the layer.

        This method iterates over the step images for the layer and crops each image
        to remove the inpainted region (the region that was inpainted in the generation
        of that step). The cropped images are then saved in the cropped steps directory.

        For each step image, crop the image to only include the inpainted region.
        If the layer velocity is -13, we should extract the 13xheight picture starting from the right.
        If the layer velocity is 240, we should extract the 240xheight starting from the left.

        Returns:
            None
        """
        ...

    def stitch_cropped_steps(self) -> None:
        """Stitch the cropped step images together to create the final layer output.

        The order of the images should be from the first step to the last step.
        The output image should be saved in the project directory with the name {layer_prefix}_stitched_inpainted_regions.png.

        Args:
            None

        Returns:
            None
        """

    def create_layer_videoclip(self) -> VideoClip:
        """
        Creates a video clip from the stitched image, panning from left to right.

        The duration is uniform for all layers and is calculated as the total number of steps
        multiplied by the number of seconds per step.

        Returns:
            VideoClip: The created video clip.
        """
        ...

    def __set_original_layer(self) -> None:
        """
        Sets the original layer for the current layer.

        This method sets the original layer image for the layer.
        The original layer is simply the slice of the input image that corresponds to the layer's dimensions.
        In the case of an object layer, the original layer is the alpha layer of the object after
        it has been extracted from the input image and joined with an alpha layer of the same size (i.e., a cutout)

        Returns:
            None
        """
        ...
