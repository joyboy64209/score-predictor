"""DataManager: the single unified entry point. The rest of the application
never talks to a provider directly - it asks the DataManager. The manager
orchestrates every provider, normalizes their output into the shared schema,
and synchronizes it into PostgreSQL with upsert/dedup logic. Provider
failures are isolated and logged; the manager degrades gracefully."""

import logging
from typing import Optional

from .config import settings
from .providers import (
    FootballDataProvider,
    ApiFootballProvider,
    StatsBombProvider,
    UnderstatProvider,
    KaggleProvider,
    ClubEloProvider,
)
from .schemas import (
    AdvancedMetric, Competition, EloRating, EventData, Fixture, Injury,
    Lineup, MatchStatistic, Odds, Player, PlayerStatistic, Season,
    StandingRow, Suspension, Team, Venue,
)
from . import db

logger = logging.getLogger("datamanager")


class DataManager:
    def __init__(self):
        self.football_data = FootballDataProvider()
        self.api_football = ApiFootballProvider()
        self.statsbomb = StatsBombProvider()
        self.understat = UnderstatProvider()
        self.kaggle = KaggleProvider()
        self.clubelo = ClubEloProvider()
        self.providers = [self.football_data, self.api_football,
                          self.statsbomb, self.understat, self.kaggle, self.clubelo]

    # ---------------- Health ----------------
    def provider_status(self) -> dict:
        status = {}
        for p in self.providers:
            try:
                status[p.name] = bool(p.check_connection())
            except Exception as exc:
                logger.error("%s health check error: %s", p.name, exc)
                status[p.name] = False
        return status

    # ---------------- Competitions / seasons / teams ----------------
    def sync_competitions(self):
        comps = self._safe(self.football_data.get_competitions)
        rows = [{"id": f"L:{c.code or c.name}", "name": c.name,
                 "country": c.country, "externalId": c.external_id} for c in comps]
        with db.connection() as conn:
            return db.upsert(conn, db.league_tbl, rows, ["id"])

    def sync_seasons(self, competition: Competition):
        seasons = self._safe(lambda: self.football_data.get_seasons(competition))
        rows = []
        for s in seasons:
            rows.append({"id": f"S:{competition.name}:{s.name}",
                         "leagueId": f"L:{competition.code or competition.name}",
                         "name": s.name})
        with db.connection() as conn:
            return db.upsert(conn, db.season_tbl, rows, ["id"])

    def sync_teams(self, competition: Competition, season: Season):
        teams = self._safe(lambda: self.football_data.get_teams(competition, season))
        rows = [{"id": f"T:{t.external_id or t.name}", "name": t.name,
                 "shortName": t.short_name, "externalId": t.external_id} for t in teams]
        with db.connection() as conn:
            return db.upsert(conn, db.team_tbl, rows, ["id"])

    # ---------------- Fixtures ----------------
    def sync_fixtures(self, competition: Competition, season: Season):
        fixtures = self._safe(lambda: self.football_data.get_fixtures(competition, season))
        rows = []
        for f in fixtures:
            rows.append({
                "id": f"F:{f.external_id}",
                "leagueId": f"L:{competition.code or competition.name}",
                "seasonId": f"S:{competition.name}:{season.name}",
                "homeTeamId": f"T:{f.home_team}",
                "awayTeamId": f"T:{f.away_team}",
                "matchday": f.matchday,
                "kickoff": f.kickoff,
                "status": f.status,
                "homeScore": f.home_score,
                "awayScore": f.away_score,
                "externalId": f.external_id,
            })
        with db.connection() as conn:
            return db.upsert(conn, db.fixture_tbl, rows, ["id"])

    # ---------------- Standings ----------------
    def sync_standings(self, competition: Competition, season: Season):
        rows_db = self._safe(lambda: self.football_data.get_standings(competition, season))
        rows = [{"id": f"ST:{competition.name}:{season.name}:{r.team_name}",
                 "competition": competition.name, "season": season.name,
                 "teamName": r.team_name, "position": r.position,
                 "played": r.played, "wins": r.wins, "draws": r.draws,
                 "losses": r.losses, "goalsFor": r.goals_for,
                 "goalsAgainst": r.goals_against, "points": r.points}
                for r in rows_db]
        with db.connection() as conn:
            return db.upsert(conn, db.standing_tbl, rows, ["id"])

    # ---------------- Advanced metrics (Understat) ----------------
    def sync_advanced_metrics(self, competition: Competition, season: Season):
        metrics = self._safe(lambda: self.understat.get_advanced_metrics(competition, season))
        rows = [{"id": f"AM:{competition.name}:{season.name}:{m.team_name}",
                 "teamName": m.team_name, "season": season.name,
                 "xg": m.xg, "xga": m.xga, "xpts": m.xpts,
                 "npxg": m.npxg, "npxga": m.npxga,
                 "ppda": m.ppda, "deep": m.deep, "sca": m.sca}
                for m in metrics]
        with db.connection() as conn:
            return db.upsert(conn, db.advanced_metric_tbl, rows, ["id"])

    # ---------------- Injuries / suspensions / lineups (API-Football) ----------------
    def sync_injuries(self, team: Team):
        items = self._safe(lambda: self.api_football.get_injuries(team))
        rows = [{"id": f"INJ:{team.name}:{i.player_name}",
                 "teamName": team.name, "playerName": i.player_name,
                 "reason": i.reason, "type": i.type, "until": i.until} for i in items]
        with db.connection() as conn:
            return db.upsert(conn, db.injury_tbl, rows, ["id"])

    def sync_suspensions(self, team: Team):
        items = self._safe(lambda: self.api_football.get_suspensions(team))
        rows = [{"id": f"SUS:{team.name}:{s.player_name}",
                 "teamName": team.name, "playerName": s.player_name,
                 "reason": s.reason, "until": s.until} for s in items]
        with db.connection() as conn:
            return db.upsert(conn, db.suspension_tbl, rows, ["id"])

    def sync_lineups(self, fixture: Fixture):
        items = self._safe(lambda: self.api_football.get_lineups(fixture))
        rows = [{"id": f"LU:{fixture.external_id}:{l.team_name}",
                 "fixtureId": f"F:{fixture.external_id}",
                 "teamName": l.team_name, "formation": l.formation,
                 "starting": l.starting_players, "substitutes": l.substitute_players}
                for l in items]
        with db.connection() as conn:
            return db.upsert(conn, db.lineup_tbl, rows, ["id"])

    # ---------------- Event data (StatsBomb) ----------------
    def sync_events(self, fixture: Fixture, limit: int = 10000):
        events = self._safe(lambda: self.statsbomb.get_event_data(fixture))
        rows = []
        for e in events[:limit]:
            rows.append({
                "id": f"EV:{fixture.external_id}:{e.minute}:{e.event_type}:{e.player_name}",
                "fixtureId": f"F:{fixture.external_id}",
                "eventType": e.event_type, "teamName": e.team_name,
                "playerName": e.player_name, "minute": e.minute,
                "x": e.x, "y": e.y, "endX": e.end_x, "endY": e.end_y, "extra": e.extra,
            })
        with db.connection() as conn:
            return db.upsert(conn, db.event_tbl, rows, ["id"])

    # ---------------- ClubElo ----------------
    def sync_elo(self):
        ratings = self._safe(self.clubelo.get_elo_ratings)
        rows = [{"id": f"ELO:{r.team_name}:{r.date or 'current'}",
                 "teamName": r.team_name, "rating": r.rating,
                 "rank": r.rank, "date": r.date, "country": r.country}
                for r in ratings]
        with db.connection() as conn:
            return db.upsert(conn, db.elo_tbl, rows, ["id"])

    # ---------------- Kaggle historical import ----------------
    def import_historical(self, competitions: Optional[list] = None) -> list[Fixture]:
        """Download + validate + return historical fixtures (no DB write here;
        persistence is done by the feature store / training pipeline)."""
        fixtures = self._safe(lambda: self.kaggle.get_historical_fixtures(competitions))
        logger.info("Kaggle historical import produced %d fixtures", len(fixtures))
        return fixtures

    # ---------------- Generic helpers ----------------
    @staticmethod
    def _safe(fn):
        try:
            return fn() or []
        except Exception as exc:
            logger.error("provider call failed: %s", exc)
            return []


data_manager = DataManager()
