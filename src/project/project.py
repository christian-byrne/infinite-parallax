import os
import json
from constants import (
    PROJECT_DATA_REL_PATH,
    CONFIG_FILENAME,
    ORIGINAL_LAYERS_DIR,
    OUTPUT_VIDEO_PATH,
    LAYER_OUTPUT_DIR,
    SALIENT_OBJECTS_DIR,
    PROJECT_WORKFLOW_DIR,
    CROPPED_STEPS_DIR,
    STITCHED_INPAINT_DIR,
    STITCHED_OBJECTS_DIR,
)
from .create_config import create_config
from utils.check_make_dir import check_make_dir
from interfaces.project_interface import ProjectInterface
from parallax_video.video import ParallaxVideo
from log.logging import Logger


class ParallaxProject(ProjectInterface):
    """
    Represents a parallax project.

    This class handles the creation of a parallax project, including initializing the project with the given name,
    setting up the project directory, loading the project configuration, creating and saving original layer slices,
    creating layer video clips, and generating the final parallax video.
    """

    def __init__(self, project_name, author=None):
        self.name = project_name
        if not author:
            self.__set_author()
        else:
            self.author = author

        self.repo_root = os.path.join(
            os.path.dirname(__file__).split("infinite-parallax")[0], "infinite-parallax"
        )
        self.logger = Logger(self)
        self.init_project_structure()

        if self.NEW_PROJECT:
            self.copy_input_image_to_project_dir()
            self.update_config("version", self.version)

        ParallaxVideo(self, self.logger)

    def log(self, *args, **kwargs):
        self.logger.log(caller_prefix="PROJECT MANAGER", *args, **kwargs)

    def init_project_structure(self):
        self.log(
            "Loading/Creating project: ",
            f"{self.name} by {self.author}",
            pad_with_rules=True,
        )
        self.log("Repo root: ", f"{self.repo_root}")
        self.project_dir_path = os.path.join(
            self.repo_root, PROJECT_DATA_REL_PATH, self.name
        )
        self.log("Project dir path: ", f"{self.project_dir_path}")

        if not check_make_dir(self.project_dir_path):
            self.log(
                "New Project. Project directory created at:",
                f"{self.project_dir_path}",
            )
            self.NEW_PROJECT = True
            self.version = [0, 1, 0]
        else:
            self.log(
                "Loading existing project found at:",
                f"{self.project_dir_path}",
            )
            self.NEW_PROJECT = False

        self.config_file()
        if not self.NEW_PROJECT:
            self.version = self.config_file()["version"]
            self.version[2] += 1
            self.update_config("version", self.version)

    def set_config(self):
        config = create_config()
        config["project_dir_path"] = self.project_dir_path
        config["config_path"] = self.config_path
        config["project_name"] = self.name

        with open(self.config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

    def copy_input_image_to_project_dir(self):
        config = self.config_file()
        input_image_path = config["original_input_image_path"]
        input_image_filename = os.path.basename(input_image_path)
        input_image_dest_path = os.path.join(
            self.project_dir_path, input_image_filename
        )
        os.system(f"cp {input_image_path} {input_image_dest_path}")
        self.update_config("input_image_path", input_image_dest_path)

    def update_config(self, key, value):
        config = self.config_file()
        config[key] = value
        with open(self.config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)

    def config_file(self):
        path = os.path.join(self.project_dir_path, CONFIG_FILENAME)
        self.config_path = path
        if not os.path.exists(path):
            self.set_config()

        with open(path, "r") as config_file:
            return json.load(config_file)

    def workflow_dir(self):
        path = os.path.join(self.project_dir_path, PROJECT_WORKFLOW_DIR)
        check_make_dir(path)
        # Add workflow logic
        return path

    def layer_outputs_dir(self):
        path = os.path.join(self.project_dir_path, LAYER_OUTPUT_DIR)
        check_make_dir(path)
        # Add layer outputs logic
        return path

    def salient_objects_dir(self):
        path = os.path.join(self.project_dir_path, SALIENT_OBJECTS_DIR)
        check_make_dir(path)
        # Add salient objects logic
        return path

    def original_layers_dir(self):
        path = os.path.join(self.project_dir_path, ORIGINAL_LAYERS_DIR)
        check_make_dir(path)
        # Add original layers logic
        return path

    def cropped_steps_dir(self):
        path = os.path.join(self.project_dir_path, CROPPED_STEPS_DIR)
        check_make_dir(path)
        # Add cropped steps logic
        return path

    def stitched_inpainted_dir(self):
        path = os.path.join(self.project_dir_path, STITCHED_INPAINT_DIR)
        check_make_dir(path)
        # Add stitched inpainted logic
        return path

    def output_video_dir(self):
        path = os.path.join(self.project_dir_path, OUTPUT_VIDEO_PATH)
        check_make_dir(path)
        # Add output video logic
        return path

    def stitched_objects_dir(self):
        path = os.path.join(self.project_dir_path, STITCHED_OBJECTS_DIR)
        check_make_dir(path)
        # Add stitched objects logic
        return path

    def __set_author(self):
        try:
            self.author = os.getenv("USER")
        except KeyError:
            # USER environment variable not set
            self.author = "windows_user"
        except (TypeError, PermissionError):
            # USER environment variable not a string
            self.author = "secure_user"
        except ValueError:
            # USER environment variable not valid
            self.author = "nonASCII_user"
        except Exception:
            self.author = "unknown_user"
