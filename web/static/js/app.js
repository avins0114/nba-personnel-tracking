// NBA Spacing Analyzer - Frontend Application
const API_BASE = '/api';

// State
let currentGame = null;
let currentEvent = null;
let currentFrame = 0;
let isPlaying = false;
let animationFrameId = null;
let playbackSpeed = 1.0;

// Canvas setup
const canvas = document.getElementById('courtCanvas');
const ctx = canvas.getContext('2d');

// Court dimensions (NBA: 94 x 50 feet)
const COURT_WIDTH = 94;
const COURT_HEIGHT = 50;
const BASKET_X = 5.25;
const BASKET_Y = 25;
const THREE_POINT_RADIUS = 23.75;
const PAINT_WIDTH = 16;
const PAINT_LENGTH = 19;

// Colors
const TEAM_COLORS = {
    home: '#E31837',
    away: '#17408B'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadGames();
    setupCanvas();
});

function setupEventListeners() {
    document.getElementById('gameSelect').addEventListener('change', onGameSelect);
    document.getElementById('loadEventBtn').addEventListener('click', loadEvent);
    document.getElementById('playPauseBtn').addEventListener('click', togglePlayback);
    document.getElementById('showSpacing').addEventListener('change', redraw);
    document.getElementById('showVideo').addEventListener('change', toggleVideo);
    document.getElementById('speedSlider').addEventListener('input', (e) => {
        playbackSpeed = parseFloat(e.target.value);
        document.getElementById('speedValue').textContent = `${playbackSpeed.toFixed(1)}x`;
    });
}

