from PIL import Image
import numpy as np
import uuid
import os

from .image_generation import *


def create_puzzle(puzzle_config, with_ai):
    mode = puzzle_config['mode']
    players = puzzle_config['players']

    # if mode == 'competitive':
    #     img_amount = int(np.floor(difficulty_value))
    # else:
    #     img_amount = max(int(np.floor(len(players) * difficulty_value / 2)), 1) # at least one puzzle
    # img_amount = 2

    img_amount, total_time = get_amount_and_time(mode, len(players), puzzle_config['difficulty'], with_ai)
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
    return full_img_list, full_id_list, piece_detail_list, total_time


def get_amount_and_time(mode, num_players, difficulty_level, with_ai):
    difficulty_mapping = {
        'Beginner': [1, 3], # puzzle_amount, time_limit
        'Easy': [2, 5],
        'Medium': [3, 7],
        'Hard': [4, 8],
        'Expert': [5, 10],
        'Demo': [4, 2],
    }

    results = difficulty_mapping.get(difficulty_level, [4, 2])

    if mode == "competitive":
        return results[0], results[1]
    else: # collaborative
        if num_players == 1 and not with_ai:
            return results[0], results[1]

        if num_players == 1 and with_ai:
            return results[0], results[1] * 0.75

        if not with_ai:
            scaling = num_players // 2 * 0.1
            return results[0], results[1] * (1 - scaling)
        else:
            scaling = num_players // 2
            # 1 - (0.25 / scaling)
            return results[0], results[1] * (1 - (0.25 / scaling))


def split_to_pieces(img_path, img_id, grid=4, target_size=(256, 256)):
    im = Image.open(img_path)
    out_dir = 'hri_app/static/puzzles/' + str(img_id)
    os.makedirs(out_dir, exist_ok=True)

    im = im.resize(target_size)
    w, h = im.size
    piece_w = w // grid
    piece_h = h // grid

    saved_paths = []
    for r in range(grid):
        for c in range(grid):
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
