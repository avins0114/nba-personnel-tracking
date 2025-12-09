"""Data loader for SportVU JSON files."""
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .player import Player
from .ball import Ball
from .moment import Moment
from .event import Event


class SportVULoader:
    """Load and parse SportVU tracking data from JSON files.
    
    SportVU JSON structure:
    {
        "gameid": "0021500001",
        "gamedate": "2015-10-27",
        "events": [
            {
                "eventId": 1,
                "moments": [
                    [quarter, timestamp, game_clock, shot_clock, None,
                     [[team_id, player_id, x, y, radius], ...]]  # 11 items (10 players + ball)
                ],
                "home": {"teamid": 123, "name": "Lakers", ...},
                "visitor": {"teamid": 456, "name": "Celtics", ...},
                "players": {"home": [...], "visitor": [...]}
            },
            ...
        ]
    }
    """
    
    def __init__(self, filepath: str):
        """Initialize loader with path to JSON file.

        Args:
            filepath: Path to SportVU JSON file (can be .json, .zip, or .7z)
        """
        self.filepath = Path(filepath)
        self._data: Optional[Dict] = None
        self._events: Optional[List[Event]] = None
        self._temp_dir: Optional[Path] = None

    def load(self) -> Dict[str, Any]:
        """Load and cache the JSON data."""
        if self._data is None:
            # Check if file is compressed
            if self.filepath.suffix.lower() in ['.7z', '.zip']:
                json_path = self._extract_compressed_file()
            else:
                json_path = self.filepath

            with open(json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        return self._data

    def _extract_compressed_file(self) -> Path:
        """Extract compressed file and return path to JSON."""
        print(f"Extracting {self.filepath.suffix} archive...")

        # Create temp directory
        self._temp_dir = Path(tempfile.mkdtemp(prefix='nba_sportvu_'))

        if self.filepath.suffix.lower() == '.zip':
            # Handle ZIP files
            with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
                zip_ref.extractall(self._temp_dir)

        elif self.filepath.suffix.lower() == '.7z':
            # Handle 7z files using command line (more reliable than py7zr)
            import subprocess
            try:
                # Try using 7z command (install with: brew install p7zip)
                subprocess.run(['7z', 'x', str(self.filepath), f'-o{self._temp_dir}', '-y'],
                             check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback: try py7zr if available
                try:
                    import py7zr
                    with py7zr.SevenZipFile(self.filepath, mode='r') as z:
                        z.extractall(path=self._temp_dir)
                except ImportError:
                    raise RuntimeError(
                        "Cannot extract .7z file. Please either:\n"
                        "  1. Install p7zip: brew install p7zip\n"
                        "  2. Install py7zr: pip install py7zr\n"
                        "  3. Extract the file manually and use the .json file"
                    )

        # Find the JSON file in extracted contents
        json_files = list(self._temp_dir.glob('*.json'))
        if not json_files:
            raise FileNotFoundError(f"No JSON file found in {self.filepath}")

        if len(json_files) > 1:
            print(f"Found {len(json_files)} JSON files, using: {json_files[0].name}")

        return json_files[0]

    def __del__(self):
        """Cleanup temp directory on deletion."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
    
    @property
    def game_id(self) -> str:
        """Get game ID."""
        return self.load().get('gameid', '')
    
    @property
    def game_date(self) -> str:
        """Get game date."""
        return self.load().get('gamedate', '')
    
    @property
    def event_count(self) -> int:
        """Get number of events in the game."""
        return len(self.load().get('events', []))
    
    def _parse_moment(self, raw_moment: List, 
                      home_team_id: int, 
                      away_team_id: int,
                      player_info: Dict[int, Dict]) -> Moment:
        """Parse a raw moment array into a Moment object.
        
        Args:
            raw_moment: [quarter, timestamp, game_clock, shot_clock, None, positions]
            home_team_id: Home team ID
            away_team_id: Away team ID  
            player_info: Dict mapping player_id -> player metadata
        """
        quarter = raw_moment[0]
        game_clock = raw_moment[2]
        shot_clock = raw_moment[3]
        positions = raw_moment[5]
        
        players = []
        ball = None
        
        for pos in positions:
            team_id, player_id, x, y, radius = pos
            
            if player_id == Ball.BALL_ID:
                ball = Ball(x=x, y=y, radius=radius)
            else:
                # Get player metadata if available
                info = player_info.get(player_id, {})
                player = Player(
                    team_id=team_id,
                    player_id=player_id,
                    x=x,
                    y=y,
                    firstname=info.get('firstname'),
                    lastname=info.get('lastname'),
                    jersey=info.get('jersey'),
                    position=info.get('position')
                )
                players.append(player)
        
        # Ensure we have a ball
        if ball is None:
            ball = Ball(x=0, y=0, radius=0)
        
        return Moment(
            quarter=quarter,
            game_clock=game_clock,
            shot_clock=shot_clock,
            ball=ball,
            players=players,
            home_team_id=home_team_id,
            away_team_id=away_team_id
        )
    
    def _build_player_info(self, event_data: Dict) -> Dict[int, Dict]:
        """Build a lookup dict for player metadata.
        
        Returns:
            Dict mapping player_id -> {firstname, lastname, jersey, position}
        """
        player_info = {}
        
        # Home players
        home_players = event_data.get('home', {}).get('players', [])
        for p in home_players:
            player_info[p['playerid']] = {
                'firstname': p.get('firstname'),
                'lastname': p.get('lastname'),
                'jersey': p.get('jersey'),
                'position': p.get('position')
            }
        
        # Away players
        away_players = event_data.get('visitor', {}).get('players', [])
        for p in away_players:
            player_info[p['playerid']] = {
                'firstname': p.get('firstname'),
                'lastname': p.get('lastname'),
                'jersey': p.get('jersey'),
                'position': p.get('position')
            }
        
        return player_info
    
    def get_event(self, event_index: int) -> Event:
        """Load a specific event by index.
        
        Args:
            event_index: 0-based index of event
            
        Returns:
            Event object with all moments parsed
        """
        data = self.load()
        events = data.get('events', [])
        
        if event_index >= len(events):
            event_index = len(events) - 1
        if event_index < 0:
            event_index = 0
            
        event_data = events[event_index]
        
        # Get team IDs
        home_team = event_data.get('home', {})
        away_team = event_data.get('visitor', {})
        home_team_id = home_team.get('teamid', 0)
        away_team_id = away_team.get('teamid', 0)
        
        # Build player lookup
        player_info = self._build_player_info(event_data)
        
        # Parse all moments
        moments = []
        for raw_moment in event_data.get('moments', []):
            try:
                moment = self._parse_moment(
                    raw_moment, 
                    home_team_id, 
                    away_team_id,
                    player_info
                )
                moments.append(moment)
            except (IndexError, TypeError, ValueError) as e:
                # Skip malformed moments
                continue
        
        return Event(
            event_id=event_data.get('eventId', event_index),
            moments=moments,
            home_team=home_team,
            away_team=away_team
        )
    
    def get_all_events(self) -> List[Event]:
        """Load all events from the game.
        
        Returns:
            List of Event objects
        """
        if self._events is None:
            self._events = []
            for i in range(self.event_count):
                try:
                    event = self.get_event(i)
                    if event.moments:  # Only include events with moments
                        self._events.append(event)
                except Exception:
                    continue
        return self._events
    
    def get_game_info(self) -> Dict[str, Any]:
        """Get basic game information."""
        data = self.load()
        first_event = data.get('events', [{}])[0] if data.get('events') else {}
        
        return {
            'game_id': self.game_id,
            'game_date': self.game_date,
            'home_team': first_event.get('home', {}).get('name', 'Unknown'),
            'away_team': first_event.get('visitor', {}).get('name', 'Unknown'),
            'event_count': self.event_count
        }


def load_game(filepath: str) -> SportVULoader:
    """Convenience function to create a loader.
    
    Args:
        filepath: Path to SportVU JSON file
        
    Returns:
        SportVULoader instance
    """
    return SportVULoader(filepath)
