import json
import uuid
import random
import string
from flask import Flask, render_template_string, redirect, url_for, request, make_response, jsonify
import logging

# --- 1. Configuration & Helper Functions ---

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Unique ID generation for games
def generate_game_code(length=7):
    """Generates a unique, short, alphanumeric code (e.g., 6NH3D2E)."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not any(game['code'] == code for game in GAMES_DATA):
            return code

# Simple password for web-based access (in a real app, use environment variables and proper authentication)
ADMIN_PASSWORD = "softballadmin"  # TODO: Move to environment variable in production

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
        "balls": 3,
        "strikes": 1,
        "outs": 2,
        "bases_state": "13"
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
        "balls": 0,
        "strikes": 0,
        "outs": 0,
        "bases_state": "0"
    }
]

# --- 2. HTML Templates ---

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Live Softball Scores</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries" onerror="console.warn('Tailwind CDN failed to load')"></script>
<style type="text/tailwindcss">
    :root {
      --primary-color: #f97316;
      --background-color: #111827;
      --card-color: #1f2937;
      --text-primary: #ffffff;
      --text-secondary: #9ca3af;
      --border-color: #374151;
    }
    .material-symbols-outlined {
      font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
<style>
    body { min-height: 100vh; }
</style>
</head>
<body class="bg-background-color text-text-primary" style='font-family: Lexend, "Noto Sans", sans-serif;'>

<div class="relative flex h-auto min-h-screen w-full flex-col justify-start group/design-root overflow-x-hidden">

    <!-- Header -->
    <header class="sticky top-0 z-10 bg-background-color/80 backdrop-blur-sm border-b border-border-color">
        <div class="flex items-center p-4">
            <h1 class="text-2xl font-black tracking-tight text-center flex-1 text-primary">SOFTBALL LIVE SCORES</h1>
            <a href="{{ url_for('web_login') }}" class="text-sm font-semibold text-text-secondary hover:text-primary transition-colors ml-4">Admin</a>
        </div>
    </header>

    <!-- Main Content Area with Games Loop -->
    <main class="p-4 space-y-4 flex-grow max-w-lg mx-auto w-full">
        
        {% for game in games %}
        <a href="{{ url_for('game_detail', game_code=game.code) }}" class="block">
            <div class="bg-card-color rounded-xl shadow-lg p-4 flex items-center justify-between transition duration-300 hover:shadow-primary/20
                 {% if game.status == 'UPCOMING' %}opacity-70{% endif %}">
                
                <div class="flex flex-col">
                    <p class="font-bold text-lg leading-tight">{{ game.away_team|default('Unknown Team') }} vs. {{ game.home_team|default('Unknown Team') }}</p>

                    <div class="flex items-center gap-2 mt-1">
                        {% if game.status == 'LIVE' %}
                        <span class="text-red-500 text-sm font-bold animate-pulse">● LIVE</span>
                        <p class="text-text-secondary text-sm">{{ game.period|default('N/A') }}</p>
                        {% else %}
                        <p class="text-text-secondary text-sm font-medium">{{ game.time|default('TBD') }}</p>
                        {% endif %}
                    </div>
                </div>

                <!-- Score & Game Code -->
                <div class="text-right">
                    <div class="text-4xl font-extrabold text-primary">
                        {{ game.away_score|default(0) }} - {{ game.home_score|default(0) }}
                    </div>
                    <p class="text-xs text-text-secondary mt-1">Code: {{ game.code|default('N/A') }}</p>
                </div>
            </div>
        </a>
        {% else %}
        <div class="text-center p-8 bg-card-color/50 rounded-lg mt-12">
            <p class="text-lg text-text-secondary">No live games currently scheduled.</p>
        </div>
        {% endfor %}
        
    </main>

</div>

</body>
</html>
"""

