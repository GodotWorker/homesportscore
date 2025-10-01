import json
import uuid
import random
import string
import re
from flask import Flask, render_template_string, redirect, url_for, request, make_response, jsonify

# --- 1. Configuration & Helper Functions ---

# Unique ID generation for games
def generate_game_code(length=7):
    """Generates a unique, short, alphanumeric code (e.g., 6NH3D2E)."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def ordinal(n):
    if n % 100 in (11, 12, 13):
        return f"{n}th"
    elif n % 10 == 1:
        return f"{n}st"
    elif n % 10 == 2:
        return f"{n}nd"
    elif n % 10 == 3:
        return f"{n}rd"
    else:
        return f"{n}th"

# Simple password for web-based access (in a real app, this would use proper authentication)
ADMIN_PASSWORD = "softballadmin"

# Provided list of teams with image URLs
TEAMS_DATA = {
    "Genl Hendrik Schoeman": "https://www.checkelog.co.za/images/Front_Logos/Laerskool-Genl-Hendrik-Schoeman.png",
    "Hermanstad": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Hermanstad.jpg",
    "Homespun": "https://www.checkelog.co.za/images/Front_Logos/High_Schools/Homespun.jpg",
    "Rachel de Beer": "https://lsrdb.co.za/sitepad-data/uploads/2023/09/Rachel-de-Beer-Nuwe-Logo.png",
    "Simon Bekker": "https://www.checkelog.co.za/images/Front_Logos/Laerskool-Simon-Bekker.jpg",
    "Skuilkrans": "https://upload.wikimedia.org/wikipedia/commons/b/b3/Laerskool_Skuilkrans,_logo_in_Gracelaan,_Pretoria,_a.jpg",
    "Totiusdal": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Totiusdal.png",
    "Danie Malan": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Danie-Malan.jpg",
    "Hennopspark": "http://hennops.com/wp-content/uploads/2018/12/cropped-LAERSKOOL-HENNOPSPARK-SKOOLWAPEN-en-kleure-2.png",
    "Louis Leipoldt": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Louis-Leipoldt.png",
    "Saamspan": "https://www.checkelog.co.za/images/Front_Logos/Laerskool-Saamspan.png",
    "Villieria": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Villeria.gif",
    "Voorpos": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Voorpos_New.jpg",
    "Tuine": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Tuine.png",
    "Tygerpoort": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Tygerpoort.png",
    "Genl Beyers": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool_Genl_Beyers_-_New.png",
    "Haakdoorn": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Haakdoorn.png",
    "Pierneef": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Pierneef.gif",
    "Silverton": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Silverton.jpeg",
    "Uniefees": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Uniefees-New.jpg",
    "Voortrekker Eeufees": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Voortrekker-Eeufees.jpg",
    "Broederstroom": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Broederstroom.png",
    "Brits": "https://www.checkelog.co.za/images/Front_Logos/Primary_Schools/Laerskool-Brits.jpg",
    "Hartbeespoort High School": "https://hsharties.co.za/wp-content/uploads/2024/01/Harties-logo-portrait-trsprt.png"
}
AGE_GROUPS = [f"U{i}" for i in range(10, 20)]
GENDER_OPTIONS = ["B", "G"]

# Global variable for dynamic state management (simulating a database)
GAMES_DATA = [
    {
        "code": "8C7F0A4",
        "home_team": "Phoenix Bats",
        "away_team": "Canyon Cats",
        "home_score": 14,
        "away_score": 7,
        "status": "LIVE",
        "period": "1st Inning",
        "game_type": "League Game",
        "age_group": "U14",
        "gender": "B",
        "time": None,
        "device_id": "DEV-001",
        "balls": 3, "strikes": 1, "outs": 2, "bases_state": "13"
    },
    {
        "code": "A1B2C3D",
        "home_team": "Hermanstad",
        "away_team": "Rachel de Beer",
        "home_score": 0,
        "away_score": 0,
        "status": "UPCOMING",
        "period": "Pre-Game",
        "game_type": "Semis",
        "age_group": "U12",
        "gender": "G",
        "time": "16:00",
        "device_id": "DEV-002",
        "balls": 0, "strikes": 0, "outs": 0, "bases_state": "0"
    }
]

# --- 2. HTML Templates ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Live Softball Scores</title>
<link href="data:image/x-icon;base64," rel="icon" type="image/x-icon"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<style type="text/tailwindcss">
  :root {
    --primary-color: #0b73da;
    --background-color: #f5f7f8;
    --card-color: #e5e7eb;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border-color: #d1d5db;
  }
  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
</style>
<style>
  body {
    min-height: max(884px, 100dvh);
  }
</style>
</head>
<body class="bg-background-color text-text-primary" style='font-family: Lexend, "Noto Sans", sans-serif;'>
<div class="relative flex h-auto min-h-screen w-full flex-col justify-between group/design-root overflow-x-hidden">
<div class="flex-grow">
<header class="sticky top-0 z-10 bg-background-color/80 backdrop-blur-sm">
<div class="flex items-center p-4 justify-between">
<h1 class="text-xl font-bold tracking-tight text-center flex-1">Live Scores</h1>
<a href="{{ url_for('web_login') }}" class="flex items-center justify-center rounded-full h-10 w-10 text-text-primary hover:bg-card-color transition-colors">
<span class="material-symbols-outlined"> settings </span>
</a>
</div>
<div class="border-b border-border-color px-4">
<nav class="flex gap-4 -mb-px">
<a class="{% if filter == 'all' %}flex items-center justify-center border-b-2 border-primary-color text-primary-color py-3 px-2{% else %}flex items-center justify-center border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-text-secondary py-3 px-2 transition-colors{% endif %}" href="/softball?filter=all">
<span class="text-sm font-semibold">All</span>
</a>
<a class="{% if filter == 'live' %}flex items-center justify-center border-b-2 border-primary-color text-primary-color py-3 px-2{% else %}flex items-center justify-center border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-text-secondary py-3 px-2 transition-colors{% endif %}" href="/softball?filter=live">
<span class="text-sm font-semibold">Live</span>
</a>
<a class="{% if filter == 'upcoming' %}flex items-center justify-center border-b-2 border-primary-color text-primary-color py-3 px-2{% else %}flex items-center justify-center border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-text-secondary py-3 px-2 transition-colors{% endif %}" href="/softball?filter=upcoming">
<span class="text-sm font-semibold">Upcoming</span>
</a>
<a class="{% if filter == 'past' %}flex items-center justify-center border-b-2 border-primary-color text-primary-color py-3 px-2{% else %}flex items-center justify-center border-b-2 border-transparent text-text-secondary hover:text-text-primary hover:border-text-secondary py-3 px-2 transition-colors{% endif %}" href="/softball?filter=past">
<span class="text-sm font-semibold">Past</span>
</a>
</nav>
</div>
</header>
<main class="p-4 space-y-4">
{% for game in games %}
<a href="{{ url_for('game_detail', game_code=game.code) }}">
<div class="bg-card-color rounded-lg p-4 flex items-center justify-between {% if game.status == 'UPCOMING' %}opacity-70{% endif %}">
<div class="flex flex-col">
<p class="font-semibold">{{ game.away_team }} vs. {{ game.home_team }}</p>
<div class="flex items-center gap-2">
{% if game.status == 'LIVE' %}
<span class="text-red-500 text-sm font-bold animate-pulse">● LIVE</span>
<p class="text-text-secondary text-sm">{{ game.period }}</p>
{% elif game.status == 'FINISHED' %}
<p class="text-text-secondary text-sm font-bold">FINAL</p>
{% else %}
<p class="text-text-secondary text-sm">{{ game.time }}</p>
{% endif %}
</div>
</div>
<div class="text-lg font-bold">{{ game.away_score }} - {{ game.home_score }}</div>
</div>
</a>
{% else %}
<div class="text-center p-8 bg-card-color rounded-lg mt-12">
<p class="text-lg text-text-secondary">No live games currently scheduled.</p>
</div>
{% endfor %}
</main>
</div>
</div>
</body>
</html>
"""

