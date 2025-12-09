#!/usr/bin/env python3
"""
Quick test script for CV tracking functionality.

This script tests the CV pipeline without requiring a video file.
It generates a test report showing which components are working.
"""

import sys
from pathlib import Path

def test_dependencies():
    """Test if all CV dependencies are installed."""
    print("=" * 60)
    print("Testing CV Dependencies")
    print("=" * 60)

    deps = {
        'opencv-python': 'cv2',
        'torch': 'torch',
        'ultralytics': 'ultralytics',
        'deep-sort-realtime': 'deep_sort_realtime',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib'
    }

    all_ok = True
    for name, module in deps.items():
        try:
            __import__(module)
            print(f"✓ {name:25} installed")
        except ImportError:
            print(f"✗ {name:25} MISSING")
            all_ok = False

    print()
    return all_ok


def test_models():
    """Test if YOLO models can be loaded."""
    print("=" * 60)
    print("Testing YOLO Model")
    print("=" * 60)

    try:
        from ultralytics import YOLO
        print("Loading YOLOv8 nano model (this may download ~6MB)...")
        model = YOLO('yolov8n.pt')
        print("✓ YOLOv8 model loaded successfully")
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to load YOLO: {e}")
        print()
        return False


def test_cv_modules():
    """Test if CV modules can be imported."""
    print("=" * 60)
    print("Testing CV Modules")
    print("=" * 60)

    modules = [
        'src.cv.video_loader',
        'src.cv.player_detector',
        'src.cv.player_tracker',
        'src.cv.court_detector',
        'src.cv.cv_data_adapter'
    ]

    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module:30} OK")
        except Exception as e:
            print(f"✗ {module:30} FAILED: {e}")
            all_ok = False

    print()
    return all_ok


def test_gpu():
    """Check if GPU is available for acceleration."""
    print("=" * 60)
    print("GPU Availability")
    print("=" * 60)

    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
        else:
            print("⚠ No GPU detected - will use CPU (slower)")
            print("  Consider using a GPU for faster processing")
    except Exception as e:
        print(f"✗ Could not check GPU: {e}")

    print()


def show_usage_examples():
    """Show usage examples."""
    print("=" * 60)
    print("Usage Examples")
    print("=" * 60)
    print()
    print("1. Process a video with CV tracking:")
    print("   python src/main.py --video game.mp4 --max-frames 250")
    print()
    print("2. Calibrate court homography:")
    print("   python src/main.py --video game.mp4 --calibrate")
    print()
    print("3. Compare CV vs SportVU:")
    print("   python src/main.py --game data.json --video game.mp4 --compare")
    print()
    print("See CV_README.md for more details!")
    print()


def main():
    print()
    print("NBA Player Tracking - Computer Vision Test")
    print()

    # Run tests
    deps_ok = test_dependencies()
    if not deps_ok:
        print("❌ Some dependencies are missing!")
        print("Install with: pip install -r requirements.txt")
        sys.exit(1)

    models_ok = test_models()
    modules_ok = test_cv_modules()
    test_gpu()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if deps_ok and models_ok and modules_ok:
        print("✓ All tests passed! CV tracking is ready to use.")
        print()
        show_usage_examples()
        return 0
    else:
        print("❌ Some tests failed. Check errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
