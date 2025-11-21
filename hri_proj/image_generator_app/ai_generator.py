import os
import re
import time
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

# Optimize performance
if torch.cuda.is_available():
    # Enable CUDA optimizations (similar to ComfyUI)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    # Enable cudaMallocAsync if available (PyTorch 2.0+)
    try:
        torch.cuda.set_per_process_memory_fraction(0.9)  # Use 90% of VRAM
    except Exception:
        pass
else:
    # Use all available CPU cores
    torch.set_num_threads(os.cpu_count() or 4)
    # Enable CPU optimizations
    torch.set_num_interop_threads(os.cpu_count() or 4)

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

def _load_base_pipe(device: str = "cpu"):
    global _BASE_PIPE
    # If device changed, reset the pipe
    if _BASE_PIPE is not None:
        try:
            current_device = str(_BASE_PIPE.device) if hasattr(_BASE_PIPE, 'device') else None
            # Normalize device strings for comparison (cuda:0 -> cuda)
            if current_device:
                current_device = current_device.split(':')[0]
            device_normalized = device.split(':')[0]
            if current_device and current_device != device_normalized:
                _BASE_PIPE = None
        except Exception:
            # If we can't determine device, reset to be safe
            _BASE_PIPE = None
    
    if _BASE_PIPE is not None:
        return _BASE_PIPE

    # Validate device - allow CUDA even with warnings, will fall back if operations fail
    if device == "cuda" and not torch.cuda.is_available():
        print("Warning: CUDA requested but not available. Falling back to CPU.")
        device = "cpu"
    
    base_model_id = getattr(
        settings, "SDXL_BASE_ID", "stabilityai/stable-diffusion-xl-base-1.0"
    )

    scheduler = EulerDiscreteScheduler.from_pretrained(
        base_model_id, subfolder="scheduler"
    )
    
    try:
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

        # Test CUDA first if requested
        if device == "cuda":
            try:
                test_tensor = torch.tensor([1.0], device='cuda')
                test_result = test_tensor * 2
                print(f"[BASE PIPE] CUDA test successful: {test_result.item()}")
                del test_tensor, test_result
                torch.cuda.empty_cache()
                # CUDA works - use CPU offloading for better memory efficiency (like ComfyUI)
                try:
                    pipe.enable_model_cpu_offload()
                    print(f"[BASE PIPE] Enabled CPU offloading (VAE/text encoders on CPU, UNet on GPU)")
                except Exception:
                    # Fallback to standard GPU loading
                    pipe.to(device)
                    print(f"[BASE PIPE] Using standard GPU loading (all models on GPU)")
            except Exception as e:
                error_msg = str(e)
                if "no kernel image" in error_msg.lower() or "compute capability" in error_msg.lower():
                    print(f"[BASE PIPE] CUDA not compatible with this GPU (compute capability mismatch). Using CPU instead.")
                else:
                    print(f"[BASE PIPE] CUDA test failed. Using CPU instead.")
                # CUDA failed, need to reload with float32 for CPU
                device = "cpu"
                _BASE_PIPE = None
                return _load_base_pipe(device)
        else:
            # CPU mode
            try:
                pipe.to(device)
            except Exception as e:
                print(f"[BASE PIPE] Warning: Failed to move pipeline to {device}. Reloading with float32 for CPU.")
                device = "cpu"
                _BASE_PIPE = None
                return _load_base_pipe(device)
        
        pipe.enable_attention_slicing()
        # Additional optimizations for CPU
        if device == "cpu":
            try:
                pipe.enable_attention_slicing(slice_size="max")
            except Exception:
                pass
        _BASE_PIPE = pipe
        return pipe
    except Exception as e:
        # If anything fails and we were trying CUDA, retry with CPU
        if device == "cuda":
            print(f"Error loading pipeline on CUDA ({e}). Retrying with CPU.")
            device = "cpu"
            return _load_base_pipe(device)
        raise



