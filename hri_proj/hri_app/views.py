from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .core_functions.puzzle_generation import *
from .core_functions.ai_rating import *
from .models import *

from datetime import datetime
import json
# Create your views here.


def home(request):
    request.session.clear()
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
    mode = request.session.get('mode', 'collaborative')

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
    mode = request.session.get('mode', 'collaborative')
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

    players = request.session.get('players', [])
    mode = request.session.get('mode', 'collaborative')
    difficulty = request.POST.get('difficulty')
    character = request.POST.get('character')
    activity = request.POST.get('activity')
    bg_color = request.POST.get('bg_color')

    puzzle_config = {
        'difficulty': difficulty,
        'character': character,
        'activity': activity,
        'bg_color': bg_color,
        'players': players,
        'mode': mode
    }

    if request.method == "POST":

        piece_full_id = request.POST.get("piece_id")
        piece_id = int(piece_full_id.split('_')[1])
        x = float(request.POST.get("x", 0))
        y = float(request.POST.get("y", 0))
        target_left = float(request.POST.get("target_left", 0))
        target_top = float(request.POST.get("target_top", 0))
        target_right = float(request.POST.get("target_right", 0))
        target_bottom = float(request.POST.get("target_bottom", 0))
        print(piece_full_id, target_left, target_top, target_right, target_bottom)
        width = abs(target_right - target_left)
        height = abs(target_bottom - target_top)
        grid_width = width / 4
        grid_height = height / 4

        target_row = piece_id // 4
        target_col = np.mod(piece_id, 4)
        print(target_row, target_col, grid_height, grid_width)

        target_x = target_col * grid_width + target_left
        target_y = target_row * grid_height + target_top
        success = (abs(x - target_x) <= tolerance and abs(y - target_y) <= tolerance)
        print(x, y, target_x, target_y, success)

        # record to log and return the verification results
        PieceDragLog.objects.create(piece_id=piece_full_id, x=x, y=y, timestamp=timezone.now(), success=success)

        if success:
            full_info_list = request.session.get('full_info_list', [])
            players = request.session.get('players', [])
            # players = ['test_name_1', 'test_name_2']
            index = int(request.POST.get("index"))
            action = 'piece_matched'
            # print(full_info_list)
            puzzle_id = full_info_list[index][1]  # get puzzle_id

            for name in players:
                PersonalRecordDetail.objects.create(
                    name=name,
                    puzzle_id=puzzle_id,
                    action=action,
                    timestamp=timezone.now()
                )

        return JsonResponse({
            "success": bool(success),
            "correct_x": float(target_x),
            "correct_y": float(target_y),
        })

    full_img_list, full_id_list, piece_detail_list = create_puzzle(puzzle_config)
    full_info_list = list(zip(full_img_list, full_id_list, piece_detail_list))
    request.session['full_info_list'] = full_info_list
    puzzle_config['full_info_list'] = full_info_list
    # print(full_info_list)
    return render(request, "solve_puzzle_collaborative.html", {'puzzle_config': puzzle_config})


@csrf_exempt
def save_personal_record_detail(request):
    if request.method == "POST":
        full_info_list = request.session.get('full_info_list', [])
        players = request.session.get('players', [])
        # players = ['test_name_1', 'test_name_2']
        index = int(request.POST.get("index"))
        action = request.POST.get("action")
        puzzle_id = full_info_list[index][1] # get puzzle_id

        for name in players:
            PersonalRecordDetail.objects.create(
                name=name,
                puzzle_id=puzzle_id,
                action=action,
                timestamp=timezone.now()
            )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'invalid method'})


@csrf_exempt
def save_personal_record_general(request):
    assert NotImplementedError


@csrf_exempt
def solve_compete(request):
    assert NotImplementedError


def manual_rating(request):
    players = request.session.get('players', [])
    mode = request.session.get('mode', 'collaborative')
    # print(players)
    if len(players) > 2:
        return render(request, "manual_rating_multi_players.html", {'players': players, 'mode': mode})
    else:
        return render(request, "manual_rating_two_players.html", {'players': players, 'mode': mode})


