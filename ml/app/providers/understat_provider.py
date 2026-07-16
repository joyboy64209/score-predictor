"""Understat provider. Scrapes xG / xGA / xPoints / advanced attacking &
defensive metrics from https://understat.com using the embedded JSON in the
page (no fragile DOM parsing). Falls back gracefully when blocked."""

import json
import logging
import re
from typing import Optional

from .base_provider import BaseProvider
from ..schemas import AdvancedMetric, Competition, Season, Team
from ..config import settings
from ..http import request_json

logger = logging.getLogger("provider.understat")

UNDERSTAT_LEAGUE = {
    "English Premier League": "EPL",
    "La Liga": "La_liga",
    "Bundesliga": "Bundesliga",
    "Serie A": "Serie_A",
    "Ligue 1": "Ligue_1",
}


class UnderstatProvider(BaseProvider):
    name = "Understat"
    description = "xG, xGA, xPoints, shot maps, advanced attacking/defensive metrics"

    def _url(self, league_code: str, season: str) -> str:
        return f"https://understat.com/league/{league_code}/{season}"

    def check_connection(self) -> bool:
        data = request_json("https://understat.com/league/EPL/2023",
                            provider=self.name, fallback=lambda: None)
        return data is not None

    def get_advanced_metrics(self, competition: Competition, season: Season) -> list[AdvancedMetric]:
        code = UNDERSTAT_LEAGUE.get(competition.name)
        if not code:
            return []
        year = season.start_year or int(season.name[:4])
        html = self._fetch_html(code, str(year))
        if not html:
            return []
        teams = self._extract_teams(html)
        out = []
        for t in teams:
            out.append(AdvancedMetric(
                team_name=t.get("title") or t.get("teamName"),
                season_name=season.name,
                xg=_to_float(t.get("xG")),
                xga=_to_float(t.get("xGA")),
                xpts=_to_float(t.get("xPTS")),
                npxg=_to_float(t.get("NPxG")),
                npxga=_to_float(t.get("NPxGA")),
                ppda=_to_float(t.get("PPDA")),
                deep=_to_float(t.get("Deep")),
                sca=_to_float(t.get("SCA")),
            ))
        return out

    def _fetch_html(self, league_code: str, season: str) -> Optional[str]:
        from ..http import get_session
        try:
            resp = get_session().get(self._url(league_code, season),
                                     headers={"User-Agent": "Mozilla/5.0"}, timeout=settings.http_timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            logger.warning("Understat fetch failed: %s", exc)
            return None

    def _extract_teams(self, html: str) -> list[dict]:
        """Understat embeds teams stats in a JSON payload inside <script>."""
        m = re.search(r"var teamsData\s*=\s*JSON\.parse\('(.*?)'\)", html, re.DOTALL)
        if not m:
            return []
        raw = m.group(1).replace("\\'", "'").replace('\\"', '"')
        try:
            return json.loads(raw.encode().decode("unicode_escape"))
        except Exception as exc:
            logger.warning("Understat teams parse failed: %s", exc)
            return []


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
