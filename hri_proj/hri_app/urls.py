from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('exit/', views.clear_and_exit, name='clear_and_exit'),
    path('mode_selection/', views.mode_seletion, name='mode_selection'),
    path('form_team_compete/', views.form_team_compete, name='form_team_compete'),
    path('form_team_collab_multi/', views.form_team_collaborative_multi, name='form_team_collaborative_multi'),
    path('form_team_collab_two/', views.form_team_collaborative_two, name='form_team_collaborative_two'),
    path('form_team_collab_single/', views.form_team_collaborative_single, name='form_team_collaborative_single'),
    path('puzzle_settings/', views.puzzle_settings, name='puzzle_settings'),
    path('instruction/', views.instruction, name='instruction'),
    path('solve_compete/', views.solve_compete, name='solve_compete'),
    path('solve_collab/', views.solve_collab, name='solve_collab'),
    path('save_personal_record_detail/', views.save_personal_record_detail, name='save_personal_record_detail'),
    path('save_personal_record_general/', views.save_personal_record_general, name='save_personal_record_general'),
    path('manual_rating/', views.manual_rating, name='manual_rating'),
    path('submit_ratings/', views.submit_ratings, name='submit_ratings'),
    path('ai_rating/', views.ai_rating, name='ai_rating'),
    path('view_history/', views.view_history, name='view_history'),
    path('new_puzzle/', views.new_puzzle, name='new_puzzle'),
    path('change_mode/', views.change_mode, name='change_mode'),
]

