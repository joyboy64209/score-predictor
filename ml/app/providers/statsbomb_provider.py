"""StatsBomb Open Data provider. Reads historical event data (shots, passes,
defensive actions) via the `statsbombpy` package when installed, and also
supports parsing the Kaggle StatsBomb dataset export directory."""

import json
import logging
import os
from typing import Optional

from .base_provider import BaseProvider
from ..schemas import Competition, EventData, Fixture, Season, Team
from ..config import settings

logger = logging.getLogger("provider.statsbomb")


class StatsBombProvider(BaseProvider):
    name = "StatsBomb Open Data"
    description = "Historical event data, xG, passes, shots, defensive actions"

    def __init__(self, kaggle_dir: Optional[str] = None):
        self.kaggle_dir = kaggle_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "datasets", "kaggle", "ChampionsLeague",
        )

    def check_connection(self) -> bool:
        try:
            import statsbombpy  # noqa: F401
            return True
        except Exception:
            # fall back to Kaggle export directory
            return os.path.isdir(self.kaggle_dir)

    def get_competitions(self) -> list[Competition]:
        try:
            from statsbombpy.api import competitions
            df = competitions()
            out = []
            for _, r in df.iterrows():
                out.append(Competition(
                    name=r.get("competition_name"),
                    code=r.get("competition_id"),
                    country=r.get("country_name"),
                    external_id=str(r.get("competition_id")),
                ))
            return out
        except Exception as exc:
            logger.warning("StatsBomb competitions unavailable: %s", exc)
            return []

    def get_seasons(self, competition: Competition) -> list[Season]:
        try:
            from statsbombpy.api import matches
            df = matches(competition_id=int(competition.external_id))
            seen = set()
            out = []
            for _, r in df.iterrows():
                sn = str(r.get("season_name"))
                if sn in seen:
                    continue
                seen.add(sn)
                out.append(Season(
                    competition_name=competition.name,
                    name=sn,
                    external_id=str(r.get("season_id")),
                ))
            return out
        except Exception as exc:
            logger.warning("StatsBomb seasons unavailable: %s", exc)
            return []

    def get_event_data(self, fixture: Fixture) -> list[EventData]:
        """Try live API first, then fall back to the Kaggle export dir."""
        events = self._events_from_api(fixture)
        if events:
            return events
        return self._events_from_kaggle(fixture)

    def _events_from_api(self, fixture: Fixture) -> list[EventData]:
        try:
            from statsbombpy.api import events
            df = events(match_id=int(fixture.external_id))
            out = []
            for _, r in df.iterrows():
                out.append(EventData(
                    external_fixture_id=fixture.external_id,
                    event_type=r.get("type", {}).get("name") if isinstance(r.get("type"), dict) else r.get("type"),
                    team_name=r.get("team", {}).get("name") if isinstance(r.get("team"), dict) else r.get("team"),
                    player_name=r.get("player", {}).get("name") if isinstance(r.get("player"), dict) else r.get("player"),
                    minute=r.get("minute"),
                    x=r.get("location", [None, None])[0] if r.get("location") else None,
                    y=r.get("location", [None, None])[1] if r.get("location") else None,
                    end_x=r.get("pass_end_location", [None, None])[0] if r.get("pass_end_location") else None,
                    end_y=r.get("pass_end_location", [None, None])[1] if r.get("pass_end_location") else None,
                    extra={"xg": (r.get("shot", {}) or {}).get("statsbomb_xg")},
                ))
            return out
        except Exception as exc:
            logger.debug("StatsBomb live events unavailable: %s", exc)
            return []

    def _events_from_kaggle(self, fixture: Fixture) -> list[EventData]:
        # Search recursively for an events JSON whose id matches the fixture
        if not os.path.isdir(self.kaggle_dir):
            return []
        target = fixture.external_id
        for root, _, files in os.walk(self.kaggle_dir):
            if "events.json" in files:
                try:
                    with open(os.path.join(root, "events.json"), encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue
                out = []
                matched = False
                for ev in data:
                    mid = str(ev.get("match_id"))
                    if mid == target:
                        matched = True
                    if not matched:
                        continue
                    loc = ev.get("location")
                    out.append(EventData(
                        external_fixture_id=mid,
                        event_type=_name(ev.get("type")),
                        team_name=_name(ev.get("team")),
                        player_name=_name(ev.get("player")),
                        minute=ev.get("minute"),
                        x=loc[0] if loc else None,
                        y=loc[1] if loc else None,
                        extra={"xg": (ev.get("shot") or {}).get("statsbomb_xg")},
                    ))
                if matched:
                    return out
        return []


def _name(obj):
    if isinstance(obj, dict):
        return obj.get("name")
    return obj