async function loadGames() {
    try {
        const response = await fetch(`${API_BASE}/games`);
        const data = await response.json();
        const select = document.getElementById('gameSelect');
        
        select.innerHTML = '<option value="">Select a game...</option>';
        data.games.forEach(game => {
            const option = document.createElement('option');
            option.value = game.filename;
            option.textContent = `${game.away_team} @ ${game.home_team} (${game.game_date})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading games:', error);
        document.getElementById('gameSelect').innerHTML = '<option value="">Error loading games</option>';
    }
}

function onGameSelect(e) {
    currentGame = e.target.value;
    if (currentGame) {
        loadGameInfo();
    }
}

async function loadGameInfo() {
    try {
        const response = await fetch(`${API_BASE}/game/${currentGame}/info`);
        const info = await response.json();
        // Could display game info here
    } catch (error) {
        console.error('Error loading game info:', error);
    }
}

async function loadEvent() {
    const eventIndex = parseInt(document.getElementById('eventInput').value);
    if (isNaN(eventIndex) || !currentGame) {
        alert('Please select a game and enter a valid event number');
        return;
    }

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE}/game/${currentGame}/event/${eventIndex}`);
        if (!response.ok) {
            throw new Error('Failed to load event');
        }
        currentEvent = await response.json();
        currentFrame = 0;
        
        displayEventInfo();
        setupCanvas();
        redraw();
        updateMetrics();
    } catch (error) {
        console.error('Error loading event:', error);
        alert('Error loading event: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayEventInfo() {
    const infoDiv = document.getElementById('eventInfo');
    if (currentEvent) {
        infoDiv.innerHTML = `
            <strong>${currentEvent.home_team} vs ${currentEvent.away_team}</strong><br>
            Frames: ${currentEvent.frame_count}<br>
            Duration: ${currentEvent.duration.toFixed(1)}s<br>
            Offense: ${currentEvent.offensive_team_id === currentEvent.home_team_id ? currentEvent.home_team : currentEvent.away_team}
        `;
    }
}

function setupCanvas() {
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth - 32; // padding
    const aspectRatio = COURT_WIDTH / COURT_HEIGHT;
    const canvasHeight = containerWidth / aspectRatio;
    
    canvas.width = containerWidth;
    canvas.height = canvasHeight;
    
    // Scale factor for drawing
    canvas.scaleX = canvas.width / COURT_WIDTH;
    canvas.scaleY = canvas.height / COURT_HEIGHT;
}

function redraw() {
    if (!currentEvent || !currentEvent.moments || currentEvent.moments.length === 0) {
        return;
    }

    const moment = currentEvent.moments[currentFrame];
    if (!moment) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw court
    drawCourt();

    // Draw spacing overlay if enabled
    if (document.getElementById('showSpacing').checked) {
        drawSpacingOverlay(moment);
    }

    // Draw players and ball
    drawPlayers(moment);
    drawBall(moment);

    // Update clock
    updateClock(moment);

    // Update spacing display
    updateSpacingDisplay(moment);
}

function drawCourt() {
    const scaleX = canvas.scaleX;
    const scaleY = canvas.scaleY;

    // Court background
    ctx.fillStyle = '#F5E6C8';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Court outline
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2 * scaleX;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);

    // Center line
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();

    // Left basket area
    drawBasketArea(BASKET_X, BASKET_Y, scaleX, scaleY, true);
    
    // Right basket area
    drawBasketArea(COURT_WIDTH - BASKET_X, BASKET_Y, scaleX, scaleY, false);
}

function drawBasketArea(basketX, basketY, scaleX, scaleY, leftSide) {
    const x = basketX * scaleX;
    const y = basketY * scaleY;

    // Paint
    ctx.fillStyle = '#E8D4B8';
    const paintX = leftSide ? 0 : (COURT_WIDTH - PAINT_LENGTH) * scaleX;
    const paintY = (basketY - PAINT_WIDTH / 2) * scaleY;
    ctx.fillRect(paintX, paintY, PAINT_LENGTH * scaleX, PAINT_WIDTH * scaleY);
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2 * scaleX;
    ctx.strokeRect(paintX, paintY, PAINT_LENGTH * scaleX, PAINT_WIDTH * scaleY);

    // Basket
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2 * scaleX;
    ctx.beginPath();
    ctx.arc(x, y, 0.75 * scaleX, 0, Math.PI * 2);
    ctx.stroke();

    // Three-point line
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2 * scaleX;
    ctx.beginPath();
    ctx.arc(x, y, THREE_POINT_RADIUS * scaleX, 0, Math.PI * 2);
    ctx.stroke();
}

function drawSpacingOverlay(moment) {
    if (!currentEvent) return;

    const offense = moment.players.filter(p => 
        p.team_id === currentEvent.offensive_team_id
    );

    if (offense.length < 3) return;

    // Calculate convex hull
    const points = offense.map(p => ({
        x: p.x * canvas.scaleX,
        y: p.y * canvas.scaleY
    }));

    // Simple convex hull (Graham scan simplified)
    const hull = calculateConvexHull(points);

    if (hull.length >= 3) {
        ctx.fillStyle = 'rgba(52, 168, 83, 0.3)';
        ctx.strokeStyle = '#34a853';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(hull[0].x, hull[0].y);
        for (let i = 1; i < hull.length; i++) {
            ctx.lineTo(hull[i].x, hull[i].y);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
    }
}

function calculateConvexHull(points) {
    if (points.length < 3) return points;

    // Sort by x, then y
    points.sort((a, b) => a.x - b.x || a.y - b.y);

    const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);

    const lower = [];
    for (let i = 0; i < points.length; i++) {
        while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], points[i]) <= 0) {
            lower.pop();
        }
        lower.push(points[i]);
    }

    const upper = [];
    for (let i = points.length - 1; i >= 0; i--) {
        while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], points[i]) <= 0) {
            upper.pop();
        }
        upper.push(points[i]);
    }

    upper.pop();
    lower.pop();
    return lower.concat(upper);
}

function drawPlayers(moment) {
    if (!currentEvent) return;

    moment.players.forEach(player => {
        const isHome = player.team_id === currentEvent.home_team_id;
        const color = isHome ? TEAM_COLORS.home : TEAM_COLORS.away;
        
        const x = player.x * canvas.scaleX;
        const y = player.y * canvas.scaleY;
        const radius = 2.5 * canvas.scaleX;

        // Player circle
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Jersey number
        ctx.fillStyle = 'white';
        ctx.font = `${8 * canvas.scaleX}px Inter`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(player.jersey || player.player_id, x, y);
    });
}

