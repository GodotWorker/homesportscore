# --- Imports and Flask App ---
from flask import Flask, request, jsonify, Response
import os
import json
from threading import Lock
from flask import stream_with_context
import uuid
from datetime import datetime

app = Flask(__name__)

# --- Game Lifecycle Endpoints ---
@app.route('/api/games', methods=['GET'])
def api_list_games():
    status = request.args.get('status')
    return jsonify(list_games(status))

@app.route('/api/game', methods=['POST'])
def api_begin_game():
    data = request.json
    game = {
        'id': str(uuid.uuid4()),
        'teamA': data.get('teamA'),
        'teamB': data.get('teamB'),
        'scoreA': 0,
        'scoreB': 0,
        'status': 'live',
        'startTime': datetime.now().isoformat(),
        'period': data.get('period', '1st Qtr'),
        'meta': data.get('meta', {})
    }
    add_game(game)
    return jsonify(game)

@app.route('/api/game/<game_id>', methods=['PATCH'])
def api_update_game(game_id):
    updates = request.json
    update_game(game_id, updates)
    return jsonify(get_game(game_id))

@app.route('/api/game/<game_id>/end', methods=['POST'])
def api_end_game(game_id):
    update_game(game_id, {'status': 'past', 'endTime': datetime.now().isoformat()})
    return jsonify(get_game(game_id))
# --- Game Data Model and Storage ---
GAMES_FILE = 'games.json'

def load_games():
  if os.path.exists(GAMES_FILE):
    with open(GAMES_FILE, 'r') as f:
      try:
        return json.load(f)
      except Exception:
        return []
  return []

def save_games(games):
  with open(GAMES_FILE, 'w') as f:
    json.dump(games, f)

def add_game(game):
  games = load_games()
  games.append(game)
  save_games(games)

def update_game(game_id, updates):
  games = load_games()
  for game in games:
    if game.get('id') == game_id:
      game.update(updates)
      break
  save_games(games)

def get_game(game_id):
  games = load_games()
  for game in games:
    if game.get('id') == game_id:
      return game
  return None

def list_games(status=None):
  games = load_games()
  if status:
    return [g for g in games if g.get('status') == status]
  return games
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
    # Load all games
    games = load_games()
    # Build HTML for each game
    def game_card(game):
        live_dot = '<span class="text-red-500 text-sm font-bold animate-pulse">● LIVE</span>' if game['status'] == 'live' else ''
        period = f'<p class="text-text-secondary text-sm">{game.get("period", "")}</p>' if game['status'] == 'live' else f'<p class="text-text-secondary text-sm">{game.get("startTime", "")}</p>'
        opacity = '' if game['status'] == 'live' else 'opacity-70'
        return f'''
        <div class="bg-card-color rounded-lg p-4 flex items-center justify-between {opacity}">
            <div class="flex flex-col">
                <p class="font-semibold">{game.get("teamA", "Team A")} vs. {game.get("teamB", "Team B")}</p>
                <div class="flex items-center gap-2">
                    {live_dot}
                    {period}
                </div>
            </div>
            <div class="text-lg font-bold">{game.get("scoreA", 0)} - {game.get("scoreB", 0)}</div>
        </div>
        '''
    game_cards = '\n'.join([game_card(g) for g in games])
    # Serve main screen UI
    html = f"""
<!DOCTYPE html>
<html lang=\"en\"><head>
<meta charset=\"utf-8\"/>
<link crossorigin=\"\" href=\"https://fonts.gstatic.com/\" rel=\"preconnect\"/>
<link as=\"style\" href=\"https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900\" onload=\"this.rel='stylesheet'\" rel=\"stylesheet\"/>
<link href=\"https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined\" rel=\"stylesheet\"/>
<title>Live Scoreboard</title>
<link href=\"data:image/x-icon;base64,\" rel=\"icon\" type=\"image/x-icon\"/>
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
      .material-symbols-outlined {{
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
      }}
    </style>
<style>
    body {{
      min-height: max(884px, 100dvh);
    }}
  </style>
  </head>
<body class=\"bg-background-color text-text-primary\" style='font-family: Lexend, "Noto Sans", sans-serif;'>
<div class=\"relative flex h-auto min-h-screen w-full flex-col justify-between group/design-root overflow-x-hidden\">
<div class=\"flex-grow\">
<header class=\"sticky top-0 z-10 bg-background-color/80 backdrop-blur-sm\">
<div class=\"flex items-center p-4 justify-between\">
<h1 class=\"text-xl font-bold tracking-tight text-center flex-1\">Live Scores</h1>
<button class=\"flex items-center justify-center rounded-full h-10 w-10 text-text-primary hover:bg-card-color transition-colors\">
<span class=\"material-symbols-outlined\"> settings </span>
</button>
</div>
<div class=\"border-b border-border-color px-4\">
<nav class=\"flex gap-4 -mb-px\">
<a class=\"flex items-center justify-center border-b-2 border-primary-color text-primary-color py-3 px-2\" href=\"#\">
<span class=\"text-sm font-semibold\">All</span>
</a>
<a class=\"flex items-center justify-center border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-text-secondary py-3 px-2 transition-colors\" href=\"#\">
<span class=\"text-sm font-semibold\">Live</span>
</a>
<a class=\"flex items-center justify-center border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-text-secondary py-3 px-2 transition-colors\" href=\"#\">
<span class=\"text-sm font-semibold\">Upcoming</span>
</a>
</nav>
</div>
</header>
<main class=\"p-4 space-y-4\">
{game_cards}
</main>
</div>
<footer class=\"sticky bottom-0 bg-background-color/80 backdrop-blur-sm border-t border-border-color\">
<nav class=\"flex justify-around py-2\">
<a class=\"flex flex-col items-center justify-center gap-1 text-text-secondary w-full py-2 hover:text-primary-color transition-colors\" href=\"#\">
<span class=\"material-symbols-outlined\"> home </span>
<span class=\"text-xs font-medium\">Home</span>
</a>
<a class=\"flex flex-col items-center justify-center gap-1 text-primary-color w-full py-2 rounded-lg bg-primary-color/10\" href=\"#\">
<span class=\"material-symbols-outlined\" style=\"font-variation-settings: 'FILL' 1\"> emoji_events </span>
<span class=\"text-xs font-medium\">Scores</span>
</a>
<a class=\"flex flex-col items-center justify-center gap-1 text-text-secondary w-full py-2 hover:text-primary-color transition-colors\" href=\"#\">
<span class=\"material-symbols-outlined\"> leaderboard </span>
<span class=\"text-xs font-medium\">Standings</span>
</a>
<a class=\"flex flex-col items-center justify-center gap-1 text-text-secondary w-full py-2 hover:text-primary-color transition-colors\" href=\"#\">
<span class=\"material-symbols-outlined\"> newspaper </span>
<span class=\"text-xs font-medium\">News</span>
</a>
<a class=\"flex flex-col items-center justify-center gap-1 text-text-secondary w-full py-2 hover:text-primary-color transition-colors\" href=\"#\">
<span class=\"material-symbols-outlined\"> more_horiz </span>
<span class=\"text-xs font-medium\">More</span>
</a>
</nav>
</footer>
</div>

</body></html>
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

@app.route('/api/begin', methods=['GET', 'POST'])
def api_begin():
    ip = request.args.get('ip') or request.form.get('ip')
    if not ip:
        return jsonify({'error': 'No IP provided'}), 400
    set_begin_ip(ip)
    return jsonify({'success': True, 'ip': ip})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
