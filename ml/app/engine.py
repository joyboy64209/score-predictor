"""Prediction engine: derives full market probabilities from a base
1X2 (home/draw/away) distribution plus team features, then qualifies
predictions against configurable confidence thresholds and ranks them."""

from dataclasses import dataclass, field
from typing import Optional

MARKET = "MARKET"
DOUBLE = "DOUBLE_CHANCE"
COMBO = "COMBINATION"
OTHER = "OTHER"


@dataclass
class Threshold:
    MATCH_RESULT: float = 70.0
    DOUBLE_CHANCE: float = 90.0
    OTHER: float = 80.0
    COMBINATION: float = 80.0


@dataclass
class Prediction:
    market: str
    selection: str
    probability: float
    confidence: float
    section: str
    expected_value: Optional[float] = None
    reasons: list = field(default_factory=list)
    status: str = "QUALIFIED"


COMBINATION_BETS = [
    ("HOME_WIN_AND_OVER_2_5", "HOME", "OVER_2_5"),
    ("HOME_WIN_AND_UNDER_4_5", "HOME", "UNDER_4_5"),
    ("AWAY_WIN_AND_OVER_2_5", "AWAY", "OVER_2_5"),
    ("DRAW_AND_UNDER_3_5", "DRAW", "UNDER_3_5"),
    ("1X_AND_OVER_2_5", "1X", "OVER_2_5"),
    ("1X_AND_UNDER_4_5", "1X", "UNDER_4_5"),
    ("X2_AND_OVER_2_5", "X2", "OVER_2_5"),
    ("X2_AND_UNDER_4_5", "X2", "UNDER_4_5"),
    ("12_AND_OVER_2_5", "12", "OVER_2_5"),
    ("HOME_WIN_AND_BTTS", "HOME", "BTTS_YES"),
    ("AWAY_WIN_AND_BTTS", "AWAY", "BTTS_YES"),
    ("HOME_WIN_TO_NIL", "HOME", "AWAY_CLEAN_SHEET_NO"),
    ("AWAY_WIN_TO_NIL", "AWAY", "HOME_CLEAN_SHEET_NO"),
    ("OVER_2_5_AND_BTTS", "OVER_2_5", "BTTS_YES"),
    ("UNDER_4_5_AND_BTTS", "UNDER_4_5", "BTTS_YES"),
    ("HOME_OVER_1_5_AND_HOME_WIN", "HOME_OVER_1_5", "HOME"),
    ("AWAY_OVER_1_5_AND_AWAY_WIN", "AWAY_OVER_1_5", "AWAY"),
]

OVER_UNDER_LINES = [0.5, 1.5, 2.5, 3.5, 4.5]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def sectionalise(market_type: str) -> str:
    if market_type in ("MATCH_RESULT",):
        return "matchResult"
    if market_type == "DOUBLE_CHANCE":
        return "doubleChance"
    if market_type == "COMBINATION":
        return "combination"
    return "other"


