"""Feature store. Computes a rich, configurable set of features from
normalized match data (fixtures + results + standings + advanced metrics +
Elo). Designed so new features are added by registering a FeatureCalculator;
nothing else needs to change. Missing values are handled gracefully."""

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd

from .schemas import Fixture


@dataclass
class FeatureCalculator:
    name: str
    description: str
    fn: Callable[["MatchContext"], Optional[float]]


@dataclass
class MatchContext:
    """All inputs a feature calculator may use for one fixture."""
    row: dict
    home_last: pd.DataFrame = field(default_factory=pd.DataFrame)
    away_last: pd.DataFrame = field(default_factory=pd.DataFrame)
    home_standing: Optional[dict] = None
    away_standing: Optional[dict] = None
    home_advanced: Optional[dict] = None
    away_advanced: Optional[dict] = None
    home_elo: Optional[float] = None
    away_elo: Optional[float] = None
    home_injuries: int = 0
    away_injuries: int = 0
    home_suspensions: int = 0
    away_suspensions: int = 0


class FeatureStore:
    def __init__(self):
        self.calculators: list[FeatureCalculator] = []
        self._register_defaults()

    # ---------- registration ----------
    def register(self, calc: FeatureCalculator):
        self.calculators.append(calc)

    def _register_defaults(self):
        C = FeatureCalculator
        self.register(C("home_advantage", "Home advantage proxy", lambda c: 1.0))
        self.register(C("away_advantage", "Away advantage proxy", lambda c: 0.0))
        self.register(C("recent_form_home", "Home recent form (pts/3)", _recent_form("home")))
        self.register(C("recent_form_away", "Away recent form (pts/3)", _recent_form("away")))
        self.register(C("last5_win_pct_home", "Home win% last 5", _win_pct("home", 5)))
        self.register(C("last10_win_pct_home", "Home win% last 10", _win_pct("home", 10)))
        self.register(C("last5_win_pct_away", "Away win% last 5", _win_pct("away", 5)))
        self.register(C("last10_win_pct_away", "Away win% last 10", _win_pct("away", 10)))
        self.register(C("goals_scored_home", "Home avg goals scored", _avg("home", "home_score")))
        self.register(C("goals_scored_away", "Away avg goals scored", _avg("away", "away_score")))
        self.register(C("goals_conceded_home", "Home avg goals conceded", _avg("home", "away_score")))
        self.register(C("goals_conceded_away", "Away avg goals conceded", _avg("away", "home_score")))
        self.register(C("goal_diff_home", "Home goal difference", _goal_diff("home")))
        self.register(C("goal_diff_away", "Away goal difference", _goal_diff("away")))
        self.register(C("xg_home", "Home xG (advanced)", lambda c: _g(c.home_advanced, "xg")))
        self.register(C("xg_away", "Away xG (advanced)", lambda c: _g(c.away_advanced, "xga")))
        self.register(C("xga_home", "Home xGA", lambda c: _g(c.home_advanced, "xga")))
        self.register(C("xga_away", "Away xGA", lambda c: _g(c.away_advanced, "xg")))
        self.register(C("shots_home", "Home shots", lambda c: _g(c.row, "home_shots")))
        self.register(C("shots_away", "Away shots", lambda c: _g(c.row, "away_shots")))
        self.register(C("shots_on_target_home", "Home SOT", lambda c: _g(c.row, "home_shots_on_target")))
        self.register(C("shots_on_target_away", "Away SOT", lambda c: _g(c.row, "away_shots_on_target")))
        self.register(C("possession_home", "Home possession", lambda c: _g(c.row, "home_possession")))
        self.register(C("possession_away", "Away possession", lambda c: _g(c.row, "away_possession")))
        self.register(C("pass_accuracy_home", "Home pass accuracy", lambda c: _g(c.row, "home_pass_accuracy")))
        self.register(C("pass_accuracy_away", "Away pass accuracy", lambda c: _g(c.row, "away_pass_accuracy")))
        self.register(C("corners_home", "Home corners", lambda c: _g(c.row, "home_corners")))
        self.register(C("corners_away", "Away corners", lambda c: _g(c.row, "away_corners")))
        self.register(C("yellow_cards_home", "Home yellow cards", lambda c: _g(c.row, "home_yellow")))
        self.register(C("yellow_cards_away", "Away yellow cards", lambda c: _g(c.row, "away_yellow")))
        self.register(C("red_cards_home", "Home red cards", lambda c: _g(c.row, "home_red")))
        self.register(C("red_cards_away", "Away red cards", lambda c: _g(c.row, "away_red")))
        self.register(C("elo_home", "Home Elo", lambda c: c.home_elo))
        self.register(C("elo_away", "Away Elo", lambda c: c.away_elo))
        self.register(C("elo_diff", "Elo difference (home-away)", lambda c: _safe_sub(c.home_elo, c.away_elo)))
        self.register(C("league_position_home", "Home league position", lambda c: _g(c.home_standing, "position")))
        self.register(C("league_position_away", "Away league position", lambda c: _g(c.away_standing, "position")))
        self.register(C("rest_days_home", "Home rest days", lambda c: _g(c.row, "rest_days_home")))
        self.register(C("rest_days_away", "Away rest days", lambda c: _g(c.row, "rest_days_away")))
        self.register(C("h2h_win_pct_home", "Head-to-head win% for home", _h2h))
        self.register(C("injury_score_home", "Home injury score", lambda c: float(c.home_injuries)))
        self.register(C("injury_score_away", "Away injury score", lambda c: float(c.away_injuries)))
        self.register(C("suspension_score_home", "Home suspension score", lambda c: float(c.home_suspensions)))
        self.register(C("suspension_score_away", "Away suspension score", lambda c: float(c.away_suspensions)))
        self.register(C("attack_rating_home", "Home attack rating (xG-based)", _attack("home")))
        self.register(C("attack_rating_away", "Away attack rating", _attack("away")))
        self.register(C("defense_rating_home", "Home defense rating (xGA-based)", _defense("home")))
        self.register(C("defense_rating_away", "Away defense rating", _defense("away")))
        self.register(C("momentum_home", "Home momentum (last5 - last10 form)", _momentum("home")))
        self.register(C("momentum_away", "Away momentum", _momentum("away")))
        self.register(C("btts_pct_home", "Home BTTS % (last 10)", _btts("home")))
        self.register(C("over25_pct_home", "Home over2.5 % (last 10)", _over("home", 2.5)))
        self.register(C("clean_sheet_pct_home", "Home clean sheet %", _clean("home")))

    # ---------- computation ----------
    def feature_names(self) -> list[str]:
        return [c.name for c in self.calculators]

    def compute(self, ctx: MatchContext) -> dict:
        out = {}
        for calc in self.calculators:
            try:
                val = calc.fn(ctx)
            except Exception:
                val = None
            out[calc.name] = _fill(val)
        return out

    def compute_batch(self, contexts: list[MatchContext]) -> pd.DataFrame:
        rows = [self.compute(c) for c in contexts]
        df = pd.DataFrame(rows)
        return df.fillna(df.mean(numeric_only=True)).fillna(0.0)


