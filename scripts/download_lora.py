#!/usr/bin/env python3
"""
Script to download the StoryBookRedmond LoRA from Hugging Face
and save it to the models/loras directory.

NOTE: The LoRA file will be automatically downloaded when needed
during image generation. This script is provided for manual download
if you prefer to download it beforehand or if automatic download fails.
"""

import os
import sys
from pathlib import Path
import urllib.request
from urllib.error import URLError, HTTPError


def download_file(url: str, destination: Path, chunk_size: int = 8192):
    """
    Download a file from a URL with progress indication.
    
    Args:
        url: The URL to download from
        destination: Path where the file should be saved
        chunk_size: Size of chunks to read at a time (default: 8KB)
    """
    try:
        print(f"Downloading from: {url}")
        print(f"Destination: {destination}")
        
        # Create parent directories if they don't exist
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists
        if destination.exists():
            file_size = destination.stat().st_size
            print(f"File already exists ({file_size / (1024*1024):.2f} MB).")
            response = input("Do you want to overwrite it? (y/n): ").strip().lower()
            if response != 'y':
                print("Download cancelled.")
                return False
        
        # Open the URL
        with urllib.request.urlopen(url) as response:
            # Get file size from headers
            total_size = int(response.headers.get('Content-Length', 0))
            total_size_mb = total_size / (1024 * 1024)
            
            print(f"File size: {total_size_mb:.2f} MB")
            print("Downloading...")
            
            downloaded = 0
            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Print progress every 10MB
                    if downloaded % (10 * 1024 * 1024) < chunk_size:
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"Progress: {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size_mb:.1f} MB)", end='\r')
                        else:
                            print(f"Downloaded: {downloaded / (1024*1024):.1f} MB", end='\r')
            
            print()  # New line after progress
            print(f"✓ Download complete! File saved to: {destination}")
            return True
            
    except HTTPError as e:
        print(f"✗ HTTP Error {e.code}: {e.reason}")
        return False
    except URLError as e:
        print(f"✗ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def main():
    """Main function to download the LoRA file."""
    # Hugging Face URL (use 'resolve' instead of 'blob' for direct download)
    lora_url = "https://huggingface.co/artificialguybr/StoryBookRedmond/resolve/main/StoryBookRedmond-KidsRedmAF.safetensors"
    
    # Determine the repository root (assuming script is in repo root)
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir
    
    # Path to models/loras directory
    models_dir = repo_root / "models" / "loras"
    lora_file = models_dir / "StoryBookRedmond-KidsRedmAF.safetensors"
    
    print("=" * 60)
    print("LoRA Download Script")
    print("=" * 60)
    print(f"Repository root: {repo_root}")
    print(f"Models directory: {models_dir}")
    print(f"Target file: {lora_file}")
    print("=" * 60)
    print()
    
    # Download the file
    success = download_file(lora_url, lora_file)
    
    if success:
        print()
        print("=" * 60)
        print("✓ Success! The LoRA file has been downloaded.")
        print(f"  Location: {lora_file}")
        print("=" * 60)
        return 0
    else:
        print()
        print("=" * 60)
        print("✗ Download failed. Please check the error messages above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

