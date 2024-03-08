from PIL import Image
import os
from preprocessors.preprocess_step_input import LayerShifter
from comfy_api.client import ComfyClient
from comfy_api.server import ComfyServer
from workflow_wrapper.workflow import ComfyAPIWorkflow
from interfaces.project_interface import ProjectInterface
from interfaces.logger_interface import LoggerInterface
from constants import INPAINT_WORKFLOW_PATH, FEATHERING_MARGIN


class InpaintLooper:
    def __init__(
        self,
        project: ProjectInterface,
        logger: LoggerInterface,
        caller_prefix="INPAINT LOOP",
    ):
        self.project = project
        self.logger = logger
        self.caller_prefix = caller_prefix

        self.log(
            "Inpainting workflow location:",
            os.path.join(project.repo_root, INPAINT_WORKFLOW_PATH),
        )
        input(
            "\nYou can edit the workflow now if the default values are not working."
            + "\nPress ENTER when done or to skip editing."
            + self.logger.get_prompt()
        )

        self.shift_preprocessor = LayerShifter(project, logger)
        self.workflow = ComfyAPIWorkflow(
            project,
            logger,
            os.path.join(project.repo_root, INPAINT_WORKFLOW_PATH),
            "INPAINT-LOOP > WF",
        )
        # NOTE: Change if workflow changes or custom nodes are updated
        self.workflow.update(
            "ImpactWildcardProcessor",
            "wildcard_text",
            project.config_file()["prompt_prepend"],
        )
        self.workflow.update(
            "GrowMaskWithBlur",
            "expand",
            int(FEATHERING_MARGIN * 1.85)
        )
        self.workflow.update(
            "GrowMaskWithBlur",
            "blur_radius",
            FEATHERING_MARGIN / 4
        )

    def log(self, *args, **kwargs):
        self.logger.log(caller_prefix=self.caller_prefix, *args, **kwargs)

    def iterative_inpaint(self, n_iterations):
        # Start with input image (salient objects should be removed already)
        start_image_fullpath = self.shift_preprocessor.create_shifted_image(
            Image.open(self.project.config_file()["input_image_path"])
        )
        self.workflow.update(
            "LoadImage", "image", os.path.basename(start_image_fullpath)
        )

        try:
            server = ComfyServer(
                self.project,
                self.logger,
                self.project.layer_outputs_dir(),
                self.project.layer_outputs_dir(),
                "INPAINT-LOOP > SERVER",
            )
            server.start()

            for i in range(n_iterations):
                client = ComfyClient(
                    self.project, self.workflow, self.logger, f"IP-STEP {i+1} > CLIENT"
                )
                client.queue_workflow()
                end_image_filename = f"end_step_{i+1:05d}_.png"
                start_image_fullpath = self.shift_preprocessor.create_shifted_image(
                    Image.open(
                        os.path.join(
                            self.project.layer_outputs_dir(), end_image_filename
                        )
                    )
                )
                self.workflow.update(
                    "LoadImage", "image", os.path.basename(start_image_fullpath)
                )
                client.disconnect()

        except Exception as e:
            self.log(f"Error with comfy server/client during inpaint loop: {e}")
            raise e

        finally:
            try:
                server.kill()
                client.disconnect()
            except Exception as e:
                self.log(f"Error stopping comfy server/client: {e}")
            
        self.log("Inpaint loop: Completed")
