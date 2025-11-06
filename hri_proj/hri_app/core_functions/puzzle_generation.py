from PIL import Image
import numpy as np
import uuid
import os

from .image_generation import *


def create_puzzle(puzzle_config):
    mode = puzzle_config['mode']
    players = puzzle_config['players']
    difficulty_map = {
        'Beginner': 1,
        'Easy': 2,
        'Medium': 3,
        'Hard': 4,
        'Expert': 5
    }
    difficulty_value = difficulty_map.get(puzzle_config['difficulty'], 1) # at least one puzzle
    # if mode == 'competitive':
    #     img_amount = int(np.floor(difficulty_value))
    # else:
    #     img_amount = max(int(np.floor(len(players) * difficulty_value / 2)), 1) # at least one puzzle
    img_amount = 2
    full_img_list = []
    full_id_list = []
    piece_detail_list = []
    print(img_amount)
    for i in range(img_amount):
        img_path = create_single_img(puzzle_config)
        print(img_path)
        img_id = uuid.uuid4().int
        piece_detail = split_to_pieces(img_path, img_id)
        piece_detail_with_id = [(i, x.replace('hri_app/static/', '')) for i, x in enumerate(piece_detail)]
        random.shuffle(piece_detail_with_id)
        full_img_list.append(img_path.replace('hri_app/static/', ''))
        full_id_list.append(img_id)
        piece_detail_list.append(piece_detail_with_id)
    return full_img_list, full_id_list, piece_detail_list


def split_to_pieces(img_path, img_id, row=4, col=4, target_size=(256, 256)):
    im = Image.open(img_path)
    out_dir = 'hri_app/static/puzzles/' + str(img_id)
    os.makedirs(out_dir, exist_ok=True)

    im = im.resize(target_size)
    w, h = im.size
    piece_w = w // row
    piece_h = h // col

    saved_paths = []
    for r in range(row):
        for c in range(col):
            left = c * piece_w
            upper = r * piece_h
            right = left + piece_w
            lower = upper + piece_h
            box = (left, upper, right, lower)

            tile = im.crop(box)
            fname = f"piece_{r}_{c}.png"
            out_path = os.path.join(out_dir, fname)
            tile.save(out_path)
            saved_paths.append(out_path)

    return saved_paths