GAME_DETAIL_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Live Score</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries" onerror="console.warn('Tailwind CDN failed to load')"></script>
<style type="text/tailwindcss">
    :root {
      --primary-color: #f97316;
      --background-color: #111827;
      --card-color: #1f2937;
      --text-primary: #ffffff;
      --text-secondary: #9ca3af;
      --border-color: #374151;
    }
    .material-symbols-outlined {
      font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
</style>
<style>
    body { min-height: 100dvh; }
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
{% else %}
<span class="text-text-secondary text-sm font-bold">{{ game.status|default('UPCOMING') }}</span>
{% endif %}
</div>
<div class="flex items-center gap-2 text-sm font-semibold">
    <span class="text-text-secondary">{% if game.period %}{{ game.period }}{% else %}{{ game.time|default('TBD') }}{% endif %}</span>
<svg class="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M5 15l7-7 7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
</div>
</div>
<!-- Team and Score Layout -->
<div class="flex items-center justify-around text-center mb-6">
<!-- Away Team Column -->
<div class="flex flex-col items-center gap-3">
<img src="{{ teams_data[game.away_team]|default('https://via.placeholder.com/80') }}" alt="{{ game.away_team|default('Unknown Team') }} logo" class="w-20 h-20 md:w-24 md:h-24 rounded-full object-contain">
<h2 class="text-xl md:text-2xl font-bold text-text-primary">{{ game.away_team|default('Unknown Team') }}</h2>
</div>
<!-- Score Center -->
<div class="flex items-center">
<span class="text-5xl md:text-7xl font-black text-text-primary mx-4">{{ game.away_score|default(0) }}</span>
<span class="text-4xl md:text-5xl font-light text-text-secondary">-</span>
<span class="text-5xl md:text-7xl font-black text-text-primary mx-4">{{ game.home_score|default(0) }}</span>
</div>
<!-- Home Team Column -->
<div class="flex flex-col items-center gap-3">
<img src="{{ teams_data[game.home_team]|default('https://via.placeholder.com/80') }}" alt="{{ game.home_team|default('Unknown Team') }} logo" class="w-20 h-20 md:w-24 md:h-24 rounded-full object-contain">
<h2 class="text-xl md:text-2xl font-bold text-text-primary">{{ game.home_team|default('Unknown Team') }}</h2>
</div>
</div>
{% if game.status == 'LIVE' and 'Inning' in game.period|default('') %}
<div class="grid grid-cols-3 gap-4 text-center bg-background-color/30 p-4 rounded-lg">
<div>
<p class="text-sm text-text-secondary font-medium">BALLS</p>
<p class="text-2xl font-bold text-text-primary">{{ game.balls|default(0) }}</p>
</div>
<div>
<p class="text-sm text-text-secondary font-medium">STRIKES</p>
<p class="text-2xl font-bold text-text-primary">{{ game.strikes|default(0) }}</p>
</div>
<div>
<p class="text-sm text-text-secondary font-medium">OUTS</p>
<p class="text-2xl font-bold text-text-primary">{{ game.outs|default(0) }}</p>
</div>
</div>
<div class="mt-6 flex justify-center items-center">
<div class="relative w-24 h-24">
<!-- Base Runner Diamond -->
<!-- Second Base (Left) -->
<div class="absolute top-1/2 left-0 -translate-y-1/2 w-6 h-6 rounded-sm transform rotate-45 
     {% if '2' in game.bases_state|default('0') %}bg-primary-color{% else %}bg-border-color/50{% endif %}"></div>
<!-- Third Base (Top) -->
<div class="absolute top-0 left-1/2 -translate-x-1/2 w-6 h-6 rounded-sm transform rotate-45 
     {% if '3' in game.bases_state|default('0') %}bg-primary-color{% else %}bg-border-color/50{% endif %}"></div>
<!-- First Base (Right) -->
<div class="absolute top-1/2 right-0 -translate-y-1/2 w-6 h-6 rounded-sm transform rotate-45 
     {% if '1' in game.bases_state|default('0') %}bg-primary-color{% else %}bg-border-color/50{% endif %}"></div>
<!-- Home Plate (Bottom) -->
<div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-6 bg-border-color rounded-sm transform rotate-45"></div>
</div>
</div>
{% endif %}
</div>
<!-- Refresh Button for viewing scores -->
<div class="absolute bottom-4 right-4 z-10">
<button onclick="window.location.reload()" class="flex items-center justify-center rounded-full h-12 w-12 text-text-primary bg-card-color/50 hover:bg-card-color transition-colors backdrop-blur-sm">
<span class="material-symbols-outlined"> refresh </span>
</button>
</div>
</div>

</body></html>
"""

ADMIN_HEAD = r"""
<html class="dark" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{{ title }}</title>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;700;900&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries" onerror="console.warn('Tailwind CDN failed to load')"></script>
<style>
    .form-select {
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%239ca3af' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg>%3e");
        background-position: right 0.5rem center;
        background-repeat: no-repeat;
        background-size: 1.5em 1.5em;
        padding-right: 2.5rem;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
</style>
<script>
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    primary: "#f97316",
                    "background-light": "#f5f7f8",
                    "background-dark": "#101922",
                },
                fontFamily: {
                    display: ["Lexend"],
                },
                borderRadius: {
                    DEFAULT: "0.5rem",
                    lg: "0.75rem",
                    xl: "1rem",
                    full: "9999px"
                },
            },
        },
    };
</script>
<style>
    body {
      min-height: 100dvh;
    }
</style>
</head>
<body class="bg-background-light dark:bg-background-dark font-display text-slate-800 dark:text-white">
"""

WEB_LOGIN_TEMPLATE = ADMIN_HEAD + f"""
<div class="flex flex-col h-screen justify-center items-center p-4">
    <div class="w-full max-w-sm p-8 bg-white dark:bg-slate-800 rounded-xl shadow-2xl">
        <h1 class="text-2xl font-bold text-center text-primary mb-2">Web Admin Access</h1>
        <h2 class="text-lg font-medium text-center text-slate-900 dark:text-white mb-6">Create or Score Games</h2>
        <form method="POST" action="{{ url_for('web_login') }}">
            <div id="error-message" class="hidden p-3 bg-red-100 dark:bg-red-900/50 border border-red-500 rounded-lg mb-4 text-center text-sm">
                Incorrect password. Try again.
            </div>
            <div class="space-y-4">
                <input type="password" name="password" placeholder="Password" class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-primary focus:ring-primary" autofocus>
                <button type="submit" class="w-full bg-primary text-white font-bold py-3 px-5 rounded-lg hover:bg-orange-600 transition-colors">
                    Login
                </button>
            </div>
        </form>
        <p class="text-xs text-center text-slate-500 dark:text-slate-400 mt-4">Hint: Password is "{ADMIN_PASSWORD}"</p>
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

