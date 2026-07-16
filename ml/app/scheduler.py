"""Background synchronization scheduler. Runs recurring jobs to pull data
from each provider, plus orchestrates on-demand sync/train jobs. Includes a
comprehensive health check used by GET /health.

Jobs:
  - football-data: competitions, fixtures, standings
  - api-football:   injuries, lineups, player stats
  - understat:      xG / xGA / advanced metrics
  - statsbomb:      historical event data
  - clubelo:        Elo ratings
"""

import logging
import os
import threading
from datetime import datetime

from .config import settings
from .data_manager import data_manager
from . import training
from .schemas import Competition, Season

logger = logging.getLogger("scheduler")

# Top competitions we care about (mapped to provider names)
COMPETITIONS = {
    "English Premier League": "PL",
    "La Liga": "PD",
    "Bundesliga": "BL1",
    "Serie A": "SA",
    "Ligue 1": "FL1",
    "UEFA Champions League": "CL",
}


class Scheduler:
    def __init__(self):
        self._timer = None
        self._stop = False
        self.last_run = {}

    # ---- lifecycle ----
    def start(self, interval_sec: int = 21600):
        self.interval = interval_sec
        self._stop = False
        self._schedule_next()

    def stop(self):
        self._stop = True
        if self._timer:
            self._timer.cancel()

    def _schedule_next(self):
        if self._stop:
            return
        self._timer = threading.Timer(self.interval, self._run_all)
        self._timer.daemon = True
        self._timer.start()

    def _run_all(self):
        try:
            self.run_sync_competitions(list(COMPETITIONS.keys()))
            self.run_sync_elo()
        except Exception as exc:
            logger.error("scheduled sync failed: %s", exc)
        finally:
            self._schedule_next()

    # ---- jobs ----
    def run_sync_competitions(self, competitions: list[str]):
        logger.info("Syncing competitions: %s", competitions)
        for name in competitions:
            try:
                comp = Competition(name=name, code=COMPETITIONS.get(name))
                data_manager.sync_competitions()
                season = Season(competition_name=name, name="2023/2024",
                                start_year=2023, external_id="2023")
                data_manager.sync_teams(comp, season)
                data_manager.sync_fixtures(comp, season)
                data_manager.sync_standings(comp, season)
                data_manager.sync_advanced_metrics(comp, season)
                self.last_run["competitions"] = _now()
            except Exception as exc:
                logger.error("competition sync failed for %s: %s", name, exc)
        return {"status": "done"}

    def run_sync_elo(self):
        try:
            n = data_manager.sync_elo()
            self.last_run["elo"] = _now()
            return {"status": "done", "rows": n}
        except Exception as exc:
            logger.error("elo sync failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def run_import_kaggle(self, competitions: list[str]):
        try:
            fixtures = data_manager.import_historical(competitions)
            self.last_run["kaggle"] = _now()
            return {"status": "done", "fixtures": len(fixtures)}
        except Exception as exc:
            logger.error("kaggle import failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    def run_train(self, model_name: str = "gradient_boosting",
                  competitions: list = None):
        competitions = competitions or list(COMPETITIONS.keys())
        try:
            fixtures = data_manager.import_historical(competitions)
            if not fixtures:
                return {"status": "error", "error": "no historical fixtures available"}
            result = training.train(fixtures, model_name=model_name)
            self.last_run["train"] = _now()
            return result
        except Exception as exc:
            logger.error("training failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    # ---- health ----
    def health_check(self) -> dict:
        provider_status = data_manager.provider_status()
        db_ok = self._check_db()
        model_ok = self._check_model()
        kaggle_present = self._kaggle_present()
        return {
            "status": "ok" if db_ok else "degraded",
            "timestamp": _now(),
            "providers": provider_status,
            "database": db_ok,
            "model_present": model_ok,
            "kaggle_datasets_present": kaggle_present,
            "last_run": self.last_run,
        }

    def _check_db(self) -> bool:
        try:
            db.fetch_one("SELECT 1")
            return True
        except Exception as exc:
            logger.warning("db health: %s", exc)
            return False

    def _check_model(self) -> bool:
        try:
            training.list_versions()
            return True
        except Exception:
            return False

    def _kaggle_present(self) -> bool:
        base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "kaggle")
        if not os.path.isdir(base):
            return False
        for root, _, files in os.walk(base):
            if any(f.endswith((".csv", ".json")) for f in files):
                return True
        return False


def _now():
    return datetime.utcnow().isoformat() + "Z"


scheduler = Scheduler()