def _load_refiner_pipe(device: str = "cpu"):
    global _REFINER_PIPE
    # If device changed, reset the pipe
    if _REFINER_PIPE is not None:
        try:
            current_device = str(_REFINER_PIPE.device) if hasattr(_REFINER_PIPE, 'device') else None
            # Normalize device strings for comparison (cuda:0 -> cuda)
            if current_device:
                current_device = current_device.split(':')[0]
            device_normalized = device.split(':')[0]
            if current_device and current_device != device_normalized:
                _REFINER_PIPE = None
        except Exception:
            # If we can't determine device, reset to be safe
            _REFINER_PIPE = None
    
    if _REFINER_PIPE is not None:
        return _REFINER_PIPE

    # Validate device - allow CUDA even with warnings, will fall back if operations fail
    if device == "cuda" and not torch.cuda.is_available():
        print("Warning: CUDA requested but not available. Falling back to CPU.")
        device = "cpu"
    
    refiner_model_id = getattr(
        settings, "SDXL_REFINER_ID", "stabilityai/stable-diffusion-xl-refiner-1.0"
    )

    scheduler = EulerDiscreteScheduler.from_pretrained(
        refiner_model_id, subfolder="scheduler"
    )
    
    try:
        pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            refiner_model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            use_safetensors=True,
            scheduler=scheduler,
        )
        
        # Test CUDA first if requested
        if device == "cuda":
            try:
                test_tensor = torch.tensor([1.0], device='cuda')
                test_result = test_tensor * 2
                print(f"[REFINER PIPE] CUDA test successful: {test_result.item()}")
                del test_tensor, test_result
                torch.cuda.empty_cache()
                # CUDA works - use CPU offloading for better memory efficiency (like ComfyUI)
                try:
                    pipe.enable_model_cpu_offload()
                    print(f"[REFINER PIPE] Enabled CPU offloading (VAE/text encoders on CPU, UNet on GPU)")
                except Exception:
                    # Fallback to standard GPU loading
                    pipe.to(device)
                    print(f"[REFINER PIPE] Using standard GPU loading (all models on GPU)")
            except Exception as e:
                error_msg = str(e)
                if "no kernel image" in error_msg.lower() or "compute capability" in error_msg.lower():
                    print(f"[REFINER PIPE] CUDA not compatible with this GPU (compute capability mismatch). Using CPU instead.")
                else:
                    print(f"[REFINER PIPE] CUDA test failed. Using CPU instead.")
                # CUDA failed, need to reload with float32 for CPU
                device = "cpu"
                _REFINER_PIPE = None
                return _load_refiner_pipe(device)
        else:
            # CPU mode
            try:
                pipe.to(device)
            except Exception as e:
                print(f"[REFINER PIPE] Warning: Failed to move refiner pipeline to {device}. Reloading with float32 for CPU.")
                device = "cpu"
                _REFINER_PIPE = None
                return _load_refiner_pipe(device)
        
        pipe.enable_attention_slicing()
        # Additional optimizations for CPU
        if device == "cpu":
            try:
                pipe.enable_attention_slicing(slice_size="max")
            except Exception:
                pass
        _REFINER_PIPE = pipe
        return pipe
    except Exception as e:
        # If anything fails and we were trying CUDA, retry with CPU
        if device == "cuda":
            print(f"Error loading refiner pipeline on CUDA ({e}). Retrying with CPU.")
            device = "cpu"
            return _load_refiner_pipe(device)
        raise

# ---------- MAIN GENERATION FUNCTION ----------