ADMIN_DASHBOARD_TEMPLATE = ADMIN_HEAD + r"""
<div class="flex flex-col min-h-screen">
<header class="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
<h1 class="text-2xl font-black text-primary">Admin Dashboard</h1>
<a href="{{ url_for('web_logout') }}" class="text-sm font-semibold text-slate-500 hover:text-red-500 transition-colors">Logout</a>
</header>
<main class="p-4 space-y-6 flex-grow">
<h2 class="text-xl font-bold dark:text-white">Active Games (Scoring)</h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
{% for game in games %}
<div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-4 space-y-2 border-l-4 {% if game.status == 'LIVE' %}border-green-500{% elif game.status == 'UPCOMING' %}border-primary{% else %}border-slate-500{% endif %}">
<p class="font-bold text-lg leading-tight">{{ game.away_team|default('Unknown Team') }} vs. {{ game.home_team|default('Unknown Team') }} ({{ game.age_group|default('N/A') }}{{ game.gender|default('') }})</p>
<div class="flex items-center justify-between text-sm">
<span class="font-medium text-slate-500 dark:text-slate-400">Status: <span class="font-bold {% if game.status == 'LIVE' %}text-green-500{% else %}text-primary{% endif %}">{{ game.status|default('UPCOMING') }}</span></span>
<span class="font-medium text-slate-500 dark:text-slate-400">Score: <span class="font-bold">{{ game.away_score|default(0) }} - {{ game.home_score|default(0) }}</span></span>
</div>
<div class="flex justify-between items-center mt-2 pt-2 border-t border-slate-700/50">
<a href="{{ url_for('scoring_interface', game_code=game.code) }}" class="text-sm font-medium text-primary hover:underline">
Score Game (Web)
</a>
<span class="text-xs text-slate-600 dark:text-slate-500">Code: {{ game.code|default('N/A') }}</span>
</div>
</div>
{% endfor %}
{% if not games %}
<p class="text-slate-500 italic">No games created yet.</p>
{% endif %}
</div>
</main>
<footer class="p-4 border-t border-slate-200 dark:border-slate-700 flex justify-between gap-4">
<a href="{{ url_for('new_game_setup', device_id='web') }}" class="flex-1 text-center bg-primary text-white font-bold py-3 px-5 rounded-lg hover:bg-orange-600 transition-colors">
Create New Game (Web)
</a>
<a href="{{ url_for('hotspot_setup', device_id='DEV-' ~ device_id_suffix) }}" class="flex-1 text-center bg-slate-700 text-white font-bold py-3 px-5 rounded-lg hover:bg-slate-600 transition-colors">
Setup New Device
</a>
</footer>
</div>
</body>
</html>
"""

HOTSPOT_SETUP_TEMPLATE = ADMIN_HEAD + r"""
<div class="flex flex-col h-screen justify-center items-center p-4">
    <div class="w-full max-w-sm p-6 bg-white dark:bg-slate-800 rounded-xl shadow-xl">
        <h1 class="text-2xl font-bold text-center text-primary mb-2">Device: {{ device_id|default('Unknown Device') }}</h1>
        <h2 class="text-xl font-medium text-center text-slate-900 dark:text-white mb-6">Hotspot Setup</h2>
        <div id="connect-section">
            <p class="text-center text-sm text-slate-600 dark:text-slate-400 mb-6">Enter the admin hotspot details to configure the scoring device.</p>
            <div class="space-y-4">
                <input type="text" id="ssid" value="AdminHotspot" placeholder="Hotspot Name (SSID)" class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-primary focus:ring-primary">
                <input type="password" id="password" value="12345678" placeholder="Password" class="w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-primary focus:ring-primary">
                <button onclick="simulateConnection('{{ device_id|default('web') }}')" class="w-full bg-primary text-white font-bold py-3 px-5 rounded-lg hover:bg-orange-600 transition-colors">
                    Connect & Configure
                </button>
            </div>
        </div>
        <div id="loading-section" class="hidden text-center">
            <p class="text-primary font-semibold mb-2">Attempting connection...</p>
            <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Simulating network configuration... Success will redirect automatically.</p>
        </div>
        <div id="error-section" class="hidden p-3 bg-red-100 dark:bg-red-900/50 border border-red-500 rounded-lg mt-4 text-center">
             <p class="text-red-700 dark:text-red-300 text-sm">Connection failed. Please check details and try again.</p>
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

NEW_GAME_SETUP_TEMPLATE = ADMIN_HEAD + r"""
<div class="flex flex-col h-screen justify-between">
<div>
<header class="p-4 flex items-center justify-between">
<a href="{{ url_for('web_admin') }}" class="text-slate-800 dark:text-white hover:text-primary transition-colors">
<span class="material-symbols-outlined"> arrow_back </span>
</a>
<h1 class="text-xl font-bold text-slate-900 dark:text-white text-center flex-1 pr-6">
    New Game Setup
    {% if device_id != 'web' %} 
    <span class="text-sm font-normal text-slate-500 dark:text-slate-400 block">Device: {{ device_id|default('Unknown Device') }}</span>
    {% endif %}
