"""
Parser module for fetching and parsing KHL player statistics
from the allhockey.ru website.

This module exposes functions for downloading the raw HTML
for a given season and tournament (regular season or play‑off),
parsing the statistics table into structured Python data and
searching for players by name.  The allhockey.ru website uses
a predictable URL pattern where the last year of a season (for
example 2025 for the 2024/2025 season) together with a numeric
code identifies the type of tournament:

* 312 – regular season player stats (bombardiers list)
* 315 – play‑off player stats

Each page contains a table with columns:

    №, Игрок, Команда, Ком (abbr), Амп (position), О (points), Ш (goals),
    А (assists), И (games), +/- (plus/minus), Штр (penalty minutes),
    БВ (shots on goal), %БВ (shot percentage), ВП/И (average TOI).

Only a subset of these fields is needed for the mini‑app (games,
goals, assists, points, +/- and penalty minutes).

Note: All network access is done via the ``requests`` module.
Ensure that you run this code from an environment with internet
access. For local testing without network access you can use the
``parse_html`` function directly on a saved HTML file.
"""
from __future__ import annotations

import datetime
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)


@dataclass
class PlayerStats:
    """Data structure to hold statistics for a single player."""

    name: str
    team: str
    team_abbr: str
    position: str
    points: int
    goals: int
    assists: int
    games: int
    plus_minus: int
    penalty: int

    @property
    def to_dict(self) -> Dict[str, str | int]:
        """Return a dictionary representation for JSON serialization."""
        return {
            "name": self.name,
            "team": self.team,
            "team_abbr": self.team_abbr,
            "position": self.position,
            "points": self.points,
            "goals": self.goals,
            "assists": self.assists,
            "games": self.games,
            "plus_minus": self.plus_minus,
            "penalty": self.penalty,
        }


def _season_to_year(season: str) -> int:
    """Convert a season string like "2024/2025" into the ending year integer (2025).

    If the season is a single year ("2025"), it is returned as int.
    """
    if "/" in season:
        parts = season.split("/")
        try:
            return int(parts[1])
        except (IndexError, ValueError):
            raise ValueError(f"Invalid season format: {season}")
    return int(season)


def _build_url(season: str, playoff: bool) -> str:
    """Build the URL for the allhockey.ru statistics page.

    :param season: season in format "YYYY/YYYY" or the ending year
    :param playoff: if True return play‑off stats; otherwise regular.
    """
    year = _season_to_year(season)
    code = 315 if playoff else 312
    return f"https://allhockey.ru/stat/khl/{year}/{code}/player"


def fetch_html(season: str, playoff: bool = False, *, timeout: int = 30) -> str:
    """Download the raw HTML for the given season and tournament.

    :param season: season in format "YYYY/YYYY" or just the ending year
    :param playoff: True for play‑off stats
    :param timeout: request timeout in seconds
    :returns: HTML content as text
    :raises HTTPError: if the request fails
    """
    url = _build_url(season, playoff)
    LOGGER.info("Fetching stats page: %s", url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0 Safari/537.36"
        ),
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_html(html: str) -> List[PlayerStats]:
    """Parse the player statistics table from raw HTML.

    The function locates the table element containing the player
    statistics and extracts each row into a :class:`PlayerStats`.

    :param html: raw HTML text
    :returns: list of PlayerStats
    :raises ValueError: if no table is found
    """
    soup = BeautifulSoup(html, "html.parser")
    # Find the statistics table by searching for the header 'Игрок'
    table = None
    for candidate in soup.find_all("table"):
        # gather the first few header cells
        cells = [th.get_text().strip() for th in candidate.find_all(["th", "td"])]
        if cells and "Игрок" in cells:
            table = candidate
            break
    if table is None:
        raise ValueError("Statistics table not found in the provided HTML")

    players: List[PlayerStats] = []
    # Skip the header row(s). The first row contains column names.
    for tr in table.find_all("tr")[1:]:
        cols = [c.get_text().strip() for c in tr.find_all(["td", "th"])]
        if not cols or len(cols) < 12:
            continue  # skip rows that don't match expected structure
        try:
            # columns: 0: rank, 1: player name, 2: team, 3: team abbr, 4: position,
            # 5: points, 6: goals, 7: assists, 8: games, 9: plus/minus,
            # 10: penalty, ...
            name = cols[1]
            team = cols[2]
            team_abbr = cols[3]
            position = cols[4]
            points = int(cols[5]) if cols[5].isdigit() else 0
            goals = int(cols[6]) if cols[6].isdigit() else 0
            assists = int(cols[7]) if cols[7].isdigit() else 0
            games = int(cols[8]) if cols[8].isdigit() else 0
            # plus/minus may include a sign and digits
            plus_minus = int(cols[9]) if re.match(r"^-?\d+$", cols[9]) else 0
            penalty = int(cols[10]) if cols[10].isdigit() else 0
            players.append(
                PlayerStats(
                    name=name,
                    team=team,
                    team_abbr=team_abbr,
                    position=position,
                    points=points,
                    goals=goals,
                    assists=assists,
                    games=games,
                    plus_minus=plus_minus,
                    penalty=penalty,
                )
            )
        except Exception as exc:
            LOGGER.debug("Failed to parse row: %s", cols, exc_info=exc)
            continue
    return players


@lru_cache(maxsize=10)
def get_players(season: str, playoff: bool = False) -> List[PlayerStats]:
    """Return all player statistics for a given season and tournament.

    Uses caching to avoid repeated network calls.
    """
    html = fetch_html(season, playoff)
    return parse_html(html)


def search_players(query: str, players: Iterable[PlayerStats], limit: int = 10) -> List[PlayerStats]:
    """Search for players whose names start with the given query (case‑insensitive).

    :param query: partial player name in Russian
    :param players: iterable of PlayerStats to search in
    :param limit: maximum number of results to return
    :returns: a list of matching players (up to ``limit``)
    """
    q = query.strip().lower()
    if not q:
        return []
    matches: List[PlayerStats] = []
    for p in players:
        name_lower = p.name.lower()
        if name_lower.startswith(q):
            matches.append(p)
            if len(matches) >= limit:
                break
    return matches


def get_player_stats(name: str, season: str, playoff: bool = False) -> Optional[PlayerStats]:
    """Retrieve statistics for a single player by exact name match.

    :param name: full player name (case-insensitive)
    :param season: season in format "YYYY/YYYY" or the ending year
    :param playoff: True for play‑off stats
    :returns: PlayerStats or None if not found
    """
    players = get_players(season, playoff)
    target = name.lower().strip()
    for p in players:
        if p.name.lower() == target:
            return p
    return None
