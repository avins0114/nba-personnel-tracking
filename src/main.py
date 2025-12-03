#!/usr/bin/env python3
"""NBA Player Spacing Analysis - Main Entry Point.

Usage:
    python main.py --game data/games/sample.json --event 50
    python main.py --game data/games/sample.json --event 50 --show-spacing
    python main.py --game data/games/sample.json --export-metrics
"""
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.data_loader import SportVULoader
from src.visualizer import GameVisualizer, visualize_event
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(
        description='NBA Player Spacing Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --game games/Lakers@Celtics.json --event 50
  python main.py --game games/Lakers@Celtics.json --event 50 --show-spacing
  python main.py --game games/Lakers@Celtics.json --export-metrics --output metrics.csv
        """
    )
    
    parser.add_argument('--game', '-g', required=True,
                        help='Path to SportVU JSON game file')
    parser.add_argument('--event', '-e', type=int, default=0,
                        help='Event index to visualize (default: 0)')
    parser.add_argument('--show-spacing', '-s', action='store_true',
                        help='Show spacing overlay (convex hull)')
    parser.add_argument('--frame', '-f', type=int, default=None,
                        help='Show single frame instead of animation')
    parser.add_argument('--save', type=str, default=None,
                        help='Save animation to file (e.g., output.gif)')
    parser.add_argument('--export-metrics', action='store_true',
                        help='Export spacing metrics to CSV')
    parser.add_argument('--output', '-o', type=str, default='metrics.csv',
                        help='Output file for metrics export')
    parser.add_argument('--info', action='store_true',
                        help='Just print game info and exit')
    
    args = parser.parse_args()
    
    # Check file exists
    game_path = Path(args.game)
    if not game_path.exists():
        print(f"Error: Game file not found: {game_path}")
        sys.exit(1)
    
    # Load game
    print(f"Loading game: {game_path}")
    loader = SportVULoader(str(game_path))
    
    # Print game info
    info = loader.get_game_info()
    print(f"\nGame: {info['away_team']} @ {info['home_team']}")
    print(f"Date: {info['game_date']}")
    print(f"Events: {info['event_count']}")
    
    if args.info:
        return
    
    # Export metrics mode
    if args.export_metrics:
        export_metrics(loader, args.output)
        return
    
    # Load specific event
    print(f"\nLoading event {args.event}...")
    event = loader.get_event(args.event)
    
    if not event.moments:
        print("Error: Event has no tracking data")
        sys.exit(1)
    
    print(f"Event has {event.frame_count} frames ({event.duration:.1f} seconds)")
    
    # Print event metrics summary
    if event.home_team_id and event.away_team_id:
        print("\n--- Metrics Summary ---")
        # Try to determine offensive team from first moment with ball handler
        off_team = None
        for moment in event.moments[:10]:
            off_team = moment.get_offensive_team_id()
            if off_team:
                break
        
        if off_team:
            def_team = event.away_team_id if off_team == event.home_team_id else event.home_team_id
            metrics = event.get_metrics_summary(off_team, def_team)
            
            print(f"Avg Spacing Score: {metrics['avg_spacing']:.1f}")
            print(f"Max Spacing Score: {metrics['max_spacing']:.1f}")
            print(f"Avg Hull Area: {metrics['avg_hull_area']:.0f} sq ft")
            print(f"Avg Pairwise Distance: {metrics['avg_pairwise_dist']:.1f} ft")
            print(f"Avg Defender Distance: {metrics['avg_defender_dist']:.1f} ft")
            print(f"Open Shot %: {metrics['open_shot_pct']:.1f}%")
    
    # Single frame mode
    if args.frame is not None:
        print(f"\nShowing frame {args.frame}...")
        viz = GameVisualizer(event)
        viz.show_frame(args.frame, show_spacing=args.show_spacing)
        return
    
    # Animation mode
    print("\nStarting animation...")
    print("(Close window to exit)")
    
    viz = GameVisualizer(event)
    anim = viz.animate(show_spacing=args.show_spacing, save_path=args.save)
    
    if args.save:
        print(f"Animation saved to: {args.save}")
    else:
        plt.tight_layout()
        plt.show()


def export_metrics(loader: SportVULoader, output_path: str):
    """Export metrics for all events to CSV."""
    import csv
    
    print(f"\nExporting metrics to {output_path}...")
    
    events = loader.get_all_events()
    print(f"Processing {len(events)} events...")
    
    rows = []
    for i, event in enumerate(events):
        if not event.moments or not event.home_team_id:
            continue
        
        # Try to determine offensive team
        off_team = None
        for moment in event.moments[:10]:
            off_team = moment.get_offensive_team_id()
            if off_team:
                break
        
        if not off_team:
            continue
            
        def_team = event.away_team_id if off_team == event.home_team_id else event.home_team_id
        
        try:
            metrics = event.get_metrics_summary(off_team, def_team)
            metrics['event_id'] = event.event_id
            metrics['event_index'] = i
            metrics['offensive_team_id'] = off_team
            rows.append(metrics)
        except Exception as e:
            print(f"  Skipping event {i}: {e}")
    
    if not rows:
        print("No valid events to export")
        return
    
    # Write CSV
    fieldnames = ['event_index', 'event_id', 'offensive_team_id', 
                  'duration_seconds', 'frame_count',
                  'avg_spacing', 'max_spacing', 'spacing_variance',
                  'avg_hull_area', 'avg_pairwise_dist', 
                  'avg_defender_dist', 'open_shot_pct']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Exported {len(rows)} events to {output_path}")


if __name__ == '__main__':
    main()
