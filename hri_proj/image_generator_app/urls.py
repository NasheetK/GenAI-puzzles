from django.urls import path
from .views import generate_puzzles_view, check_progress

app_name = "image_generator_app"

urlpatterns = [
    path("generate-puzzles/", generate_puzzles_view, name="generate_puzzles"),
    path("progress/<str:progress_id>/", check_progress, name="check_progress"),
]
