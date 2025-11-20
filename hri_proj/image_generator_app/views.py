# hri_proj/image_generator_app/views.py
from pathlib import Path
from django.shortcuts import render
from django.conf import settings

from .forms import PuzzlePromptForm
from .ai_generator import generate_puzzle_images

def generate_puzzles_view(request):
    image_urls = None

    if request.method == "POST":
        form = PuzzlePromptForm(request.POST)
        if form.is_valid():
            character = form.cleaned_data["character"]
            activity = form.cleaned_data["activity"]

            paths: list[Path] = generate_puzzle_images(character, activity, num_images=5)

            # convert file paths inside static/imgs to URLs under STATIC_URL
            image_urls = []
            static_dir = Path(settings.BASE_DIR) / "hri_app" / "static"
            for p in paths:
                try:
                    # Get relative path from static directory
                    rel_path = p.relative_to(static_dir)
                    # Convert to URL path (use forward slashes)
                    url_path = str(rel_path).replace('\\', '/')
                    url = settings.STATIC_URL + url_path
                    image_urls.append(url)
                except ValueError:
                    # If path is not under static_dir, try fallback method
                    path_str = str(p)
                    if 'static' in path_str:
                        parts = path_str.split('static')
                        if len(parts) > 1:
                            rel = parts[1].replace('\\', '/').lstrip('/')
                            url = settings.STATIC_URL + rel
                            image_urls.append(url)
    else:
        form = PuzzlePromptForm()

    return render(
        request,
        "generate_puzzles.html",
        {"form": form, "image_urls": image_urls},
    )

# Create your views here.
