#!/usr/bin/env python3
"""Flask backend API for NBA Spacing Analyzer web frontend."""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
from pathlib import Path
import json
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_loader import SportVULoader
from src.event import Event

app = Flask(__name__, static_folder='web/static', static_url_path='/static')
CORS(app)

# Serve static files from web directory
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('web/static', path)

# Global cache for loaded games
_game_cache = {}


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('web', 'index.html')


@app.route('/api/games', methods=['GET'])
def list_games():
    """List available game JSON files."""
    data_dir = Path('data')
    if not data_dir.exists():
        return jsonify({'games': []})
    
    games = []
    for json_file in data_dir.glob('*.json'):
        try:
            loader = SportVULoader(str(json_file))
            info = loader.get_game_info()
            games.append({
                'filename': json_file.name,
                'path': str(json_file),
                'game_id': info.get('game_id', ''),
                'game_date': info.get('game_date', ''),
                'home_team': info.get('home_team', 'Unknown'),
                'away_team': info.get('away_team', 'Unknown'),
                'event_count': info.get('event_count', 0)
            })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            continue
    
    return jsonify({'games': games})


@app.route('/api/game/<path:filename>/info', methods=['GET'])
def get_game_info(filename):
    """Get game information."""
    game_path = Path('data') / filename
    if not game_path.exists():
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        loader = SportVULoader(str(game_path))
        info = loader.get_game_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/<path:filename>/events', methods=['GET'])
def get_events(filename):
    """Get list of events in a game."""
    game_path = Path('data') / filename
    if not game_path.exists():
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        loader = SportVULoader(str(game_path))
        event_count = loader.event_count
        
        events = []
        for i in range(min(event_count, 100)):  # Limit to first 100 for performance
            try:
                event = loader.get_event(i)
                if event.moments:
                    events.append({
                        'index': i,
                        'event_id': event.event_id,
                        'frame_count': event.frame_count,
                        'duration': event.duration
                    })
            except Exception:
                continue
        
        return jsonify({'events': events, 'total': event_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/<path:filename>/event/<int:event_index>', methods=['GET'])
def get_event_data(filename, event_index):
    """Get full event data with all moments."""
    game_path = Path('data') / filename
    if not game_path.exists():
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        loader = SportVULoader(str(game_path))
        event = loader.get_event(event_index)
        
        if not event.moments:
            return jsonify({'error': 'Event has no tracking data'}), 404
        
        # Determine offensive team
        off_team = None
        for moment in event.moments[:10]:
            off_team = moment.get_offensive_team_id()
            if off_team:
                break
        
        if not off_team:
            return jsonify({'error': 'Could not determine offensive team'}), 400
        
        def_team = event.away_team_id if off_team == event.home_team_id else event.home_team_id
        
        # Get metrics summary
        metrics = event.get_metrics_summary(off_team, def_team)
        
        # Serialize moments
        moments_data = []
        for moment in event.moments:
            players_data = []
            for player in moment.players:
                players_data.append({
                    'team_id': player.team_id,
                    'player_id': player.player_id,
                    'x': player.x,
                    'y': player.y,
                    'jersey': player.jersey,
                    'name': player.name
                })
            
            moments_data.append({
                'quarter': moment.quarter,
                'game_clock': moment.game_clock,
                'shot_clock': moment.shot_clock if moment.shot_clock else None,
                'ball': {
                    'x': moment.ball.x,
                    'y': moment.ball.y,
                    'radius': moment.ball.radius
                },
                'players': players_data
            })
        
        # Calculate spacing over time
        spacing_over_time = event.spacing_over_time(off_team)
        hull_area_over_time = event.hull_area_over_time(off_team)
        
        return jsonify({
            'event_id': event.event_id,
            'event_index': event_index,
            'home_team_id': event.home_team_id,
            'away_team_id': event.away_team_id,
            'home_team': event.home_team.get('name', 'Home') if event.home_team else 'Home',
            'away_team': event.away_team.get('name', 'Away') if event.away_team else 'Away',
            'offensive_team_id': off_team,
            'defensive_team_id': def_team,
            'frame_count': event.frame_count,
            'duration': event.duration,
            'metrics': metrics,
            'spacing_over_time': spacing_over_time,
            'hull_area_over_time': hull_area_over_time,
            'moments': moments_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/game/<path:filename>/event/<int:event_index>/metrics', methods=['GET'])
def get_event_metrics(filename, event_index):
    """Get metrics for a specific event."""
    game_path = Path('data') / filename
    if not game_path.exists():
        return jsonify({'error': 'Game not found'}), 404
    
    try:
        loader = SportVULoader(str(game_path))
        event = loader.get_event(event_index)
        
        if not event.moments:
            return jsonify({'error': 'Event has no tracking data'}), 404
        
        # Determine offensive team
        off_team = None
        for moment in event.moments[:10]:
            off_team = moment.get_offensive_team_id()
            if off_team:
                break
        
        if not off_team:
            return jsonify({'error': 'Could not determine offensive team'}), 400
        
        def_team = event.away_team_id if off_team == event.home_team_id else event.home_team_id
        metrics = event.get_metrics_summary(off_team, def_team)
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/video', methods=['GET'])
def get_video():
    """Get video file path."""
    video_path = Path('avinash_akshay_566_final.mov')
    static_video = Path('web/static/video/avinash_akshay_566_final.mov')
    
    # Copy video to static if it exists in root
    if video_path.exists() and not static_video.exists():
        static_video.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(video_path, static_video)
    
    if static_video.exists() or video_path.exists():
        return jsonify({
            'exists': True,
            'filename': 'avinash_akshay_566_final.mov',
            'path': '/static/video/avinash_akshay_566_final.mov'
        })
    return jsonify({'exists': False})


if __name__ == '__main__':
    # Create data directory if it doesn't exist
    Path('data').mkdir(exist_ok=True)
    
    # Copy video to static if it exists
    video_src = Path('avinash_akshay_566_final.mov')
    video_dest = Path('web/static/video/avinash_akshay_566_final.mov')
    if video_src.exists() and not video_dest.exists():
        video_dest.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        try:
            shutil.copy2(video_src, video_dest)
            print(f"✓ Copied video to {video_dest}")
        except Exception as e:
            print(f"Warning: Could not copy video: {e}")
    
    # Try to use port 5001 (5000 is often used by AirPlay on macOS)
    port = 5001
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        # Port 5001 also in use, try 8000
        port = 8000
    sock.close()
    
    print("\n" + "="*50)
    print("🏀 NBA Spacing Analyzer Web Server")
    print("="*50)
    print(f"\n✓ Server starting on http://localhost:{port}")
    print("✓ Open the URL in your browser to use the interface")
    print("\nPress Ctrl+C to stop the server\n")
    app.run(debug=True, host='0.0.0.0', port=port)

