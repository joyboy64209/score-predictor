"""Base class for all data providers. Concrete providers implement the
normalized fetch methods they support; unsupported methods return empty
lists / None. The DataManager is the only consumer."""

from abc import ABC
from typing import Optional

from ..schemas import (
    AdvancedMetric, Competition, EloRating, EventData, Fixture, Injury,
    Lineup, MatchStatistic, Odds, Player, PlayerStatistic, Season,
    StandingRow, Suspension, Team, Venue,
)


class BaseProvider(ABC):
    name: str = "base"
    description: str = ""

    # --- Connection / health ---
    def check_connection(self) -> bool:
        """Return True if the provider is reachable / configured."""
        return True

    # --- Competitions / seasons / teams ---
    def get_competitions(self) -> list[Competition]:
        return []

    def get_seasons(self, competition: Competition) -> list[Season]:
        return []

    def get_teams(self, competition: Competition, season: Season) -> list[Team]:
        return []

    def get_venues(self, competition: Competition, season: Season) -> list[Venue]:
        return []

    # --- Fixtures / results ---
    def get_fixtures(self, competition: Competition, season: Season) -> list[Fixture]:
        return []

    # --- Standings ---
    def get_standings(self, competition: Competition, season: Season) -> list[StandingRow]:
        return []

    # --- Statistics ---
    def get_match_statistics(self, fixture: Fixture) -> Optional[MatchStatistic]:
        return None

    def get_player_statistics(self, fixture: Fixture) -> list[PlayerStatistic]:
        return []

    def get_advanced_metrics(self, competition: Competition, season: Season) -> list[AdvancedMetric]:
        return []

    # --- Injuries / suspensions / lineups ---
    def get_injuries(self, team: Team) -> list[Injury]:
        return []

    def get_suspensions(self, team: Team) -> list[Suspension]:
        return []

    def get_lineups(self, fixture: Fixture) -> list[Lineup]:
        return []

    # --- Odds ---
    def get_odds(self, fixture: Fixture) -> list[Odds]:
        return []

    # --- Event data (StatsBomb) ---
    def get_event_data(self, fixture: Fixture) -> list[EventData]:
        return []

    # --- Elo (ClubElo) ---
    def get_elo_ratings(self) -> list[EloRating]:
        return []

    # --- Bulk historical import (Kaggle) ---
    def get_historical_fixtures(self) -> list[Fixture]:
        return []
