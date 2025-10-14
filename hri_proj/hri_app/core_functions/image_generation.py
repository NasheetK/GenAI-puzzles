
import random


def create_single_img(puzzle_config):
    image1 = "hri_app/static/imgs/tl.png"
    image2 = "hri_app/static/imgs/zp.png"

    selected_image = random.choice([image1, image2])
    return selected_image
