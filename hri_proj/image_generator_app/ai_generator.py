import os
import re
from pathlib import Path
from typing import List, Optional

import torch
from PIL import Image
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    EulerDiscreteScheduler,
)
from django.conf import settings

_BASE_PIPE = None
_REFINER_PIPE = None

# ---------- PATH HELPERS ----------

def _normalize_token(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", s)


def _static_img_dir() -> Path:
    # BASE_DIR is hri_proj/, so hri_app/static/imgs is directly under it
    return Path(settings.BASE_DIR) / "hri_app" / "static" / "imgs"


def _next_index(character: str, activity: str) -> int:
    img_dir = _static_img_dir()
    img_dir.mkdir(parents=True, exist_ok=True)

    char_tok = _normalize_token(character)
    act_tok = _normalize_token(activity)
    pattern = re.compile(
        rf"^{char_tok}_{act_tok}_(\d{{5}})\.(png|jpg|jpeg)$", re.IGNORECASE
    )

    max_idx = 0
    for fname in os.listdir(img_dir):
        m = pattern.match(fname)
        if m:
            idx = int(m.group(1))
            max_idx = max(max_idx, idx)

    return max_idx + 1


def _load_overlay_image(filename: str) -> Optional[Image.Image]:
    """Load an overlay image from the static/imgs directory."""
    img_dir = _static_img_dir()
    overlay_path = img_dir / filename.lower()
    
    if overlay_path.exists():
        try:
            overlay = Image.open(overlay_path)
            # Convert to RGBA if not already (for transparency support)
            if overlay.mode != 'RGBA':
                overlay = overlay.convert('RGBA')
            return overlay
        except Exception as e:
            print(f"Warning: Could not load overlay image {filename}: {e}")
            return None
    return None


def _superimpose_overlays(base_image: Image.Image, character: str, activity: str) -> Image.Image:
    """
    Superimpose character and activity overlay images on the base generated image.
    
    Args:
        base_image: The generated image from the AI pipeline
        character: Character name (e.g., "Cat", "Bear")
        activity: Activity name (e.g., "School", "Forest")
    
    Returns:
        The composite image with overlays applied
    """
    # Convert base image to RGBA if needed
    if base_image.mode != 'RGBA':
        composite = base_image.convert('RGBA')
    else:
        composite = base_image.copy()
    
    width, height = composite.size
    
    # Load overlay images
    char_overlay = _load_overlay_image(f"{character.lower()}.png")
    activity_overlay = _load_overlay_image(f"{activity.lower()}.png")
    
    # Superimpose character overlay (if available)
    if char_overlay:
        # Resize overlay to match base image size (or scale proportionally)
        char_overlay_resized = char_overlay.resize((width, height), Image.Resampling.LANCZOS)
        # Composite with alpha blending
        composite = Image.alpha_composite(composite, char_overlay_resized)
    
    # Superimpose activity overlay (if available)
    if activity_overlay:
        # Resize overlay to match base image size (or scale proportionally)
        activity_overlay_resized = activity_overlay.resize((width, height), Image.Resampling.LANCZOS)
        # Composite with alpha blending
        composite = Image.alpha_composite(composite, activity_overlay_resized)
    
    # Convert back to RGB for saving (if no transparency needed in final output)
    return composite.convert('RGB')

# ---------- PIPELINE LOADERS (BASE + REFINER) ----------

def _load_base_pipe():
    global _BASE_PIPE
    if _BASE_PIPE is not None:
        return _BASE_PIPE

    #device = "cuda" if torch.cuda.is_available() else "cpu"
    device = "cpu"
    base_model_id = getattr(
        settings, "SDXL_BASE_ID", "stabilityai/stable-diffusion-xl-base-1.0"
    )

    scheduler = EulerDiscreteScheduler.from_pretrained(
        base_model_id, subfolder="scheduler"
    )
    pipe = StableDiffusionXLPipeline.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
        scheduler=scheduler,
    )

    # LoRA from workflow: StoryBookRedmond-KidsRedmAF.safetensors with strength 0.6
    if hasattr(settings, "PUZZLE_LORA_PATH") and os.path.exists(settings.PUZZLE_LORA_PATH):
        pipe.load_lora_weights(settings.PUZZLE_LORA_PATH)
        try:
            pipe.set_adapters("default", weight=0.6)
        except Exception:
            pass

    pipe.to(device)
    pipe.enable_attention_slicing()
    _BASE_PIPE = pipe
    return pipe



