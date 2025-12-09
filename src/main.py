#!/usr/bin/env python3
"""NBA Player Spacing Analysis - Main Entry Point.

Usage:
    # SportVU data mode
    python main.py --game data/games/sample.json --event 50
    python main.py --game data/games/sample.json --event 50 --show-spacing
    python main.py --game data/games/sample.json --export-metrics

    # Computer Vision mode
    python main.py --video data/videos/game.mp4 --max-frames 250
    python main.py --video data/videos/game.mp4 --calibrate

    # Comparison mode
    python main.py --game data/games/sample.json --video data/videos/game.mp4 --compare
"""
import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import SportVULoader
from src.visualizer import GameVisualizer, visualize_event
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(
        description='NBA Player Spacing Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SportVU mode
  python main.py --game games/Lakers@Celtics.json --event 50
  python main.py --game games/Lakers@Celtics.json --event 50 --show-spacing
  python main.py --game games/Lakers@Celtics.json --export-metrics --output metrics.csv

  # Computer Vision mode
  python main.py --video videos/game.mp4 --max-frames 250
  python main.py --video videos/game.mp4 --calibrate

  # Comparison mode
  python main.py --game games/sample.json --video videos/game.mp4 --compare
        """
    )

    # Data source arguments
    parser.add_argument('--game', '-g', type=str,
                        help='Path to SportVU JSON game file')
    parser.add_argument('--video', '-v', type=str,
                        help='Path to video file for CV tracking')

    # SportVU-specific arguments
    parser.add_argument('--event', '-e', type=int, default=0,
                        help='Event index to visualize (default: 0)')

    # CV-specific arguments
    parser.add_argument('--max-frames', type=int, default=None,
                        help='Maximum frames to process from video (default: all frames)')
    parser.add_argument('--start-frame', type=int, default=0,
                        help='Starting frame for video processing (default: 0)')
    parser.add_argument('--calibrate', action='store_true',
                        help='Interactively calibrate court homography before processing')
    parser.add_argument('--manual-select', action='store_true',
                        help='Manually select players in first frame (much more accurate!)')
    parser.add_argument('--half-court', action='store_true',
                        help='Video shows only half court (typical broadcast angle)')
    parser.add_argument('--show-video', action='store_true',
                        help='Show original video alongside court visualization (CV mode only)')

    # Visualization arguments
    parser.add_argument('--show-spacing', '-s', action='store_true',
                        help='Show spacing overlay (convex hull)')
    parser.add_argument('--frame', '-f', type=int, default=None,
                        help='Show single frame instead of animation')
    parser.add_argument('--save', type=str, default=None,
                        help='Save animation to file (e.g., output.gif)')

    # Comparison mode
    parser.add_argument('--compare', action='store_true',
                        help='Compare CV tracking with SportVU data (requires both --game and --video)')

    # Export arguments
    parser.add_argument('--export-metrics', action='store_true',
                        help='Export spacing metrics to CSV')
    parser.add_argument('--output', '-o', type=str, default='metrics.csv',
                        help='Output file for metrics export')
    parser.add_argument('--info', action='store_true',
                        help='Just print game info and exit')

    args = parser.parse_args()

    # Validate arguments
    if not args.game and not args.video:
        parser.error('Must specify either --game or --video')

    if args.compare and (not args.game or not args.video):
        parser.error('--compare requires both --game and --video')

    # Determine mode
    if args.compare:
        return run_comparison_mode(args)
    elif args.video:
        return run_cv_mode(args)
    else:
        return run_sportvu_mode(args)


def run_sportvu_mode(args):
    """Run with SportVU data."""
    from src.event import Event

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
    print_event_metrics(event)

    # Visualize
    visualize_event_interactive(event, args)


def run_cv_mode(args):
    """Run with computer vision tracking."""
    from src.cv.cv_data_adapter import CVDataAdapter
    from src.cv.court_detector import CourtDetector
    from src.event import Event

    # Check file exists
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"\n=== Computer Vision Mode ===")
    print(f"Video: {video_path}")
    end_info = f"{args.start_frame + args.max_frames}" if args.max_frames else "end"
    print(f"Processing frames {args.start_frame} to {end_info}")
    if args.show_video:
        print("Video display: Enabled (side-by-side visualization)")

    # Initialize adapter
    court_detector = CourtDetector() if args.calibrate else None
    adapter = CVDataAdapter(str(video_path), court_detector, half_court=args.half_court)

    # Calibrate if requested
    if args.calibrate:
        print("\n--- Court Calibration ---")
        print("Interactive keypoint selection will open.")
        if adapter.setup_court_calibration(args.start_frame):
            print("Calibration successful!")
        else:
            print("Calibration cancelled. Using approximate mapping.")

    # Process video
    print("\n--- Processing Video ---")
    if args.manual_select:
        moments = adapter.process_video_with_manual_selection(
            start_frame=args.start_frame,
            max_frames=args.max_frames,
            store_frames=args.show_video  # Store frames if video display requested
        )
    else:
        moments = adapter.process_video(
            start_frame=args.start_frame,
            max_frames=args.max_frames,
            store_frames=args.show_video  # Store frames if video display requested
        )

    if not moments:
        print("Error: No tracking data extracted from video")
        sys.exit(1)

    # Create event from moments
    event = Event(
        event_id=0,
        moments=moments,
        home_team={'teamid': adapter.HOME_TEAM_ID, 'name': 'Home Team', 'abbreviation': 'HOME'},
        away_team={'teamid': adapter.AWAY_TEAM_ID, 'name': 'Away Team', 'abbreviation': 'AWAY'}
    )

    print(f"\nExtracted {event.frame_count} frames ({event.duration:.1f} seconds)")

    # Print metrics
    print_event_metrics(event)

    # Visualize (pass video frames if available)
    video_frames = adapter.video_frames if args.show_video else None
    visualize_event_interactive(event, args, video_frames=video_frames, half_court=args.half_court)

    adapter.close()


def run_comparison_mode(args):
    """Compare CV tracking with SportVU data."""
    from src.cv.cv_data_adapter import CVDataAdapter
    from src.cv.court_detector import CourtDetector
    from src.event import Event
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    # Load SportVU data
    game_path = Path(args.game)
    if not game_path.exists():
        print(f"Error: Game file not found: {game_path}")
        sys.exit(1)

    # Load video
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"\n=== Comparison Mode ===")
    print("Loading SportVU data...")
    loader = SportVULoader(str(game_path))
    sportvu_event = loader.get_event(args.event)

    print("Processing video with computer vision...")
    court_detector = CourtDetector() if args.calibrate else None
    adapter = CVDataAdapter(str(video_path), court_detector)

    if args.calibrate:
        print("Calibrating court...")
        adapter.setup_court_calibration(args.start_frame)

    cv_moments = adapter.process_video(
        start_frame=args.start_frame,
        max_frames=args.max_frames
    )

    cv_event = Event(
        event_id=0,
        moments=cv_moments,
        home_team={'teamid': adapter.HOME_TEAM_ID, 'name': 'Home Team', 'abbreviation': 'HOME'},
        away_team={'teamid': adapter.AWAY_TEAM_ID, 'name': 'Away Team', 'abbreviation': 'AWAY'}
    )

    # Compare metrics
    print("\n=== Comparison ===")
    print(f"\nSportVU: {sportvu_event.frame_count} frames, {sportvu_event.duration:.1f}s")
    print_event_metrics(sportvu_event)

    print(f"\nComputer Vision: {cv_event.frame_count} frames, {cv_event.duration:.1f}s")
    print_event_metrics(cv_event)

    # Side-by-side visualization
    print("\nCreating side-by-side visualization...")
    fig = plt.figure(figsize=(16, 6))
    gs = GridSpec(1, 2, figure=fig)

    # SportVU visualization
    ax1 = fig.add_subplot(gs[0, 0])
    viz1 = GameVisualizer(sportvu_event, ax=ax1)
    ax1.set_title('SportVU Ground Truth', fontsize=14, fontweight='bold')

    # CV visualization
    ax2 = fig.add_subplot(gs[0, 1])
    viz2 = GameVisualizer(cv_event, ax=ax2)
    ax2.set_title('Computer Vision Tracking', fontsize=14, fontweight='bold')

    # Sync animations
    print("Starting synchronized animations...")
    print("(Close window to exit)")

    anim1 = viz1.animate(show_spacing=args.show_spacing)
    anim2 = viz2.animate(show_spacing=args.show_spacing)

    plt.tight_layout()
    plt.show()

    adapter.close()


def print_event_metrics(event):
    """Print event metrics summary."""
    if not event.home_team_id or not event.away_team_id:
        return

    print("\n--- Metrics Summary ---")
    # Try to determine offensive team
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


def visualize_event_interactive(event, args, video_frames=None, half_court=False):
    """Interactive visualization of an event.

    Args:
        event: Event to visualize
        args: Command-line arguments
        video_frames: Optional list of video frames for side-by-side display
        half_court: Whether to show only half court
    """
    # Single frame mode
    if args.frame is not None:
        print(f"\nShowing frame {args.frame}...")
        viz = GameVisualizer(event, video_frames=video_frames, half_court=half_court)
        viz.show_frame(args.frame, show_spacing=args.show_spacing)
        return

    # Animation mode
    print("\nStarting animation...")
    print("(Close window to exit)")

    viz = GameVisualizer(event, video_frames=video_frames, half_court=half_court)
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
