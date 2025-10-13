from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .core_functions.puzzle_generation import *
from .core_functions.ai_rating import *
from .models import *

# Create your views here.
def home(request):
    return render(request, 'home_page.html')

@csrf_exempt  # Disable CSRF for API endpoints (for simplicity)
def clear_and_exit(request):
    request.session.clear()
    return render(request, 'home_page.html')

def mode_seletion(request):
    return render(request, 'mode_selection.html')

@csrf_exempt
def form_team_compete(request):
    if request.method == "POST":
        players = [v for k, v in request.POST.items() if k.startswith("member_") and v.strip()]
        request.session['players'] = players
        request.session['mode'] = 'competitive'
        return redirect('puzzle_settings')
    return render(request, 'form_team_competitive.html')

def form_team_collaborative_two(request):
    return render(request, 'form_team_collaborative.html', {'count': 2, 'add_flag': False})

@csrf_exempt
def form_team_collaborative_multi(request):
    if request.method == "POST":
        players = [v for k, v in request.POST.items() if k.startswith("member_") and v.strip()]
        request.session['players'] = players
        request.session['mode'] = 'collaborative'
        return redirect('puzzle_settings')
    return render(request, 'form_team_collaborative.html', {'count': 3, 'add_flag': True})

@csrf_exempt
def puzzle_settings(request):
    difficulties = ['Beginner', 'Easy', 'Medium', 'Hard', 'Expert']
    characters = ['Rabbit', 'Cat', 'Dog', 'Tiger']
    activities = ['School', 'Playground', 'Forest']
    bg_colors = ['Red', 'Green', 'Blue', 'Yellow']

    players = request.session.get('players', [])
    mode = request.session.get('mode', '')

    if request.method == "POST":

        difficulty = request.POST.get('difficulty')
        character = request.POST.get('character')
        activity = request.POST.get('activity')
        bg_color = request.POST.get('bg_color')

        # print(players)
        puzzle_config = {
            'difficulty': difficulty,
            'character': character,
            'activity': activity,
            'bg_color': bg_color,
            'players': players,
            'mode': mode
        }
        full_img_list, full_id_list, piece_detail_list = create_puzzle(puzzle_config)

        # save to database
        for img_path, img_id, pieces in zip(full_img_list, full_id_list, piece_detail_list):
            puzzle_img = PuzzleImage.objects.create(
                img_id=img_id,
                img_path=img_path
            )
            for i, piece in enumerate(pieces):
                PuzzlePiece.objects.create(
                    puzzle_image=puzzle_img,
                    piece_number=i,
                    piece_path=piece
                )

        request.session['full_img_list'] = full_img_list
        request.session['full_id_list'] = full_id_list
        request.session['piece_detail_list'] = piece_detail_list
        return redirect('instruction')

    return render(request, 'puzzle_settings.html', {
        'difficulties': difficulties,
        'characters': characters,
        'activities': activities,
        'bg_colors': bg_colors
    })

@csrf_exempt
def instruction(request):
    players = request.session.get('players', [])
    mode = request.session.get('mode', '')
    full_img_list = request.session.get('full_img_list', [])
    count = len(full_img_list)

    message = 'Hi'
    for name in players:
        message += ' ' + name
    message += ', \n'
    info = "You will be solving " + str(count) + " puzzles in " + mode + ' mode in 5 minutes.'
    message += info

    if request.method == "POST":
        if mode == 'competitive':
            return redirect('solve_compete')
        else:
            return redirect('solve_collab')

    return render(request, 'game_instruction.html', {'message': message})

@csrf_exempt
def solve_collab(request):
    tolerance = 10 # tolerance for slight differences between drop location and target location
    if request.method == "POST":
        piece_id = request.POST.get("piece_id")
        x = float(request.POST.get("x", 0))
        y = float(request.POST.get("y", 0))
        target_left = float(request.POST.get("target_left", 0))
        target_top = float(request.POST.get("target_top", 0))
        target_right = float(request.POST.get("target_right", 0))
        target_bottom = float(request.POST.get("target_bottom", 0))

        print(target_left, target_top, target_right, target_bottom)
        width = abs(target_right - target_left)
        height = abs(target_bottom - target_top)
        # print(piece_id)
        if piece_id == 'item_1':
            target_x = target_left
            target_y = target_top
            print(x, y, target_x, target_y)
            success = (abs(x - target_x) <= tolerance and abs(y - target_y) <= tolerance)
        elif piece_id == 'item_2':
            target_x = target_left + width / 2.0
            target_y = target_top
            print(x, y, target_x, target_y)
            success = (abs(x - target_x) <= tolerance) and (abs(y - target_y) <= tolerance)
        else:
            target_x = 0
            target_y = 0
            success = False

        # record to log and return the verification results
        PieceDragLog.objects.create(piece_id=piece_id, x=x, y=y, timestamp=timezone.now(), success=success)
        # print(success, target_x, target_y)
        return JsonResponse({
            "success": success,
            "correct_x": target_x,
            "correct_y": target_y,
        })

    return render(request, "solve_puzzle_collaborative.html")

@csrf_exempt
def solve_compete(request):
    assert NotImplementedError

def manual_rating(request):
    players = request.session.get('players', [])
    if len(players) > 2:
        return render(request, "manual_rating_multi_players.html")
    else:
        return render(request, "manual_rating_two_players.html")
