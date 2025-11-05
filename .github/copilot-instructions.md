## Quick orientation

This is a small Django app used for a Social Robotics course project. Key places to look:

- `hri_proj/hri_app/views.py` — primary request handlers and session usage. Most UX flows (create puzzle → solve → rating/history) start here.
- `hri_proj/hri_app/models.py` — persistent schema: `PuzzleImage`, `PuzzlePiece`, `PieceDragLog`, `PersonalRecordDetail`, `PersonalRecordGeneral`.
- `hri_proj/hri_app/core_functions/` — helper logic:
  - `puzzle_generation.py` — `create_puzzle()` and `split_to_pieces()` (creates images, slices into 4x4 by default).
  - `image_generation.py` — currently returns a static image; extend this to use external image sources.
  - `ai_rating.py` — AI scoring hook; currently stubbed (`get_ai_score` returns constant 3).

## Big-picture data flow (what to change when you touch X)

- User picks settings → `views.puzzle_settings` calls `create_puzzle()` → images are created under `hri_app/static/puzzles/<img_id>/` and `PuzzleImage` / `PuzzlePiece` rows are inserted.
- Session keys used broadly: `players`, `mode`, `full_img_list`, `full_id_list`, `piece_detail_list`, `full_info_list`, `ai_task_score`. Views rely on these being present.
- During gameplay `solve_collab` / `solve_compete` log piece drops to `PieceDragLog` and matched events to `PersonalRecordDetail`.
- Ratings submission (`submit_ratings`) reads `PersonalRecordDetail` and calls `get_ai_score` to compute AI task score and persists `PersonalRecordGeneral`.

## Project-specific conventions and notes for code edits

- Static paths: functions and DB entries intentionally strip the `hri_app/static/` prefix before saving to sessions/DB. When generating or returning paths, keep or adapt this convention consistently (see `puzzle_generation.py` and uses in `views.py`).
- Image slicing: `split_to_pieces(img_path, img_id, row=4, col=4, target_size=(256,256))` — changes to piece layout or tile size should be made here and propagated to front-end positioning math in `views.solve_collab`.
- CSRF: many endpoints use `@csrf_exempt` for simplicity. If you re-enable CSRF, update the front-end fetch/XHR calls accordingly.
- TTS: `pyttsx3` is initialized at module import in `views.py` and targets Windows (`pywin32`, `comtypes` in `requirements.txt`). Run on Windows or adjust TTS if developing on another OS.

## How to run & quick developer setup (Windows-focused)

1. Create a virtual environment and install deps:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Run migrations and start the dev server:

```powershell
python hri_proj\manage.py migrate
python hri_proj\manage.py runserver
```

Notes: this project uses SQLite (db.sqlite3 at `hri_proj/db.sqlite3`). `pyttsx3` + `pywin32` are Windows-specific; if you develop on Linux/macOS, stub or remove TTS initialization in `views.py`.

## Where to implement AI or image improvements

- AI scoring: `hri_proj/hri_app/core_functions/ai_rating.py` — implement `get_ai_score(player_count, puzzle_count, related_records)`; `submit_ratings` in `views.py` calls it.
- Image generation: replace `create_single_img` in `image_generation.py` to pull/generate richer images. Keep returned path format `hri_app/static/...` (or update callsites if you change that contract).

## Testing and debugging tips

- There are no automated tests in the repo yet (`hri_app/tests.py` is available to add tests). For quick manual checks:
  - Use `python hri_proj\manage.py runserver` and exercise flows from `/` in the browser.
  - Inspect generated images at `hri_app/static/puzzles/<img_id>/` and DB rows via the Django admin (enable admin or query via shell).
- To debug front-end drop math, look at `views.solve_collab` — it computes grid cell size and verifies drop success using center coordinates. Any layout change in templates/CSS must be coordinated with this logic.

## Files to reference when editing

- `hri_proj/hri_app/views.py` — main logic and where session keys are used.
- `hri_proj/hri_app/core_functions/puzzle_generation.py` and `image_generation.py` — image creation and piece slicing.
- `hri_proj/hri_app/core_functions/ai_rating.py` — AI scoring entrypoint for implementers.
- `hri_proj/hri_app/models.py` — schema for all persisted records.

## Gotchas / safety checks

- `SECRET_KEY` is checked into `settings.py`. Treat this repo as non-production/demo only (DEBUG=True). If you deploy, rotate secrets and set DEBUG=False.
- Paths assume running from repository root; if you change working directories, update path joins.
- Many endpoints use `csrf_exempt` — be careful when adding state-changing APIs.

If anything here is unclear or you want the instructions to emphasize other workflows (CI, specific local dev shortcuts, or testing harnesses), tell me which areas to expand and I will iterate.
