"""Unified internal schema. Every provider normalizes into these
dataclasses so the rest of the application has a single, stable contract."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Competition:
    name: str
    code: Optional[str] = None
    country: Optional[str] = None
    external_id: Optional[str] = None


@dataclass
class Season:
    competition_name: str
    name: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    external_id: Optional[str] = None


@dataclass
class Team:
    name: str
    short_name: Optional[str] = None
    external_id: Optional[str] = None


@dataclass
class Player:
    name: str
    team_name: Optional[str] = None
    external_id: Optional[str] = None
    position: Optional[str] = None


@dataclass
class Venue:
    name: str
    city: Optional[str] = None
    external_id: Optional[str] = None


@dataclass
class Fixture:
    external_id: str
    competition_name: str
    season_name: str
    home_team: str
    away_team: str
    kickoff: datetime
    status: str = "SCHEDULED"
    matchday: Optional[int] = None
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    round: Optional[str] = None


@dataclass
class StandingRow:
    competition_name: str
    season_name: str
    team_name: str
    position: int
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0


@dataclass
class MatchStatistic:
    external_fixture_id: str
    home_team: str
    away_team: str
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_passes: Optional[int] = None
    away_passes: Optional[int] = None
    home_pass_accuracy: Optional[float] = None
    away_pass_accuracy: Optional[float] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_yellow: Optional[int] = None
    away_yellow: Optional[int] = None
    home_red: Optional[int] = None
    away_red: Optional[int] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_xga: Optional[float] = None
    away_xga: Optional[float] = None


@dataclass
class PlayerStatistic:
    external_fixture_id: str
    player_name: str
    team_name: str
    minutes: Optional[int] = None
    goals: int = 0
    assists: int = 0
    rating: Optional[float] = None


@dataclass
class TeamStatistic:
    external_fixture_id: str
    team_name: str
    external_id: Optional[str] = None


@dataclass
class Injury:
    team_name: str
    player_name: str
    reason: Optional[str] = None
    type: Optional[str] = None
    until: Optional[str] = None


@dataclass
class Suspension:
    team_name: str
    player_name: str
    reason: Optional[str] = None
    until: Optional[str] = None


@dataclass
class Lineup:
    external_fixture_id: str
    team_name: str
    formation: Optional[str] = None
    starting_players: list = field(default_factory=list)
    substitute_players: list = field(default_factory=list)


@dataclass
class AdvancedMetric:
    """Understat / xG style advanced team metrics for a season."""
    team_name: str
    season_name: str
    xg: Optional[float] = None
    xga: Optional[float] = None
    xpts: Optional[float] = None
    npxg: Optional[float] = None
    npxga: Optional[float] = None
    ppda: Optional[float] = None
    deep: Optional[float] = None
    sca: Optional[float] = None


@dataclass
class EventData:
    """StatsBomb event-level record (shot, pass, defensive action, ...)."""
    external_fixture_id: str
    event_type: str
    team_name: str
    player_name: Optional[str] = None
    minute: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    end_x: Optional[float] = None
    end_y: Optional[float] = None
    extra: dict = field(default_factory=dict)


@dataclass
class Odds:
    external_fixture_id: str
    bookmaker: Optional[str] = None
    home: Optional[float] = None
    draw: Optional[float] = None
    away: Optional[float] = None


@dataclass
class EloRating:
    team_name: str
    rating: float
    rank: Optional[int] = None
    date: Optional[str] = None
    country: Optional[str] = None
