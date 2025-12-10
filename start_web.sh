#!/bin/bash
# Start the NBA Spacing Analyzer web server

echo "🏀 Starting NBA Spacing Analyzer Web Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Copy video if it exists
if [ -f "avinash_akshay_566_final.mov" ] && [ ! -f "web/static/video/avinash_akshay_566_final.mov" ]; then
    echo "Copying video file..."
    cp avinash_akshay_566_final.mov web/static/video/
fi

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "✅ Server starting..."
echo "🌐 Server will start on http://localhost:5001 (or 8000 if 5001 is in use)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Flask server
python app.py

