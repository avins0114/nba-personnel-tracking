# NBA Spacing Analyzer 🏀📊

> Ever wonder why Steph Curry breaks defenses just by existing? Or how the 2014 Spurs made passing look like art? This tool shows you the math behind the magic.

## What Does This Thing Do?

This tool analyzes **real NBA tracking data** to measure:
- 🎯 How spread out teams are on offense (spacing)
- 🧲 How much "gravity" star players create
- 👀 When players are wide open vs. smothered
- 📏 Literally every player position 25 times per second

It's like having a basketball PhD in your terminal.

## Quick Start

### 1. Set Up Your Environment

```bash
# Clone or cd into this repo
cd nba-spacing-analysis

# Make a virtual environment (keeps things clean)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the goods
pip install -r requirements.txt
```

### 2. Get Some Data

You'll need SportVU tracking data (JSON files). We've included sample data in `data/`, or grab more from:
- https://github.com/linouk23/NBA-Player-Movements
- https://github.com/sealneaward/nba-movement-data

Extract any `.7z` files:
```bash
7z x data/01.01.2016.CHA.at.TOR.7z -o data/
```

### 3. Start Analyzing

```bash
# See what's in a game file
python -m src.main --game data/0021500492.json --info

# Watch a possession with spacing visualization
python -m src.main --game data/0021500492.json --event 50 --show-spacing

# Check out a single frame
python -m src.main --game data/0021500492.json --event 50 --frame 100 --show-spacing

# Export ALL the metrics to CSV for data science stuff
python -m src.main --game data/0021500492.json --export-metrics -o my_analysis.csv
```

## Commands Explained

### `--info` - Game Info
See basic game details without loading everything.

```bash
python -m src.main --game data/0021500492.json --info
```

**Output:**
```
Game: Charlotte Hornets @ Toronto Raptors
Date: 2016-01-01
Events: 452
```

### `--event <number>` - Watch a Play
Animate a specific possession. Each game has hundreds of "events" (possessions/plays).

```bash
python -m src.main --game data/0021500492.json --event 100
```

This opens a matplotlib animation showing:
- All 10 players moving in real-time
- The ball
- Game clock, shot clock
- Live spacing metrics (if you add `--show-spacing`)

**Pro tip:** Add `--show-spacing` to see the offensive team's spacing polygon overlay in real-time. Bigger green blob = better spacing.

### `--frame <number>` - Freeze Frame Analysis
Want to see one specific moment? Use `--frame` to show a single snapshot instead of the full animation.

```bash
python -m src.main --game data/0021500492.json --event 50 --frame 200 --show-spacing
```

Great for screenshots or analyzing specific moments like "right when Curry gets the ball."

### `--export-metrics` - Data Dump Mode
Export every possession's metrics to CSV for spreadsheet analysis, ML models, or whatever nerdy thing you're building.

```bash
python -m src.main --game data/0021500492.json --export-metrics -o my_stats.csv
```

**What you get:**
- Spacing scores (0-100 scale)
- Convex hull area (square feet covered)
- Average pairwise distances
- Defender proximity
- Open shot percentages
- And more...

### `--save <filename>` - Export Animation
Save the animation as a GIF instead of just watching it.

```bash
python -m src.main --game data/0021500492.json --event 50 --show-spacing --save cool_play.gif
```

Now you can post it, share it, or use it in presentations.

## What The Metrics Actually Mean

### Spacing Score (0-100)
**TL;DR:** How well-spaced is the offense?

- **90+** = Elite spacing (2017 Rockets vibes)
- **70-90** = Good spacing (modern NBA)
- **50-70** = Meh spacing (standing around)
- **<50** = Yikes (everyone's in the paint)

**Formula:** Combines hull area, pairwise distances, 3-point positioning, and paint density.

### Convex Hull Area
**TL;DR:** Draw a rubber band around all 5 offensive players. How much floor space do they cover?

- **600-800 sq ft** = Great spacing
- **400-600 sq ft** = Decent spacing
- **<400 sq ft** = Cramped, defense can guard everyone easily

### Average Pairwise Distance
**TL;DR:** Average distance between every pair of teammates.

- **25+ feet** = Spread out nicely
- **15-25 feet** = Normal
- **<15 feet** = Too bunched up

### Defender Distance
**TL;DR:** How close is the nearest defender to each offensive player?

- **>10 feet** = Open, plenty of space
- **6-10 feet** = Contested but manageable
- **<6 feet** = Locked up, someone needs help

### Open Shot Percentage
**TL;DR:** What % of the possession did at least one player have 6+ feet of space?

**100%** = Always had an open man (elite offense or bad defense)
**50%** = Sometimes open, sometimes not
**<25%** = Smothered all possession

## Real-World Use Cases

### 🎬 Film Study
Watch how spacing changes throughout a possession:
```bash
python -m src.main --game data/0021500492.json --event 100 --show-spacing
```

### 📊 Statistical Analysis
Export a whole game and analyze in pandas/Excel:
```bash
python -m src.main --game data/0021500492.json --export-metrics -o spacing_data.csv
```

Then in Python:
```python
import pandas as pd
df = pd.read_csv('spacing_data.csv')

# Find possessions with elite spacing
print(df[df['avg_spacing'] > 90])

# Correlation between spacing and duration
print(df[['avg_spacing', 'duration_seconds']].corr())
```

### 🔬 Research Questions
- Does better spacing correlate with offensive efficiency?
- How does spacing change in clutch vs. non-clutch situations?
- Which teams had the best spacing in 2015-16?
- How much space does a star player create just by being on the court?

### 🎮 Content Creation
Make GIFs of cool plays with analytics overlays:
```bash
python -m src.main --game data/0021500492.json --event 50 --show-spacing --save highlight.gif
```

## Tips & Tricks

### Finding Cool Plays
Start with low event numbers (early game) or browse around:
```bash
# Quick loop through events
for i in {50..60}; do
  python -m src.main --game data/0021500492.json --event $i --frame 0 --show-spacing
done
```

### Performance
Big game files (100MB+) take a few seconds to load. Be patient on first load.

### Troubleshooting

**"No module named src.data_loader"**
Make sure you're running as a module: `python -m src.main` not `python src/main.py`

**Animation window is blank/frozen**
Your matplotlib backend might be weird. Try setting:
```bash
export MPLBACKEND=TkAgg  # or Qt5Agg
```

**"Event has no tracking data"**
Some events are dead balls or don't have tracking. Try a different event number.

## Data Notes

- **Court dimensions:** 94 x 50 feet (full court)
- **Frame rate:** 25 fps (one "moment" every 0.04 seconds)
- **Players:** Always 10 (5 per team)
- **Coordinates:** (0, 0) is one corner, (94, 50) is opposite corner
- **Season:** This sample data is from 2015-16

## What's Next?

Some ideas to extend this:
- Add shot outcome data (did they score?)
- Track individual player gravity over time
- Compare spacing across different eras
- Build a web dashboard
- Train ML models to predict shot success from spacing
- Analyze how spacing changes with different lineups

## Credits

Built on the shoulders of:
- [NBA-Player-Movements](https://github.com/linouk23/NBA-Player-Movements) for visualization inspiration
- SportVU tracking system (RIP, replaced by Second Spectrum)
- The basketball analytics community 📊🏀

---

**Have fun! And remember:** Good spacing is like good code—when it's done right, everything just flows.
