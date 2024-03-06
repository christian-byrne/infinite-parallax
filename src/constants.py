PROJECT_DATA_REL_PATH = "data/projects"
CONFIG_FILENAME = "config.json"
LAYER_OUTPUT_DIR = "layer_outputs"
# Recommended: 8 (px)
FEATHERING_MARGIN = 8
ORIGINAL_LAYERS_DIR = "original_layers"
STITCHED_INPAINT_DIR = "stitched_inpainted"
CROPPED_STEPS_DIR = "cropped_steps"
LAYER_VIDEOS_DIR = "videos/layer_videos"
DEV = True
VIDEO_CODEC = "libx264"
OUTPUT_VIDEO_PATH = "output"
SALIENT_OBJECTS_DIR = "salient_objects"
WORKFLOW_DIR = "project_workflows"
LOGS_DIR = "logs"
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