GAME_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Live Score</title>
<link href="data:image/x-icon;base64," rel="icon" type="image/x-icon"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<style type="text/tailwindcss">
  :root {
    --primary-color: #0b73da;
    --background-color: #f5f7f8;
    --card-color: #e5e7eb;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border-color: #d1d5db;
  }
  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
</style>
<style>
  body {
    min-height: max(884px, 100dvh);
  }
</style>
</head>
<body class="bg-background-color text-text-primary" style='font-family: Lexend, "Noto Sans", sans-serif;'>
<div class="relative flex h-full min-h-screen w-full flex-col justify-center items-center group/design-root overflow-hidden p-4">
<div class="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-primary-color/20 via-transparent to-transparent opacity-50"></div>
<div class="w-full max-w-md bg-card-color/50 backdrop-blur-xl rounded-2xl shadow-2xl p-6 md:p-8 z-10">
<div class="flex justify-between items-center mb-6">
<div class="flex items-center gap-2">
{% if game.status == 'LIVE' %}
<span class="text-red-500 text-sm font-bold animate-pulse">● LIVE</span>
{% elif game.status == 'FINISHED' %}
<span class="text-text-secondary text-sm font-bold">FINAL</span>
{% else %}
<span class="text-text-secondary text-sm font-bold">{{ game.status }}</span>
{% endif %}
</div>
<div class="flex items-center gap-2 text-sm font-semibold">
<span class="text-text-secondary">{% if game.period %}{{ game.period }}{% else %}{{ game.time }}{% endif %}</span>
<svg class="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M5 15l7-7 7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
</div>
</div>
<div class="flex items-center justify-around text-center mb-6">
<div class="flex flex-col items-center gap-3">
<div class="w-20 h-20 md:w-24 md:h-24 rounded-full bg-border-color flex items-center justify-center">
<span class="text-4xl font-bold text-white">{{ game.away_team[0] }}</span>
</div>
<h2 class="text-xl md:text-2xl font-bold text-text-primary">{{ game.away_team }}</h2>
</div>
<div class="flex items-center">
<span class="text-5xl md:text-7xl font-black text-text-primary mx-4">{{ game.away_score }}</span>
<span class="text-4xl md:text-5xl font-light text-text-secondary">-</span>
<span class="text-5xl md:text-7xl font-black text-text-primary mx-4">{{ game.home_score }}</span>
</div>
<div class="flex flex-col items-center gap-3">
<div class="w-20 h-20 md:w-24 md:h-24 rounded-full bg-border-color flex items-center justify-center">
<span class="text-4xl font-bold text-white">{{ game.home_team[0] }}</span>
</div>
<h2 class="text-xl md:text-2xl font-bold text-text-primary">{{ game.home_team }}</h2>
</div>
</div>
{% if game.status == 'LIVE' and 'Inning' in game.period %}
<div class="grid grid-cols-3 gap-4 text-center bg-background-color/30 p-4 rounded-lg">
<div>
<p class="text-sm text-text-secondary font-medium">BALLS</p>
<p class="text-2xl font-bold text-text-primary">{{ game.balls }}</p>
</div>
<div>
<p class="text-sm text-text-secondary font-medium">STRIKES</p>
<p class="text-2xl font-bold text-text-primary">{{ game.strikes }}</p>
</div>
<div>
<p class="text-sm text-text-secondary font-medium">OUTS</p>
<p class="text-2xl font-bold text-text-primary">{{ game.outs }}</p>
</div>
</div>
<div class="mt-6 flex justify-center items-center">
<div class="relative w-24 h-24">
<div class="absolute top-1/2 left-0 -translate-y-1/2 w-6 h-6 rounded-sm transform rotate-45
     {% if '2' in game.bases_state %}bg-primary-color{% else %}bg-border-color/50{% endif %}"></div>