</h1>
<div class="w-6"></div>
</header>
<main class="p-4 space-y-6">
<div id="game-status" class="hidden p-3 bg-red-100 dark:bg-red-900/50 border border-red-500 rounded-lg mb-4 text-center">
    <p id="game-status-message" class="text-red-700 dark:text-red-300 text-sm font-medium">Validation Error</p>
</div>
<form id="new-game-form" method="POST" action="{{ url_for('create_game') }}" onsubmit="return validateGameForm()">
<input type="hidden" name="device_id" value="{{ device_id|default('web') }}">
<div class="flex items-center justify-between space-x-2">
<div class="flex-1">
<label class="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-1">Away Team</label>
<select name="away_team" aria-label="Team 1" class="form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary" id="team-1">
<option value="" disabled selected>Select Team</option>
{% for team_name in team_names %}
<option>{{ team_name }}</option>
{% endfor %}
</select>
</div>
<span class="text-slate-500 dark:text-slate-400 font-bold text-lg">vs</span>
<div class="flex-1">
<label class="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-1">Home Team</label>
<select name="home_team" aria-label="Team 2" class="form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary" id="team-2">
<option value="" disabled selected>Select Team</option>
{% for team_name in team_names %}
<option>{{ team_name }}</option>
{% endfor %}
</select>
</div>
</div>
<div class="space-y-2 mt-6">
<label class="text-sm font-medium text-slate-700 dark:text-slate-300" for="game-type">Game Type</label>
<select name="game_type" class="form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary" id="game-type">
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
<label class="text-sm font-medium text-slate-700 dark:text-slate-300" for="age-group">Age Group</label>
<select name="age_group" class="form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary" id="age-group">
<option value="" disabled selected>Select Age</option>
{% for age in age_groups %}
<option>{{ age }}</option>
{% endfor %}
</select>
</div>
<div class="space-y-2">
<label class="text-sm font-medium text-slate-700 dark:text-slate-300" for="gender">Gender</label>
<select name="gender" class="form-select w-full rounded-lg border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:border-primary focus:ring-primary" id="gender">
<option value="" disabled selected>Select Gender</option>
{% for gender in gender_options %}
<option>{{ gender }}</option>
{% endfor %}
</select>
</div>
</div>
</form>
</main>
</div>
<footer class="p-4 pb-8">
<button form="new-game-form" type="submit" class="w-full bg-primary text-white font-bold py-3 px-5 rounded-lg hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary dark:focus:ring-offset-background-dark">
    Go Live!
</button>
</footer>
</div>
<script>
    function validateGameForm() {
        const team1 = document.getElementById('team-1').value;
        const team2 = document.getElementById('team-2').value;
        const gameType = document.getElementById('game-type').value;
        const ageGroup = document.getElementById('age-group').value;
        const gender = document.getElementById('gender').value;

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

        return true;
    }
</script>
</body>
</html>
"""

SCORING_INTERFACE_TEMPLATE = ADMIN_HEAD + r"""
<div class="flex flex-col h-screen justify-between" id="scoring-app">
<header class="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
    <h1 class="text-xl font-bold text-primary">{{ game.away_team[0]|default('?') }} vs {{ game.home_team[0]|default('?') }} Scorepad</h1>
    <span class="text-sm font-medium text-slate-500 dark:text-slate-400">Game Code: <span class="font-bold text-primary">{{ game.code|default('N/A') }}</span></span>