def _load_refiner_pipe():
    global _REFINER_PIPE
    if _REFINER_PIPE is not None:
        return _REFINER_PIPE

    #device = "cuda" if torch.cuda.is_available() else "cpu"
    device = "cpu"
    refiner_model_id = getattr(
        settings, "SDXL_REFINER_ID", "stabilityai/stable-diffusion-xl-refiner-1.0"
    )

    scheduler = EulerDiscreteScheduler.from_pretrained(
        refiner_model_id, subfolder="scheduler"
    )
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        refiner_model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        use_safetensors=True,
        scheduler=scheduler,
    )
    pipe.to(device)
    pipe.enable_attention_slicing()
    _REFINER_PIPE = pipe
    return pipe

# ---------- MAIN GENERATION FUNCTION ----------

def generate_puzzle_images(
    character: str,
    activity: str,
    num_images: int = 5,
) -> List[Path]:
    """
    Reimplements your ComfyUI SDXL Base + Refiner workflow:

    - 768 x 768 resolution (EmptyLatentImage: [768, 768, 10])
    - 25 steps (steps PrimitiveNode)
    - Euler sampler, "normal" scheduler
    - CFG = 8
    - Split at 20 / 25 steps -> denoising_end/start = 0.8
    - LoRA StoryBookRedmond-KidsRedmAF at strength ~0.6
    - Negative prompt: "text, watermark"
    """
    base_pipe = _load_base_pipe()
    refiner_pipe = _load_refiner_pipe()

    device = base_pipe._execution_device if hasattr(base_pipe, "_execution_device") else base_pipe.device

    height = 768
    width = 768
    total_steps = 25
    cfg_scale = 8.0

    # 20/25 = 0.8 switch point (matches start_at_step / end_at_step)
    switch_frac = 20 / 25

    positive_prompt = (
        f"A cute cartoon {character.lower()}, at the {activity.lower()}, bright pastel colors, "
        "simple shapes, children’s book illustration style, soft lighting, cheerful atmosphere, "
        "friendly expression, for kids aged 6 to 8, high quality, clean outlines"
    )
    negative_prompt = "text, watermark"

    # Repeat prompt num_images times (batch = 5 like EmptyLatentImage)
    prompts = [positive_prompt] * num_images
    neg_prompts = [negative_prompt] * num_images

    generator = torch.Generator(device=device).manual_seed(torch.seed())

    # ---- BASE: sample latents up to 80% denoising (like base KSampler end_at_step = 20)
    base_out = base_pipe(
        prompt=prompts,
        negative_prompt=neg_prompts,
        num_inference_steps=total_steps,
        guidance_scale=cfg_scale,
        height=height,
        width=width,
        denoising_end=switch_frac,
        output_type="latent",
        generator=generator,
    )

    latents = base_out.images  # latent tensor batch

    # ---- REFINER: continue from 80% to 100% (start_at_step = 20)
    refined = refiner_pipe(
        prompt=prompts,
        negative_prompt=neg_prompts,
        num_inference_steps=total_steps,
        guidance_scale=cfg_scale,
        denoising_start=switch_frac,
        image=latents,
        generator=generator,
    )

    images = refined.images

    # ---- Save to hri_app/static/imgs with incremental filenames
    img_dir = _static_img_dir()
    img_dir.mkdir(parents=True, exist_ok=True)

    char_tok = _normalize_token(character)
    act_tok = _normalize_token(activity)

    current_idx = _next_index(character, activity)
    saved_paths: List[Path] = []

    for img in images:
        # Ensure img is a PIL Image (diffusers typically returns PIL Images)
        if not isinstance(img, Image.Image):
            # If it's a tensor or numpy array, convert to PIL Image
            import numpy as np
            if hasattr(img, 'cpu'):
                img_array = img.cpu().numpy()
            else:
                img_array = np.array(img)
            # Normalize to 0-255 range if needed
            if img_array.max() <= 1.0:
                img_array = (img_array * 255).astype(np.uint8)
            img = Image.fromarray(img_array)
        
        # Superimpose character and activity overlays
        img_with_overlays = _superimpose_overlays(img, character, activity)
        
        # Save the final composite image
        fname = f"{char_tok}_{act_tok}_{current_idx:05d}.png"
        path = img_dir / fname
        img_with_overlays.save(path)
        saved_paths.append(path)
        current_idx += 1

    return saved_paths
