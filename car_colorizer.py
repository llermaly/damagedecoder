from PIL import Image
import os

color_map = {
    0: "gray",  # Not visible
    1: "green",  # Seems OK
    2: "yellow",  # Minor Damage
    3: "red",  # Major damage
}

# TODO: Add the real parts of each side of the car

sides_map = {
    "front": {
        "image": "images/car_parts/car_front.png",
        "numbers": "images/car_parts/car_front_numbers.png",
        "parts": [
            "roof",
            "windshield",
            "hood",
            "grill",
            "front_bumper",
            "right_mirror",
            "left_mirror",
            "front_right_light",
            "front_left_light"
        ],
    },
    "back": {
        "image": "images/car_parts/car_back.png",
        "numbers": "images/car_parts/car_back_numbers.png",
        "parts": [
            "rear_window",
            "trunk_tgate",
            "trunk_cargo_area",
            "rear_bumper",
            "right_tail_light",
            "left_tail_light",
        ],
    },
    "left": {
        "image": "images/car_parts/car_left.png",
        "numbers": "images/car_parts/car_left_numbers.png",
        "parts": [
            "left_rear_quarter",
            "left_rear_door",
            "left_front_door",
            "left_fender",
            "left_front_tire",
            "left_rear_tire",
        ],
    },
    "right": {
        "image": "images/car_parts/car_right.png",
        "numbers": "images/car_parts/car_right_numbers.png",
        "parts": [
            "right_rear_quarter",
            "right_rear_door",
            "right_front_door",
            "right_fender",
            "right_front_tire",
            "right_rear_tire",
        ],
    },
}


def colorize(image, condition):
    color = color_map.get(condition, "gray")
    overlay = Image.new("RGBA", image.size, color=color)
    r, g, b, alpha = image.split()
    alpha_transparency = 76  # Around 30% transparency
    transparent_alpha = alpha.point(lambda p: p * alpha_transparency // 255)
    overlay.putalpha(transparent_alpha)
    return Image.alpha_composite(image, overlay)


def process_car_parts(conditions, side):
    base_image = Image.open(sides_map[side]["image"]).convert("RGBA")
    numbers = Image.open(sides_map[side]["numbers"]).convert("RGBA")
    for part in sides_map[side]["parts"]:
        print(f"Processing part: {part}")
        try:
            part_image_path = f"images/car_parts/{part}.png"
            if not os.path.exists(part_image_path):
                print(f"Image for part '{part}' not found. Skipping.")
                continue
            part_image = Image.open(part_image_path).convert("RGBA")
            colored_part = colorize(part_image, conditions[part])
            base_image.paste(colored_part, (0, 0), colored_part.split()[3])
        except FileNotFoundError:
            print(f"File not found: {part}.png - Skipping this part.")
        except Exception as e:
            print(f"An error occurred while processing {part}: {e}")
    base_image.paste(numbers, (0, 0), numbers.split()[3])
    return base_image
