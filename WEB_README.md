# NBA Spacing Analyzer - Web Interface

A modern, interactive web interface for analyzing NBA player spacing and movement data.

## Quick Start

### 1. Start the Web Server

```bash
./start_web.sh
```

Or manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start server
python app.py
```

### 2. Open in Browser

Navigate to: **http://localhost:5000**

## Features

### 🎮 Interactive Visualization
- Real-time court visualization with player positions
- Animated playback at 25 FPS
- Adjustable playback speed (0.5x - 2.0x)
- Spacing overlay showing convex hull of offensive players

### 📊 Metrics Dashboard
- **Spacing Score**: Composite metric (0-100) measuring offensive spacing quality
- **Hull Area**: Floor space covered by offensive players (square feet)
- **Average Distance**: Mean pairwise distance between offensive players
- **Defender Distance**: Average distance to nearest defender

### 🎥 Video Integration
- Toggle video display alongside court visualization
- Sync video playback with tracking data

### 📁 Game Management
- Browse available game files
- Select specific events/possessions
- View game and event information

## Usage

1. **Select a Game**: Choose from available SportVU JSON files in the dropdown
2. **Load an Event**: Enter an event number (0-indexed) and click "Load Event"
3. **Control Playback**: Use Play/Pause button and speed slider
4. **Toggle Features**: 
   - Check "Show Spacing Overlay" to see convex hull visualization
   - Check "Show Video" to display video alongside court

## Data Format

The web interface expects SportVU JSON files in the `data/` directory. These files contain:
- Player positions (x, y coordinates) at 25 FPS
- Ball position and height
- Game clock and shot clock
- Team and player metadata

## API Endpoints

The backend provides REST API endpoints:

- `GET /api/games` - List available games
- `GET /api/game/<filename>/info` - Get game information
- `GET /api/game/<filename>/events` - List events in a game
- `GET /api/game/<filename>/event/<index>` - Get full event data
- `GET /api/game/<filename>/event/<index>/metrics` - Get event metrics

## Architecture

- **Backend**: Flask REST API (`app.py`)
- **Frontend**: Vanilla JavaScript with HTML5 Canvas (`web/`)
- **Visualization**: Custom court rendering with real-time player tracking
- **Data Source**: SportVU JSON tracking data

## Troubleshooting

**No games showing up?**
- Make sure you have JSON files in the `data/` directory
- Check that files are valid SportVU format

**Video not playing?**
- Ensure `avinash_akshay_566_final.mov` exists in the project root
- Video will be copied to `web/static/video/` on first run

**Canvas not rendering?**
- Check browser console for errors
- Ensure JavaScript is enabled
- Try refreshing the page

## Development

To modify the frontend:
- HTML: `web/index.html`
- CSS: `web/static/css/style.css`
- JavaScript: `web/static/js/app.js`

To modify the backend:
- API routes: `app.py`
- Core logic: `src/` directory

## Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari

Requires modern browser with Canvas API support.

