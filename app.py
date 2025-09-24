from flask import Flask, request, jsonify, Response
import os
import json
from threading import Lock
from flask import stream_with_context

app = Flask(__name__)
STATE_FILE = 'score_state.json'

def get_default_state():
    return {
        'homeRuns': '0',
        'awayRuns': '0',
        'balls': '0',
        'strikes': '0',
        'outs': '0',
        'lastSide': None  # Add lastSide to state
    }

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return get_default_state()
    return get_default_state()

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

@app.route('/api/score')
def api_score():
    state = load_state()
    return jsonify(state)

@app.route('/')
def index():
    state = load_state()
    # Ensure defaults for display
    for k in ['homeRuns', 'awayRuns', 'balls', 'strikes', 'outs']:
        if state.get(k) is None:
            state[k] = '0'
    last_side = state.get('lastSide')
    # Serve HTML scoreboard
    html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\"/>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>
<link crossorigin=\"\" href=\"https://fonts.gstatic.com/\" rel=\"preconnect\"/>
<link as=\"style\" href=\"https://fonts.googleapis.com/css2?display=swap&family=Lexend:wght@400;500;700;900&family=Noto+Sans:wght@400;500;700;900\" onload=\"this.rel='stylesheet'\" rel=\"stylesheet\"/>
<title>Live Score</title>
<script src=\"https://cdn.tailwindcss.com?plugins=forms,container-queries\"></script>
<style type=\"text/tailwindcss\">
  :root {{
    --primary-color: #0b73da;
    --background-color: #111827;
    --card-color: #1f2937;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --border-color: #374151;
  }}
</style>
<style>
  .live-dot {{
    animation: blink 3s infinite;
  }}
  @keyframes blink {{
    0%, 50%, 100% {{ opacity: 1; }}
    25%, 75% {{ opacity: 0; }}
  }}
  .highlight {{
    background-color: #37415155;
    border-radius: 0.75rem;
    transition: background 0.3s;
    box-shadow: 0 0 0 2px #37415155;
    padding: 0.25em 0.5em;
    position: relative;
    display: inline-block;
  }}
  .batting-label {{
    display: block;
    font-size: 0.75rem;
    color: #9ca3af;
    text-align: center;
    margin-top: 0.15em;
    font-weight: 500;
    letter-spacing: 0.02em;
  }}
</style>
</head>
<body class=\"bg-background-color text-text-primary\" style='font-family: Lexend, "Noto Sans", sans-serif;'>
<div class=\"relative flex h-full min-h-screen w-full flex-col justify-center items-center overflow-hidden p-4\">
  <div class=\"absolute top-0 left-0 w-full h-full bg-gradient-to-br from-primary-color/20 via-transparent to-transparent opacity-50\"></div>
  <div class=\"w-full max-w-md bg-card-color/50 backdrop-blur-xl rounded-2xl shadow-2xl p-6 md:p-8 z-10\">
    <!-- Header with LIVE dot -->
    <div class=\"flex justify-center items-center mb-6\">
      <span class=\"text-red-500 text-sm font-bold live-dot\">● LIVE</span>
    </div>
    <!-- Scoreboard -->
    <div class=\"flex items-center justify-center mb-6\">
      <span id=\"homeRuns\" class=\"text-5xl md:text-7xl font-black text-text-primary mx-4{' highlight' if last_side == 'home' else ''}\">{state['homeRuns']}
        {"<span class='batting-label'>Currently Batting</span>" if last_side == 'home' else ""}
      </span>
      <span class=\"text-4xl md:text-5xl font-light text-text-secondary\">-</span>
      <span id=\"awayRuns\" class=\"text-5xl md:text-7xl font-black text-text-primary mx-4{' highlight' if last_side == 'away' else ''}\">{state['awayRuns']}
        {"<span class='batting-label'>Currently Batting</span>" if last_side == 'away' else ""}
      </span>
    </div>
    <!-- Current batter info -->
    <div class=\"grid grid-cols-3 gap-4 text-center bg-background-color/30 p-4 rounded-lg\">
      <div>
        <p class=\"text-sm text-text-secondary font-medium\">BALLS</p>
        <p id=\"balls\" class=\"text-2xl font-bold text-text-primary\">{state['balls']}</p>
      </div>
      <div>
        <p class=\"text-sm text-text-secondary font-medium\">STRIKES</p>
        <p id=\"strikes\" class=\"text-2xl font-bold text-text-primary\">{state['strikes']}</p>
      </div>
      <div>
        <p class=\"text-sm text-text-secondary font-medium\">OUTS</p>
        <p id=\"outs\" class=\"text-2xl font-bold text-text-primary\">{state['outs']}</p>
      </div>
    </div>
  </div>
</div>
<script>
function updateScore() {{
  fetch('/api/score')
    .then(response => response.json())
    .then(data => {{
      document.getElementById('homeRuns').textContent = data.homeRuns;
      document.getElementById('awayRuns').textContent = data.awayRuns;
      document.getElementById('balls').textContent = data.balls;
      document.getElementById('strikes').textContent = data.strikes;
      document.getElementById('outs').textContent = data.outs;
      // Highlight last side and show batting label
      document.getElementById('homeRuns').classList.remove('highlight');
      document.getElementById('awayRuns').classList.remove('highlight');
      document.querySelectorAll('.batting-label').forEach(e => e.remove());
      if (data.lastSide === 'home') {{
        document.getElementById('homeRuns').classList.add('highlight');
        let label = document.createElement('span');
        label.className = 'batting-label';
        label.textContent = 'Currently Batting';
        document.getElementById('homeRuns').appendChild(label);
      }} else if (data.lastSide === 'away') {{
        document.getElementById('awayRuns').classList.add('highlight');
        let label = document.createElement('span');
        label.className = 'batting-label';
        label.textContent = 'Currently Batting';
        document.getElementById('awayRuns').appendChild(label);
      }}
    }});
}}
setInterval(updateScore, 2000);
</script>
</body>
</html>
    """
    return Response(html, mimetype='text/html')

@app.route('/api/update')
def api_update():
    state = load_state()
    params = request.args
    # Reset all values if reset=true
    if params.get('reset') == 'true':
        state = get_default_state()
        save_state(state)
        return Response('Score reset', mimetype='text/plain')
    # If parameters exist, update the score/state
    if params:
        # Ensure defaults
        for k in ['homeRuns', 'awayRuns', 'balls', 'strikes', 'outs']:
            if state.get(k) is None:
                state[k] = '0'
        # Update runs depending on side
        if params.get('side') == 'home':
            state['homeRuns'] = params.get('runs', state['homeRuns'])
            state['lastSide'] = 'home'
        elif params.get('side') == 'away':
            state['awayRuns'] = params.get('runs', state['awayRuns'])
            state['lastSide'] = 'away'
        # Update batter state
        if params.get('balls') is not None:
            state['balls'] = params.get('balls')
        if params.get('strikes') is not None:
            state['strikes'] = params.get('strikes')
        if params.get('outs') is not None:
            state['outs'] = params.get('outs')
        save_state(state)
        return Response('Score updated', mimetype='text/plain')
    return Response('No update parameters provided', mimetype='text/plain')

# --- Video Feed Handling ---

latest_frame = None
frame_lock = Lock()

@app.route('/api/feed', methods=['POST'])
def api_feed():
    global latest_frame
    with frame_lock:
        latest_frame = request.data
    return Response('Frame received', mimetype='text/plain')

@app.route('/stream')
def stream():
    def generate():
        while True:
            with frame_lock:
                frame = latest_frame
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(stream_with_context(generate()), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
