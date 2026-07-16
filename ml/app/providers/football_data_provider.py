"""football-data.org provider (competitions, fixtures, teams, standings, results)."""

import logging
from datetime import datetime
from typing import Optional

from .base_provider import BaseProvider
from ..schemas import Competition, Fixture, Season, StandingRow, Team
from ..config import settings
from ..http import request_json

logger = logging.getLogger("provider.football_data")
BASE = "https://api.football-data.org/v4"


class FootballDataProvider(BaseProvider):
    name = "football-data.org"
    description = "Competitions, fixtures, teams, standings, results"

    # Map football-data competition codes -> our competition names
    CODE_TO_NAME = {
        "PL": "English Premier League",
        "PD": "La Liga",
        "BL1": "Bundesliga",
        "SA": "Serie A",
        "FL1": "Ligue 1",
        "CL": "UEFA Champions League",
    }

    def _headers(self):
        return {"X-Auth-Token": settings.football_data_api_key}

    def check_connection(self) -> bool:
        if not settings.has_football_data:
            logger.warning("football-data: no API key configured")
            return False
        data = request_json(f"{BASE}/competitions", headers=self._headers(),
                            provider=self.name, fallback=lambda: {"count": 0, "competitions": []})
        return isinstance(data, dict) and "competitions" in data

    def get_competitions(self) -> list[Competition]:
        data = request_json(f"{BASE}/competitions", headers=self._headers(),
                            provider=self.name, fallback=lambda: {"competitions": []})
        out = []
        for c in data.get("competitions", []) if isinstance(data, dict) else []:
            code = c.get("code")
            if code in self.CODE_TO_NAME or c.get("plan") == "TIER_ONE":
                out.append(Competition(
                    name=self.CODE_TO_NAME.get(code, c.get("name")),
                    code=code,
                    country=(c.get("area") or {}).get("name"),
                    external_id=str(c.get("id")),
                ))
        return out

    def get_seasons(self, competition: Competition) -> list[Season]:
        data = request_json(f"{BASE}/competitions/{competition.external_id}",
                            headers=self._headers(), provider=self.name,
                            fallback=lambda: {"seasons": []})
        out = []
        for s in data.get("seasons", []) if isinstance(data, dict) else []:
            yr = s.get("startDate", "")[:4]
            out.append(Season(
                competition_name=competition.name,
                name=s.get("startDate", "")[:4] + "/" + s.get("endDate", "")[2:4],
                start_year=int(yr) if yr.isdigit() else None,
                end_year=int(s.get("endDate", "")[2:4]) if s.get("endDate", "")[2:4].isdigit() else None,
                external_id=str(s.get("id")),
            ))
        return out

    def get_teams(self, competition: Competition, season: Season) -> list[Team]:
        url = f"{BASE}/competitions/{competition.external_id}/teams"
        data = request_json(url, headers=self._headers(),
                            params={"season": season.start_year},
                            provider=self.name, fallback=lambda: {"teams": []})
        return [
            Team(name=t.get("name"), short_name=t.get("shortName"), external_id=str(t.get("id")))
            for t in data.get("teams", []) if isinstance(data, dict)
        ]

    def get_fixtures(self, competition: Competition, season: Season) -> list[Fixture]:
        url = f"{BASE}/competitions/{competition.external_id}/matches"
        data = request_json(url, headers=self._headers(),
                            params={"season": season.start_year},
                            provider=self.name, fallback=lambda: {"matches": []})
        out = []
        for m in data.get("matches", []) if isinstance(data, dict) else []:
            home = (m.get("homeTeam") or {}).get("name")
            away = (m.get("awayTeam") or {}).get("name")
            if not home or not away:
                continue
            ko = m.get("utcDate")
            out.append(Fixture(
                external_id=str(m.get("id")),
                competition_name=competition.name,
                season_name=season.name,
                home_team=home,
                away_team=away,
                kickoff=datetime.fromisoformat(ko.replace("Z", "+00:00")) if ko else datetime.now(),
                status=m.get("status", "SCHEDULED"),
                matchday=m.get("matchday"),
                venue=(m.get("venue") or {}).get("name"),
                home_score=(m.get("score") or {}).get("fullTime", {}).get("home"),
                away_score=(m.get("score") or {}).get("fullTime", {}).get("away"),
            ))
        return out

    def get_standings(self, competition: Competition, season: Season) -> list[StandingRow]:
        url = f"{BASE}/competitions/{competition.external_id}/standings"
        data = request_json(url, headers=self._headers(),
                            params={"season": season.start_year},
                            provider=self.name, fallback=lambda: {"standings": []})
        out = []
        tables = (data.get("standings") or []) if isinstance(data, dict) else []
        for table in tables:
            for row in table.get("table", []):
                team = (row.get("team") or {}).get("name")
                if not team:
                    continue
                out.append(StandingRow(
                    competition_name=competition.name,
                    season_name=season.name,
                    team_name=team,
                    position=row.get("position", 0),
                    played=row.get("playedGames", 0),
                    wins=row.get("won", 0),
                    draws=row.get("draw", 0),
                    losses=row.get("lost", 0),
                    goals_for=row.get("goalsFor", 0),
                    goals_against=row.get("goalsAgainst", 0),
                    points=row.get("points", 0),
                ))
        return out
