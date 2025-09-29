# --- Begin Game IP ---
BEGIN_IP_FILE = 'begin_ip.json'
def set_begin_ip(ip):
  with open(BEGIN_IP_FILE, 'w') as f:
    json.dump({'ip': ip}, f)

def get_begin_ip():
  if os.path.exists(BEGIN_IP_FILE):
    with open(BEGIN_IP_FILE, 'r') as f:
      try:
        return json.load(f).get('ip')
      except Exception:
        return None
  return None
from flask import Flask, request, jsonify, Response
import os
import json
from threading import Lock
from flask import stream_with_context

app = Flask(__name__)
STATE_FILE = 'score_state.json'
HISTORY_FILE = 'score_history.json'

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

def save_history(state):
  history = []
  if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r') as f:
      try:
        history = json.load(f)
      except Exception:
        history = []
  history.append(state)
  with open(HISTORY_FILE, 'w') as f:
    json.dump(history, f)

def pop_history():
  history = []
  if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r') as f:
      try:
        history = json.load(f)
      except Exception:
        history = []
  if len(history) > 1:
    history.pop()  # Remove current state
    prev = history[-1]
    with open(HISTORY_FILE, 'w') as f:
      json.dump(history, f)
    return prev
  return None


def save_state(state):
  with open(STATE_FILE, 'w') as f:
    json.dump(state, f)
  save_history(state)

@app.route('/api/score')
def api_score():
    state = load_state()
    return jsonify(state)


@app.route('/')
def index():
    user_ip = request.remote_addr
    begin_ip = get_begin_ip()
    if begin_ip and user_ip == begin_ip:
        # Serve New Game Setup HTML
        html = """
<!DOCTYPE html>
<html class=\"dark\" lang=\"en\"><head>
<meta charset=\"utf-8\"/>
<meta content=\"width=device-width, initial-scale=1.0\" name=\"viewport\"/>
<title>New Game Setup</title>
<link href=\"https://fonts.googleapis.com\" rel=\"preconnect\"/>
<link crossorigin=\"\" href=\"https://fonts.gstatic.com/\" rel=\"preconnect\"/>
<link href=\"https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;700;900&amp;display=swap\" rel=\"stylesheet\"/>
<script src=\"https://cdn.tailwindcss.com?plugins=forms,container-queries\"></script>
<style>body { min-height: max(884px, 100dvh); } .form-select { background-image: url('data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 20 20\'%3e%3cpath stroke=\'%239ca3af\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'1.5\' d=\'M6 8l4 4 4-4\'/\%3e%3c/svg%3e'); background-position: right 0.5rem center; background-repeat: no-repeat; background-size: 1.5em 1.5em; padding-right: 2.5rem; -webkit-print-color-adjust: exact; print-color-adjust: exact; }</style>
<body class=\"bg-background-light dark:bg-background-dark font-display\">
<div class=\"flex flex-col h-screen justify-between\">
<div>
<header class=\"p-4 flex items-center justify-between\">
<button class=\"text-slate-800 dark:text-white\"><svg fill=\"currentColor\" height=\"24\" viewBox=\"0 0 256 256\" width=\"24\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z\"></path></svg></button>
<h1 class=\"text-xl font-bold text-slate-900 dark:text-white text-center flex-1 pr-6\">New Game</h1>
</header>
<main class=\"p-4 space-y-6\">
<div class=\"flex items-center justify-between space-x-2\">
<div class=\"flex-1\">
<select aria-label=\"Team 1\" class=\"form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary\" id=\"team-1\">
<option>Select Team</option>
{''.join([f'<option>{team}</option>' for team in load_teams()])}
</select>
</div>
<span class=\"text-slate-500 dark:text-slate-400 font-bold text-lg\">vs</span>
<div class=\"flex-1\">
<select aria-label=\"Team 2\" class=\"form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary\" id=\"team-2\">
<option>Select Team</option>
{''.join([f'<option>{team}</option>' for team in load_teams()])}
</select>
</div>
</div>
<div class=\"space-y-2\">
<label class=\"text-sm font-medium text-slate-700 dark:text-slate-300\" for=\"game-type\">Game Type</label>
<select class=\"form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary\" id=\"game-type\">
<option>Select Game Type</option>
<option>Semis</option>
<option>Finals</option>
<option>Playoffs</option>
<option>League Game</option>
<option>Exhibition</option>
</select>
</div>
<div class=\"grid grid-cols-2 gap-4\">
<div class=\"space-y-2\">
<label class=\"text-sm font-medium text-slate-700 dark:text-slate-300\" for=\"age-group\">Age Group</label>
<select class=\"form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary\" id=\"age-group\">
<option>Select Age</option>
<option>U10</option>
<option>U12</option>
<option>U14</option>
<option>U16</option>
<option>U18</option>
</select>
</div>
<div class=\"space-y-2\">
<label class=\"text-sm font-medium text-slate-700 dark:text-slate-300\" for=\"gender\">Gender</label>
<select class=\"form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary\" id=\"gender\">
<option>Select Gender</option>
<option>G (Girls)</option>
<option>B (Boys)</option>
<option>Co-ed</option>
</select>
</div>
</div>
</main>
</div>
<footer class=\"p-4 pb-8\">
<button class=\"w-full bg-red-600 text-white font-bold py-3 px-5 rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-background-dark\">Go Live!</button>
</footer>
</div>
</body></html>
        """
        return Response(html, mimetype='text/html')
    # Otherwise, serve scoreboard
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
  updated = False
  # Ensure defaults
  for k in ['homeRuns', 'awayRuns', 'balls', 'strikes', 'outs']:
    if state.get(k) is None:
      state[k] = '0'

  # Only update runs based on side
  side = params.get('side')
  if side in ['home', 'away']:
    run_key = 'homeRuns' if side == 'home' else 'awayRuns'
    # Increment/decrement
    if params.get('add_runs') is not None:
      try:
        state[run_key] = str(int(state[run_key]) + int(params.get('add_runs')))
        updated = True
      except Exception:
        pass
    # Direct set
    if params.get('runs') is not None:
      state[run_key] = params.get('runs')
      updated = True
    state['lastSide'] = side
    updated = True
  # Balls, strikes, outs can still be set directly or incremented
  for k in ['balls', 'strikes', 'outs']:
    add_key = f'add_{k}'
    if add_key in params:
      try:
        state[k] = str(int(state[k]) + int(params[add_key]))
        updated = True
      except Exception:
        pass
    if params.get(k) is not None:
      state[k] = params.get(k)
      updated = True
  if updated:
    save_state(state)
    return Response('Score updated', mimetype='text/plain')
  return Response('No update parameters provided', mimetype='text/plain')

# Undo endpoint
@app.route('/api/undo', methods=['POST'])
def api_undo():
  prev = pop_history()
  if prev:
    with open(STATE_FILE, 'w') as f:
      json.dump(prev, f)
    return Response('Undo successful', mimetype='text/plain')
  return Response('Nothing to undo', mimetype='text/plain')

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
