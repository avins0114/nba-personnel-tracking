#!/usr/bin/env python3
"""
NBA Player Spacing Analysis - Entry Point

Run from project root:
    python main.py --video game.mp4 --max-frames 250
    python main.py --game data.json --event 50
    python main.py --game data.json --video game.mp4 --compare
"""

if __name__ == '__main__':
    from src.main import main
    main()
