# Adjust
DEV = True
COMFY_PATH = "/home/c_byrne/tools/sd/sd-interfaces/ComfyUI"
FEATHERING_MARGIN = 8  # Recommended: 8 (px)

# Don't Need to Adjust
PROJECT_DATA_REL_PATH = "projects" # rel path from repo root
CONFIG_FILENAME = "config.json"
LAYER_OUTPUT_DIR = "layers/layer_outputs"
ORIGINAL_LAYERS_DIR = "originals/original_layers"
STITCHED_INPAINT_DIR = "stitches/stitched_inpainted"
CROPPED_STEPS_DIR = "layers/cropped_steps"
LAYER_VIDEOS_DIR = "videos/layer_videos"
VIDEO_CODEC = "libx264"
OUTPUT_VIDEO_PATH = "output"
SALIENT_OBJECTS_DIR = "objects/alpha_layers/salient_objects"
PROJECT_WORKFLOW_DIR = "project_workflows"
GLOABL_LOGS_DIR = "logs" # rel path from repo root
COMFY_PORT = 8188
COMFY_API_MAX_CONNECT_ATTEMPTS = 18
SALIENT_OBJECTS_WORKFLOW_PATH = "workflow-templates/api/salient_object/salient_object-remove_inpaint_extract-v2-API_VERSION.json"
INPAINT_WORKFLOW_PATH = "workflow-templates/api/inpaint/inpaint_with_lora_stack-API_VERSION.json"
SALIENT_OBJECT_ALPHA_LAYER_PREFIX = "salient_object_alpha_layer"
BASE_LAYER_WITHOUT_OBJECTS_PREFIX = "base_layer-salient_object_removed"
START_STEP_PREFIX = "start_step"
STITCHED_OBJECTS_DIR = "stitches/stitched_object_alphas"
DEFAULT_DISTANCES = {
    "cloud_layer": {
        "mathematically_accurate_distance": 16.18,
        "creates_best_output_distance": 280,
    },
    "horizon_layer": {
        "mathematically_accurate_distance": 0.15,
        "creates_best_output_distance": 50,
    },
    # Past depth of field in landscape paintings
    "background_layer": {
        "mathematically_accurate_distance": 689,
        "creates_best_output_distance": 690,
    },
    "foreground_layer": {
        # Arbitrary base
        "mathematically_accurate_distance": 800,
        "creates_best_output_distance": 800,
    },
}
