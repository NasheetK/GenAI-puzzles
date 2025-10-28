
import random
from glob import glob


def create_single_img(puzzle_config):
    character = puzzle_config['character']
    activity = puzzle_config['activity']
    img_folder = "hri_app/static/imgs/" + character + "_" + activity + "/*"
    # image1 = "hri_app/static/imgs/tl.png"
    # image2 = "hri_app/static/imgs/zp.png"
    img_list = glob(img_folder)
    # print(img_list)
    selected_image = random.choice(img_list)
    return selected_image
