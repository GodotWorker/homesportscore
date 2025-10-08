import json
import uuid
import random
import string
import re
from datetime import datetime
import mysql.connector
from flask import Flask, render_template_string, redirect, url_for, request, make_response, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# --- 1. Configuration & Helper Functions ---

# MySQL Configuration
DB_CONFIG = {
    'host': 'homesport.mysql.pythonanywhere-services.com',
    'user': 'homesport',
    'password': 'Dp9m%UCS9$wX@tCYEn72',
    'database': 'homesport$default'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(7) UNIQUE NOT NULL,
            home_team VARCHAR(255) NOT NULL,
            away_team VARCHAR(255) NOT NULL,
            home_score INT DEFAULT 0,
            away_score INT DEFAULT 0,
            status ENUM('UPCOMING', 'LIVE', 'FINISHED') DEFAULT 'UPCOMING',
            period VARCHAR(50) DEFAULT 'Pre-Game',
            game_type VARCHAR(50) NOT NULL,
            age_group VARCHAR(10) NOT NULL,
            gender ENUM('B', 'G') NOT NULL,
            time TIME NULL,
            device_id VARCHAR(20) NOT NULL,
            balls INT DEFAULT 0,
            strikes INT DEFAULT 0,
            outs INT DEFAULT 0,
            bases_state VARCHAR(10) DEFAULT '0',
            finished_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add finished_at column if it doesn't exist
    cursor.execute("SHOW COLUMNS FROM games LIKE 'finished_at'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE games ADD COLUMN finished_at TIMESTAMP NULL")
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('super_admin', 'admin', 'editor') DEFAULT 'editor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed super admin if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'mj'")
    if not cursor.fetchone():
        hash_pw = generate_password_hash('softball')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'super_admin')", ('mj', hash_pw))
    
    # New table for players
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            team VARCHAR(255) NOT NULL,
            positions TEXT NULL,
            jersey_number INT NULL,
            image_url VARCHAR(500) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Make jersey_number NULL if not already
    cursor.execute("SHOW COLUMNS FROM players LIKE 'jersey_number'")
    col_info = cursor.fetchone()
    if col_info and col_info[2] == 'NO':
        cursor.execute("ALTER TABLE players MODIFY COLUMN jersey_number INT NULL")
    
    # Add image_url to players if not exists
    cursor.execute("SHOW COLUMNS FROM players LIKE 'image_url'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE players ADD COLUMN image_url VARCHAR(500) NULL")
    
    # New table for teams (to store additional details, but use TEAMS_DATA for logos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            image_url VARCHAR(500) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add image_url to teams if not exists
    cursor.execute("SHOW COLUMNS FROM teams LIKE 'image_url'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE teams ADD COLUMN image_url VARCHAR(500) NULL")
    
    # Seed sample teams if empty
    cursor.execute("SELECT COUNT(*) FROM teams")
    if cursor.fetchone()[0] == 0:
        for team_name in TEAMS_DATA.keys():
            cursor.execute("INSERT IGNORE INTO teams (name) VALUES (%s)", (team_name,))
    
    # Update teams with image_urls from TEAMS_DATA
    for team_name, image_url in TEAMS_DATA.items():
        cursor.execute("UPDATE teams SET image_url = %s WHERE name = %s", (image_url, team_name))
    
    # Seed sample players if empty
    cursor.execute("SELECT COUNT(*) FROM players")
    if cursor.fetchone()[0] == 0:
        sample_players = [
            ("John Doe", "Hermanstad", "Pitcher", 12, None),
            ("Jane Smith", "Hermanstad", "Catcher", 5, None),
            ("Mike Johnson", "Simon Bekker", "1st Base", 23, None),
            ("Emily Davis", "Simon Bekker", "Shortstop", 7, None),
        ]
        for name, team, position, jersey, image_url in sample_players:
            cursor.execute("INSERT INTO players (name, team, positions, jersey_number, image_url) VALUES (%s, %s, %s, %s, %s)", (name, team, position, jersey, image_url))
    
    # Stories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            author_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

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
POSITIONS = ["Pitcher", "Catcher", "1st Base", "2nd Base", "3rd Base", "Shortstop", "Left Field", "Center Field", "Right Field"]

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_games():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM games ORDER BY created_at DESC")
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    # Format finished_at for display
    for game in games:
        game['finished_at_formatted'] = None
        finished_at = game.get('finished_at')
        if finished_at:
            try:
                game['finished_at_formatted'] = datetime.strptime(str(finished_at), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
            except ValueError:
                pass  # Invalid date format
    return games

def get_players():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM players ORDER BY team, name")
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    for player in players:
        if player.get('positions') == "Everywhere":
            player['positions_list'] = ["Everywhere"]
        elif player.get('positions'):
            player['positions_list'] = [p.strip() for p in player['positions'].split(',')]
        else:
            player['positions_list'] = []
        player['image_url'] = player.get('image_url', '')
    return players

def get_teams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teams ORDER BY name")
    teams = cursor.fetchall()
    cursor.close()
    conn.close()
    # Enrich with logos
    for team in teams:
        team['logo'] = team.get('image_url', TEAMS_DATA.get(team['name'], ''))
    return teams

def get_stories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, u.username as author_name 
        FROM stories s 
        LEFT JOIN users u ON s.author_id = u.id 
        ORDER BY s.created_at DESC
    """)
    stories = cursor.fetchall()
    cursor.close()
    conn.close()
    return stories

def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def find_game(game_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM games WHERE code = %s", (game_code,))
    game = cursor.fetchone()
    cursor.close()
    conn.close()
    if game:
        game['finished_at_formatted'] = None
        finished_at = game.get('finished_at')
        if finished_at:
            try:
                game['finished_at_formatted'] = datetime.strptime(str(finished_at), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
            except ValueError:
                pass
    return game

def create_game_db(home_team, away_team, device_id, game_type, age_group, gender, status, time_str=None):
    code = generate_game_code()
    period = "1st Inning Top" if status == 'LIVE' else "Pre-Game"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO games (code, home_team, away_team, status, period, game_type, age_group, gender, time, device_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (code, home_team, away_team, status, period, game_type, age_group, gender, time_str, device_id))
    conn.commit()
    cursor.close()
    conn.close()
    return code

def update_game(game_code, updates):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [game_code]
    cursor.execute(f"UPDATE games SET {set_clause} WHERE code = %s", values)
    conn.commit()
    cursor.close()
    conn.close()

def delete_game_db(game_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games WHERE code = %s", (game_code,))
    conn.commit()
    cursor.close()
    conn.close()

def update_user(user_id, updates):
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
    conn.commit()
    cursor.close()
    conn.close()

def create_user(username, password, role):
    hash_pw = generate_password_hash(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, hash_pw, role))
    conn.commit()
    cursor.close()
    conn.close()

# --- Authorization ---
def get_current_user():
    if 'user_id' not in session:
        return None
    return get_user(session['user_id'])

def is_authorized(required_role='editor'):
    user = get_current_user()
    if not user:
        return False
    role_order = {'editor': 0, 'admin': 1, 'super_admin': 2}
    return role_order.get(user['role'], -1) >= role_order.get(required_role, 0)

def is_super_admin():
    user = get_current_user()
    return user and user['role'] == 'super_admin'

# --- 2. HTML Templates ---

# Base header for navigation
BASE_HEADER = """
<header class="sticky top-0 z-10 bg-background-color/80 backdrop-blur-sm">
<div class="flex items-center p-4 justify-between">
<h1 class="text-xl font-bold tracking-tight text-center flex-1"><a href="{{ url_for('home') }}">Softball Hub</a></h1>
<div class="flex items-center gap-4">
<a href="{{ url_for('scores') }}" class="text-text-secondary hover:text-primary-color transition-colors">Scores</a>
<a href="{{ url_for('players') }}" class="text-text-secondary hover:text-primary-color transition-colors">Players</a>
<a href="{{ url_for('teams') }}" class="text-text-secondary hover:text-primary-color transition-colors">Teams</a>
<a href="{{ url_for('stories') }}" class="text-text-secondary hover:text-primary-color transition-colors">Stories</a>
{% if current_user %}
<a href="{{ url_for('web_admin') }}" class="text-text-secondary hover:text-primary-color transition-colors">Dashboard</a>
<a href="{{ url_for('web_logout') }}" class="text-red-500 hover:text-red-700 transition-colors">Logout ({{ current_user.username }})</a>
{% else %}
<a href="{{ url_for('web_login') }}" class="flex items-center justify-center rounded-full h-10 w-10 text-primary-color hover:bg-primary-color/10 transition-colors bg-card-color">
<span class="material-symbols-outlined"> settings </span>
</a>
{% endif %}
</div>
</div>
</header>
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Home</title>
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
""" + BASE_HEADER + """
<main class="p-4 space-y-6">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-primary-color mb-4">Welcome to Softball Hub</h1>
    <p class="text-xl text-text-secondary mb-8">Your one-stop destination for live scores, player stats, team rosters, and inspiring stories from the diamond.</p>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <a href="{{ url_for('scores') }}" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> sports_score </span>
      <h2 class="text-xl font-bold">Live Scores</h2>
      <p class="text-text-secondary">Follow games in real-time</p>
    </a>
    <a href="{{ url_for('players') }}" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> person </span>
      <h2 class="text-xl font-bold">Players</h2>
      <p class="text-text-secondary">View profiles and stats</p>
    </a>
    <a href="{{ url_for('teams') }}" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> groups </span>
      <h2 class="text-xl font-bold">Teams</h2>
      <p class="text-text-secondary">Rosters and schedules</p>
    </a>
    <a href="{{ url_for('stories') }}" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> article </span>
      <h2 class="text-xl font-bold">Stories</h2>
      <p class="text-text-secondary">Highlights and news</p>
    </a>
  </div>
  {% if current_user %}
  <div class="text-center">
    <a href="{{ url_for('web_admin') }}" class="bg-primary-color text-white font-bold py-3 px-6 rounded-lg hover:bg-primary-color/80 transition-colors">Admin Dashboard</a>
  </div>
  {% endif %}
</main>
</div>
</body>
</html>
"""

SCORES_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Scores</title>
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
""" + BASE_HEADER + """
<main class="p-4 space-y-6">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-primary-color mb-4">Live Scores</h1>
    <p class="text-xl text-text-secondary mb-8">Track all the action from ongoing and upcoming games.</p>
  </div>
  {% if games %}
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4">
    {% for game in games %}
    <div class="bg-card-color rounded-lg p-4 border-l-4 border-primary-color">
      <div class="flex justify-between items-center mb-2">
        <h3 class="text-lg font-bold">{{ game.home_team }} vs {{ game.away_team }}</h3>
        <span class="text-sm text-text-secondary">{{ game.status }}</span>
      </div>
      <div class="text-2xl font-bold text-center mb-2">{{ game.home_score }} - {{ game.away_score }}</div>
      <p class="text-text-secondary">{{ game.period }}</p>
      {% if game.finished_at_formatted %}
      <p class="text-sm text-text-secondary mt-2">Finished: {{ game.finished_at_formatted }}</p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p class="text-center text-text-secondary">No games scheduled yet.</p>
  {% endif %}
  {% if current_user and is_authorized('editor') %}
  <div class="text-center">
    <a href="{{ url_for('create_game') }}" class="bg-primary-color text-white font-bold py-2 px-4 rounded-lg hover:bg-primary-color/80 transition-colors">Create New Game</a>
  </div>
  {% endif %}
</main>
</div>
</body>
</html>
"""

PLAYERS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Players</title>
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
""" + BASE_HEADER + """
<main class="p-4 space-y-6">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-primary-color mb-4">Players</h1>
    <p class="text-xl text-text-secondary mb-8">Explore player profiles and statistics.</p>
  </div>
  {% if players %}
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {% for player in players %}
    <div class="bg-card-color rounded-lg p-4">
      {% if player.image_url %}
      <img src="{{ player.image_url }}" alt="{{ player.name }}" class="w-full h-auto max-h-48 object-contain rounded mb-2">
      {% endif %}
      <h3 class="text-lg font-bold">{{ player.name }}</h3>
      <p class="text-text-secondary">Team: {{ player.team }}</p>
      <p class="text-text-secondary">Jersey: #{{ player.jersey_number or 'N/A' }}</p>
      <p class="text-text-secondary">Positions: {{ player.positions_list | join(', ') if player.positions_list else 'N/A' }}</p>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p class="text-center text-text-secondary">No players found.</p>
  {% endif %}
</main>
</div>
</body>
</html>
"""

TEAMS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Teams</title>
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
""" + BASE_HEADER + """
<main class="p-4 space-y-6">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-primary-color mb-4">Teams</h1>
    <p class="text-xl text-text-secondary mb-8">View team rosters and details.</p>
  </div>
  {% if teams %}
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {% for team in teams %}
    <div class="bg-card-color rounded-lg p-4">
      {% if team.logo %}
      <img src="{{ team.logo }}" alt="{{ team.name }}" class="w-full h-auto max-h-48 object-contain rounded mb-2">
      {% endif %}
      <h3 class="text-lg font-bold">{{ team.name }}</h3>
      {% if team.description %}
      <p class="text-text-secondary">{{ team.description }}</p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p class="text-center text-text-secondary">No teams found.</p>
  {% endif %}
</main>
</div>
</body>
</html>
"""

STORIES_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Stories</title>
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
""" + BASE_HEADER + """
<main class="p-4 space-y-6">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-primary-color mb-4">Stories</h1>
    <p class="text-xl text-text-secondary mb-8">Read inspiring stories from the softball community.</p>
  </div>
  {% if stories %}
  <div class="space-y-4">
    {% for story in stories %}
    <div class="bg-card-color rounded-lg p-4">
      <h3 class="text-lg font-bold mb-2">{{ story.title }}</h3>
      <p class="text-text-secondary mb-2">{{ story.content[:200] }}...</p>
      <div class="text-sm text-text-secondary">
        By {{ story.author_name or 'Anonymous' }} on {{ story.created_at.strftime('%Y-%m-%d') }}
      </div>
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p class="text-center text-text-secondary">No stories yet.</p>
  {% endif %}
</main>
</div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Login</title>
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
</head>
<body class="bg-background-color text-text-primary min-h-screen flex items-center justify-center" style='font-family: Lexend, "Noto Sans", sans-serif;'>
<div class="max-w-md w-full space-y-8">
  <div>
    <h2 class="mt-6 text-center text-3xl font-bold text-text-primary">Sign in to your account</h2>
  </div>
  <form class="mt-8 space-y-6" action="{{ url_for('web_login') }}" method="POST">
    <div class="rounded-md shadow-sm space-y-4">
      <div>
        <label for="username" class="block text-sm font-medium text-text-secondary">Username</label>
        <input id="username" name="username" type="text" required class="relative block w-full rounded-md border-0 py-1.5 px-3 text-text-primary placeholder:text-text-secondary bg-card-color focus:outline-none focus:ring-1 focus:ring-primary-color focus:border-primary-color sm:text-sm">
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-text-secondary">Password</label>
        <input id="password" name="password" type="password" required class="relative block w-full rounded-md border-0 py-1.5 px-3 text-text-primary placeholder:text-text-secondary bg-card-color focus:outline-none focus:ring-1 focus:ring-primary-color focus:border-primary-color sm:text-sm">
      </div>
    </div>
    <div>
      <button type="submit" class="group relative flex w-full justify-center rounded-md bg-primary-color py-2 px-4 text-sm font-medium text-white hover:bg-primary-color/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-color">
        Sign in
      </button>
    </div>
  </form>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="mt-4">
        {% for message in messages %}
          <p class="text-red-600 text-sm">{{ message }}</p>
        {% endfor %}
      </div>
    {% endif %}
  {% endwith %}
</div>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Admin Dashboard</title>
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
""" + BASE_HEADER + """
<main class="p-4 space-y-6">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-primary-color mb-4">Admin Dashboard</h1>
    <p class="text-xl text-text-secondary mb-8">Manage games, users, and content.</p>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {% if is_authorized('editor') %}
    <a href="{{ url_for('create_game') }}" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> add </span>
      <h2 class="text-xl font-bold">Create Game</h2>
    </a>
    {% endif %}
    {% if is_authorized('admin') %}
    <a href="#" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> manage_accounts </span>
      <h2 class="text-xl font-bold">Manage Users</h2>
    </a>
    {% endif %}
    {% if is_super_admin() %}
    <a href="#" class="bg-card-color rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <span class="material-symbols-outlined text-4xl text-primary-color mb-2 block"> security </span>
      <h2 class="text-xl font-bold">System Settings</h2>
    </a>
    {% endif %}
  </div>
  <div class="bg-card-color rounded-lg p-6">
    <h2 class="text-xl font-bold mb-4">Quick Stats</h2>
    <p>Total Games: {{ games|length }}</p>
    <p>Total Players: {{ players|length }}</p>
    <p>Total Stories: {{ stories|length }}</p>
  </div>
</main>
</div>
</body>
</html>
"""

CREATE_GAME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link crossorigin="" href="https://fonts.gstatic.com/" rel="preconnect"/>
<link as="style" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Lexend%3Awght%40400%3B500%3B700%3B900&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" onload="this.rel='stylesheet'" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
<title>Softball Hub - Create Game</title>
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
</head>
<body class="bg-background-color text-text-primary min-h-screen" style='font-family: Lexend, "Noto Sans", sans-serif;'>
<div class="relative flex h-auto min-h-screen w-full flex-col justify-between group/design-root overflow-x-hidden">
""" + BASE_HEADER + """
<main class="p-4">
  <div class="max-w-md mx-auto bg-card-color rounded-lg p-6">
    <h2 class="text-2xl font-bold mb-4">Create New Game</h2>
    <form action="{{ url_for('create_game') }}" method="POST">
      <div class="space-y-4">
        <div>
          <label for="home_team" class="block text-sm font-medium text-text-secondary">Home Team</label>
          <select id="home_team" name="home_team" required class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
            {% for team in teams %}
            <option value="{{ team.name }}">{{ team.name }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="away_team" class="block text-sm font-medium text-text-secondary">Away Team</label>
          <select id="away_team" name="away_team" required class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
            {% for team in teams %}
            <option value="{{ team.name }}">{{ team.name }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="game_type" class="block text-sm font-medium text-text-secondary">Game Type</label>
          <input id="game_type" name="game_type" type="text" required class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
        </div>
        <div>
          <label for="age_group" class="block text-sm font-medium text-text-secondary">Age Group</label>
          <select id="age_group" name="age_group" required class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
            {% for age in AGE_GROUPS %}
            <option value="{{ age }}">{{ age }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="gender" class="block text-sm font-medium text-text-secondary">Gender</label>
          <select id="gender" name="gender" required class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
            {% for g in GENDER_OPTIONS %}
            <option value="{{ g }}">{{ 'Boys' if g == 'B' else 'Girls' }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="status" class="block text-sm font-medium text-text-secondary">Status</label>
          <select id="status" name="status" required class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
            <option value="UPCOMING">Upcoming</option>
            <option value="LIVE">Live</option>
          </select>
        </div>
        <div>
          <label for="time" class="block text-sm font-medium text-text-secondary">Time (Optional)</label>
          <input id="time" name="time" type="time" class="block w-full rounded-md border-0 py-1.5 px-3 bg-white text-text-primary">
        </div>
        <div>
          <button type="submit" class="w-full bg-primary-color text-white py-2 px-4 rounded-md hover:bg-primary-color/80">Create Game</button>
        </div>
      </div>
    </form>
  </div>
</main>
</div>
</body>
</html>
"""

# --- 3. Flask App Setup ---

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change to a secure random key

# Initialize database on module import (runs once when the module is loaded, e.g., in WSGI)
init_db()

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE, current_user=get_current_user())

