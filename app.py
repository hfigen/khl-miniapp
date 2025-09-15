"""
Flask application for the KHL statistics Telegram mini‑app.

This application serves both the static web app (front‑end) and a
set of JSON APIs used by the front‑end to search for players and
retrieve their statistics.  It also exposes an optional Telegram
bot handler which can be run separately to integrate the web app
into a Telegram channel.

Run with:

    FLASK_APP=khl_stats.app FLASK_ENV=development flask run --reload --port=8000

Adjust the port as needed and configure the ``WEB_APP_URL`` below
to point to your publicly accessible URL when deploying.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

from .parser import PlayerStats, get_player_stats, get_players, search_players

LOGGER = logging.getLogger(__name__)

# Create Flask app
BASE_DIR = os.path.dirname(__file__)
app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR)

@app.route('/')
def index() -> str:
    """Serve the main page for the Telegram mini‑app."""
    return render_template('index.html')


@app.route('/api/search')
def api_search() -> Dict[str, List[Dict[str, str]]]:
    """Endpoint for player name autocomplete.

    Query parameters:
      * q: partial player name (required)
      * season: season in format "YYYY/YYYY" (optional, defaults to current season)
      * playoff: 'true' to search in play‑off stats (optional)

    Returns JSON list of players with their name, team and position.
    """
    query = request.args.get('q', '')
    season = request.args.get('season') or os.environ.get('DEFAULT_SEASON', '')
    playoff_param = request.args.get('playoff', 'false').lower()
    playoff = playoff_param in ('1', 'true', 'yes')

    if not query:
        return jsonify({'players': []})

    # If season is not specified, default to the current KHL season (approx.)
    if not season:
        # Determine the current season; KHL seasons typically start in one year and end in the next.
        today = request.environ.get('werkzeug.request')  # type: ignore[attr-defined]
        # Fallback: compute from current date
        from datetime import date
        current_year = date.today().year
        # For September and later, season ends next year; for earlier months, ends this year
        end_year = current_year + 1 if date.today().month >= 7 else current_year
        start_year = end_year - 1
        season = f"{start_year}/{end_year}"

    try:
        players = get_players(season, playoff)
    except Exception as exc:
        LOGGER.exception("Failed to retrieve players for season %s", season)
        return jsonify({'error': 'Failed to load player list'}), 500

    matches = search_players(query, players, limit=10)
    return jsonify({'players': [p.to_dict for p in matches]})


@app.route('/api/stats')
def api_stats() -> Dict[str, Dict[str, str | int]]:
    """Endpoint for retrieving statistics for a single player.

    Query parameters:
      * player: full player name (required)
      * season: season in format "YYYY/YYYY" (required)
      * playoff: 'true' to retrieve play‑off stats (optional)
    """
    name = request.args.get('player', '').strip()
    season = request.args.get('season', '').strip()
    playoff_param = request.args.get('playoff', 'false').lower()
    playoff = playoff_param in ('1', 'true', 'yes')
    if not name or not season:
        return jsonify({'error': 'Missing player or season parameter'}), 400

    try:
        stats = get_player_stats(name, season, playoff)
    except Exception as exc:
        LOGGER.exception("Error retrieving stats for %s", name)
        return jsonify({'error': 'Failed to fetch player stats'}), 500
    if not stats:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify({'stats': stats.to_dict})


def main() -> None:
    """Run the Flask app standalone."""
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
