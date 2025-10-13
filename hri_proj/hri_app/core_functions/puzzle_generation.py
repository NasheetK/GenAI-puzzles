import numpy as np
import uuid
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
    if mode == 'competitive':
        img_amount = int(np.floor(difficulty_value))
    else:
        img_amount = max(int(np.floor(len(players) * difficulty_value / 2)), 1) # at least one puzzle
    full_img_list = []
    full_id_list = []
    piece_detail_list = []
    for i in range(img_amount):
        img_path = create_single_img(puzzle_config)
        img_id = uuid.uuid4().int
        piece_detail = split_to_pieces(img_path, piece_count=16)
        full_img_list.append(img_path)
        full_id_list.append(img_id)
        piece_detail_list.append(piece_detail)
    return full_img_list, full_id_list, piece_detail_list

def split_to_pieces(img_path, piece_count=16):
    return ["static/imgs/assignment1_img_sub1.png", "static/imgs/assignment1_img_sub2.png"]