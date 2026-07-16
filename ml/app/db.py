"""Database access layer (PostgreSQL via SQLAlchemy). Provides a connection
engine, upsert helpers and simple queries used by the DataManager, feature
store and training pipeline. Mirrors the Prisma schema and extends it with
new normalized entities (players, venues, stats, events, standings, elo)."""

from contextlib import contextmanager
from typing import Iterable, Optional

from sqlalchemy import (
    create_engine, Engine, text, MetaData, Table, Column, String, Integer,
    Float, DateTime, Boolean, JSON, UniqueConstraint, BigInteger,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .config import settings


def make_engine(url: Optional[str] = None) -> Engine:
    return create_engine(url or settings.database_url, future=True, pool_pre_ping=True)


engine = make_engine()


metadata = MetaData()

# --- Core (mirrors Prisma) ---
league_tbl = Table("League", metadata, Column("id", String, primary_key=True),
                   Column("name", String), Column("country", String), Column("externalId", String))
season_tbl = Table("Season", metadata, Column("id", String, primary_key=True),
                   Column("leagueId", String), Column("name", String),
                   Column("startDate", DateTime), Column("endDate", DateTime))
team_tbl = Table("Team", metadata, Column("id", String, primary_key=True),
                 Column("name", String), Column("shortName", String), Column("externalId", String))
fixture_tbl = Table("Fixture", metadata,
                    Column("id", String, primary_key=True),
                    Column("leagueId", String), Column("seasonId", String),
                    Column("homeTeamId", String), Column("awayTeamId", String),
                    Column("matchday", Integer), Column("kickoff", DateTime),
                    Column("status", String), Column("homeScore", Integer),
                    Column("awayScore", Integer), Column("externalId", String))
team_season_stat_tbl = Table("TeamSeasonStat", metadata,
                             Column("id", String, primary_key=True),
                             Column("teamId", String), Column("seasonId", String),
                             Column("played", Integer), Column("wins", Integer),
                             Column("draws", Integer), Column("losses", Integer),
                             Column("goalsFor", Integer), Column("goalsAgainst", Integer))

# --- New normalized entities ---
player_tbl = Table("Player", metadata, Column("id", String, primary_key=True),
                   Column("name", String), Column("teamId", String), Column("externalId", String),
                   Column("position", String))
venue_tbl = Table("Venue", metadata, Column("id", String, primary_key=True),
                  Column("name", String), Column("city", String), Column("externalId", String))
match_stat_tbl = Table("MatchStatistic", metadata,
                       Column("id", String, primary_key=True),
                       Column("fixtureId", String), Column("homeShots", Integer),
                       Column("awayShots", Integer), Column("homeShotsOnTarget", Integer),
                       Column("awayShotsOnTarget", Integer), Column("homePossession", Float),
                       Column("awayPossession", Float), Column("homePassAccuracy", Float),
                       Column("awayPassAccuracy", Float), Column("homeCorners", Integer),
                       Column("awayCorners", Integer), Column("homeYellow", Integer),
                       Column("awayYellow", Integer), Column("homeRed", Integer),
                       Column("awayRed", Integer), Column("homeXg", Float), Column("awayXg", Float),
                       Column("homeXga", Float), Column("awayXga", Float))
player_stat_tbl = Table("PlayerStatistic", metadata,
                        Column("id", String, primary_key=True),
                        Column("fixtureId", String), Column("playerName", String),
                        Column("teamName", String), Column("minutes", Integer),
                        Column("goals", Integer), Column("assists", Integer), Column("rating", Float))
standing_tbl = Table("Standing", metadata,
                    Column("id", String, primary_key=True), Column("competition", String),
                    Column("season", String), Column("teamName", String),
                    Column("position", Integer), Column("played", Integer),
                    Column("wins", Integer), Column("draws", Integer), Column("losses", Integer),
                    Column("goalsFor", Integer), Column("goalsAgainst", Integer),
                    Column("points", Integer))
advanced_metric_tbl = Table("AdvancedMetric", metadata,
                            Column("id", String, primary_key=True), Column("teamName", String),
                            Column("season", String), Column("xg", Float), Column("xga", Float),
                            Column("xpts", Float), Column("npxg", Float), Column("npxga", Float),
                            Column("ppda", Float), Column("deep", Float), Column("sca", Float))
injury_tbl = Table("Injury", metadata, Column("id", String, primary_key=True),
                   Column("teamName", String), Column("playerName", String),
                   Column("reason", String), Column("type", String), Column("until", String))
suspension_tbl = Table("Suspension", metadata, Column("id", String, primary_key=True),
                       Column("teamName", String), Column("playerName", String),
                       Column("reason", String), Column("until", String))
lineup_tbl = Table("Lineup", metadata, Column("id", String, primary_key=True),
                   Column("fixtureId", String), Column("teamName", String),
                   Column("formation", String), Column("starting", JSON), Column("substitutes", JSON))
event_tbl = Table("EventData", metadata, Column("id", String, primary_key=True),
                  Column("fixtureId", String), Column("eventType", String),
                  Column("teamName", String), Column("playerName", String),
                  Column("minute", Integer), Column("x", Float), Column("y", Float),
                  Column("endX", Float), Column("endY", Float), Column("extra", JSON))
elo_tbl = Table("EloRating", metadata, Column("id", String, primary_key=True),
                Column("teamName", String), Column("rating", Float), Column("rank", Integer),
                Column("date", String), Column("country", String))
odds_tbl = Table("Odds", metadata, Column("id", String, primary_key=True),
                 Column("fixtureId", String), Column("bookmaker", String),
                 Column("home", Float), Column("draw", Float), Column("away", Float))
feature_tbl = Table("FeatureRow", metadata, Column("id", String, primary_key=True),
                    Column("fixtureId", String), Column("features", JSON), Column("label", Integer),
                    Column("datasetVersion", String), Column("createdAt", DateTime))
model_version_tbl = Table("ModelVersion", metadata,
                          Column("id", String, primary_key=True), Column("name", String),
                          Column("algorithm", String), Column("metrics", JSON),
                          Column("trainedAt", DateTime), Column("isActive", Boolean))
prediction_tbl = Table("Prediction", metadata,
                       Column("id", String, primary_key=True), Column("fixtureId", String),
                       Column("market", String), Column("selection", String),
                       Column("probability", Float), Column("confidence", Float),
                       Column("expectedValue", Float), Column("status", String),
                       Column("reasons", JSON), Column("modelVersion", String),
                       Column("createdAt", DateTime))


@contextmanager
def connection():
    with engine.begin() as conn:
        yield conn


def upsert(conn, table: Table, rows: Iterable[dict], conflict_cols: list[str]):
    """Insert rows, updating on conflict. Skips empty."""
    rows = [r for r in rows if r]
    if not rows:
        return 0
    stmt = pg_insert(table).values(rows)
    update_cols = {c.name: stmt.excluded[c.name] for c in table.columns
                   if c.name not in conflict_cols and c.name != "id"}
    if update_cols:
        stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
    conn.execute(stmt)
    return len(rows)


def init_db():
    """Idempotently create all tables. Mirrors Prisma models + new entities.
    Safe to call at startup; only creates what is missing."""
    metadata.create_all(engine)
    with connection() as conn:
        # ensure the Config singleton row exists for thresholds
        conn.execute(text(
            "INSERT INTO \"Config\" (id, thresholds) VALUES ('singleton', "
            "'{\"MATCH_RESULT\":70,\"DOUBLE_CHANCE\":90,\"OTHER\":80,\"COMBINATION\":80}') "
            "ON CONFLICT (id) DO NOTHING"
        ))


def fetch_one(query: str, params: Optional[dict] = None):
    with connection() as conn:
        return conn.execute(text(query), params or {}).mappings().first()


def fetch_all(query: str, params: Optional[dict] = None):
    with connection() as conn:
        return conn.execute(text(query), params or {}).mappings().all()


class DbDataProvider:
    """Reads normalized fixtures/team stats from Postgres for the prediction
    feature path (serving). Returns normalized Fixture + team form summary."""

    def __init__(self, database_url: Optional[str] = None):
        self.engine = make_engine(database_url) if database_url else engine

    def get_fixture(self, fixture_id: str):
        from .schemas import Fixture
        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT * FROM "Fixture" WHERE id = :id'),
                               {"id": fixture_id}).mappings().first()
            if not row:
                return None
            return Fixture(
                external_id=row["externalId"] or row["id"],
                competition_name="",
                season_name="",
                home_team=row["homeTeamId"],
                away_team=row["awayTeamId"],
                kickoff=row["kickoff"],
                status=row.get("status", "SCHEDULED"),
                matchday=row.get("matchday"),
                home_score=row.get("homeScore"),
                away_score=row.get("awayScore"),
            )

    def get_team_stats(self, team_id: str):
        with self.engine.connect() as conn:
            row = conn.execute(
                text('SELECT * FROM "TeamSeasonStat" WHERE "teamId" = :t ORDER BY "seasonId" DESC LIMIT 1'),
                {"t": team_id}).mappings().first()
        if not row:
            return {"played": 0, "wins": 0, "draws": 0, "losses": 0,
                    "goalsFor": 0, "goalsAgainst": 0}
        return dict(row)


def fetch_all(query: str, params: Optional[dict] = None):
    with connection() as conn:
        return conn.execute(text(query), params or {}).mappings().all()
