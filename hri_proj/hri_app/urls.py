from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('exit/', views.clear_and_exit, name='clear_and_exit'),
    path('mode_selection/', views.mode_seletion, name='mode_selection'),
    path('form_team_compete/', views.form_team_compete, name='form_team_compete'),
    path('form_team_collab_multi/', views.form_team_collaborative_multi, name='form_team_collaborative_multi'),
    path('form_team_collab_two/', views.form_team_collaborative_two, name='form_team_collaborative_two'),
    path('puzzle_settings/', views.puzzle_settings, name='puzzle_settings'),
]
