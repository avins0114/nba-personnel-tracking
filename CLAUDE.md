# NBA Player Spacing Analysis - Claude Code Instructions

## Project Overview
This project analyzes NBA player spacing and "gravity" metrics using **two data sources**:
1. **SportVU tracking data** (2015-16 season) - ground-truth coordinates at 25 FPS
2. **Computer Vision** (NEW!) - extract tracking from video footage using YOLO + DeepSORT

This builds on the visualization approach from linouk23/NBA-Player-Movements but adds advanced spacing analytics and CV tracking capabilities.

## Data Sources

### Option 1: SportVU Data (Recommended for Accuracy)
Pre-extracted SportVU tracking data gives ground-truth x,y coordinates at 25 FPS for all 10 players + ball.

**Data format** (JSON):
- `events[]` - list of plays/possessions
- `events[].moments[]` - snapshots at 25Hz
- Each moment: `[team_id, player_id, x, y, radius]` for 10 players + ball
- Court dimensions: 94 x 50 feet (half court: 47 x 50)

### Option 2: Computer Vision Tracking (NEW!)
Extract tracking data from video footage using deep learning:
- **Detection**: YOLOv8 for player detection
- **Tracking**: DeepSORT for consistent player IDs across frames
- **Mapping**: Homography for pixel → court coordinate transformation
- **Accuracy**: ±1-2 feet position error (vs ±0.1 feet for SportVU)

See **CV_README.md** for detailed CV usage guide.

## Project Structure
```
nba-spacing-analysis/
├── CLAUDE.md           # This file - project instructions
├── CV_README.md        # Computer vision usage guide
├── test_cv.py          # Test CV dependencies
├── src/
│   ├── data_loader.py  # Load/parse SportVU JSON
│   ├── court.py        # Court drawing utilities
│   ├── player.py       # Player class
│   ├── ball.py         # Ball class
│   ├── moment.py       # Single frame snapshot
│   ├── event.py        # Full possession/play
│   ├── metrics.py      # Spacing/gravity calculations
│   ├── visualizer.py   # Matplotlib animations
│   ├── main.py         # CLI entry point (supports both SportVU and CV)
│   └── cv/             # Computer vision modules
│       ├── video_loader.py      # Video I/O
│       ├── player_detector.py   # YOLO detection
│       ├── player_tracker.py    # DeepSORT tracking
│       ├── court_detector.py    # Homography calibration
│       └── cv_data_adapter.py   # CV → SportVU format converter
├── data/
│   ├── games/          # SportVU JSON files go here
│   └── videos/         # Video files for CV tracking
├── output/             # Generated visualizations
└── requirements.txt
```

## Core Metrics to Implement

### 1. Spacing Metrics (Offensive)
- **Convex Hull Area**: Area of polygon formed by 5 offensive players
- **Average Pairwise Distance**: Mean distance between all offensive player pairs
- **Paint Density**: Number of offensive players within the paint
- **Three-Point Spread**: Players positioned beyond the arc

### 2. Gravity Metrics (Per-Player)
- **Defensive Attention**: Distance of nearest defender to each offensive player
- **Help Distance**: How far help defenders are from the ball handler
- **Defensive Collapse**: Change in defender positions when star player has ball
- **Off-Ball Gravity**: Defender movement in response to off-ball player movement

### 3. Derived Metrics
- **Open Shot Opportunities**: Moments where shooter has >6ft of space
- **Driving Lane Quality**: Clear path width to the basket
- **Spacing Score**: Composite metric combining hull area + spread

## Implementation Phases

### Phase 1: Data Loading & Visualization (Week 1)
1. Implement `data_loader.py` to parse SportVU JSON
2. Create `court.py` with matplotlib court drawing
3. Build basic `visualizer.py` with FuncAnimation
4. Test with sample game data

### Phase 2: Core Classes (Week 1-2)
1. `Player`, `Ball`, `Moment`, `Event` classes
2. Team identification (home/away by team_id)
3. Possession detection (which team has ball)

### Phase 3: Spacing Metrics (Week 2-3)
1. Implement convex hull calculation (scipy.spatial)
2. Pairwise distance calculations
3. Zone-based metrics (paint, 3pt line, corners)

### Phase 4: Gravity Metrics (Week 3-4)
1. Defender assignment (nearest defender heuristic)
2. Help defense positioning
3. Per-player gravity scores

### Phase 5: Visualization & Analysis (Week 4-5)
1. Animated overlays showing metrics in real-time
2. Possession-level summaries
3. Correlation with shot outcomes (if play-by-play available)

## Key Libraries
```
# Core analytics
numpy, pandas, matplotlib, scipy

# Computer vision (optional, for video tracking)
opencv-python, torch, ultralytics, deep-sort-realtime
```

## Running the Project

### SportVU Mode (Ground Truth Data)
```bash
# Basic visualization of a play
python src/main.py --game data/games/sample.json --event 50

# With spacing overlay
python src/main.py --game data/games/sample.json --event 50 --show-spacing

# Export metrics to CSV
python src/main.py --game data/games/sample.json --export-metrics
```

### Computer Vision Mode (Video Input)
```bash
# Test CV dependencies
python test_cv.py

# Process video with CV tracking
python src/main.py --video data/videos/game.mp4 --max-frames 250

# With court calibration (for accurate coordinates)
python src/main.py --video data/videos/game.mp4 --calibrate --show-spacing

# Compare CV tracking vs SportVU ground truth
python src/main.py --game data.json --video game.mp4 --compare --event 50
```

See **CV_README.md** for detailed CV usage instructions.

## Code Style
- Use type hints
- Docstrings for public methods
- Keep visualization and metrics logic separate
- NumPy vectorized operations where possible

## Testing
- Validate coordinates are within court bounds (0-94, 0-50)
- Check that exactly 10 players + 1 ball per moment
- Verify convex hull areas are reasonable (typical: 200-800 sq ft)

## Sample Data
Download from: https://github.com/linouk23/NBA-Player-Movements/tree/master/data
Or: https://github.com/sealneaward/nba-movement-data

## References
- Original visualization: https://github.com/linouk23/NBA-Player-Movements
- SportVU data structure: https://github.com/rajshah4/NBA_SportVu
- Court dimensions: https://www.nbastuffer.com/analytics101/sportvu-data/
