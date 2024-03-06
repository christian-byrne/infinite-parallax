from typing import Protocol


class ProjectInterface(Protocol):

    name: str  # The name of the project.
    version: str  # The version of the project.
    author: str  # The author of the project.
    repo_root: str  # The root directory of the project repository.

    def update_config(self, key: str, value: any) -> None:
        """
        Update the configuration file with the given key-value pair.
        The change will be written to the actual configuration file.

        Args:
            key (str): The key to update in the configuration file.
            value (Any): The value to set for the given key.

        Returns:
            None
        """
        ...

    def config_file(self) -> dict:
        """
        Reads the configuration file and returns its contents as a dictionary.

        If the configuration file does not exist, it will be created by calling the `set_config` method.

        Returns:
            dict: The contents of the configuration file as a dictionary.
        """
        ...

    def workflow_dir(self) -> str:
        """
        Returns the path to the workflow directory within the project directory.

        This method first constructs the path by joining the project directory path with the constant WORKFLOW_DIR.
        Then, it checks if the directory exists and creates it if it doesn't.
        Finally, it returns the path to the workflow directory.

        Returns:
            str: The path to the workflow directory.
        """
        ...

    def layer_outputs_dir(self) -> str:
        """
        Returns the directory path for storing layer outputs.

        The directory path is determined by joining the project directory path
        with the constant LAYER_OUTPUT_DIR. If the directory does not exist,
        it will be created using the check_make_dir function.

        Returns:
            str: The directory path for layer outputs.
        """
        ...

    def salient_objects_dir(self) -> str:
        """
        Returns the path to the directory where salient objects are stored.

        This method constructs the path by joining the project directory path with the
        SALIENT_OBJECTS_DIR constant. It also checks if the directory exists and creates
        it if it doesn't.

        Returns:
            str: The path to the salient objects directory.
        """
        ...

    def original_layers_dir(self) -> str:
        """
        Returns the path to the directory where the original layers are stored.

        The path is determined by joining the project directory path with the
        constant ORIGINAL_LAYERS_DIR. If the directory does not exist, it will
        be created using the check_make_dir function.

        Returns:
            str: The path to the original layers directory.
        """
        ...

    def cropped_steps_dir(self) -> str:
        """
        Returns the path to the directory where cropped steps are stored.

        The path is determined by joining the project directory path with the
        constant CROPPED_STEPS_DIR. If the directory does not exist, it will
        be created using the check_make_dir function.

        Returns:
            str: The path to the cropped steps directory.
        """
        ...

    def stitched_inpainted_dir(self) -> str:
        """
        Returns the path to the directory where stitched and inpainted images are stored.
        These images are the finalized image frames for each layer which will be panned over
        in the output video according to the vector of motion.

        The path is determined by joining the project directory path with the
        constant STITCHED_INPAINT_DIR. If the directory does not exist, it will
        be created using the check_make_dir function.

        Returns:
            str: The path to the stitched and inpainted directory.
        """
        ...

    def output_video_dir(self) -> str:
        """
        Returns the path to the directory where the output video will be saved.

        The path is determined by joining the project directory path with the
        constant OUTPUTS_USER_REL_PATH. If the directory does not exist, it will
        be created using the check_make_dir function.

        Returns:
            str: The path to the output video directory.
        """
        ...