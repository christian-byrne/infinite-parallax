import time
from PIL import Image
import math
import re

def create_config():

    using_depth_maps = False
    using_segmentation = False

    config = {"created_at": time.ctime()}

    original_input_image_path = input("Enter the input image path: ")
    config["original_input_image_path"] = original_input_image_path
    input_image = Image.open(original_input_image_path)

    print(
        "Direction of Parallax (0-360 degrees)",
        "0 degrees is to the right",
        "90 degrees is up",
        "180 degrees is left",
        "270 degrees is down",
    )
    direction = float(input("> "))
    # handle if given negative angle
    if direction < 0:
        direction = 360 + direction
    # convert to 0-360 form
    direction = direction % 360
    direction_theta = math.radians(direction)
    config["direction"] = direction
    config["direction_theta"] = direction_theta
    int_direction = int(direction)
    if int_direction == 0:
        config["velocity_vector"] = (1, 0)
    elif int_direction == 180:
        config["velocity_vector"] = (-1, 0)
    elif int_direction == 90:
        config["velocity_vector"] = (0, 1)
    elif int_direction == 270:
        config["velocity_vector"] = (0, -1)
    else:
        config["velocity_vector"] = (math.cos(direction_theta), math.sin(direction_theta))

    layers = []
    if not using_segmentation:
        num_layers = int(input("Enter the number of layers: "))
        for i in range(num_layers):
            layer = {}
            layers.append(layer)

    if not using_segmentation:
        print("Layers start from the top of the image and go down")
        print("The top layer is Layer 0. The bottom layer is Layer N-1.")
        for i in range(num_layers):
            if i == len(layers) - 1:
                print(
                    "The last layer is calculated automatically",
                    "to ensure the entire image is covered.",
                )

                total_height_before_last_layer = sum(
                    [layer["height"] for layer in layers[:-1]]
                )
                height_last_layer = input_image.height - total_height_before_last_layer
                print(f"Height of last layer: {height_last_layer}px")
            else:
                layers[i]["height"] = float(input(f"Height of Layer {i} (in pixels): "))

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
    if not using_depth_maps:
        print(
            "You can think of distance in terms of whatever unit you want,",
            "as long as it's consistent.",
            "For example, you can give distance on a scale of 0-100,",
            "where 0 is right in front of the camera",
            "and 100 is the horizon.",
        )
        for i in range(num_layers):
            layers[i]["distance"] = input(
                f"Distance of Layer {i} from the camera: "
            )
            # Clean any units or non-numeric characters and convert to float
            layers[i]["distance"] = re.sub(
                "[^0-9]", "", layers[i]["distance"]
            )
            layers[i]["distance"] = float(layers[i]["distance"])

    # Convert distances to percentages
    total_distance = sum([layer["distance"] for layer in layers])
    for i in range(num_layers):
        layers[i]["distance_ratio"] = layers[i]["distance"] / total_distance

    print(
        "Smoothness",
        "The base change in distance in between each inpainting step",
        "More smoothness means more intermediate frames, and a smoother transition",
        "at the cost of more time and memory",
    )

    config["smoothness"] = int(input("(int) Smoothness (recommended 20-100): "))

    print(
        "Frames Per Second",
        "The base speed of the final video",
        "Lower FPS usually creates better results",
    )

    config["fps"] = int(input("(int) Frames Per Second: "))

    for i in range(num_layers):
        layers[i]["velocity"] = (
            config["velocity_vector"][0]
            * layers[i]["distance_ratio"]
            * config["smoothness"],
            config["velocity_vector"][1]
            * layers[i]["distance_ratio"]
            * config["smoothness"],
        )

    # Each layer requires enough steps so that it can move the full distance of the image
    # This is calculated by dividing the distance of the layer by the velocity of the layer
    for i in range(num_layers):
        if layers[i]["velocity"][0] == 0:
            layers[i]["steps_x"] = 0
        else:
            layers[i]["steps_x"] = abs(int(
                input_image.width / layers[i]["velocity"][0]
            ))
        if layers[i]["velocity"][1] == 0:
            layers[i]["steps_y"] = 0
        else:
            layers[i]["steps_y"] = abs(int(
                input_image.height / layers[i]["velocity"][1]
            ))

    config["max_steps"] = abs(max(
        [layers[i]["steps_x"] for i in range(num_layers)]
    ))

    config["layers"] = layers
    return config