function drawBall(moment) {
    const x = moment.ball.x * canvas.scaleX;
    const y = moment.ball.y * canvas.scaleY;
    const radius = (1.2 + moment.ball.radius * 0.1) * canvas.scaleX;

    ctx.fillStyle = '#FF6B00';
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 1;
    ctx.stroke();
}

function updateClock(moment) {
    const quarter = moment.quarter;
    const gameClock = moment.game_clock;
    const shotClock = moment.shot_clock || 0;
    
    const mins = Math.floor(gameClock / 60);
    const secs = (gameClock % 60).toFixed(2);
    
    document.getElementById('clockDisplay').textContent = 
        `Q${quarter} | ${mins}:${secs.padStart(5, '0')} | Shot: ${shotClock.toFixed(1)}`;
}

function updateSpacingDisplay(moment) {
    if (!currentEvent || !document.getElementById('showSpacing').checked) {
        document.getElementById('spacingDisplay').textContent = '';
        return;
    }

    // Calculate spacing score (simplified)
    const offense = moment.players.filter(p => 
        p.team_id === currentEvent.offensive_team_id
    );

    if (offense.length < 3) {
        document.getElementById('spacingDisplay').textContent = '';
        return;
    }

    // Calculate hull area
    const points = offense.map(p => ({ x: p.x, y: p.y }));
    const hull = calculateConvexHull(points);
    const hullArea = calculatePolygonArea(hull);

    // Simple spacing score
    const spacingScore = Math.min(100, (hullArea / 800) * 100);

    document.getElementById('spacingDisplay').textContent = 
        `Spacing: ${spacingScore.toFixed(1)} | Hull: ${hullArea.toFixed(0)} sq ft`;
}

function calculatePolygonArea(points) {
    if (points.length < 3) return 0;
    let area = 0;
    for (let i = 0; i < points.length; i++) {
        const j = (i + 1) % points.length;
        area += points[i].x * points[j].y;
        area -= points[j].x * points[i].y;
    }
    return Math.abs(area) / 2;
}

function updateMetrics() {
    if (!currentEvent || !currentEvent.metrics) return;

    const metrics = currentEvent.metrics;
    document.getElementById('spacingScore').textContent = 
        metrics.avg_spacing ? metrics.avg_spacing.toFixed(1) : '--';
    document.getElementById('hullArea').textContent = 
        metrics.avg_hull_area ? `${metrics.avg_hull_area.toFixed(0)} sq ft` : '--';
    document.getElementById('avgDistance').textContent = 
        metrics.avg_pairwise_dist ? `${metrics.avg_pairwise_dist.toFixed(1)} ft` : '--';
    document.getElementById('defenderDist').textContent = 
        metrics.avg_defender_dist ? `${metrics.avg_defender_dist.toFixed(1)} ft` : '--';
}

function togglePlayback() {
    if (!currentEvent || !currentEvent.moments) return;

    isPlaying = !isPlaying;
    document.getElementById('playPauseBtn').textContent = isPlaying ? 'Pause' : 'Play';

    if (isPlaying) {
        animate();
    } else {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }
    }
}

let lastFrameTime = 0;
function animate() {
    if (!isPlaying || !currentEvent) return;

    const now = performance.now();
    const elapsed = now - lastFrameTime;
    const frameInterval = (1000 / 25) / playbackSpeed; // 25 FPS

    if (elapsed >= frameInterval) {
        currentFrame = (currentFrame + 1) % currentEvent.moments.length;
        redraw();
        updateMetrics();
        lastFrameTime = now;
    }

    animationFrameId = requestAnimationFrame(animate);
}

function toggleVideo() {
    const showVideo = document.getElementById('showVideo').checked;
    const videoContainer = document.getElementById('videoContainer');
    if (showVideo) {
        videoContainer.classList.remove('hidden');
    } else {
        videoContainer.classList.add('hidden');
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

// Handle window resize
window.addEventListener('resize', () => {
    setupCanvas();
    redraw();
});