</header>
<main class="p-4 flex-grow space-y-6 overflow-y-auto">

    <!-- Live Scoreboard Display -->
    <div class="bg-primary/10 dark:bg-primary/20 p-4 rounded-xl shadow-lg border-t-4 border-primary">
        <div class="flex justify-between items-center mb-3">
            <span id="period-display" class="text-sm font-semibold">{{ game.period|default('N/A') }}</span>
            <span class="text-xs font-mono bg-slate-700/50 px-2 py-0.5 rounded-full">Device: {{ game.device_id|default('Unknown') }}</span>
        </div>
        <div class="flex justify-between items-center text-center">
            <div class="w-1/3">
                <img src="{{ teams_data[game.away_team]|default('https://via.placeholder.com/80') }}" alt="{{ game.away_team|default('Unknown Team') }} logo" class="w-16 h-16 mx-auto rounded-full object-contain">
                <p class="text-xl font-medium">{{ game.away_team|default('Unknown Team') }}</p>
                <p id="away-score" class="text-5xl font-extrabold text-white">{{ game.away_score|default(0) }}</p>
            </div>
            <span class="text-4xl font-light text-slate-500">-</span>
            <div class="w-1/3">
                <img src="{{ teams_data[game.home_team]|default('https://via.placeholder.com/80') }}" alt="{{ game.home_team|default('Unknown Team') }} logo" class="w-16 h-16 mx-auto rounded-full object-contain">
                <p class="text-xl font-medium">{{ game.home_team|default('Unknown Team') }}</p>
                <p id="home-score" class="text-5xl font-extrabold text-white">{{ game.home_score|default(0) }}</p>
            </div>
        </div>
    </div>

    <!-- Base State, Balls, Strikes, Outs -->
    <div class="grid grid-cols-3 gap-3 text-center">
        <div class="bg-slate-700/50 p-3 rounded-lg">
            <p class="text-xs text-slate-400 dark:text-slate-400">BALLS</p>
            <p id="balls" class="text-2xl font-extrabold text-white">{{ game.balls|default(0) }}</p>
        </div>
        <div class="bg-slate-700/50 p-3 rounded-lg">
            <p class="text-xs text-slate-400 dark:text-slate-400">STRIKES</p>
            <p id="strikes" class="text-2xl font-extrabold text-white">{{ game.strikes|default(0) }}</p>
        </div>
        <div class="bg-slate-700/50 p-3 rounded-lg">
            <p class="text-xs text-slate-400 dark:text-slate-400">OUTS</p>
            <p id="outs" class="text-2xl font-extrabold text-white">{{ game.outs|default(0) }}</p>
        </div>
    </div>
    
    <!-- Base Runner Diamond -->
    <div class="mt-4 flex justify-center items-center">
        <div class="relative w-28 h-28">
            <!-- Third Base (Top) -->
            <div id="base-3" onclick="toggleBase('3')" class="cursor-pointer absolute top-0 left-1/2 -translate-x-1/2 w-8 h-8 rounded-sm transform rotate-45 transition-colors duration-200
                  {% if '3' in game.bases_state|default('0') %}bg-primary hover:bg-red-500{% else %}bg-slate-600 hover:bg-slate-500{% endif %}"></div>
            <!-- Second Base (Left) -->
            <div id="base-2" onclick="toggleBase('2')" class="cursor-pointer absolute top-1/2 left-0 -translate-y-1/2 w-8 h-8 rounded-sm transform rotate-45 transition-colors duration-200
                  {% if '2' in game.bases_state|default('0') %}bg-primary hover:bg-red-500{% else %}bg-slate-600 hover:bg-slate-500{% endif %}"></div>
            <!-- First Base (Right) -->
            <div id="base-1" onclick="toggleBase('1')" class="cursor-pointer absolute top-1/2 right-0 -translate-y-1/2 w-8 h-8 rounded-sm transform rotate-45 transition-colors duration-200
                  {% if '1' in game.bases_state|default('0') %}bg-primary hover:bg-red-500{% else %}bg-slate-600 hover:bg-slate-500{% endif %}"></div>
            <!-- Home Plate (Bottom) -->
            <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-8 bg-slate-400 rounded-sm transform rotate-45"></div>
        </div>
    </div>
    
    <!-- Scoring Buttons -->
    <div class="space-y-3">
        <p class="text-lg font-bold mt-4 border-b border-slate-700 pb-1 text-primary">SCORING ACTIONS</p>
        <div class="grid grid-cols-2 gap-3">
            <button onclick="sendUpdate('H_SCORE_PLUS')" class="bg-green-600 text-white font-bold py-3 rounded-xl hover:bg-green-700 transition-colors shadow-lg">
                Home Run +1
            </button>
            <button onclick="sendUpdate('A_SCORE_PLUS')" class="bg-green-600 text-white font-bold py-3 rounded-xl hover:bg-green-700 transition-colors shadow-lg">
                Away Run +1
            </button>
        </div>

        <p class="text-lg font-bold mt-4 border-b border-slate-700 pb-1 text-primary">PITCH & BASE STATE</p>
        <div class="grid grid-cols-3 gap-3">
            <button onclick="sendUpdate('BALL_PLUS')" class="bg-slate-700 text-white font-bold py-3 rounded-xl hover:bg-slate-600 transition-colors">Ball +1</button>
            <button onclick="sendUpdate('STRIKE_PLUS')" class="bg-slate-700 text-white font-bold py-3 rounded-xl hover:bg-slate-600 transition-colors">Strike +1</button>
            <button onclick="sendUpdate('OUT_PLUS')" class="bg-red-700 text-white font-bold py-3 rounded-xl hover:bg-red-800 transition-colors">Out +1</button>
        </div>

        <p class="text-lg font-bold mt-4 border-b border-slate-700 pb-1 text-primary">INNING & RESET</p>
        <div class="grid grid-cols-2 gap-3">
             <button onclick="sendUpdate('NEXT_INNING')" class="bg-indigo-600 text-white font-bold py-3 rounded-xl hover:bg-indigo-700 transition-colors">Next Half Inning</button>
             <button onclick="sendUpdate('RESET_COUNT')" class="bg-slate-500 text-white font-bold py-3 rounded-xl hover:bg-slate-600 transition-colors">Reset Count</button>
        </div>
        
    </div>

    <!-- API Status Message -->
    <div id="status-message" class="mt-4 p-3 rounded-lg text-center hidden text-sm font-medium"></div>
