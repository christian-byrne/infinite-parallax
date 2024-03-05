import time
from PIL import Image
import math
import re
from termcolor import colored


def create_config():
    """
    Creates a configuration dictionary for the infinite parallax effect.

    Returns:
        dict: The configuration dictionary containing various parameters for the effect.
    """
    # lambda function to print list of messages in a easily readable manner
    print_list = lambda messages: print(
        colored("\n" + "\n".join(messages) + "\n", "cyan")
    )
    using_depth_maps = False
    using_segmentation = False

    config = {"created_at": time.ctime()}

    original_input_image_path = input("Enter the input image path: ")
    config["original_input_image_path"] = original_input_image_path
    input_image = Image.open(original_input_image_path)
    config["input_image_width"] = input_image.width
    config["input_image_height"] = input_image.height

    print_list(
        [
            "Direction of Parallax (0-360 degrees)",
            "0 degrees is to the right",
            "90 degrees is up",
            "180 degrees is left",
            "270 degrees is down",
        ]
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
        config["velocity_vector"] = (
            math.cos(direction_theta),
            math.sin(direction_theta),
        )

    layers = []
    if not using_segmentation:
        num_layers = int(input("Enter the number of layers: "))
        for i in range(num_layers):
            layer = {}
            layers.append(layer)

    if not using_segmentation:
        print_list(
            [
                "Layers start from the top of the image and go down",
                "The top layer is Layer 0. The bottom layer is Layer N-1.",
            ]
        )
        for i in range(num_layers):
            if i == len(layers) - 1:
                print_list(
                    [
                        "The last layer is calculated automatically",
                        "to ensure the entire image is covered.",
                    ]
                )

                total_height_before_last_layer = sum(
                    [layer["height"] for layer in layers[:-1]]
                )
                height_last_layer = input_image.height - total_height_before_last_layer
                print(f"Height of last layer: {height_last_layer}px")
                layers[i]["height"] = int(height_last_layer)
            else:
                layers[i]["height"] = int(input(f"Height of Layer {i} (in pixels): "))

    if not using_depth_maps:
        print_list(
            [
                "You can think of distance in terms of whatever unit you want,",
                "as long as it's consistent.",
                "For example, you can give distance on a scale of 0-100,",
                "where 0 is right in front of the camera",
                "and 100 is the horizon.",
            ]
        )
        for i in range(num_layers):
            layers[i]["distance"] = input(f"Distance of Layer {i} from the camera: ")
            # Clean any units or non-numeric characters and convert to float
            layers[i]["distance"] = re.sub("[^0-9]", "", layers[i]["distance"])
            layers[i]["distance"] = float(layers[i]["distance"])

    # Convert distances to ratios
    total_distance = sum([layer["distance"] for layer in layers])
    for i in range(num_layers):
        layers[i]["distance_ratio"] = layers[i]["distance"] / total_distance

    print_list(
        [
            "Smoothness",
            "More smoothness means intermediate frames, and a smoother transition",
            "at the cost of more time and memory",
            "\nRecommended: 16",
        ]
    )

    config["smoothness"] = int(1000 / int(input("(int) Smoothness (0-100): ")))

    print_list(
        [
            "Seconds Per Step",
            "The base speed of the final video",
            "The more seconds per step, the slower the parallax motion, which usually creates better looking results but the motion may become unnoticeable",
            "\nRecommended: 5, assuming a smoothness of 16",
        ]
    )
    config["seconds_per_step"] = int(input("(int) Seconds Per Step: "))

    print_list(
        [
            "Frame Per Second of the Output Video",
            "The speed is different from the seconds per step",
            "A video moving across one step every 5 seconds can be 10 FPS or 60 FPS",
            "FPS just determines how many total frames are created using the function that creates frames with the coordinate(time) function",
            "Increasing FPS will increase the total number of frames, but the speed of the parallax motion will remain the same",
            "Compared with the other config options, the performance impact of creating higher FPS is very low",
            "Recommended: 30",
        ]
    )
    config["fps"] = int(input("(int) Frame Per Second of the Output Video: "))


    for i in range(num_layers):
        layers[i]["velocity"] = (
            config["velocity_vector"][0]
            * layers[i]["distance_ratio"]
            * config["smoothness"],
            config["velocity_vector"][1]
            * layers[i]["distance_ratio"]
            * config["smoothness"],
        )
        # Round to 1 decimal place
        layers[i]["velocity"] = (
            round(layers[i]["velocity"][0], 1),
            round(layers[i]["velocity"][1], 1),
        )

    # Each layer requires enough steps so that it can move the full distance of the image
    # This is calculated by dividing the distance of the layer by the velocity of the layer
    for i in range(num_layers):
        if layers[i]["velocity"][0] == 0:
            layers[i]["steps_x"] = 0
        else:
            layers[i]["steps_x"] = abs(
                int(input_image.width / layers[i]["velocity"][0])
            )
        if layers[i]["velocity"][1] == 0:
            layers[i]["steps_y"] = 0
        else:
            layers[i]["steps_y"] = abs(
                int(input_image.height / layers[i]["velocity"][1])
            )

    config["max_steps"] = abs(max([layers[i]["steps_x"] for i in range(num_layers)]))

    config["layers"] = layers
    return config
