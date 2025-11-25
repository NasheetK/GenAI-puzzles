from django import forms

def is_cuda_available():
    """Check if CUDA is available (even if there are compatibility warnings)."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        # torch not installed, CUDA not available
        return False

class PuzzlePromptForm(forms.Form):
    CHARACTER_CHOICES = [
        ("Cat", "Cat"),
        ("Dog", "Dog"),
        ("Tiger", "Tiger"),
        ("Rabbit", "Rabbit"),
        ("Bear", "Bear"),
    ]
    ACTIVITY_CHOICES = [
        ("School", "School"),
        ("Playground", "Playground"),
        ("Forest", "Forest"),
    ]
    
    # Check if CUDA is available (allow it even with warnings - will fall back if it fails)
    cuda_available = is_cuda_available()
    DEVICE_CHOICES = [
        ("cpu", "CPU"),
    ]
    if cuda_available:
        DEVICE_CHOICES.append(("cuda", "CUDA (GPU)"))

    character = forms.ChoiceField(choices=CHARACTER_CHOICES)
    activity = forms.ChoiceField(choices=ACTIVITY_CHOICES)
    device = forms.ChoiceField(
        choices=DEVICE_CHOICES,
        initial="cuda" if cuda_available else "cpu",
        label="Device",
        help_text="Select CPU for slower but compatible processing, or CUDA for faster GPU processing. Will automatically fall back to CPU if CUDA fails."
    )
