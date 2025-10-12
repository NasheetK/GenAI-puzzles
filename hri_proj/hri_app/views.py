from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
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
    difficulties = ['Easy', 'Medium', 'Hard']
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

        print(players)
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
        if mode == 'competitive':
            return render(request, 'solve_puzzle_competitive.html')
        else:
            return render(request, 'solve_puzzle_collaborative.html')

    return render(request, 'puzzle_settings.html', {
        'difficulties': difficulties,
        'characters': characters,
        'activities': activities,
        'bg_colors': bg_colors
    })