def get_records_from_db(name, puzzle_id_list):
    records_all = []
    time_start = 0
    time_end = 0
    for puzzle_id in puzzle_id_list:
        records_refined = []
        records_raw = PersonalRecordDetail.objects.filter(
            name=name,
            puzzle_id=puzzle_id
        ).order_by('timestamp')
        for r in records_raw:
            cur_time = int(r.timestamp.timestamp() * 1000)
            if time_start == 0:
                time_start = cur_time
                time_end = cur_time
            elif time_end < cur_time:
                time_end = cur_time
            records_refined.append({
                'detail_id': r.detail_id,
                'name': r.name,
                'puzzle_id': r.puzzle_id,
                'action': r.action,
                'timestamp': cur_time  # 13-digit timestamp
            })
        records_all.append(records_refined)
        time_start = datetime.fromtimestamp(time_start / 1000).strftime("%Y-%m-%d %H:%M:%S")
        time_end = datetime.fromtimestamp(time_end / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return records_all, time_start, time_end


def get_manual_ratings_by_name(data, name):
    for record in data:
        if record['name'] == name:
            return record['ratings']
    return [0, 0]


@csrf_exempt
def submit_ratings(request):
    if request.method == "POST":
        ai_score = request.session.get('ai_task_score', {})
        print(ai_score)
        if ai_score: # already predicted in previous button clicks
            return JsonResponse({'status': 'ok'})
        request.session['ai_task_score'] = {}
        players = request.session.get('players', [])
        print(players)
        data = json.loads(request.body)
        print(data)
        mode = request.session.get('mode', 'collaborative')
        ai_task_score = 0
        time_start, time_end = 0, 0
        if mode == 'collaborative':
            full_info_list = request.session.get('full_info_list', [])
            puzzle_id_list = [x[1] for x in full_info_list]
            related_records, time_start, time_end = get_records_from_db(players[0], puzzle_id_list)
            ai_task_score = get_ai_score(len(players), len(puzzle_id_list), related_records)
        for name in players:
            self_feeling_score, self_task_score = get_manual_ratings_by_name(data, name)
            team_member = ','.join(players)
            difficulty = request.session.get('difficulty', 'Beginner')
            character = request.session.get('character', 'Rabbit')
            activity = request.session.get('activity', 'School')
            bg_color = request.session.get('bg_color', 'Red')
            full_info_list = request.session.get('full_info_list', [])
            puzzle_id_list = [x[1] for x in full_info_list]
            if mode == 'competitive':
                related_records, time_start, time_end = get_records_from_db(name, puzzle_id_list)
                ai_task_score = get_ai_score(1, len(puzzle_id_list), related_records)

            PersonalRecordGeneral.objects.create(
                name=name,
                team_member=team_member,
                game_mode=mode,
                difficulty=difficulty,
                character=character,
                activity=activity,
                bg_color=bg_color,
                puzzle_amount=len(puzzle_id_list),
                time_start=time_start,
                time_end=time_end,
                self_feeling_score=self_feeling_score,
                self_task_score=self_task_score,
                ai_task_score=ai_task_score
            )
            print('submit general record')
            request.session['ai_task_score'][name] = ai_task_score
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'invalid method'})


@csrf_exempt
def ai_rating(request):
    ai_task_score = request.session.get('ai_task_score', {})
    players = request.session.get('players', [])
    mode = request.session.get('mode', 'collaborative')
    message = 'Hi'
    for name in players:
        message += ' ' + name
    message += ', \n'

    if mode == 'collaborative':
        info = 'Your final task score given by AI is: ' + str(ai_task_score[players[0]]) + '. \nCongratulations!'
    else:
        info = 'Your final task score given by AI is as below. \n'
        for name in players:
            info += name + ': ' + str(ai_task_score[name]) + '\n'
        info += 'Congratulations!'

    message += info

    return render(request, 'ai_rating.html', {'message': message})


@csrf_exempt
def view_history(request):
    players = request.session.get('players', [])
    player_records = {}
    for name in players:
        records = PersonalRecordGeneral.objects.filter(
            name=name
        ).order_by('time_start')
        records_refined = []
        for r in records:
            records_refined.append({
                'record_id': r.record_id,
                'name': r.name,
                'team_member': r.team_member,
                'game_mode': r.game_mode,
                'difficulty': r.difficulty,
                'puzzle_amount': r.puzzle_amount,
                'time_start': r.time_start.strftime("%Y-%m-%d %H:%M:%S"),
                'time_end': r.time_end.strftime("%Y-%m-%d %H:%M:%S"),
                'self_feeling_score': r.self_feeling_score,
                'self_task_score': r.self_task_score,
                'ai_task_score': r.ai_task_score,
            })
        player_records[name] = records_refined

    context = {
        'players': players,
        'player_records': json.dumps(player_records)}
    print(context)
    return render(request, 'view_history.html', context)


@csrf_exempt
def new_puzzle(request):
    return redirect('puzzle_settings')


@csrf_exempt
def change_mode(request):
    mode = request.session.get('mode', 'collaborative')
    if mode == 'collaborative':
        request.session['mode'] = 'competitive'
    elif mode == 'competitive':
        request.session['mode'] = 'collaborative'
    return redirect('puzzle_settings')

