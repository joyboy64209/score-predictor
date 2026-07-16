"""Provider abstraction: the rest of the system depends only on this
interface, so data can come from any football API or a CSV file without
changing business logic."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FixtureData:
    fixture_id: str
    home_team_id: str
    away_team_id: str
    matchday: Optional[int]
    home_form: float = 0.5
    away_form: float = 0.5
    home_xg: float = 1.4
    away_xg: float = 1.2
    home_clean_sheet: float = 0.35
    away_clean_sheet: float = 0.3
    btts: float = 0.55
    over_lines: dict = field(default_factory=dict)


@dataclass
class TeamStat:
    team_id: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0


class DataProvider(ABC):
    @abstractmethod
    def get_fixture(self, fixture_id: str) -> FixtureData:
        ...

    @abstractmethod
    def get_team_stats(self, team_id: str) -> TeamStat:
        ...

    @abstractmethod
    def list_fixtures(self) -> list[FixtureData]:
        ...


class CsvDataProvider(DataProvider):
    """Reads fixtures/team stats from CSV files. Path configurable."""

    def __init__(self, fixtures_csv: str, stats_csv: str):
        import pandas as pd
        self.fx = pd.read_csv(fixtures_csv)
        self.stats = pd.read_csv(stats_csv)

    def get_fixture(self, fixture_id: str) -> FixtureData:
        row = self.fx[self.fx["fixture_id"] == fixture_id].iloc[0]
        return self._row_to_fixture(row)

    def get_team_stats(self, team_id: str) -> TeamStat:
        row = self.stats[self.stats["team_id"] == team_id].iloc[0]
        return TeamStat(**row.to_dict())

    def list_fixtures(self) -> list[FixtureData]:
        return [self._row_to_fixture(r) for _, r in self.fx.iterrows()]

    def _row_to_fixture(self, row) -> FixtureData:
        return FixtureData(
            fixture_id=str(row["fixture_id"]),
            home_team_id=str(row["home_team_id"]),
            away_team_id=str(row["away_team_id"]),
            matchday=int(row["matchday"]) if "matchday" in row else None,
            home_form=float(row.get("home_form", 0.5)),
            away_form=float(row.get("away_form", 0.5)),
        )


class DbDataProvider(DataProvider):
    """Fallback provider that queries the Postgres DB directly."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        from sqlalchemy import create_engine, text
        engine = create_engine(self.database_url)
        return engine

    def get_fixture(self, fixture_id: str) -> FixtureData:
        engine = self._connect()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM \"Fixture\" WHERE id = :id"),
                {"id": fixture_id},
            ).mappings().first()
            stats = conn.execute(
                text("SELECT * FROM \"TeamSeasonStat\" WHERE \"teamId\" = :t"),
                {"t": row["homeTeamId"]},
            ).mappings().first()
        base = 1.4 if stats and stats["played"] else 1.0
        return FixtureData(
            fixture_id=fixture_id,
            home_team_id=row["homeTeamId"],
            away_team_id=row["awayTeamId"],
            matchday=row["matchday"],
            home_form=base,
            away_form=base * 0.9,
            home_xg=base,
            away_xg=base * 0.9,
            home_clean_sheet=0.35,
            away_clean_sheet=0.3,
            btts=0.55,
        )

    def get_team_stats(self, team_id: str) -> TeamStat:
        engine = self._connect()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM \"TeamSeasonStat\" WHERE \"teamId\" = :t"),
                {"t": team_id},
            ).mappings().first()
        return TeamStat(team_id=team_id, **(dict(row) if row else {}))

    def list_fixtures(self) -> list[FixtureData]:
        engine = self._connect()
        out = []
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id FROM \"Fixture\" LIMIT 100")).mappings().all()
        for r in rows:
            out.append(self.get_fixture(r["id"]))
        return out
