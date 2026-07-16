"""API-Football provider (injuries, suspensions, lineups, team & player
statistics, odds). Requires API_FOOTBALL_API_KEY."""

import logging
from datetime import datetime
from typing import Optional

from .base_provider import BaseProvider
from ..schemas import (
    Fixture, Injury, Lineup, Odds, PlayerStatistic, Suspension, Team,
)
from ..config import settings
from ..http import request_json

logger = logging.getLogger("provider.api_football")
BASE = "https://v3.football.api-sports.io"


class ApiFootballProvider(BaseProvider):
    name = "API-Football"
    description = "Injuries, suspensions, lineups, team/player stats, odds"

    def _headers(self):
        return {"x-apisports-key": settings.api_football_api_key}

    def check_connection(self) -> bool:
        if not settings.has_api_football:
            logger.warning("API-Football: no API key configured")
            return False
        data = request_json(f"{BASE}/status", headers=self._headers(),
                            provider=self.name, fallback=lambda: {"response": {}})
        return isinstance(data, dict) and "response" in data

    def _team_id(self, team: Team) -> Optional[str]:
        return team.external_id

    def get_injuries(self, team: Team) -> list[Injury]:
        tid = self._team_id(team)
        if not tid:
            return []
        data = request_json(f"{BASE}/injuries", headers=self._headers(),
                            params={"team": tid}, provider=self.name,
                            fallback=lambda: {"response": []})
        out = []
        for r in data.get("response", []) if isinstance(data, dict) else []:
            player = r.get("player", {})
            out.append(Injury(
                team_name=team.name,
                player_name=player.get("name"),
                reason=r.get("reason"),
                type=r.get("type"),
                until=r.get("return", {}).get("date"),
            ))
        return out

    def get_suspensions(self, team: Team) -> list[Suspension]:
        tid = self._team_id(team)
        if not tid:
            return []
        data = request_json(f"{BASE}/sidelined", headers=self._headers(),
                            params={"team": tid}, provider=self.name,
                            fallback=lambda: {"response": []})
        out = []
        for r in data.get("response", []) if isinstance(data, dict) else []:
            out.append(Suspension(
                team_name=team.name,
                player_name=r.get("player", {}).get("name"),
                reason=r.get("reason"),
                until=r.get("end"),
            ))
        return out

    def get_lineups(self, fixture: Fixture) -> list[Lineup]:
        data = request_json(f"{BASE}/fixtures/lineups", headers=self._headers(),
                            params={"fixture": fixture.external_id},
                            provider=self.name, fallback=lambda: {"response": []})
        out = []
        for r in data.get("response", []) if isinstance(data, dict) else []:
            out.append(Lineup(
                external_fixture_id=fixture.external_id,
                team_name=r.get("team", {}).get("name"),
                formation=r.get("formation"),
                starting_players=[p.get("player") for p in r.get("startXI", [])],
                substitute_players=[p.get("player") for p in r.get("substitutes", [])],
            ))
        return out

    def get_player_statistics(self, fixture: Fixture) -> list[PlayerStatistic]:
        data = request_json(f"{BASE}/fixtures/players", headers=self._headers(),
                            params={"fixture": fixture.external_id},
                            provider=self.name, fallback=lambda: {"response": []})
        out = []
        for team_block in data.get("response", []) if isinstance(data, dict) else []:
            team_name = team_block.get("team", {}).get("name")
            for p in team_block.get("players", []):
                out.append(PlayerStatistic(
                    external_fixture_id=fixture.external_id,
                    player_name=p.get("player", {}).get("name"),
                    team_name=team_name,
                    minutes=(p.get("statistics", [{}])[0].get("games", {}) or {}).get("minutes"),
                    goals=(p.get("statistics", [{}])[0].get("goals", {}) or {}).get("total") or 0,
                    rating=(p.get("statistics", [{}])[0].get("games", {}) or {}).get("rating"),
                ))
        return out

    def get_odds(self, fixture: Fixture) -> list[Odds]:
        data = request_json(f"{BASE}/odds", headers=self._headers(),
                            params={"fixture": fixture.external_id},
                            provider=self.name, fallback=lambda: {"response": []})
        out = []
        for book in data.get("response", []) if isinstance(data, dict) else []:
            for bet in book.get("bookmakers", [{}])[0].get("bets", []):
                if bet.get("name") == "Match Winner":
                    vals = {v.get("value"): v.get("odd") for v in bet.get("values", [])}
                    out.append(Odds(
                        external_fixture_id=fixture.external_id,
                        bookmaker=book.get("bookmaker", {}).get("name"),
                        home=vals.get("Home"),
                        draw=vals.get("Draw"),
                        away=vals.get("Away"),
                    ))
        return out