<div class="absolute top-0 left-1/2 -translate-x-1/2 w-6 h-6 rounded-sm transform rotate-45
     {% if '3' in game.bases_state %}bg-primary-color{% else %}bg-border-color/50{% endif %}"></div>
<div class="absolute top-1/2 right-0 -translate-y-1/2 w-6 h-6 rounded-sm transform rotate-45
     {% if '1' in game.bases_state %}bg-primary-color{% else %}bg-border-color/50{% endif %}"></div>
<div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-6 bg-primary-color rounded-sm transform rotate-45"></div>
</div>
</div>
{% endif %}
</div>
<div class="absolute bottom-4 right-4 z-10">
<button onclick="window.location.reload()" class="flex items-center justify-center rounded-full h-12 w-12 text-text-primary bg-card-color/50 hover:bg-card-color transition-colors backdrop-blur-sm">
<span class="material-symbols-outlined"> refresh </span>
</button>
</div>
</div>
</body>
</html>
"""

ADMIN_HEAD = """
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{{ title }}</title>
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<style type="text/tailwindcss">
  :root {
    --primary-color: #0b73da;
    --background-color: #f5f7f8;
    --card-color: #e5e7eb;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border-color: #d1d5db;
  }
  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }
  .form-select {
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 0.5rem center;
    background-repeat: no-repeat;
    background-size: 1.5em 1.5em;
    padding-right: 2.5rem;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
</style>
<style>
  body {
    min-height: max(884px, 100dvh);
  }
</style>
</head>
<body class="bg-background-color text-text-primary" style='font-family: Lexend, "Noto Sans", sans-serif;'>
"""

WEB_LOGIN_TEMPLATE = ADMIN_HEAD + """
<div class="flex flex-col h-screen justify-center items-center p-4">
  <div class="w-full max-w-sm p-8 bg-card-color rounded-xl shadow-2xl">
    <h1 class="text-2xl font-bold text-center text-primary-color mb-2">Web Admin Access</h1>
    <h2 class="text-lg font-medium text-center text-text-primary mb-6">Create or Score Games</h2>
    <form method="POST" action="{{ url_for('web_login') }}">
      <div id="error-message" class="hidden p-3 bg-red-100 border border-red-500 rounded-lg mb-4 text-center text-red-700 text-sm">
        Incorrect password. Try again.
      </div>
      <div class="space-y-4">
        <input type="password" name="password" placeholder="Password" class="w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color form-select" autofocus>
        <button type="submit" class="w-full bg-red-500 text-white font-bold py-3 px-5 rounded-lg hover:bg-red-600 transition-colors">
          Login
        </button>
      </div>
    </form>
    <p class="text-xs text-center text-text-secondary mt-4">Hint: Password is "{{ admin_password }}"</p>
  </div>
</div>
<script>
  {% if error %}
    document.getElementById('error-message').classList.remove('hidden');
  {% endif %}
</script>
</body>
</html>
"""

ADMIN_DASHBOARD_TEMPLATE = ADMIN_HEAD + """
<div class="flex flex-col min-h-screen">
  <header class="p-4 border-b border-border-color bg-background-color/80 backdrop-blur-sm flex items-center justify-between">
    <h1 class="text-2xl font-black text-primary-color">Admin Dashboard</h1>
    <a href="{{ url_for('web_logout') }}" class="text-sm font-semibold text-text-secondary hover:text-red-500 transition-colors">Logout</a>
  </header>
  <main class="p-4 space-y-6 flex-grow">
    <h2 class="text-xl font-bold text-text-primary">Active Games (Scoring)</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {% for game in games %}
      <div class="bg-card-color rounded-xl shadow-lg p-4 space-y-2 border-l-4 {% if game.status == 'LIVE' %}border-red-500{% elif game.status == 'UPCOMING' %}border-primary-color{% else %}border-text-secondary{% endif %}">
        <p class="font-bold text-lg leading-tight">{{ game.away_team }} vs. {{ game.home_team }} ({{ game.age_group }}{{ game.gender }})</p>
        <div class="flex items-center justify-between text-sm">
          <span class="font-medium text-text-secondary">Status: <span class="font-bold {% if game.status == 'LIVE' %}text-red-500{% else %}text-primary-color{% endif %}">{{ game.status }}</span></span>
          <span class="font-medium text-text-secondary">Score: <span class="font-bold">{{ game.away_score }} - {{ game.home_score }}</span></span>
        </div>
        <div class="flex justify-between items-center mt-2 pt-2 border-t border-border-color">
          <a href="{{ url_for('scoring_interface', game_code=game.code) }}" class="text-sm font-medium text-primary-color hover:underline">
            Score Game (Web)
          </a>
          <span class="text-xs text-text-secondary">Code: {{ game.code }}</span>
        </div>
        {% if game.status == 'UPCOMING' %}
        <div class="pt-2">
          <a href="{{ url_for('go_live', game_code=game.code) }}" class="text-sm font-medium text-green-600 hover:underline block">Go Live</a>
        </div>
        {% endif %}
      </div>
      {% endfor %}
      {% if not games %}
      <p class="text-text-secondary italic">No games created yet.</p>
      {% endif %}
    </div>
  </main>
  <footer class="p-4 border-t border-border-color bg-background-color/80 backdrop-blur-sm flex justify-between gap-4">
    <a href="{{ url_for('new_game_setup', device_id='web') }}" class="flex-1 text-center bg-red-500 text-white font-bold py-3 px-5 rounded-lg hover:bg-red-600 transition-colors">
      Create New Game (Web)
    </a>
    <a href="{{ url_for('hotspot_setup', device_id='DEV-' ~ device_id_suffix) }}" class="flex-1 text-center bg-blue-900 text-white font-bold py-3 px-5 rounded-lg hover:bg-blue-800 transition-colors">
      Setup New Device
    </a>
  </footer>
</div>
</body>
</html>
"""

HOTSPOT_SETUP_TEMPLATE = ADMIN_HEAD + """
<div class="flex flex-col h-screen justify-center items-center p-4">
  <div class="w-full max-w-sm p-6 bg-card-color rounded-xl shadow-xl">
    <h1 class="text-2xl font-bold text-center text-primary-color mb-2">Device: {{ device_id }}</h1>
    <h2 class="text-xl font-medium text-center text-text-primary mb-6">Hotspot Setup</h2>
    <div id="connect-section">
      <p class="text-center text-sm text-text-secondary mb-6">Enter the admin hotspot details to configure the scoring device.</p>
      <div class="space-y-4">
        <input type="text" id="ssid" value="AdminHotspot" placeholder="Hotspot Name (SSID)" class="w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color form-select">
        <input type="password" id="password" value="12345678" placeholder="Password" class="w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color form-select">
        <button onclick="simulateConnection('{{ device_id }}')" class="w-full bg-blue-900 text-white font-bold py-3 px-5 rounded-lg hover:bg-blue-800 transition-colors">
          Connect & Configure
        </button>
      </div>
    </div>
    <div id="loading-section" class="hidden text-center">
      <p class="text-primary-color font-semibold mb-2">Attempting connection...</p>
      <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-color mx-auto mb-4"></div>
      <p class="text-sm text-text-secondary">Simulating network configuration... Success will redirect automatically.</p>
    </div>
    <div id="error-section" class="hidden p-3 bg-red-100 border border-red-500 rounded-lg mt-4 text-center">
      <p class="text-red-700 text-sm">Connection failed. Please check details and try again.</p>
      <button onclick="resetConnection()" class="mt-2 text-sm text-red-500 underline">Try Again</button>
    </div>
  </div>
</div>
<script>
  function simulateConnection(device_id) {
    const success = Math.random() > 0.2;
    document.getElementById('error-section').classList.add('hidden');
    document.getElementById('connect-section').classList.add('hidden');
    document.getElementById('loading-section').classList.remove('hidden');
    setTimeout(() => {
      if (success) {
        window.location.href = '/softball/admin/new/' + device_id;
      } else {
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('error-section').classList.remove('hidden');
      }
    }, 3000);
  }
  function resetConnection() {
    document.getElementById('error-section').classList.add('hidden');
    document.getElementById('connect-section').classList.remove('hidden');
    document.getElementById('loading-section').classList.add('hidden');
  }
</script>
</body>
</html>
"""

NEW_GAME_SETUP_TEMPLATE = ADMIN_HEAD + """
<div class="flex flex-col h-screen justify-between">
  <div>
    <header class="p-4 flex items-center justify-between bg-background-color/80 backdrop-blur-sm border-b border-border-color">
      <a href="{{ url_for('web_admin') }}" class="text-text-primary hover:text-primary-color transition-colors">
        <span class="material-symbols-outlined"> arrow_back </span>
      </a>
      <h1 class="text-xl font-bold text-text-primary text-center flex-1 pr-6">
        New Game Setup
        {% if device_id != 'web' %}
        <span class="text-sm font-normal text-text-secondary block">Device: {{ device_id }}</span>
        {% endif %}
      </h1>
      <div class="w-6"></div>
    </header>
    <main class="p-4 space-y-6">
      <div id="game-status" class="hidden p-3 bg-red-100 border border-red-500 rounded-lg mb-4 text-center">
        <p id="game-status-message" class="text-red-700 text-sm font-medium">Validation Error</p>
      </div>
      <form id="new-game-form" method="POST" action="{{ url_for('create_game') }}" onsubmit="return validateGameForm()">
        <input type="hidden" name="device_id" value="{{ device_id }}">
        <div class="flex items-center justify-between space-x-2">
          <div class="flex-1">
            <label class="text-sm font-medium text-text-secondary block mb-1">Away Team</label>
            <select name="away_team" aria-label="Team 1" class="form-select w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color" id="team-1">
              <option value="" disabled selected>Select Team</option>
              {% for team_name in team_names %}
              <option>{{ team_name }}</option>
              {% endfor %}
            </select>
          </div>
          <span class="text-text-secondary font-bold text-lg">vs</span>
          <div class="flex-1">
            <label class="text-sm font-medium text-text-secondary block mb-1">Home Team</label>
            <select name="home_team" aria-label="Team 2" class="form-select w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color" id="team-2">
              <option value="" disabled selected>Select Team</option>
              {% for team_name in team_names %}
              <option>{{ team_name }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
        <div class="space-y-2 mt-6">
          <label class="text-sm font-medium text-text-secondary" for="game-type">Game Type</label>
          <select name="game_type" class="form-select w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color" id="game-type">
            <option value="" disabled selected>Select Game Type</option>
            <option>Semis</option>
            <option>Finals</option>
            <option>Playoffs</option>
            <option>League Game</option>
            <option>Exhibition</option>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4 mt-6">
          <div class="space-y-2">
            <label class="text-sm font-medium text-text-secondary" for="age-group">Age Group</label>
            <select name="age_group" class="form-select w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color" id="age-group">
              <option value="" disabled selected>Select Age</option>
              {% for age in age_groups %}
              <option>{{ age }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium text-text-secondary" for="gender">Gender</label>
            <select name="gender" class="form-select w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color" id="gender">
              <option value="" disabled selected>Select Gender</option>
              {% for gender in gender_options %}
              <option>{{ gender }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
        <div class="space-y-2 mt-6">
          <label class="text-sm font-medium text-text-secondary" for="status">Start Status</label>
          <select name="status" id="status" class="form-select w-full rounded-lg border-border-color bg-card-color text-text-primary focus:border-primary-color focus:ring-primary-color">
            <option value="LIVE">Start Live</option>
            <option value="UPCOMING">Upcoming</option>
          </select>
        </div>
        <div id="time-section" class="space-y-2 mt-6 hidden">
          <label class="text-sm font-medium text-text-secondary" for="time">Scheduled Time (HH:MM)</label>
          <input type="time" id="time" name="time" class="w-full rounded-lg border border-border-color bg-card-color px-3 py-2 text-text-primary focus:border-primary-color focus:ring-primary-color">
        </div>
      </form>
    </main>
  </div>
  <footer class="p-4 pb-8 bg-background-color/80 backdrop-blur-sm border-t border-border-color">
    <button form="new-game-form" type="submit" class="w-full bg-red-500 text-white font-bold py-3 px-5 rounded-lg hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
      Go Live!
    </button>
  </footer>
</div>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const statusSelect = document.getElementById('status');
    const timeSection = document.getElementById('time-section');
    function toggleTimeSection() {
      if (statusSelect.value === 'UPCOMING') {
        timeSection.classList.remove('hidden');
      } else {
        timeSection.classList.add('hidden');
      }
    }
    statusSelect.addEventListener('change', toggleTimeSection);
    toggleTimeSection();
  });

  function validateGameForm() {
    const team1 = document.getElementById('team-1').value;
    const team2 = document.getElementById('team-2').value;
    const gameType = document.getElementById('game-type').value;
    const ageGroup = document.getElementById('age-group').value;
    const gender = document.getElementById('gender').value;
    const status = document.getElementById('status').value;
    const time = document.getElementById('time').value;
    const statusDiv = document.getElementById('game-status');
    const statusMsg = document.getElementById('game-status-message');
    statusDiv.classList.add('hidden');
    if (team1 === '' || team2 === '') {
      statusMsg.innerText = 'Please select both the Away Team and the Home Team.';
      statusDiv.classList.remove('hidden');
      return false;
    }
    if (team1 === team2) {
      statusMsg.innerText = 'The Away Team and Home Team must be different.';
      statusDiv.classList.remove('hidden');
      return false;
    }
    if (gameType === '') {
      statusMsg.innerText = 'Please select the Game Type.';
      statusDiv.classList.remove('hidden');
      return false;
    }
    if (ageGroup === '') {
      statusMsg.innerText = 'Please select the Age Group.';
      statusDiv.classList.remove('hidden');
      return false;
    }
    if (gender === '') {
      statusMsg.innerText = 'Please select the Gender.';
      statusDiv.classList.remove('hidden');
      return false;
    }
    if (status === 'UPCOMING' && time === '') {
      statusMsg.innerText = 'Please select the start time for upcoming games.';
      statusDiv.classList.remove('hidden');
      return false;
    }
    return true;
  }
</script>
</body>
</html>
"""

SCORING_INTERFACE_TEMPLATE = ADMIN_HEAD + """
<div class="flex flex-col min-h-screen justify-between">
  <header class="p-4 border-b border-border-color bg-background-color/80 backdrop-blur-sm flex items-center justify-between">
    <h1 class="text-xl font-bold text-primary-color">{{ game.away_team[0] }} vs {{ game.home_team[0] }} Scorepad</h1>
    <span class="text-sm font-medium text-text-secondary">Game Code: <span class="font-bold text-primary-color">{{ game.code }}</span></span>
  </header>
  <main class="p-6 flex-grow space-y-6">
    <!-- Scoreboard -->
    <div class="bg-card-color rounded-xl p-6 shadow-lg">
      <div class="flex justify-between items-center mb-4">
        <span id="period-display" class="text-sm font-semibold text-text-secondary">{{ game.period }}</span>
        <span class="text-xs font-mono bg-border-color px-2 py-0.5 rounded-full text-text-primary">Device: {{ game.device_id }}</span>
      </div>
      <div class="flex justify-between items-center text-center">
        <div class="w-1/3">
          <p class="text-lg font-medium text-text-primary">{{ game.away_team }}</p>
          <p id="away-score" class="text-4xl font-extrabold text-primary-color">{{ game.away_score }}</p>
        </div>
        <span class="text-3xl font-light text-text-secondary">-</span>
        <div class="w-1/3">
          <p class="text-lg font-medium text-text-primary">{{ game.home_team }}</p>
          <p id="home-score" class="text-4xl font-extrabold text-primary-color">{{ game.home_score }}</p>
        </div>
      </div>
    </div>
    <!-- Count Display -->
    <div class="grid grid-cols-3 gap-4 text-center bg-card-color rounded-xl p-6 shadow-lg">
      <div>
        <p class="text-xs text-text-secondary font-medium">BALLS</p>
        <p id="balls" class="text-xl font-bold text-text-primary">{{ game.balls }}</p>
      </div>
      <div>
        <p class="text-xs text-text-secondary font-medium">STRIKES</p>
        <p id="strikes" class="text-xl font-bold text-text-primary">{{ game.strikes }}</p>
      </div>
      <div>
        <p class="text-xs text-text-secondary font-medium">OUTS</p>
        <p id="outs" class="text-xl font-bold text-text-primary">{{ game.outs }}</p>
      </div>
    </div>
    <!-- Base Runner Diamond -->
    <div class="flex justify-center items-center bg-card-color rounded-xl p-6 shadow-lg">
      <div class="relative w-24 h-24">
        <div id="base-3" onclick="toggleBase('3')" class="cursor-pointer absolute top-0 left-1/2 -translate-x-1/2 w-6 h-6 rounded-sm transform rotate-45 transition-colors duration-200 {% if '3' in game.bases_state %}bg-primary-color{% else %}bg-border-color{% endif %}"></div>
        <div id="base-2" onclick="toggleBase('2')" class="cursor-pointer absolute top-1/2 left-0 -translate-y-1/2 w-6 h-6 rounded-sm transform rotate-45 transition-colors duration-200 {% if '2' in game.bases_state %}bg-primary-color{% else %}bg-border-color{% endif %}"></div>
        <div id="base-1" onclick="toggleBase('1')" class="cursor-pointer absolute top-1/2 right-0 -translate-y-1/2 w-6 h-6 rounded-sm transform rotate-45 transition-colors duration-200 {% if '1' in game.bases_state %}bg-primary-color{% else %}bg-border-color{% endif %}"></div>
        <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-6 bg-primary-color rounded-sm transform rotate-45"></div>
      </div>
    </div>
    <!-- Scoring Controls -->
    <div class="grid grid-cols-2 gap-4 bg-card-color rounded-xl p-6 shadow-lg">
      <button onclick="sendUpdate('H_SCORE_PLUS')" class="bg-blue-900 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-800 transition-colors min-h-[48px] text-sm">Home Run +1</button>
      <button onclick="sendUpdate('A_SCORE_PLUS')" class="bg-blue-900 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-800 transition-colors min-h-[48px] text-sm">Away Run +1</button>
      <button onclick="sendUpdate('BALL_PLUS')" class="bg-blue-800 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors min-h-[48px] text-sm">Ball +1</button>
      <button onclick="sendUpdate('STRIKE_PLUS')" class="bg-blue-800 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors min-h-[48px] text-sm">Strike +1</button>
      <button onclick="sendUpdate('OUT_PLUS')" class="bg-red-500 text-white font-bold py-3 px-4 rounded-lg hover:bg-red-600 transition-colors min-h-[48px] text-sm">Out +1</button>
      <button onclick="sendUpdate('NEXT_INNING')" class="bg-blue-700 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors min-h-[48px] text-sm">Next Half Inning</button>
      <button onclick="sendUpdate('RESET_COUNT')" class="bg-blue-800 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors min-h-[48px] text-sm col-span-2">Reset Count</button>
      <button onclick="sendUpdate('END_GAME')" class="col-span-2 bg-red-900 text-white font-bold py-3 px-4 rounded-lg hover:bg-red-800 transition-colors">End Game</button>
    </div>
    <!-- Status Message -->
    <div id="status-message" class="p-3 rounded-lg text-center hidden text-sm font-medium bg-green-100 text-text-primary"></div>
  </main>
</div>
<script>
  const GAME_CODE = "{{ game.code }}";
  let currentBases = "{{ game.bases_state }}";
  function updateBasesUI() {
    ['1', '2', '3'].forEach(base => {
      const element = document.getElementById('base-' + base);
      if (element) {
        if (currentBases.includes(base)) {
          element.classList.remove('bg-border-color');
          element.classList.add('bg-primary-color');
        } else {
          element.classList.remove('bg-primary-color');
          element.classList.add('bg-border-color');
        }
      }
    });
  }
  function toggleBase(base) {
    let newBases = currentBases;
    if (newBases.includes(base)) {
      newBases = newBases.replace(base, '');
    } else {
      newBases += base;
    }
    currentBases = newBases.split('').sort().join('');
    sendUpdate('SET_BASES', { bases_state: currentBases });
  }
  async function sendUpdate(action, extraData = {}) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.classList.remove('hidden', 'bg-red-100', 'bg-green-100');
    statusDiv.classList.add('bg-border-color', 'text-text-primary');
    statusDiv.innerText = `Sending action: ${action}...`;
    const payload = {
      device_id: "{{ game.device_id }}",
      ...extraData
    };
    try {
      const response = await fetch(`/softball/api/update_score/${GAME_CODE}?action=${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.ok) {
        document.getElementById('away-score').innerText = data.away_score;
        document.getElementById('home-score').innerText = data.home_score;
        document.getElementById('balls').innerText = data.balls;
        document.getElementById('strikes').innerText = data.strikes;
        document.getElementById('outs').innerText = data.outs;
        document.getElementById('period-display').innerText = data.period;
        currentBases = data.bases_state;
        updateBasesUI();
        statusDiv.classList.remove('bg-border-color');
        statusDiv.classList.add('bg-green-100');
        statusDiv.innerText = 'Update successful!';
      } else {
        statusDiv.classList.remove('bg-border-color');
        statusDiv.classList.add('bg-red-100');
        statusDiv.innerText = 'Error: ' + (data.error || 'Failed to update score.');
      }
    } catch (error) {
      statusDiv.classList.remove('bg-border-color');
      statusDiv.classList.add('bg-red-100');
      statusDiv.innerText = 'Network Error. Could not reach server.';
      console.error(error);
    }
    setTimeout(() => {
      statusDiv.classList.add('hidden');
    }, 2000);
  }
  updateBasesUI();
</script>
</body>
</html>
"""

# --- 3. Flask App Initialization and Routing ---

app = Flask(__name__)

def find_game(game_code):
    return next((game for game in GAMES_DATA if game["code"] == game_code), None)

def is_admin():
    return request.cookies.get('admin_logged_in') == 'true'

@app.route('/')
def index():
    return redirect(url_for('softball_scores'))

@app.route('/softball')
def softball_scores():
    filter_type = request.args.get('filter', 'all').lower()
    games = GAMES_DATA[:]
    if filter_type == 'live':
        games = [g for g in games if g['status'] == 'LIVE']
    elif filter_type == 'upcoming':
        games = [g for g in games if g['status'] == 'UPCOMING']
    elif filter_type == 'past':
        games = [g for g in games if g['status'] == 'FINISHED']
        games.reverse()
    else:
        games.sort(key=lambda g: (0 if g['status']=='LIVE' else 1 if g['status']=='UPCOMING' else 2, g['code']))
    return render_template_string(HTML_TEMPLATE, games=games, filter=filter_type)

@app.route('/softball/game/<game_code>')
def game_detail(game_code):
    game = find_game(game_code)
    if game:
        return render_template_string(GAME_DETAIL_TEMPLATE, game=game)
    return f"Game with code {game_code} not found.", 404

@app.route('/softball/admin/login', methods=['GET', 'POST'])
def web_login():
    error = False
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            response = make_response(redirect(url_for('web_admin')))
            response.set_cookie('admin_logged_in', 'true', max_age=3600)
            return response
        else:
            error = True
    return render_template_string(WEB_LOGIN_TEMPLATE, title="Admin Login", error=error, admin_password=ADMIN_PASSWORD)

@app.route('/softball/admin/logout')
def web_logout():
    response = make_response(redirect(url_for('softball_scores')))
    response.set_cookie('admin_logged_in', '', expires=0)
    return response

@app.route('/softball/admin')
def web_admin():
    if not is_admin():
        return redirect(url_for('web_login'))
    admin_games = sorted(GAMES_DATA, key=lambda g: g['code'])
    device_id_suffix = str(random.randint(100, 999))
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, title="Admin Dashboard", games=admin_games, device_id_suffix=device_id_suffix)

@app.route('/softball/admin/go_live/<game_code>')
def go_live(game_code):
    if not is_admin():
        return redirect(url_for('web_login'))
    game = find_game(game_code)
    if game and game['status'] == 'UPCOMING':
        game['status'] = 'LIVE'
        game['period'] = '1st Inning'
        game['time'] = None
    return redirect(url_for('web_admin'))

@app.route('/softball/admin/hotspot_setup/<device_id>')
def hotspot_setup(device_id):
    if not is_admin() and device_id != 'web':
        return redirect(url_for('web_login'))
    return render_template_string(HOTSPOT_SETUP_TEMPLATE, title="Device Setup", device_id=device_id)

@app.route('/softball/admin/new/<device_id>')
def new_game_setup(device_id):
    if not is_admin():
        return redirect(url_for('web_login'))
    team_names = sorted(TEAMS_DATA.keys())
    return render_template_string(NEW_GAME_SETUP_TEMPLATE, 
                                 title="New Game", 
                                 team_names=team_names, 
                                 age_groups=AGE_GROUPS, 
                                 gender_options=GENDER_OPTIONS,
                                 device_id=device_id)

@app.route('/softball/admin/create_game', methods=['POST'])
def create_game():
    if not is_admin():
        return redirect(url_for('web_login'))
    home_team = request.form.get('home_team')
    away_team = request.form.get('away_team')
    device_id = request.form.get('device_id')
    game_type = request.form.get('game_type')
    age_group = request.form.get('age_group')
    gender = request.form.get('gender')
    status = request.form.get('status', 'LIVE')
    time_str = request.form.get('time', '')
    if status == 'UPCOMING' and not time_str:
        return "Time is required for upcoming games.", 400
    if not all([home_team, away_team, game_type, age_group, gender]):
        return "Missing required game details.", 400
    new_game = {
        "code": generate_game_code(),
        "home_team": home_team,
        "away_team": away_team,
        "home_score": 0,
        "away_score": 0,
        "status": status,
        "period": "Pre-Game" if status == 'UPCOMING' else "1st Inning",
        "game_type": game_type,
        "age_group": age_group,
        "gender": gender,
        "time": time_str if status == 'UPCOMING' else None,
        "device_id": device_id,
        "balls": 0, "strikes": 0, "outs": 0, "bases_state": "0"
    }
    GAMES_DATA.append(new_game)
    return redirect(url_for('scoring_interface', game_code=new_game['code']))

@app.route('/softball/admin/score/<game_code>')
def scoring_interface(game_code):
    if not is_admin():
        return redirect(url_for('web_login'))
    game = find_game(game_code)
    if not game:
        return f"Game with code {game_code} not found.", 404
    return render_template_string(SCORING_INTERFACE_TEMPLATE, title="Scorepad", game=game)

@app.route('/softball/api/update_score/<game_code>', methods=['POST'])
def update_score(game_code):
    game = find_game(game_code)
    if not game:
        return jsonify({"error": "Game not found."}), 404
    action = request.args.get('action')
    data = request.get_json(silent=True) or {}
    if 'device_id' in data and data['device_id'] != game['device_id']:
        if game['device_id'] != 'web' and data['device_id'] != 'web':
            return jsonify({"error": "Unauthorized device."}), 403
    if action == 'H_SCORE_PLUS':
        game['home_score'] += 1
        game['balls'], game['strikes'], game['outs'], game['bases_state'] = 0, 0, 0, "0"
    elif action == 'A_SCORE_PLUS':
        game['away_score'] += 1
        game['balls'], game['strikes'], game['outs'], game['bases_state'] = 0, 0, 0, "0"
    elif action == 'BALL_PLUS':
        game['balls'] += 1
        if game['balls'] >= 4:
            game['balls'], game['strikes'] = 0, 0
            scored = '3' in game['bases_state']
            new_bases_list = []
            if '2' in game['bases_state']:
                new_bases_list.append('3')
            if '1' in game['bases_state']:
                new_bases_list.append('2')
            new_bases_list.append('1')
            game['bases_state'] = ''.join(sorted(new_bases_list))
            if scored:
                if game['period'].endswith('Top'):
                    game['away_score'] += 1
                else:
                    game['home_score'] += 1
    elif action == 'STRIKE_PLUS':
        game['strikes'] += 1
        if game['strikes'] >= 3:
            game['outs'] += 1
            game['balls'], game['strikes'] = 0, 0
    elif action == 'OUT_PLUS':
        game['outs'] += 1
    elif action == 'RESET_COUNT':
        game['balls'], game['strikes'] = 0, 0
    elif action == 'SET_BASES' and 'bases_state' in data:
        game['bases_state'] = data['bases_state'].split('').sort().join('').replace('0', '')
    elif action == 'NEXT_INNING':
        game['balls'], game['strikes'], game['outs'], game['bases_state'] = 0, 0, 0, "0"
        current_period = game['period']
        if current_period.endswith('Top'):
            game['period'] = current_period.replace('Top', 'Bottom')
        elif current_period.endswith('Bottom'):
            inning_num_str = re.match(r'\d+', current_period.split()[0]).group()
            inning_num = int(inning_num_str)
            game['period'] = f"{ordinal(inning_num + 1)} Inning Top"
        elif 'Inning' in current_period:
            game['period'] += " Top"
        else:
            if game['status'] != 'LIVE':
                game['status'] = 'LIVE'
            game['period'] = "1st Inning Top"
    elif action == 'END_GAME':
        game['status'] = 'FINISHED'
        game['period'] = 'Final'
    if game['outs'] >= 3:
        game['outs'] = 0
        game['balls'], game['strikes'], game['bases_state'] = 0, 0, "0"
        current_period = game['period']
        if current_period.endswith('Top'):
            game['period'] = current_period.replace('Top', 'Bottom')
        elif current_period.endswith('Bottom'):
            inning_num_str = re.match(r'\d+', current_period.split()[0]).group()
            inning_num = int(inning_num_str)
            game['period'] = f"{ordinal(inning_num + 1)} Inning Top"
    return jsonify({
        "game_code": game['code'],
        "away_score": game['away_score'],
        "home_score": game['home_score'],
        "balls": game['balls'],
        "strikes": game['strikes'],
        "outs": game['outs'],
        "bases_state": game['bases_state'],
        "period": game['period']
    })

@app.errorhandler(404)
def page_not_found(e):
    error_html = ADMIN_HEAD + f"""
    <div class="flex flex-col h-screen justify-center items-center p-4">
      <div class="text-center">
        <h1 class="text-6xl font-black text-primary-color mb-4">404</h1>
        <p class="text-xl text-text-primary mb-6">Page Not Found</p>
        <a href="{url_for('softball_scores')}" class="bg-primary-color text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-color/80 transition-colors">
          Go to Home
        </a>
      </div>
    </div>
    </body></html>
    """
    return render_template_string(error_html), 404

