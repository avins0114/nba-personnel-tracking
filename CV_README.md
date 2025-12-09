# Computer Vision Tracking - Quick Start Guide

This document explains how to use the computer vision tracking feature to analyze NBA game footage.

## Overview

The CV tracking system uses:
- **YOLOv8** for player detection
- **DeepSORT** for multi-object tracking across frames
- **Homography transformation** for mapping pixel coordinates to real court coordinates

## Installation

Install the CV dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- `opencv-python` - Video processing
- `torch` & `torchvision` - Deep learning
- `ultralytics` - YOLOv8 object detection
- `deep-sort-realtime` - Multi-object tracking

## Usage

### 1. Basic CV Mode

Process a video file and extract player tracking data:

```bash
python src/main.py --video path/to/game.mp4 --max-frames 250
```

Options:
- `--max-frames N` - Process N frames (default: 250, ~10 seconds at 25 FPS)
- `--start-frame N` - Start from frame N (default: 0)
- `--show-spacing` - Show convex hull spacing overlay
- `--save output.gif` - Save animation to file

### 2. Court Calibration Mode

For accurate coordinate mapping, calibrate the court homography:

```bash
python src/main.py --video path/to/game.mp4 --calibrate --max-frames 250
```

This will:
1. Display the first frame
2. Prompt you to click 4 court corner points
3. Compute homography transformation
4. Process the video with accurate court coordinates

**Point order:**
1. Near-left baseline corner
2. Far-left baseline corner
3. Far-right baseline corner
4. Near-right baseline corner

### 3. Comparison Mode

Compare CV tracking with ground-truth SportVU data:

```bash
python src/main.py --game data/games/sample.json --video data/videos/game.mp4 --compare --event 50
```

This creates a side-by-side visualization showing:
- **Left**: SportVU ground truth tracking
- **Right**: Computer vision tracking

Perfect for evaluating CV accuracy!

## Expected Performance

### Accuracy
- **Player Detection**: ~85-95% (depends on camera angle and occlusion)
- **Position Error**: ±1-2 feet (vs ±0.1 feet for SportVU)
- **Team Classification**: ~80% (jersey color-based, simple heuristic)
- **Processing Speed**: ~5-10 FPS on GPU, ~1-2 FPS on CPU

### Limitations
- **Camera Movement**: Works best with fixed camera angles
- **Occlusions**: Players off-screen or blocked won't be tracked
- **Ball Tracking**: Not implemented (dummy ball at center court)
- **Player Re-ID**: May swap IDs if players cross or overlap
- **Referees/Coaches**: Heuristic filtering (not perfect)

## Architecture

```
src/cv/
├── video_loader.py       # Video I/O and frame extraction
├── player_detector.py    # YOLO-based player detection
├── player_tracker.py     # DeepSORT tracking with team classification
├── court_detector.py     # Homography calibration
└── cv_data_adapter.py    # Converts CV output to SportVU format
```

## Pipeline Overview

```
Video File
    ↓
[VideoLoader] - Extract frames at 25 FPS
    ↓
[PlayerDetector] - Detect people using YOLO
    ↓
[PlayerTracker] - Track players across frames (DeepSORT)
    ↓
[CourtDetector] - Transform pixel → court coordinates
    ↓
[CVDataAdapter] - Convert to SportVU Moment format
    ↓
Visualization & Metrics
```

## Tips for Best Results

### 1. Video Selection
- Use **half-court offensive possessions** (easier than transition)
- **Fixed camera angle** (broadcast angle changes complicate homography)
- **Clear court visibility** (avoid crowd shots, close-ups)
- **Good lighting** (indoor arenas work best)

### 2. Frame Range
- Start with **10 seconds** (`--max-frames 250`)
- Avoid **timeouts, free throws** (lots of movement off-court)
- Pick moments with **5v5 on court** (full lineup)

### 3. Calibration
- Always use `--calibrate` for **accurate metrics**
- Click corners **precisely** (affects all downstream coords)
- Use a frame with **clear court lines visible**

### 4. Testing
- Try **NBA 2K gameplay footage** first (cleaner, fixed camera)
- Compare with **SportVU data** to validate accuracy
- Start with **short clips** before processing full games

## Example Workflow

```bash
# 1. Test basic detection (no calibration)
python src/main.py --video game.mp4 --max-frames 100

# 2. Calibrate court for accurate metrics
python src/main.py --video game.mp4 --calibrate --max-frames 250 --show-spacing

# 3. Compare with ground truth
python src/main.py --game data.json --video game.mp4 --compare --event 50

# 4. Export metrics
python src/main.py --video game.mp4 --max-frames 1000 --export-metrics --output cv_metrics.csv
```

## Troubleshooting

### No players detected
- Check video quality and brightness
- Try lowering `confidence_threshold` in `PlayerDetector`
- Ensure players are visible (not zoomed to coaches/bench)

### Inaccurate positions
- Use `--calibrate` for homography
- Ensure court is fully visible in frame
- Check camera angle (works best from high, center-court view)

### Slow processing
- Use `yolov8n.pt` (nano) model for speed
- Reduce `--max-frames`
- Use GPU (check: `torch.cuda.is_available()`)

### Players swapping IDs
- Increase `max_age` in PlayerTracker (keeps tracks alive longer)
- Reduce player crowding (avoid paint traffic)
- Use better re-identification features (future improvement)

## Future Enhancements

Potential improvements:
- **Automatic court detection** (deep learning keypoint detection)
- **Ball tracking** (smaller object, harder to detect)
- **Better team classification** (train CNN on jersey colors)
- **Player jersey number recognition** (OCR)
- **Play-by-play integration** (sync with game clock)
- **Real-time processing** (optimize for live streams)

## References

- [YOLO Documentation](https://docs.ultralytics.com/)
- [DeepSORT Paper](https://arxiv.org/abs/1703.07402)
- [Basketball Court Detection](https://github.com/lood339/basketball-court-detection)
- [NBA Movement Data](https://github.com/sealneaward/nba-movement-data)
