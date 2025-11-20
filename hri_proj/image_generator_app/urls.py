from django.urls import path
from .views import generate_puzzles_view

app_name = "image_generator_app"

urlpatterns = [
    path("generate-puzzles/", generate_puzzles_view, name="generate_puzzles"),
]
