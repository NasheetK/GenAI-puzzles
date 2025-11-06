from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('exit/', views.clear_and_exit, name='clear_and_exit'),
    path('select_players', views.select_players, name='select_players'),
    path('mode_selection/', views.mode_seletion, name='mode_selection'),
    path('form_team_compete/', views.form_team_compete, name='form_team_compete'),
    path('form_team_collab_multi/', views.form_team_collaborative_multi, name='form_team_collaborative_multi'),
    path('form_team_collab_two/', views.form_team_collaborative_two, name='form_team_collaborative_two'),
    path('form_team_collab_single/', views.form_team_collaborative_single, name='form_team_collaborative_single'),
    path('puzzle_settings/', views.puzzle_settings, name='puzzle_settings'),
    path('instruction/', views.instruction, name='instruction'),
    path('solve_compete/', views.solve_compete, name='solve_compete'),
    path('solve_collab/', views.solve_collab, name='solve_collab'),
    path('solve_collab_ai/', views.solve_collab_ai, name='solve_collab_ai'),
    path('save_personal_record_detail_collab/', views.save_personal_record_detail_collab, name='save_personal_record_detail_collab'),
    path('save_personal_record_detail_compete/', views.save_personal_record_detail_compete, name='save_personal_record_detail_compete'),
    path('manual_rating/', views.manual_rating, name='manual_rating'),
    path('submit_ratings/', views.submit_ratings, name='submit_ratings'),
    path('ai_rating/', views.ai_rating, name='ai_rating'),
    path('get_scoring_board/', views.get_scoring_board, name='get_scoring_board'),
    path('view_history/', views.view_history, name='view_history'),
    path('new_puzzle/', views.new_puzzle, name='new_puzzle'),
    path('change_mode/', views.change_mode, name='change_mode'),
]

