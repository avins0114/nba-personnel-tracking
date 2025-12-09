#!/bin/bash
# NBA Tracking Tool - Shell Aliases Setup
#
# Run this to add convenient aliases to your shell:
#   source setup_aliases.sh
#
# Or add to your ~/.zshrc or ~/.bashrc:
#   source ~/Documents/nba-personnel-tracking/setup_aliases.sh

NBA_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
alias nba-activate="source $NBA_DIR/venv/bin/activate"

# Main launcher
alias nba="cd $NBA_DIR && source venv/bin/activate && ./nba"

# Quick commands
alias nba-play="cd $NBA_DIR && source venv/bin/activate && python main.py --game"
alias nba-video="cd $NBA_DIR && source venv/bin/activate && python main.py --video"
alias nba-export="cd $NBA_DIR && source venv/bin/activate && python main.py --export-metrics"

# Specific use cases
alias nba-cv="cd $NBA_DIR && source venv/bin/activate && python main.py --video \$1 --half-court --show-video --show-spacing"
alias nba-manual="cd $NBA_DIR && source venv/bin/activate && python main.py --video \$1 --manual-select --half-court --show-video --show-spacing"

echo "NBA Tracking aliases loaded!"
echo ""
echo "Available commands:"
echo "  nba                 - Interactive menu"
echo "  nba play <file>     - View SportVU data"
echo "  nba video <file>    - Track from video"
echo "  nba-activate        - Activate virtual environment"
echo ""
echo "Examples:"
echo "  nba"
echo "  nba play data/games/sample.json"
echo "  nba video garland_fadeaway3.mp4"
echo ""