def derive_markets(
    home_p: float,
    draw_p: float,
    away_p: float,
    features: dict,
) -> list[Prediction]:
    """Expand base 1X2 into the full set of supported markets."""
    home_p, draw_p, away_p = _clamp01(home_p), _clamp01(draw_p), _clamp01(away_p)
    total = home_p + draw_p + away_p
    home_p, draw_p, away_p = home_p / total, draw_p / total, away_p / total

    btts = features.get("btts", 0.55)
    over_p = {line: features.get(f"over_{line}", 0.5) for line in OVER_UNDER_LINES}
    home_goals = features.get("home_xg", 1.4)
    away_goals = features.get("away_xg", 1.2)
    home_clean = features.get("home_clean_sheet", 0.35)
    away_clean = features.get("away_clean_sheet", 0.3)

    preds: list[Prediction] = []

    # Match result
    preds.append(Prediction("MATCH_RESULT", "HOME", home_p, home_p * 100, "matchResult",
                            reasons=_why("Home win", features)))
    preds.append(Prediction("MATCH_RESULT", "DRAW", draw_p, draw_p * 100, "matchResult",
                            reasons=_why("Draw", features)))
    preds.append(Prediction("MATCH_RESULT", "AWAY", away_p, away_p * 100, "matchResult",
                            reasons=_why("Away win", features)))

    # Double chance
    dc = {
        "1X": home_p + draw_p,
        "X2": draw_p + away_p,
        "12": home_p + away_p,
    }
    for sel, p in dc.items():
        preds.append(Prediction("DOUBLE_CHANCE", sel, p, p * 100, "doubleChance",
                                reasons=[f"Combined probability {p:.0%}"]))

    # BTTS
    preds.append(Prediction("BTTS", "YES", btts, btts * 100, "other", reasons=["Both sides scoring form"]))
    preds.append(Prediction("BTTS", "NO", 1 - btts, (1 - btts) * 100, "other"))

    # Over / Under
    for line in OVER_UNDER_LINES:
        p = over_p[line]
        preds.append(Prediction("OVER_UNDER", f"OVER_{line}", p, p * 100, "other",
                                reasons=[f"Line {line}"]))
        preds.append(Prediction("OVER_UNDER", f"UNDER_{line}", 1 - p, (1 - p) * 100, "other"))

    # Team goals (over 1.5)
    home_over = _clamp01(home_goals / 1.5 * 0.5 + 0.25)
    away_over = _clamp01(away_goals / 1.5 * 0.5 + 0.25)
    preds.append(Prediction("TEAM_GOALS", "HOME_OVER_1_5", home_over, home_over * 100, "other"))
    preds.append(Prediction("TEAM_GOALS", "AWAY_OVER_1_5", away_over, away_over * 100, "other"))

    # First team to score
    fts_home = home_p * 0.7 + 0.1
    preds.append(Prediction("FIRST_TEAM_TO_SCORE", "HOME", fts_home, fts_home * 100, "other"))
    preds.append(Prediction("FIRST_TEAM_TO_SCORE", "AWAY", 1 - fts_home, (1 - fts_home) * 100, "other"))

    # Clean sheets
    preds.append(Prediction("CLEAN_SHEET", "HOME_CLEAN_SHEET", home_clean, home_clean * 100, "other"))
    preds.append(Prediction("CLEAN_SHEET", "AWAY_CLEAN_SHEET", away_clean, away_clean * 100, "other"))

    # Draw no bet
    preds.append(Prediction("DRAW_NO_BET", "HOME", home_p, home_p * 100, "other"))
    preds.append(Prediction("DRAW_NO_BET", "AWAY", away_p, away_p * 100, "other"))

    # Exact score (simple poisson sampling of top scores)
    for h in range(0, 4):
        for a in range(0, 4):
            p = _poisson(home_goals, h) * _poisson(away_goals, a)
            preds.append(Prediction("EXACT_SCORE", f"{h}-{a}", p, p * 100, "other"))

    # Goal range
    for label, lo, hi in [("0-1", 0, 1), ("2-3", 2, 3), ("4+", 4, 99)]:
        p = sum(_poisson(home_goals, h) * _poisson(away_goals, a)
                for h in range(0, 10) for a in range(0, 10)
                if lo <= h + a <= hi)
        preds.append(Prediction("GOAL_RANGE", label, p, p * 100, "other"))

    # Half winners (heuristic split of full-time probabilities)
    preds.append(Prediction("HALF_WINNER", "HOME", home_p * 0.95, home_p * 95, "other"))
    preds.append(Prediction("HALF_WINNER", "DRAW", draw_p * 1.1, draw_p * 110, "other"))
    preds.append(Prediction("HALF_WINNER", "AWAY", away_p * 0.95, away_p * 95, "other"))

    return preds


def derive_combinations(predictions: list[Prediction]) -> list[Prediction]:
    """Build combination bets from the base market map using independence."""
    prob_map = {(p.market, p.selection): p.probability for p in predictions}
    out: list[Prediction] = []
    for combo_sel, a, b in COMBINATION_BETS:
        pa = prob_map.get(("MATCH_RESULT", a)) or prob_map.get(("DOUBLE_CHANCE", a)) or prob_map.get(("BTTS", a)) or prob_map.get(("OVER_UNDER", a)) or prob_map.get(("TEAM_GOALS", a)) or prob_map.get(("CLEAN_SHEET", a))
        pb = prob_map.get(("MATCH_RESULT", b)) or prob_map.get(("DOUBLE_CHANCE", b)) or prob_map.get(("BTTS", b)) or prob_map.get(("OVER_UNDER", b)) or prob_map.get(("TEAM_GOALS", b)) or prob_map.get(("CLEAN_SHEET", b))
        if pa is None or pb is None:
            continue
        p = pa * pb
        out.append(Prediction("COMBINATION", combo_sel, p, p * 100, "combination",
                              reasons=[f"{a} × {b} (independent)"]))
    return out


def qualify_and_rank(predictions: list[Prediction], thresholds: Threshold) -> list[Prediction]:
    """Apply configurable thresholds and rank by confidence then EV."""
    threshold_for = {
        "MATCH_RESULT": thresholds.MATCH_RESULT,
        "DOUBLE_CHANCE": thresholds.DOUBLE_CHANCE,
        "COMBINATION": thresholds.COMBINATION,
    }
    qualified = []
    for p in predictions:
        t = threshold_for.get(p.market, thresholds.OTHER)
        if p.confidence >= t:
            p.status = "QUALIFIED"
            qualified.append(p)
        else:
            p.status = "REJECTED"
    qualified.sort(key=lambda p: (p.confidence, p.expected_value or 0), reverse=True)
    return qualified


def _poisson(lam: float, k: int) -> float:
    import math
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _why(outcome: str, features: dict) -> list:
    factors = [f"Model favours {outcome.lower()}"]
    if features.get("home_form") is not None:
        factors.append(f"Home form index {features['home_form']:.2f}")
    if features.get("away_form") is not None:
        factors.append(f"Away form index {features['away_form']:.2f}")
    return factors
