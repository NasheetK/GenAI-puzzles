# hri_proj/image_generator_app/views.py
import time
import threading
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .forms import PuzzlePromptForm
from .ai_generator import generate_puzzle_images

# Module-level progress storage (thread-safe for reading, single writer per progress_id)
_progress_store = {}
_progress_lock = threading.Lock()

def generate_puzzles_view(request):
    image_urls = None

    if request.method == "POST":
        form = PuzzlePromptForm(request.POST)
        if form.is_valid():
            character = form.cleaned_data["character"]
            activity = form.cleaned_data["activity"]
            device = form.cleaned_data["device"]

            # Initialize progress tracking
            progress_id = f"progress_{int(time.time() * 1000)}"
            start_time = time.time()
            
            with _progress_lock:
                _progress_store[progress_id] = {
                    'status': 'starting',
                    'stage': 'Initializing...',
                    'progress': 0,
                    'total_steps': 100,
                    'start_time': start_time,
                    'elapsed_time': 0,
                    'estimated_remaining': 0,
                    'estimated_completion': 0,
                }
            
            # Store progress_id in session for retrieval
            request.session['last_progress_id'] = progress_id
            request.session.save()
            
            # Run generation in a separate thread to avoid blocking
            def generate_in_thread():
                try:
                    # Update progress callback function
                    def update_progress(stage, progress, total_steps=100):
                        elapsed = time.time() - start_time
                        # Estimate remaining time based on progress
                        if progress > 0:
                            estimated_total = elapsed / (progress / total_steps)
                            estimated_remaining = max(0, estimated_total - elapsed)
                            estimated_completion = time.time() + estimated_remaining
                        else:
                            estimated_remaining = 0
                            estimated_completion = 0
                        
                        with _progress_lock:
                            _progress_store[progress_id] = {
                                'status': 'running',
                                'stage': stage,
                                'progress': progress,
                                'total_steps': total_steps,
                                'start_time': start_time,
                                'elapsed_time': elapsed,
                                'estimated_remaining': estimated_remaining,
                                'estimated_completion': estimated_completion,
                            }

                    paths = generate_puzzle_images(
                        character, activity, num_images=5, device=device,
                        progress_callback=update_progress
                    )

                    # Convert file paths to URLs
                    image_urls_list = []
                    static_dir = Path(settings.BASE_DIR) / "hri_app" / "static"
                    for p in paths:
                        try:
                            rel_path = p.relative_to(static_dir)
                            url_path = str(rel_path).replace('\\', '/')
                            url = settings.STATIC_URL + url_path
                            image_urls_list.append(url)
                        except ValueError:
                            path_str = str(p)
                            if 'static' in path_str:
                                parts = path_str.split('static')
                                if len(parts) > 1:
                                    rel = parts[1].replace('\\', '/').lstrip('/')
                                    url = settings.STATIC_URL + rel
                                    image_urls_list.append(url)

                    # Mark as complete
                    with _progress_lock:
                        _progress_store[progress_id] = {
                            'status': 'completed',
                            'stage': 'Complete!',
                            'progress': 100,
                            'total_steps': 100,
                            'start_time': start_time,
                            'elapsed_time': time.time() - start_time,
                            'estimated_remaining': 0,
                            'estimated_completion': time.time(),
                            'image_urls': image_urls_list,
                        }
                except Exception as e:
                    with _progress_lock:
                        _progress_store[progress_id] = {
                            'status': 'error',
                            'stage': f'Error: {str(e)}',
                            'progress': 0,
                            'total_steps': 100,
                            'start_time': start_time,
                            'elapsed_time': time.time() - start_time,
                            'estimated_remaining': 0,
                            'estimated_completion': 0,
                        }

            thread = threading.Thread(target=generate_in_thread)
            thread.daemon = True
            thread.start()

            # Return the progress ID to the client
            from .forms import is_cuda_available
            cuda_available = is_cuda_available()
            return render(
                request,
                "generate_puzzles.html",
                {
                    "form": form,
                    "image_urls": None,
                    "cuda_available": cuda_available,
                    "progress_id": progress_id,
                },
            )
    else:
        form = PuzzlePromptForm()
        # Check if there's a completed progress with images
        image_urls = None
        last_progress_id = request.session.get('last_progress_id')
        if last_progress_id:
            with _progress_lock:
                if last_progress_id in _progress_store:
                    progress_data = _progress_store[last_progress_id]
                    if progress_data.get('status') == 'completed' and 'image_urls' in progress_data:
                        image_urls = progress_data['image_urls']

    from .forms import is_cuda_available
    cuda_available = is_cuda_available()
    
    return render(
        request,
        "generate_puzzles.html",
        {"form": form, "image_urls": image_urls, "cuda_available": cuda_available},
    )


@csrf_exempt
def check_progress(request, progress_id):
    """Endpoint to check generation progress"""
    with _progress_lock:
        if progress_id in _progress_store:
            progress_data = _progress_store[progress_id].copy()
            # Always update elapsed_time based on current time and start_time
            if 'start_time' in progress_data:
                current_elapsed = time.time() - progress_data['start_time']
                progress_data['elapsed_time'] = current_elapsed
                # Recalculate estimates if still running
                if progress_data.get('status') in ('running', 'starting') and progress_data.get('progress', 0) > 0:
                    progress = progress_data.get('progress', 0)
                    total_steps = progress_data.get('total_steps', 100)
                    if progress > 0:
                        estimated_total = current_elapsed / (progress / total_steps)
                        progress_data['estimated_remaining'] = max(0, estimated_total - current_elapsed)
                        progress_data['estimated_completion'] = time.time() + progress_data['estimated_remaining']
            
            # Include image_urls only when completed
            if progress_data.get('status') == 'completed' and 'image_urls' in progress_data:
                # Keep image_urls for completion
                pass
            elif 'image_urls' in progress_data:
                # Don't send image_urls in progress updates
                progress_data.pop('image_urls')
            return JsonResponse(progress_data)
        else:
            return JsonResponse({'status': 'not_found', 'message': 'Progress ID not found'})

# Create your views here.