def generate_puzzle_images(
    character: str,
    activity: str,
    num_images: int = 5,
    device: str = "cpu",
    progress_callback=None,
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
    # Validate device - allow CUDA even with warnings, will fall back if operations fail
    if device == "cuda" and not torch.cuda.is_available():
        print("Warning: CUDA requested but not available. Falling back to CPU.")
        device = "cpu"
    
    if progress_callback:
        progress_callback("Loading models...", 5, 100)
    
    base_pipe = _load_base_pipe(device)
    refiner_pipe = _load_refiner_pipe(device)

    # Get the actual device from the pipe and verify it
    execution_device = base_pipe._execution_device if hasattr(base_pipe, "_execution_device") else base_pipe.device
    actual_base_device = str(base_pipe.device) if hasattr(base_pipe, 'device') else "unknown"
    actual_refiner_device = str(refiner_pipe.device) if hasattr(refiner_pipe, 'device') else "unknown"
    
    print(f"[GENERATION] Requested device: {device}")
    print(f"[GENERATION] Base pipe device: {actual_base_device}, Execution device: {execution_device}")
    print(f"[GENERATION] Refiner pipe device: {actual_refiner_device}")
    
    # Warn if CUDA was requested but we're using CPU
    if device == "cuda" and "cpu" in str(execution_device).lower():
        print(f"⚠️  WARNING: CUDA was requested but execution is on CPU!")
        print(f"   Your PyTorch installation doesn't support your RTX 5080 GPU (sm_120 compute capability).")
        print(f"   CPU generation is 50-100x slower than GPU. Expected time: ~8-10 minutes per image on CPU.")
        print(f"   To use GPU: Install PyTorch with CUDA 12.x+ that supports sm_120, or use ComfyUI which has compatible PyTorch.")
        print(f"   For now, generation will continue on CPU (much slower but will work).")

    height = 768
    width = 768
    total_steps = 25
    cfg_scale = 8.0

    # 20/25 = 0.8 switch point (matches start_at_step / end_at_step)
    switch_frac = 20 / 25

    positive_prompt = (
        f"A cute cartoon {character.lower()}, at the {activity.lower()}, bright pastel colors, "
        "simple shapes, children's book illustration style, soft lighting, cheerful atmosphere, "
        "friendly expression, for kids aged 6 to 8, high quality, clean outlines"
    )
    negative_prompt = "text, watermark"

    # Repeat prompt num_images times (batch = 5 like EmptyLatentImage)
    prompts = [positive_prompt] * num_images
    neg_prompts = [negative_prompt] * num_images

    # Create generator on the execution device
    generator = torch.Generator(device=execution_device).manual_seed(torch.seed())
    print(f"[GENERATION] Generator device: {generator.device}")

    if progress_callback:
        progress_callback("Generating base images...", 15, 100)

    # ---- BASE: sample latents up to 80% denoising (like base KSampler end_at_step = 20)
    base_start = time.time()
    try:
        print(f"[TIMING] Starting base generation (batch size: {num_images}, steps: {total_steps}, device: {execution_device})")
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
        base_time = time.time() - base_start
        print(f"[TIMING] Base generation completed in {base_time:.2f}s ({base_time/num_images:.2f}s per image)")
    except (RuntimeError, Exception) as e:
        # If CUDA fails during generation, retry with CPU
        if device == "cuda":
            print(f"Error during base generation on CUDA ({e}). Retrying with CPU.")
            return generate_puzzle_images(character, activity, num_images, "cpu", progress_callback)
        raise

    if progress_callback:
        progress_callback("Refining images...", 50, 100)

    # ---- REFINER: continue from 80% to 100% (start_at_step = 20)
    refiner_start = time.time()
    try:
        print(f"[TIMING] Starting refiner (batch size: {num_images}, steps: {total_steps}, device: {execution_device})")
        refined = refiner_pipe(
            prompt=prompts,
            negative_prompt=neg_prompts,
            num_inference_steps=total_steps,
            guidance_scale=cfg_scale,
            denoising_start=switch_frac,
            image=latents,
            generator=generator,
        )
        print(f"[REFINER] Pipeline call completed, extracting images...")
        images = refined.images
        print(f"[REFINER] Extracted {len(images)} images from refiner output")
        refiner_time = time.time() - refiner_start
        print(f"[TIMING] Refiner completed in {refiner_time:.2f}s ({refiner_time/num_images:.2f}s per image)")
        
        # Update progress immediately after refiner completes (before saving)
        if progress_callback:
            print(f"[PROGRESS] Updating progress to 75%...")
            progress_callback("Refining complete, preparing to save...", 75, 100)
            print(f"[PROGRESS] Progress updated to 75%")
            # Small delay to ensure progress update is processed
            time.sleep(0.1)
    except (RuntimeError, Exception) as e:
        # If CUDA fails during refinement, retry with CPU
        print(f"[ERROR] Exception during refiner: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        if device == "cuda":
            print(f"Error during refinement on CUDA ({e}). Retrying with CPU.")
            return generate_puzzle_images(character, activity, num_images, "cpu", progress_callback)
        raise

    if progress_callback:
        progress_callback("Applying overlays and saving...", 80, 100)

    # ---- Save to hri_app/static/imgs with incremental filenames
    print(f"[SAVING] Starting to save {len(images)} images...")
    img_dir = _static_img_dir()
    img_dir.mkdir(parents=True, exist_ok=True)

    char_tok = _normalize_token(character)
    act_tok = _normalize_token(activity)

    current_idx = _next_index(character, activity)
    saved_paths: List[Path] = []
    print(f"[SAVING] Starting index: {current_idx}")

    for idx, img in enumerate(images):
        try:
            print(f"[SAVING] Processing image {idx + 1}/{num_images}...")
            if progress_callback:
                # Update progress: 80% base + ((idx + 1)/num_images) * 20% for saving
                # This ensures we reach 100% when the last image is processed
                progress = 80 + int(((idx + 1) / num_images) * 20)
                progress_callback(f"Saving image {idx + 1} of {num_images}...", progress, 100)
            
            # Ensure img is a PIL Image (diffusers typically returns PIL Images)
            if not isinstance(img, Image.Image):
                print(f"[SAVING] Converting image {idx + 1} to PIL Image...")
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
            print(f"[SAVING] Applying overlays to image {idx + 1}...")
            img_with_overlays = _superimpose_overlays(img, character, activity)
            
            # Save the final composite image
            fname = f"{char_tok}_{act_tok}_{current_idx:05d}.png"
            path = img_dir / fname
            print(f"[SAVING] Saving image {idx + 1} to {path}...")
            img_with_overlays.save(path)
            saved_paths.append(path)
            print(f"[SAVING] Successfully saved image {idx + 1}")
            current_idx += 1
        except Exception as e:
            print(f"[ERROR] Failed to save image {idx + 1}: {e}")
            import traceback
            traceback.print_exc()
            # Continue with next image even if one fails
            continue
    
    # Ensure we mark as 100% complete
    print(f"[SAVING] All images processed. Marking as complete...")
    if progress_callback:
        progress_callback("All images saved!", 100, 100)
    
    print(f"[TIMING] Saved {len(saved_paths)} images successfully")
    return saved_paths