# --------------------- helpers ---------------------
def _fill(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    return float(v)


def _g(d, key):
    if isinstance(d, dict):
        return d.get(key)
    if d is None:
        return None
    return getattr(d, key, None)


def _recent_form(side):
    def fn(c: MatchContext):
        df = c.home_last if side == "home" else c.away_last
        if df is None or len(df) == 0:
            return 0.5
        pts = ((df["result"] == "W").astype(int) * 3 +
               (df["result"] == "D").astype(int)).sum()
        return float(pts) / (3 * len(df))
    return fn


def _win_pct(side, n):
    def fn(c: MatchContext):
        df = (c.home_last if side == "home" else c.away_last).head(n)
        if df is None or len(df) == 0:
            return 0.5
        return float((df["result"] == "W").mean())
    return fn


def _avg(side, col):
    def fn(c: MatchContext):
        df = c.home_last if side == "home" else c.away_last
        if df is None or len(df) == 0 or col not in df:
            return None
        return float(df[col].mean())
    return fn


def _goal_diff(side):
    def fn(c: MatchContext):
        gs = _avg(side, "home_score" if side == "home" else "away_score")(c)
        gc = _avg(side, "away_score" if side == "home" else "home_score")(c)
        if gs is None or gc is None:
            return None
        return gs - gc
    return fn


def _safe_sub(a, b):
    if a is None or b is None:
        return None
    return a - b


def _h2h(c: MatchContext):
    # requires precomputed h2h on context.row
    return _g(c.row, "h2h_win_pct_home")


def _attack(side):
    def fn(c: MatchContext):
        adv = c.home_advanced if side == "home" else c.away_advanced
        return _g(adv, "xg")
    return fn


def _defense(side):
    def fn(c: MatchContext):
        adv = c.home_advanced if side == "home" else c.away_advanced
        return _g(adv, "xga")
    return fn


def _momentum(side):
    def fn(c: MatchContext):
        a = _win_pct(side, 5)(c)
        b = _win_pct(side, 10)(c)
        if a is None or b is None:
            return 0.0
        return a - b
    return fn


def _btts(side):
    def fn(c: MatchContext):
        df = (c.home_last if side == "home" else c.away_last).head(10)
        if df is None or len(df) == 0 or "btts" not in df:
            return 0.5
        return float(df["btts"].mean())
    return fn


def _over(side, line):
    def fn(c: MatchContext):
        df = (c.home_last if side == "home" else c.away_last).head(10)
        if df is None or len(df) == 0 or "total_goals" not in df:
            return 0.5
        return float((df["total_goals"] > line).mean())
    return fn


def _clean(side):
    def fn(c: MatchContext):
        df = (c.home_last if side == "home" else c.away_last).head(10)
        if df is None or len(df) == 0:
            return 0.5
        col = "away_score" if side == "home" else "home_score"
        if col not in df:
            return 0.5
        return float((df[col] == 0).mean())
    return fn
