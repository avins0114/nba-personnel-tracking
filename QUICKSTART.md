# NBA Player Tracking - Quick Start

## 🚀 Super Easy Mode

Just run the interactive menu:

```bash
./nba
```

Then select what you want to do!

## ⚡ Quick Commands

### View a Play (SportVU Data)
```bash
./nba play data/games/sample.json 50
```

### Track from Video
```bash
./nba video garland_fadeaway3.mp4
```

### Compare CV vs SportVU
```bash
./nba compare data.json video.mp4
```

## 🔧 One-Time Setup (Optional)

Add to your shell for even easier access:

```bash
# Add this line to ~/.zshrc or ~/.bashrc
source ~/Documents/nba-personnel-tracking/setup_aliases.sh
```

Then from anywhere:
```bash
nba                    # Interactive menu
nba play <file>        # View game data
nba video <file>       # Track from video
```

## 📚 Common Tasks

### Just View a Game Play
```bash
./nba play data/games/Lakers@Celtics.json 42
```

### Track Video with Manual Selection
```bash
python main.py --video game.mp4 --manual-select --half-court --show-video
```

### Export All Metrics
```bash
python main.py --game data.json --export-metrics --output metrics.csv
```

## 🎯 SportVU Mode (Recommended)

**Best for analysis** - uses ground-truth tracking data

```bash
# Interactive
./nba play <game.json> <event_number>

# Full command
python main.py --game data.json --event 50 --show-spacing
```

**What you get:**
- Accurate player positions (±0.1 feet)
- All 10 players + ball tracked
- Spacing metrics (convex hull, pairwise distance)
- Clean visualizations

## 🎥 Computer Vision Mode (Experimental)

**Track from video** - extract data from game footage

```bash
# Quick
./nba video game.mp4

# With options
python main.py --video game.mp4 --half-court --show-video --show-spacing
```

**Options:**
- `--manual-select` - Click to select players (more accurate!)
- `--half-court` - For broadcast camera angles
- `--show-video` - Side-by-side video + court view
- `--show-spacing` - Show spacing overlay

## 📖 Full Documentation

- **CLAUDE.md** - Project overview and architecture
- **CV_README.md** - Computer vision detailed guide
- **test_cv.py** - Test CV dependencies

## 💡 Tips

1. **For best CV results**: Use `--manual-select --half-court`
2. **For broadcast videos**: Always use `--half-court`
3. **To save animations**: Add `--save output.gif`
4. **Just exploring?**: Use the interactive menu (`./nba`)

## 🆘 Help

```bash
./nba help              # Show all options
python main.py --help   # Full command-line help
```

## Examples Directory Structure

```
nba-personnel-tracking/
├── nba                    # Interactive launcher
├── data/
│   ├── games/            # Put SportVU JSON files here
│   └── videos/           # Put video files here
├── output/               # Generated visualizations
└── venv/                # Virtual environment
```

That's it! Just run `./nba` to get started. 🏀