@app.route('/scores')
def scores():
    return render_template_string(SCORES_TEMPLATE, current_user=get_current_user(), games=get_games(), is_authorized=is_authorized)

@app.route('/players')
def players():
    return render_template_string(PLAYERS_TEMPLATE, current_user=get_current_user(), players=get_players())

@app.route('/teams')
def teams():
    return render_template_string(TEAMS_TEMPLATE, current_user=get_current_user(), teams=get_teams())

@app.route('/stories')
def stories():
    return render_template_string(STORIES_TEMPLATE, current_user=get_current_user(), stories=get_stories())

@app.route('/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            return redirect(url_for('web_admin'))
        else:
            flash('Invalid username or password')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def web_logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/admin')
def web_admin():
    if not is_authorized():
        return redirect(url_for('web_login'))
    return render_template_string(ADMIN_TEMPLATE, current_user=get_current_user(), games=get_games(), players=get_players(), stories=get_stories(), is_authorized=is_authorized, is_super_admin=is_super_admin)

@app.route('/create_game', methods=['GET', 'POST'])
def create_game():
    if not is_authorized('editor'):
        return redirect(url_for('web_login'))
    if request.method == 'POST':
        home_team = request.form['home_team']
        away_team = request.form['away_team']
        game_type = request.form['game_type']
        age_group = request.form['age_group']
        gender = request.form['gender']
        status = request.form['status']
        time_str = request.form.get('time')
        device_id = str(uuid.uuid4())[:20]  # Generate a mock device ID
        code = create_game_db(home_team, away_team, device_id, game_type, age_group, gender, status, time_str)
        flash(f'Game created with code: {code}')
        return redirect(url_for('scores'))
    return render_template_string(CREATE_GAME_TEMPLATE, current_user=get_current_user(), teams=get_teams(), AGE_GROUPS=AGE_GROUPS, GENDER_OPTIONS=GENDER_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True)