</main>

<script>
    const GAME_CODE = "{{ game.code|default('N/A') }}";
    let currentBases = "{{ game.bases_state|default('0') }}";

    function updateBasesUI() {
        ['1', '2', '3'].forEach(base => {
            const element = document.getElementById('base-' + base);
            if (element) {
                if (currentBases.includes(base)) {
                    element.classList.remove('bg-slate-600', 'hover:bg-slate-500');
                    element.classList.add('bg-primary', 'hover:bg-red-500');
                } else {
                    element.classList.remove('bg-primary', 'hover:bg-red-500');
                    element.classList.add('bg-slate-600', 'hover:bg-slate-500');
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

    async function sendUpdate(action, extraData = {}, retries = 3) {
        const statusDiv = document.getElementById('status-message');
        
        statusDiv.classList.remove('hidden', 'bg-red-500/20', 'bg-green-500/20');
        statusDiv.classList.add('bg-slate-500/20', 'text-white');
        statusDiv.innerText = `Sending action: ${action}...`;

        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(`/softball/api/update_score/${GAME_CODE}?action=${action}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: "{{ game.device_id|default('web') }}", ...extraData })
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
                    statusDiv.classList.remove('bg-slate-500/20');
                    statusDiv.classList.add('bg-green-500/20');
                    statusDiv.innerText = 'Update successful!';
                    break;
                } else {
                    throw new Error(data.error || 'Failed to update score.');
                }
            } catch (error) {
                if (i === retries - 1) {
                    statusDiv.classList.remove('bg-slate-500/20');
                    statusDiv.classList.add('bg-red-500/20');
                    statusDiv.innerText = `Error after ${retries} attempts: ${error.message}`;
                }
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        setTimeout(() => statusDiv.classList.add('hidden'), 3000);
    }
    updateBasesUI();
</script>
</div>
</body>
</html>
"""

# --- 3. Flask App Initialization and Routing ---

app = Flask(__name__)

# Route to find a game by code
def find_game(game_code):
    """Utility function to find a game dictionary by its code."""
    required_fields = ["code", "home_team", "away_team", "home_score", "away_score", "status", "period", 
                      "game_type", "age_group", "gender", "time", "device_id", "balls", "strikes", "outs", "bases_state"]
    game = next((game for game in GAMES_DATA if game["code"] == game_code), None)
    if game and all(field in game for field in required_fields):
        return game
    logger.warning(f"Game not found or incomplete: {game_code}")
    return None

# Route to determine if admin cookie is set
def is_admin():
    """Checks for the admin cookie."""
    return request.cookies.get('admin_logged_in') == 'true'

@app.route('/')
def index():
    """Redirects the base URL to the softball score viewing page."""
    return redirect(url_for('softball_scores'))

@app.route('/softball')
def softball_scores():
    """Public viewing page for all live and upcoming games."""
    logger.debug(f"GAMES_DATA: {GAMES_DATA}")
    sorted_games = sorted(GAMES_DATA, key=lambda g: 0 if g['status'] == 'LIVE' else 1)
    return render_template_string(HTML_TEMPLATE, games=sorted_games)

@app.route('/softball/game/<game_code>')
def game_detail(game_code):
    """Public detail page for a single game."""
    game = find_game(game_code)
    if game:
        return render_template_string(GAME_DETAIL_TEMPLATE, game=game, teams_data=TEAMS_DATA)
    return render_template_string(ADMIN_HEAD + """
        <div class="flex flex-col h-screen justify-center items-center p-4">
            <div class="text-center">
                <h1 class="text-2xl font-bold text-primary mb-4">Game Not Found</h1>
                <p class="text-lg dark:text-white mb-6">No game found with code {{ game_code }}.</p>
                <a href="{{ url_for('softball_scores') }}" class="bg-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors">
                    Back to Games
                </a>
            </div>
        </div>
        </body></html>
    """, game_code=game_code), 404

# --- Admin Routes ---

@app.route('/softball/admin/login', methods=['GET', 'POST'])
def web_login():
    """Handles admin login via password."""
    error = False
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            response = make_response(redirect(url_for('web_admin')))
            response.set_cookie('admin_logged_in', 'true', max_age=3600, secure=(request.scheme == 'https'), httponly=True, samesite='Lax')
            logger.info("Admin login successful")
            return response
        else:
            error = True
            logger.warning("Admin login failed: incorrect password")
    
    return render_template_string(WEB_LOGIN_TEMPLATE, title="Admin Login", error=error)

@app.route('/softball/admin/logout')
def web_logout():
    """Logs the admin out by removing the cookie."""
    response = make_response(redirect(url_for('softball_scores')))
    response.set_cookie('admin_logged_in', '', expires=0, secure=(request.scheme == 'https'), httponly=True, samesite='Lax')
    logger.info("Admin logged out")
    return response

@app.route('/softball/admin')
def web_admin():
    """Admin dashboard to manage games."""
    if not is_admin():
        logger.warning("Unauthorized access to admin dashboard")
        return redirect(url_for('web_login'))

    admin_games = sorted(GAMES_DATA, key=lambda g: g['code'])
    device_id_suffix = str(random.randint(100, 999))
    
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE, title="Admin Dashboard", games=admin_games, device_id_suffix=device_id_suffix)

@app.route('/softball/admin/hotspot_setup/<device_id>')
def hotspot_setup(device_id):
    """Simulates the device setup and config phase."""
    if not is_admin() and device_id != 'web':
        logger.warning(f"Unauthorized access to hotspot setup for device_id: {device_id}")
        return redirect(url_for('web_login'))
    
    return render_template_string(HOTSPOT_SETUP_TEMPLATE, title="Device Setup", device_id=device_id)

@app.route('/softball/admin/new/<device_id>')
def new_game_setup(device_id):
    """Page to create a new game linked to a device or web session."""
    if not is_admin():
        logger.warning("Unauthorized access to new game setup")
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
    """Handles POST request to create and store a new game."""
    if not is_admin():
        logger.warning("Unauthorized access to create game")
        return redirect(url_for('web_login'))

    home_team = request.form.get('home_team')
    away_team = request.form.get('away_team')
    device_id = request.form.get('device_id')
    game_type = request.form.get('game_type')
    age_group = request.form.get('age_group')
    gender = request.form.get('gender')
    
    if not all([home_team, away_team, game_type, age_group, gender]):
        logger.error("Missing required game details")
        return jsonify({"error": "Missing required game details."}), 400

    if home_team == away_team:
        logger.error("Home and away teams must be different")
        return jsonify({"error": "Home and away teams must be different."}), 400

    new_game = {
        "code": generate_game_code(),
        "home_team": home_team,
        "away_team": away_team,
        "home_score": 0,
        "away_score": 0,
        "status": "LIVE",
        "period": "1st Inning Top",
        "game_type": game_type,
        "age_group": age_group,
        "gender": gender,
        "time": None,
        "device_id": device_id or "web",
        "balls": 0,
        "strikes": 0,
        "outs": 0,
        "bases_state": "0"
    }
    
    GAMES_DATA.append(new_game)
    logger.info(f"New game created: {new_game['code']}")
    return redirect(url_for('scoring_interface', game_code=new_game['code']))

@app.route('/softball/admin/score/<game_code>')
def scoring_interface(game_code):
    """The interactive page used by the Admin or Device to update the score."""
    if not is_admin():
        logger.warning("Unauthorized access to scoring interface")
        return redirect(url_for('web_login'))

    game = find_game(game_code)
    if not game:
        logger.error(f"Game not found: {game_code}")
        return render_template_string(ADMIN_HEAD + """
            <div class="flex flex-col h-screen justify-center items-center p-4">
                <div class="text-center">
                    <h1 class="text-2xl font-bold text-primary mb-4">Game Not Found</h1>
                    <p class="text-lg dark:text-white mb-6">No game found with code {{ game_code }}.</p>
                    <a href="{{ url_for('web_admin') }}" class="bg-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors">
                        Back to Dashboard
                    </a>
                </div>
            </div>
            </body></html>
        """, game_code=game_code), 404
    
    return render_template_string(SCORING_INTERFACE_TEMPLATE, title="Scorepad", game=game, teams_data=TEAMS_DATA)

@app.route('/softball/api/update_score/<game_code>', methods=['POST'])
def update_score(game_code):
    """API endpoint to update game state based on action."""
    game = find_game(game_code)
    if not game:
        logger.error(f"Game not found in update_score: {game_code}")
        return jsonify({"error": "Game not found."}), 404

    action = request.args.get('action')
    if not action:
        logger.error("Missing action parameter in update_score")
        return jsonify({"error": "Missing action parameter."}), 400

    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            logger.error("Invalid JSON data in update_score")
            return jsonify({"error": "Invalid JSON data."}), 400
    except Exception as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return jsonify({"error": f"JSON parsing error: {str(e)}"}), 400

    if 'device_id' in data and data['device_id'] != game['device_id']:
        if game['device_id'] != 'web' and data['device_id'] != 'web':
            logger.warning(f"Unauthorized device: {data['device_id']} for game {game_code}")
            return jsonify({"error": "Unauthorized device."}), 403

    try:
        if action == 'H_SCORE_PLUS':
            game['home_score'] += 1
            game['balls'], game['strikes'], game['outs'], game['bases_state'] = 0, 0, 0, "0"
        elif action == 'A_SCORE_PLUS':
            game['away_score'] += 1
            game['balls'], game['strikes'], game['outs'], game['bases_state'] = 0, 0, 0, "0"
        elif action == 'BALL_PLUS':
            game['balls'] += 1
            if game['balls'] >= 4:
                if '3' in game['bases_state']:
                    if '2' in game['bases_state']:
                        if '1' in game['bases_state']:
                            if '1' in game['period']:
                                game['away_score'] += 1
                            else:
                                game['home_score'] += 1
                            game['bases_state'] = '123'
                        else:
                            game['bases_state'] = '123'
                    else:
                        game['bases_state'] = '13'
                else:
                    if game['bases_state'] == '0':
                        game['bases_state'] = '1'
                    else:
                        new_bases = ""
                        if '2' in game['bases_state']: new_bases += '3'
                        if '1' in game['bases_state']: new_bases += '2'
                        new_bases += '1'
                        game['bases_state'] = ''.join(sorted(set(new_bases)))
                game['balls'], game['strikes'] = 0, 0
        elif action == 'STRIKE_PLUS':
            game['strikes'] += 1
            if game['strikes'] >= 3:
                game['outs'] += 1
                game['balls'], game['strikes'] = 0, 0
        elif action == 'OUT_PLUS':
            game['outs'] += 1
            game['balls'], game['strikes'] = 0, 0
        elif action == 'RESET_COUNT':
            game['balls'], game['strikes'] = 0, 0
        elif action == 'SET_BASES' and 'bases_state' in data:
            bases = data.get('bases_state', '')
            if not all(b in ['1', '2', '3', ''] for b in bases):
                logger.error(f"Invalid base state: {bases}")
                return jsonify({"error": "Invalid base state."}), 400
            game['bases_state'] = ''.join(sorted(set(bases.replace('0', ''))))
        elif action == 'NEXT_INNING':
            game['balls'], game['strikes'], game['outs'], game['bases_state'] = 0, 0, 0, "0"
            current_period = game['period']
            try:
                if current_period.endswith('Top'):
                    game['period'] = current_period.replace('Top', 'Bottom')
                elif current_period.endswith('Bottom'):
                    inning_num = int(current_period.split(' ')[0][:-2])
                    game['period'] = f"{inning_num + 1}th Inning Top" if inning_num % 10 != 1 else f"{inning_num + 1}st Inning Top"
                    if inning_num >= 7:
                        game['status'] = 'COMPLETED'
                elif 'Inning' in current_period:
                    game['period'] += " Top"
                else:
                    game['period'] = "1st Inning Top"
                    if game['status'] != 'LIVE':
                        game['status'] = 'LIVE'
            except (ValueError, IndexError) as e:
                logger.error(f"Invalid period format: {current_period}")
                return jsonify({"error": f"Invalid period format: {current_period}"}), 400
        else:
            logger.error(f"Invalid action: {action}")
            return jsonify({"error": f"Invalid action: {action}"}), 400

        if game['outs'] >= 3:
            game['outs'] = 0
            game['balls'], game['strikes'], game['bases_state'] = 0, 0, "0"
            current_period = game['period']
            try:
                if current_period.endswith('Top'):
                    game['period'] = current_period.replace('Top', 'Bottom')
                elif current_period.endswith('Bottom'):
                    inning_num = int(current_period.split(' ')[0][:-2])
                    game['period'] = f"{inning_num + 1}th Inning Top" if inning_num % 10 != 1 else f"{inning_num + 1}st Inning Top"
                    if inning_num >= 7:
                        game['status'] = 'COMPLETED'
            except (ValueError, IndexError) as e:
                logger.error(f"Invalid period format on outs: {current_period}")
                return jsonify({"error": f"Invalid period format: {current_period}"}), 400

        logger.info(f"Game updated: {game_code} - {action}")
        return jsonify({
            "game_code": game['code'],
            "away_score": game['away_score'],
            "home_score": game['home_score'],
            "balls": game['balls'],
            "strikes": game['strikes'],
            "outs": game['outs'],
            "bases_state": game['bases_state'],
            "period": game['period'],
            "status": game['status']
        })

    except Exception as e:
        logger.error(f"Unhandled exception in update_score: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# --- Error Handlers ---

@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 error: {str(e)}")
    return render_template_string(ADMIN_HEAD + """
        <div class="flex flex-col h-screen justify-center items-center p-4">
            <div class="text-center">
                <h1 class="text-6xl font-black text-primary mb-4">404</h1>
                <p class="text-xl dark:text-white mb-6">Page Not Found</p>
                <a href="{{ url_for('softball_scores') }}" class="bg-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors">
                    Go to Home
                </a>
            </div>
        </div>
        </body></html>
    """), 404

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return render_template_string(ADMIN_HEAD + """
        <div class="flex flex-col h-screen justify-center items-center p-4">
            <div class="text-center">
                <h1 class="text-2xl font-bold text-primary mb-4">Server Error</h1>
                <p class="text-lg dark:text-white mb-6">An unexpected error occurred. Please try again later.</p>
                <a href="{{ url_for('softball_scores') }}" class="bg-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors">
                    Back to Home
                </a>
            </div>
        </div>
        </body></html>
    """), 500

if __name__ == '__main__':
    app.run(debug=True)
