"""ClubElo provider (https://clubelo.com). Provides current and historical
Elo ratings. The public CSV endpoint is used; graceful fallback on failure."""

import csv
import io
import logging
from typing import Optional

from .base_provider import BaseProvider
from ..schemas import EloRating
from ..config import settings
from ..http import request_json

logger = logging.getLogger("provider.clubelo")

BASE = "https://api.clubelo.com"


class ClubEloProvider(BaseProvider):
    name = "ClubElo"
    description = "Club Elo ratings (current + historical)"

    def check_connection(self) -> bool:
        data = request_json(f"{BASE}/TEAM?team=English+Premier+League",
                            provider=self.name, fallback=lambda: "")
        return isinstance(data, str) and "Rank" in data

    def get_elo_ratings(self) -> list[EloRating]:
        """Fetch current Elo for all teams (the TEAM?team=ALL endpoint)."""
        csv_text = request_json(f"{BASE}/TEAM?team=ALL", provider=self.name, fallback=lambda: "")
        if not isinstance(csv_text, str) or "Rank" not in csv_text:
            return []
        return self._parse_csv(csv_text)

    def get_elo_history(self, team: str) -> list[EloRating]:
        safe = team.replace(" ", "+")
        csv_text = request_json(f"{BASE}/TEAM?team={safe}", provider=self.name, fallback=lambda: "")
        if not isinstance(csv_text, str) or "Rank" not in csv_text:
            return []
        rows = self._parse_csv(csv_text)
        for r in rows:
            r.team_name = team
        return rows

    def _parse_csv(self, csv_text: str) -> list[EloRating]:
        out = []
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            try:
                out.append(EloRating(
                    team_name=row.get("Club") or row.get("Team"),
                    rating=float(row.get("Elo")),
                    rank=_to_int(row.get("Rank")),
                    date=row.get("From") or row.get("Date"),
                    country=row.get("Country"),
                ))
            except (TypeError, ValueError):
                continue
        return out


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
